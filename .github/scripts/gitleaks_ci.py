#!/usr/bin/env python3
"""Run gitleaks for pull requests and pushes.

On pull_request the config and ignore file come from a worktree of the base
SHA. The scan uses that base, ``--ignore-gitleaks-allow``, and fails when the
base or head revision is missing or the commit range is empty.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

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
    """Fail when sha is missing or not a commit."""
    if not sha or sha == _ZERO_SHA:
        raise ScanError("missing revision", 2)
    probe = _git(repo, ["cat-file", "-e", f"{sha}^{{commit}}"])
    if probe.returncode != 0:
        raise ScanError("missing revision", 2)


def commit_count(repo: Path, revision_range: str) -> int:
    listed = _git(repo, ["rev-list", "--count", revision_range])
    if listed.returncode != 0:
        raise ScanError("missing revision", 2)
    return int(listed.stdout.strip() or "0")


def _ignore_file(worktree: Path) -> Path:
    ignore = worktree / ".gitleaksignore"
    if not ignore.is_file():
        ignore.write_text("", encoding="utf-8")
    return ignore


def _run_gitleaks(
    source: Path,
    command: list[str],
    ignore: Path,
) -> int:
    """Run gitleaks without also reading the checkout's ignore file.

    Gitleaks loads ``source/.gitleaksignore`` even when ``--gitleaks-ignore-path``
    points somewhere else. A pull request can add fingerprints there. Move that
    file aside so only the supplied ignore file is used.
    """
    source_ignore = source / ".gitleaksignore"
    held: Path | None = None
    if source_ignore.is_file() and source_ignore.resolve() != ignore.resolve():
        held = source / ".gitleaksignore.held"
        source_ignore.replace(held)
    try:
        completed = subprocess.run(command, check=False)
        return completed.returncode
    finally:
        if held is not None and held.is_file():
            held.replace(source_ignore)


def gitleaks_command(
    gitleaks: str,
    source: Path,
    config: Path,
    ignore: Path,
    log_opts: str,
) -> list[str]:
    """Build the gitleaks invocation. Secrets stay redacted."""
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


def run_pull_request_scan(repo: Path, base: str, head: str, gitleaks: str) -> int:
    """Scan base..head using the base revision's config and ignore file."""
    require_commit(repo, base)
    require_commit(repo, head)
    if commit_count(repo, f"{base}..{head}") == 0:
        raise ScanError("empty range", 3)
    parent = Path(tempfile.mkdtemp(prefix="gitleaks-base-"))
    worktree = parent / "base"
    added = _git(repo, ["worktree", "add", "--detach", str(worktree), base])
    if added.returncode != 0:
        shutil.rmtree(parent, ignore_errors=True)
        raise ScanError("missing revision", 2)
    try:
        config = worktree / ".gitleaks.toml"
        if not config.is_file():
            raise ScanError("missing revision", 2)
        command = gitleaks_command(
            gitleaks,
            repo,
            config,
            _ignore_file(worktree),
            f"{base}..{head}",
        )
        return _run_gitleaks(repo, command, _ignore_file(worktree))
    finally:
        _git(repo, ["worktree", "remove", "--force", str(worktree)])
        shutil.rmtree(parent, ignore_errors=True)


def run_push_scan(repo: Path, before: str, sha: str, gitleaks: str) -> int:
    """Scan a push range with the checked-out config."""
    require_commit(repo, sha)
    if not before or before == _ZERO_SHA:
        log_opts = "-1"
    else:
        require_commit(repo, before)
        if commit_count(repo, f"{before}..{sha}") == 0:
            raise ScanError("empty range", 3)
        log_opts = f"{before}..{sha}"
    config = repo / ".gitleaks.toml"
    if not config.is_file():
        raise ScanError("missing revision", 2)
    if (repo / ".gitleaksignore").is_file():
        command = gitleaks_command(gitleaks, repo, config, _ignore_file(repo), log_opts)
        return _run_gitleaks(repo, command, repo / ".gitleaksignore")
    with tempfile.TemporaryDirectory(prefix="gitleaks-ignore-") as empty:
        ignore = Path(empty) / ".gitleaksignore"
        ignore.write_text("", encoding="utf-8")
        command = gitleaks_command(gitleaks, repo, config, ignore, log_opts)
        return _run_gitleaks(repo, command, ignore)


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
