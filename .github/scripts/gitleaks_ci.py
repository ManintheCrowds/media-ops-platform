#!/usr/bin/env python3
"""Run gitleaks for pull requests and pushes.

Policy files are read with ``git show`` from the base revision (pull request)
or from ``github.event.before`` (push). The checkout's script, config, and
ignore file are not the gate.
"""

from __future__ import annotations

import bz2
import gzip
import hashlib
import io
import json
import lzma
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]
from typing import Mapping, Sequence

_EXACT_FINGERPRINT = re.compile(r"^[0-9a-f]{40}:[^:\s]+:[A-Za-z0-9_.-]+:[0-9]+$")

_ZERO_SHA = "0" * 40
# sha256 of the gitleaks binary inside the 8.30.1 linux_x64 tarball.
# The tarball itself is 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb.
GITLEAKS_SHA256 = "88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509"
# sha256 of the approved .gitleaks.toml. A policy change has to change this pin.
# Changing the pin and the config in one change is self-approving: main
# requires lint and unit-tests, and does not require a review.
APPROVED_CONFIG_SHA256 = "c46800467f8d1f3ec8019bfd0d693bb169b7fbe12ec37ae32f619289961ee6be"
# sha256 of an empty file. Main has no .gitleaksignore, so only empty is approved.
APPROVED_IGNORE_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
GITLEAKS_BINARY = Path("/usr/local/bin/gitleaks")
BOOTSTRAP_SHA = "f3559cbb2677eb72088bec7c56d541f0aa78a41e"
# Rule count in the gitleaks 8.30.1 default pack.
GITLEAKS_DEFAULT_RULES = 222
# Caps apply to each zip. Two container levels are unpacked. A zip or gzip
# nested deeper than that fails the scan instead of being skipped.
_ZIP_MEMBER_CAP = 32
_ZIP_MEMBER_BYTES = 1_048_576
_ZIP_TOTAL_BYTES = 4_194_304
_ARCHIVE_DEPTH = 2
# 8 KiB of newlines moves a tar magic at offset 257 out of the sniffer window.
_SAMPLE_PREFIX = "\n" * 8192
# The only path patterns the gate accepts in a global allowlist.
APPROVED_ALLOW_PATHS: tuple[str, ...] = (
    r"(?:^|/)poetry\.lock$",
    r"(?:^|/)package-lock\.json$",
    r".*\.png$",
    r".*\.jpg$",
    r".*\.jpeg$",
    r".*\.gif$",
)
# Repo-relative canary paths. Approved patterns must not match these.
_CANARY_RELATIVE_PATHS: tuple[str, ...] = (
    "aws-canary.txt",
    "nested/github-canary.txt",
    "nested/deep/slack-canary.txt",
)


