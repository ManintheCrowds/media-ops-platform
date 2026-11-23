#!/usr/bin/env python3
"""Run gitleaks for pull requests and pushes.

Policy files are read with ``git show`` from the base revision (pull request)
or from ``github.event.before`` (push). The checkout's script, config, and
ignore file are not the gate.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Mapping, Sequence

_EXACT_FINGERPRINT = re.compile(r"^[0-9a-f]{40}:[^:\s]+:[A-Za-z0-9_.-]+:[0-9]+$")

_ZERO_SHA = "0" * 40
# sha256 of the gitleaks binary inside the 8.30.1 linux_x64 tarball.
# The tarball itself is 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb.
GITLEAKS_SHA256 = "88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509"
GITLEAKS_BINARY = Path("/usr/local/bin/gitleaks")
BOOTSTRAP_SHA = "f3559cbb2677eb72088bec7c56d541f0aa78a41e"
# Rule count in the gitleaks 8.30.1 default pack.
GITLEAKS_DEFAULT_RULES = 222
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
    """Reject a config that weakens the default pack or widens the allowlist.

    ``[extend]`` must set ``useDefault = true`` and nothing else: no
    ``disabledRules``, and no ``path`` or ``url``. The only global allowlist
    is the approved path list. Regexes, ``regexTarget``, stopwords, commits,
    and per-rule allowlists are rejected, including a path pattern that would
    match a canary's repo-relative path.
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


def _mirror_relative_dirs(repo: Path, dest: Path) -> None:
    """Recreate the checkout's directories in ``dest`` without following links."""
    listed = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z", "-s"],
        check=False,
        capture_output=True,
        env=_clean_git_env(),
    )
    if listed.returncode != 0:
        raise _policy_failure()
    for record in listed.stdout.split(b"\x00"):
        if not record:
            continue
        mode, _, rest = record.partition(b" ")
        if mode == b"120000":
            continue
        tab = rest.find(b"\t")
        if tab < 0:
            continue
        relative = rest[tab + 1 :].decode("utf-8", "surrogateescape")
        parent = Path(relative).parent
        if parent.parts and parent.parts != (".",):
            _mkdir_nofollow(dest, parent)


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


def assert_policy_canaries(gitleaks: str, config: Path, repo: Path) -> None:
    """Fail unless the materialized config still matches the approved policy.

    Canaries are written at repo-relative paths in a separate temp git tree
    with the same directory layout. Nothing is written into ``repo``, and
    symlinks are not followed.
    """
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
        _mirror_relative_dirs(repo, source)
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


def _image_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith((".png", ".gif", ".jpg", ".jpeg"))


def _has_image_magic(blob: bytes) -> bool:
    return blob.startswith((b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"\xff\xd8\xff"))


def _text_like(blob: bytes) -> bool:
    sample = blob[:8192].replace(b"\x00", b"")
    if not sample:
        return False
    printable = sum(byte in (9, 10, 13) or 32 <= byte < 127 for byte in sample)
    return printable / len(sample) >= 0.85


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

    Real PNG, GIF, and JPEG bytes keep the allowlist. Text in an image name,
    a font name, or a lockfile does not.
    """
    if _image_path(path) and _has_image_magic(blob):
        return False
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
    if _allowlisted(path, allow_paths) and _text_like(blob):
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


def _blobs_in_range(repo: Path, base: str, head: str) -> list[tuple[str, str]]:
    """Return ``(commit, path)`` for every added, modified, or renamed blob.

    ``git log --format=`` drops the commit id, so the format is ``%H`` and the
    other flags are ``--name-only --diff-filter=AMR -z``. A rename contributes
    the path that exists in that commit.
    """
    listed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "log",
            "--reverse",
            "--format=%H",
            "--name-only",
            "--diff-filter=AMR",
            "-z",
            f"{base}..{head}",
        ],
        check=False,
        capture_output=True,
    )
    if listed.returncode != 0:
        raise ScanError("missing revision", 2)
    pairs: list[tuple[str, str]] = []
    commit: str | None = None
    for part in listed.stdout.split(b"\x00"):
        if part.startswith(b"\n"):
            part = part[1:]
        if not part:
            continue
        text = part.decode("utf-8", "surrogateescape")
        if len(text) == 40 and set(text) <= set("0123456789abcdef"):
            commit = text
            continue
        if commit is None:
            raise ScanError("prescan failed", 2)
        pairs.append((commit, text))
    return pairs


def prescan_opaque_files(
    repo: Path, base: str, head: str, gitleaks: str, config: Path
) -> int:
    """Scan UTF-16, NUL, and allowlisted-extension text the git diff would skip."""
    blobs = _blobs_in_range(repo, base, head)
    allow_paths = _configured_allow_paths(config)
    parent = Path(tempfile.mkdtemp(prefix="gitleaks-opaque-"))
    try:
        for commit, path in blobs:
            blob = git_show_bytes(repo, commit, path)
            if blob is None:
                raise ScanError("prescan failed", 2)
            if not _opaque(path, blob, allow_paths):
                continue
            text = _decode_opaque(blob)
            sample = parent / "sample.txt"
            sample.write_text(text, encoding="utf-8")
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
            if findings:
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
