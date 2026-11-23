#!/usr/bin/env python3
"""Run gitleaks for pull requests and pushes.

Policy files are read with ``git show`` from the base revision (pull request)
or from ``github.event.before`` (push). The checkout's script, config, and
ignore file are not the gate.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

_EXACT_FINGERPRINT = re.compile(r"^[0-9a-f]{40}:[^:\s]+:[A-Za-z0-9_.-]+:[0-9]+$")

_ZERO_SHA = "0" * 40


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


def materialize_policy(repo: Path, sha: str, dest: Path) -> tuple[Path, Path]:
    """Write the config and ignore file from sha into dest.

    The ignore file is whatever that revision stored. A missing ignore file
    becomes an empty file so the checkout's ignore file is not a fallback.
    """
    require_commit(repo, sha)
    dest.mkdir(parents=True, exist_ok=True)
    config_bytes = git_show_bytes(repo, sha, ".gitleaks.toml")
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


def _scan_range(repo: Path, policy_sha: str, head: str, gitleaks: str) -> int:
    require_commit(repo, head)
    if commit_count(repo, f"{policy_sha}..{head}") == 0:
        raise ScanError("empty range", 3)
    parent = Path(tempfile.mkdtemp(prefix="gitleaks-policy-"))
    try:
        config, ignore = materialize_policy(repo, policy_sha, parent)
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
    gitleaks = os.environ.get("GITLEAKS_BIN", "gitleaks")
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