def verified_gitleaks_binary(
    binary: Path = GITLEAKS_BINARY,
    expected_sha: str = GITLEAKS_SHA256,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Return the pinned binary. Environment overrides and PATH are ignored."""
    del environ
    if not binary.is_file():
        raise ScanError("gitleaks checksum mismatch", 2)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    if digest != expected_sha:
        raise ScanError("gitleaks checksum mismatch", 2)
    return binary


class ScanError(Exception):
    """A scan that cannot start."""

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


def _git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def require_commit(repo: Path, sha: str) -> None:
    """Fail when sha is missing, all-zero, or not a commit."""
    if not sha or set(sha) == {"0"} or sha == _ZERO_SHA:
        raise ScanError("missing revision", 2)
    probe = _git(repo, ["cat-file", "-e", f"{sha}^{{commit}}"])
    if probe.returncode != 0:
        raise ScanError("missing revision", 2)


def commit_count(repo: Path, revision_range: str) -> int:
    listed = _git(repo, ["rev-list", "--count", revision_range])
    if listed.returncode != 0:
        raise ScanError("missing revision", 2)
    return int(listed.stdout.strip() or "0")


def git_cat_blob(repo: Path, blob_sha: str) -> bytes | None:
    """Return a blob by its own id. Paths are never passed to git show."""
    shown = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "blob", blob_sha],
        check=False,
        capture_output=True,
    )
    if shown.returncode != 0:
        return None
    return shown.stdout


def git_show_bytes(repo: Path, sha: str, path: str) -> bytes | None:
    """Return a blob from sha, or None when that path is absent."""
    shown = subprocess.run(
        ["git", "-C", str(repo), "show", f"{sha}:{path}"],
        check=False,
        capture_output=True,
    )
    if shown.returncode != 0:
        return None
    return shown.stdout


def exact_ignore_text(raw: bytes) -> bytes:
    """Keep only commit:path:rule:line entries."""
    kept: list[str] = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if _EXACT_FINGERPRINT.fullmatch(stripped):
            kept.append(stripped)
    if not kept:
        return b""
    return ("\n".join(kept) + "\n").encode("utf-8")


def policy_config_bytes(repo: Path, sha: str) -> bytes | None:
    """Return the config for sha.

    The one known base that has no scan script also has a config with no
    rules. For that revision only, the checkout config is the policy so the
    self-check can run. Every other revision is read with git show.
    """
    if sha == BOOTSTRAP_SHA:
        checkout = repo / ".gitleaks.toml"
        if checkout.is_file():
            return checkout.read_bytes()
    return git_show_bytes(repo, sha, ".gitleaks.toml")


def materialize_policy(repo: Path, sha: str, dest: Path) -> tuple[Path, Path]:
    """Write the config and ignore file from sha into dest.

    The ignore file is whatever that revision stored. A missing ignore file
    becomes an empty file so the checkout's ignore file is not a fallback.
    """
    require_commit(repo, sha)
    dest.mkdir(parents=True, exist_ok=True)
    config_bytes = policy_config_bytes(repo, sha)
    if config_bytes is None:
        raise ScanError("missing revision", 2)
    config = dest / ".gitleaks.toml"
    config.write_bytes(config_bytes)
    ignore = dest / ".gitleaksignore"
    ignore_bytes = git_show_bytes(repo, sha, ".gitleaksignore")
    ignore.write_bytes(b"" if ignore_bytes is None else exact_ignore_text(ignore_bytes))
    return config, ignore


def revision_log_opts(base: str, head: str) -> str:
    """Git log options for one first-parent range. ``--all`` is refused."""
    opts = f"--diff-merges=first-parent --text {base}..{head}"
    if "--all" in opts.split():
        raise ScanError("refusing --all", 2)
    return opts


def gitleaks_command(
    gitleaks: str,
    source: Path,
    config: Path,
    ignore: Path,
    log_opts: str,
) -> list[str]:
    """Build the gitleaks invocation. Secrets stay redacted."""
    if "--all" in log_opts.split():
        raise ScanError("refusing --all", 2)
    return [
        gitleaks,
        "detect",
        "--source",
        str(source),
        "--config",
        str(config),
        "--gitleaks-ignore-path",
        str(ignore),
        "--log-opts",
        log_opts,
        "--ignore-gitleaks-allow",
        "--redact",
        "--no-banner",
        "--no-color",
        "--exit-code",
        "1",
    ]


def _run_gitleaks(source: Path, command: list[str], ignore: Path) -> int:
    """Run gitleaks without also reading the checkout's ignore file.

    Gitleaks loads ``source/.gitleaksignore`` even when ``--gitleaks-ignore-path``
    points somewhere else. Move that checkout file aside for the scan.
    """
    source_ignore = source / ".gitleaksignore"
    held: Path | None = None
    if source_ignore.is_file() and source_ignore.resolve() != ignore.resolve():
        held = source / ".gitleaksignore.held"
        source_ignore.replace(held)
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        return completed.returncode
    finally:
        if held is not None and held.is_file():
            held.replace(source_ignore)


def _policy_failure() -> ScanError:
    return ScanError("policy canary failed", 2)


def _lower_keys(value: object) -> object:
    """Lowercase TOML keys so viper's case-insensitive names cannot sneak through."""
    if isinstance(value, dict):
        return {str(key).lower(): _lower_keys(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_lower_keys(item) for item in value]
    return value


def _as_tables(raw: object) -> list[dict[str, object]]:
    if raw is None:
        return []
    tables = raw if isinstance(raw, list) else [raw]
    parsed: list[dict[str, object]] = []
    for table in tables:
        if not isinstance(table, dict):
            raise _policy_failure()
        parsed.append(table)
    return parsed


def _paths_match_canary(patterns: Sequence[str]) -> bool:
    for pattern in patterns:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise _policy_failure() from exc
        for relative in _CANARY_RELATIVE_PATHS:
            if compiled.search(relative):
                return True
    return False


def validate_policy_config(config: Path) -> None:
    """Check a few structural fields. The sha256 pin is the authoritative gate.

    ``assert_approved_config`` runs first, inside ``assert_policy_canaries``.
    This walk checks ``useDefault``, a single path allowlist, and some
    forbidden keys. With the pin absent it still accepts weakened shapes,
    including disabled rules hidden from this walk, extra allowlists, and
    path patterns this function does not treat as a canary match.
    """
    try:
        parsed = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise _policy_failure() from exc
    if not isinstance(parsed, dict):
        raise _policy_failure()
    data = _lower_keys(parsed)
    if not isinstance(data, dict):
        raise _policy_failure()
    extend = data.get("extend")
    if not isinstance(extend, dict) or extend.get("usedefault") is not True:
        raise _policy_failure()
    if set(extend) != {"usedefault"}:
        raise _policy_failure()
    if "disabledrules" in data:
        raise _policy_failure()
    tables = _as_tables(data.get("allowlist")) + _as_tables(data.get("allowlists"))
    if len(tables) != 1:
        raise _policy_failure()
    allow = tables[0]
    if set(allow) - {"description", "paths"}:
        raise _policy_failure()
    paths = allow.get("paths")
    if not isinstance(paths, list) or [str(item) for item in paths] != list(
        APPROVED_ALLOW_PATHS
    ):
        raise _policy_failure()
    if _paths_match_canary([str(item) for item in paths]):
        raise _policy_failure()
    rules = data.get("rules", [])
    if rules is None:
        rules = []
    if not isinstance(rules, list):
        raise _policy_failure()
    for rule in rules:
        if not isinstance(rule, dict):
            raise _policy_failure()
        if "allowlist" in rule or "allowlists" in rule:
            raise _policy_failure()


def _mkdir_nofollow(root: Path, relative: Path) -> None:
    cursor = root
    for part in relative.parts:
        if part in {"", ".", ".."}:
            raise _policy_failure()
        cursor = cursor / part
        if cursor.is_symlink():
            raise _policy_failure()
        if not cursor.exists():
            cursor.mkdir()
        elif not cursor.is_dir():
            raise _policy_failure()


def _write_nofollow(root: Path, relative: str, content: str) -> None:
    """Write ``content`` under ``root`` and refuse to follow a symlink."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise _policy_failure()
    _mkdir_nofollow(root, path.parent)
    destination = root.joinpath(*path.parts)
    if destination.is_symlink() or destination.exists():
        raise _policy_failure()
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)


def _clean_git_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("GIT_", "PYTHON", "LD_"))
    }
    env["PATH"] = "/usr/bin:/bin"
    env["HOME"] = os.environ.get("HOME", "/tmp")
    env["GIT_AUTHOR_NAME"] = "canary"
    env["GIT_AUTHOR_EMAIL"] = "canary@example.invalid"
    env["GIT_COMMITTER_NAME"] = "canary"
    env["GIT_COMMITTER_EMAIL"] = "canary@example.invalid"
    return env


def _git_clean(repo: Path, args: Sequence[str]) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        env=_clean_git_env(),
    )
    if completed.returncode != 0:
        raise _policy_failure()


def _canary_lines() -> dict[str, str]:
    aws = "AKIA" + "".join(["M7NP", "Q2RS", "T4VW", "X5YZ"])
    pat = "ghp_" + "".join(
        ["Ab3Cd", "Ef7Gh", "Jk2Lm", "Np5Qr", "St8Vw", "Xy1Za", "Bc4De", "F"]
    )
    slack = "".join(
        ["xoxb-", "2468013579", "-", "135792468013", "-", "Ab9Cd8Ef7Gh6Ij5Kl4Mn3"]
    )
    values = (aws, pat, slack)
    lines = {
        relative: f'key = "{value}"\n'
        for relative, value in zip(_CANARY_RELATIVE_PATHS, values, strict=True)
    }
    return lines


def assert_approved_ignore(ignore: Path) -> None:
    """Fail unless the materialized ignore file is empty.

    An ignore line for a commit that is not on the gate revision can hide
    that commit after a side-first merge. Main ships no ignore file.
    """
    digest = hashlib.sha256(ignore.read_bytes()).hexdigest()
    if digest != APPROVED_IGNORE_SHA256:
        raise _policy_failure()


def assert_approved_config(config: Path) -> None:
    """Fail unless the materialized config is the pinned approved file.

    The bootstrap base reads the checkout file. That file has to be this
    exact document too. Any other bytes fail closed.
    """
    digest = hashlib.sha256(config.read_bytes()).hexdigest()
    if digest != APPROVED_CONFIG_SHA256:
        raise _policy_failure()


def assert_policy_canaries(gitleaks: str, config: Path, repo: Path) -> None:
    """Fail unless the materialized config still matches the approved policy.

    Canaries are written at repo-relative paths in an empty temp git tree.
    The checkout's directories are not copied, so a directory at a canary
    path cannot fail the self-check. Nothing is written into ``repo``.
    """
    assert_approved_config(config)
    validate_policy_config(config)
    if _paths_match_canary(APPROVED_ALLOW_PATHS):
        raise _policy_failure()
    parent = Path(tempfile.mkdtemp(prefix="gitleaks-canary-"))
    try:
        if parent.resolve() == repo.resolve() or repo.resolve() in parent.resolve().parents:
            raise _policy_failure()
        if parent.resolve() in repo.resolve().parents:
            raise _policy_failure()
        empty = parent / "empty"
        empty.mkdir()
        sarif = parent / "rules.sarif"
        counted = subprocess.run(
            [
                gitleaks,
                "detect",
                "--no-git",
                "--source",
                str(empty),
                "--config",
                str(config),
                "--redact",
                "--no-banner",
                "--report-format",
                "sarif",
                "--report-path",
                str(sarif),
                "--exit-code",
                "0",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if counted.returncode != 0 or not sarif.is_file():
            raise _policy_failure()
        rules = (
            json.loads(sarif.read_text(encoding="utf-8"))["runs"][0]["tool"]["driver"].get(
                "rules"
            )
            or []
        )
        if len(rules) != GITLEAKS_DEFAULT_RULES:
            raise _policy_failure()
        source = parent / "src"
        source.mkdir()
        _git_clean(source, ["init", "-q"])
        lines = _canary_lines()
        for relative, content in lines.items():
            _write_nofollow(source, relative, content)
            _git_clean(source, ["add", "--", relative])
        _git_clean(source, ["commit", "-q", "-m", "canary"])
        report = parent / "canary.json"
        scanned = subprocess.run(
            [
                gitleaks,
                "detect",
                "--source",
                str(source),
                "--config",
                str(config),
                "--redact",
                "--no-banner",
                "--report-format",
                "json",
                "--report-path",
                str(report),
                "--exit-code",
                "0",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=_clean_git_env(),
        )
        if not report.is_file():
            raise _policy_failure()
        found = json.loads(report.read_text(encoding="utf-8") or "[]")
        rule_ids = {item.get("RuleID") for item in found}
        required = {"aws-access-token", "github-pat", "slack-bot-token"}
        secrets = [line.split('"', 2)[1] for line in lines.values()]
        leaked = any(
            secret in scanned.stdout or secret in scanned.stderr for secret in secrets
        )
        if not required <= rule_ids or leaked:
            raise _policy_failure()
    finally:
        shutil.rmtree(parent, ignore_errors=True)


# Path patterns from the gitleaks 8.30.1 default allowlist. useDefault merges
# these with the repo allowlist, so the main scan never opens the blobs.
_DEFAULT_ALLOW_PATHS: tuple[str, ...] = (
    r"gitleaks\.toml",
    r"(?i)\.(?:bmp|gif|jpe?g|png|svg|tiff?)$",
    r"(?i)\.(?:eot|[ot]tf|woff2?)$",
    r"(?i)\.(?:docx?|xlsx?|pdf|bin|socket|vsidx|v2|suo|wsuo|.dll|pdb|exe|gltf)$",
    r"go\.(?:mod|sum|work(?:\.sum)?)$",
    r"(?:^|/)vendor/modules\.txt$",
    r"(?:^|/)vendor/(?:github\.com|golang\.org/x|google\.golang\.org|gopkg\.in|"
    r"istio\.io|k8s\.io|sigs\.k8s\.io)(?:/.*)?$",
    r"(?:^|/)gradlew(?:\.bat)?$",
    r"(?:^|/)gradle\.lockfile$",
    r"(?:^|/)mvnw(?:\.cmd)?$",
    r"(?:^|/)\.mvn/wrapper/MavenWrapperDownloader\.java$",
    r"(?:^|/)node_modules(?:/.*)?$",
    r"(?:^|/)(?:deno\.lock|npm-shrinkwrap\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock)$",
    r"(?:^|/)bower_components(?:/.*)?$",
    r"(?:^|/)(?:angular|bootstrap|jquery(?:-?ui)?|plotly|swagger-?ui)[a-zA-Z0-9.-]*(?:\.min)?\.js(?:\.map)?$",
    r"(?:^|/)javascript\.json$",
    r"(?:^|/)(?:Pipfile|poetry)\.lock$",
    r"(?i)(?:^|/)(?:v?env|virtualenv)/lib(?:64)?(?:/.*)?$",
    r"(?i)(?:^|/)(?:lib(?:64)?/python[23](?:\.\d{1,2})+|python/[23](?:\.\d{1,2})+/lib(?:64)?)(?:/.*)?$",
    r"(?i)(?:^|/)[a-z0-9_.]+-[0-9.]+\.dist-info(?:/.+)?$",
    r"(?:^|/)vendor/(?:bundle|ruby)(?:/.*?)?$",
    r"\.gem$",
    r"verification-metadata\.xml",
    r"Database.refactorlog",
    r"(?:^|/)\.git$",
)
_LOCKFILE_NAMES = frozenset(
    {
        "poetry.lock",
        "package-lock.json",
        "go.sum",
        "go.work.sum",
        "yarn.lock",
        "pnpm-lock.yaml",
        "npm-shrinkwrap.json",
        "cargo.lock",
        "composer.lock",
        "gemfile.lock",
        "packages.lock.json",
        "gradle.lockfile",
        "pipfile.lock",
        "deno.lock",
    }
)


def _is_lockfile(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    return name in _LOCKFILE_NAMES or name.endswith(".lock")


def _configured_allow_paths(config: Path) -> list[str]:
    try:
        parsed = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        return []
    lowered = _lower_keys(parsed)
    if not isinstance(lowered, dict):
        return []
    found: list[str] = []
    for key in ("allowlist", "allowlists"):
        try:
            tables = _as_tables(lowered.get(key))
        except ScanError:
            continue
        for table in tables:
            paths = table.get("paths")
            if isinstance(paths, list):
                found.extend(str(item) for item in paths)
    return found


def _allowlisted(path: str, extra: Sequence[str]) -> bool:
    for pattern in (*_DEFAULT_ALLOW_PATHS, *extra):
        try:
            matched = re.search(pattern, path) is not None
        except re.error:
            continue
        if matched:
            return True
    return False


def _opaque(path: str, blob: bytes, allow_paths: Sequence[str] = ()) -> bool:
    """True when the git diff would skip a blob the prescan still has to read.

    Allowlisted names are always read. Image magic and high-byte padding do
    not hide a following plaintext token.
    """
    if _is_lockfile(path):
        return True
    if path.startswith("node_modules/") or "/node_modules/" in path:
        return True
    if path.endswith((".svg", ".map", ".pdf", ".min.js")):
        return True
    if blob.startswith((b"\xff\xfe", b"\xfe\xff", b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
        return True
    if b"\x00" in blob:
        return True
    if _allowlisted(path, allow_paths):
        return True
    return False


def _decode_opaque(blob: bytes) -> str:
    """Decode UTF-8, UTF-16, and UTF-32, including big-endian text with no BOM.

    NUL-stripping keeps an ASCII secret when the width-specific decode is the
    wrong endianness. Every candidate is scanned.
    """
    decoded: dict[str, None] = {}
    for encoding in (
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "utf-32",
        "utf-32-le",
        "utf-32-be",
    ):
        text = blob.decode(encoding, errors="ignore")
        if text:
            decoded.setdefault(text, None)
    stripped = blob.replace(b"\x00", b"").decode("utf-8", errors="ignore")
    if stripped:
        decoded.setdefault(stripped, None)
    return "\n".join(decoded)


def _parse_diff_tree(raw: bytes) -> list[tuple[str, str]]:
    """Return ``(blob_sha, path)`` from ``git diff-tree -z --raw``.

    A path is whatever follows the header, including a 40-hex name or a
    name that itself starts with ``:``. Anything that is not a raw header
    fails the scan.
    """
    parts = raw.split(b"\x00")
    if parts and parts[-1] == b"":
        parts.pop()
    blobs: list[tuple[str, str]] = []
    index = 0
    while index < len(parts):
        header = parts[index]
        index += 1
        try:
            text = header.decode("ascii")
        except UnicodeError as exc:
            raise ScanError("prescan failed", 1) from exc
        fields = text.split(" ")
        if len(fields) != 5 or not fields[0].startswith(":"):
            raise ScanError("prescan failed", 1)
        _old_mode, _new_mode, old_sha, new_sha, status = fields
        if len(old_sha) != 40 or len(new_sha) != 40:
            raise ScanError("prescan failed", 1)
        hex_digits = set("0123456789abcdef")
        if set(old_sha) > hex_digits or set(new_sha) > hex_digits:
            raise ScanError("prescan failed", 1)
        kind = status[:1]
        if kind not in "AMTRC" or (len(status) > 1 and not status[1:].isdigit()):
            raise ScanError("prescan failed", 1)
        if index >= len(parts):
            raise ScanError("prescan failed", 1)
        path = parts[index]
        index += 1
        if kind in "RC":
            if index >= len(parts):
                raise ScanError("prescan failed", 1)
            path = parts[index]
            index += 1
        if not path:
            raise ScanError("prescan failed", 1)
        blobs.append((new_sha, path.decode("utf-8", "surrogateescape")))
    return blobs


def _blobs_in_range(repo: Path, base: str, head: str) -> list[tuple[str, str]]:
    """Return ``(blob_sha, path)`` for added, modified, renamed, and type changes.

    Each commit is listed with ``git rev-list`` and then
    ``git diff-tree -r -z -m --first-parent -M --raw --diff-filter=AMRT``.
    Paths are never guessed from a 40-hex string.
    """
    listed = subprocess.run(
        ["git", "-C", str(repo), "rev-list", "--reverse", f"{base}..{head}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if listed.returncode != 0:
        raise ScanError("missing revision", 2)
    pairs: list[tuple[str, str]] = []
    for commit in listed.stdout.split():
        shown = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "diff-tree",
                "-r",
                "-z",
                "-m",
                "--first-parent",
                "-M",
                "--raw",
                "--diff-filter=AMRT",
                "--no-commit-id",
                commit,
            ],
            check=False,
            capture_output=True,
        )
        if shown.returncode != 0:
            raise ScanError("prescan failed", 2)
        pairs.extend(_parse_diff_tree(shown.stdout))
    return pairs


def _read_zip_members(archive: zipfile.ZipFile) -> list[bytes]:
    """Read one zip. Caps and an unreadable member fail the scan."""
    members: list[bytes] = []
    total = 0
    seen = 0
    for info in archive.infolist():
        if info.is_dir():
            continue
        seen += 1
        if seen > _ZIP_MEMBER_CAP:
            raise ScanError("prescan failed", 1)
        if info.file_size > _ZIP_MEMBER_BYTES or total >= _ZIP_TOTAL_BYTES:
            raise ScanError("prescan failed", 1)
        try:
            with archive.open(info, "r") as handle:
                data = handle.read(_ZIP_MEMBER_BYTES + 1)
        except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
            raise ScanError("prescan failed", 1) from exc
        if len(data) > _ZIP_MEMBER_BYTES or total + len(data) > _ZIP_TOTAL_BYTES:
            raise ScanError("prescan failed", 1)
        total += len(data)
        members.append(data)
    return members


def _open_zip(blob: bytes) -> zipfile.ZipFile | None:
    """Open a zip whose local header is anywhere in the blob."""
    if b"PK\x03\x04" not in blob and b"PK\x05\x06" not in blob:
        return None
    try:
        return zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile as exc:
        if blob.startswith(b"PK\x03\x04"):
            raise ScanError("prescan failed", 1) from exc
        return None


def _read_capped(blob: bytes, opener: type) -> bytes:
    """Read one compressed stream, stopping at the per-member cap."""
    try:
        with opener(io.BytesIO(blob)) as handle:
            data = handle.read(_ZIP_MEMBER_BYTES + 1)
    except (OSError, EOFError, lzma.LZMAError) as exc:
        raise ScanError("prescan failed", 1) from exc
    if len(data) > _ZIP_MEMBER_BYTES:
        raise ScanError("prescan failed", 1)
    return data


def _read_xz(blob: bytes) -> bytes:
    """Decompress one xz stream."""
    return _read_capped(blob, lzma.LZMAFile)


def _read_bz2(blob: bytes) -> bytes:
    """Decompress one bzip2 stream."""
    return _read_capped(blob, bz2.BZ2File)


def _read_gzip(blob: bytes) -> bytes:
    """Decompress one gzip member. A short or unreadable stream fails the scan."""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(blob)) as handle:
            data = handle.read(_ZIP_MEMBER_BYTES + 1)
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise ScanError("prescan failed", 1) from exc
    if len(data) > _ZIP_MEMBER_BYTES:
        raise ScanError("prescan failed", 1)
    return data


def _container_payloads(blob: bytes, depth: int) -> list[bytes]:
    """Unpack zip, gzip, xz, and bzip2 payloads down to a fixed depth.

    ``depth`` is how many containers have already been opened. A container
    past ``_ARCHIVE_DEPTH`` fails the scan.
    """
    archive = _open_zip(blob)
    stream = _stream_reader(blob)
    if depth >= _ARCHIVE_DEPTH and (archive is not None or stream is not None):
        if archive is not None:
            archive.close()
        raise ScanError("prescan failed", 1)
    if depth >= _ARCHIVE_DEPTH:
        return []
    payloads: list[bytes] = []
    if archive is not None:
        try:
            for member in _read_zip_members(archive):
                payloads.append(member)
                payloads.extend(_container_payloads(member, depth + 1))
        finally:
            archive.close()
    if stream is not None:
        data = stream(blob)
        payloads.append(data)
        payloads.extend(_container_payloads(data, depth + 1))
    return payloads


def _stream_reader(blob: bytes):
    """Return the decompressor for a stream that starts at byte 0."""
    if blob.startswith(b"\xfd7zXZ\x00"):
        return _read_xz
    if blob.startswith(b"BZh"):
        return _read_bz2
    if blob.startswith(b"\x1f\x8b"):
        return _read_gzip
    return None


def _scan_sample(parent: Path, gitleaks: str, config: Path, text: str) -> int:
    """Scan decoded text. A long blank prefix keeps tar and archive sniffers off byte 0."""
    sample = parent / "sample.txt"
    sample.write_text(_SAMPLE_PREFIX + text, encoding="utf-8")
    report = parent / "report.json"
    scanned = subprocess.run(
        [
            gitleaks,
            "detect",
            "--no-git",
            "--source",
            str(parent),
            "--config",
            str(config),
            "--ignore-gitleaks-allow",
            "--redact",
            "--no-banner",
            "--report-format",
            "json",
            "--report-path",
            str(report),
            "--exit-code",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if scanned.returncode != 0:
        raise ScanError("prescan failed", 2)
    findings = json.loads(report.read_text(encoding="utf-8") or "[]")
    return 1 if findings else 0


def prescan_opaque_files(
    repo: Path, base: str, head: str, gitleaks: str, config: Path
) -> int:
    """Scan UTF-16, NUL, and allowlisted-extension text the git diff would skip."""
    blobs = _blobs_in_range(repo, base, head)
    allow_paths = _configured_allow_paths(config)
    parent = Path(tempfile.mkdtemp(prefix="gitleaks-opaque-"))
    try:
        for blob_sha, path in blobs:
            blob = git_cat_blob(repo, blob_sha)
            if blob is None:
                raise ScanError("prescan failed", 2)
            members = _container_payloads(blob, 0)
            if not _opaque(path, blob, allow_paths) and not members:
                continue
            texts = [_decode_opaque(blob)]
            texts.extend(_decode_opaque(member) for member in members)
            for text in texts:
                if text and _scan_sample(parent, gitleaks, config, text) != 0:
                    return 1
        return 0
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def _scan_range(repo: Path, policy_sha: str, head: str, gitleaks: str) -> int:
    require_commit(repo, head)
    if commit_count(repo, f"{policy_sha}..{head}") == 0:
        raise ScanError("empty range", 3)
    parent = Path(tempfile.mkdtemp(prefix="gitleaks-policy-"))
    try:
        config, ignore = materialize_policy(repo, policy_sha, parent)
        assert_approved_ignore(ignore)
        assert_policy_canaries(gitleaks, config, repo)
        if prescan_opaque_files(repo, policy_sha, head, gitleaks, config) != 0:
            return 1
        command = gitleaks_command(
            gitleaks,
            repo,
            config,
            ignore,
            revision_log_opts(policy_sha, head),
        )
        return _run_gitleaks(repo, command, ignore)
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def run_pull_request_scan(repo: Path, base: str, head: str, gitleaks: str) -> int:
    """Scan base..head with the base revision's config and ignore file."""
    require_commit(repo, base)
    return _scan_range(repo, base, head, gitleaks)


def run_push_scan(repo: Path, before: str, sha: str, gitleaks: str) -> int:
    """Scan before..sha with the parent revision's config and ignore file.

    An all-zero or unfetchable ``before`` fails closed. The pushed commit's
    policy files are never read.
    """
    if not before or before == _ZERO_SHA or set(before) == {"0"}:
        raise ScanError("missing revision", 2)
    require_commit(repo, before)
    return _scan_range(repo, before, sha, gitleaks)


def main() -> int:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    repo = Path.cwd()
    gitleaks = str(verified_gitleaks_binary())
    try:
        if event == "pull_request":
            return run_pull_request_scan(
                repo,
                os.environ.get("PR_BASE_SHA", ""),
                os.environ.get("PR_HEAD_SHA", ""),
                gitleaks,
            )
        if event == "push":
            return run_push_scan(
                repo,
                os.environ.get("PUSH_BEFORE", ""),
                os.environ.get("PUSH_SHA", ""),
                gitleaks,
            )
    except ScanError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    print("unsupported event", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
