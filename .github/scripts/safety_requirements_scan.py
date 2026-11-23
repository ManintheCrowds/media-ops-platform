#!/usr/bin/env python3
"""Scan requirement files with Safety and keep going after a failure.

The security-scan job used to stop at the first non-zero ``safety check``.
Files later in sort order were never reported. This script runs every file
and returns a failure only after the full set has been scanned.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Protocol, Sequence


class CommandResult(Protocol):
    """The fields of a completed command this scanner reads."""

    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[Path], CommandResult]

_EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "node_modules",
        "venv",
    }
)


def discover_dependency_files(root: Path) -> list[Path]:
    """Return ``requirements.txt`` files under ``root``, in stable order.

    ``.git`` and local virtualenv directories are skipped. Other requirement
    names are intentionally not included yet.
    """
    found: list[Path] = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in _EXCLUDED_DIRECTORIES]
        for filename in filenames:
            if filename == "requirements.txt":
                found.append(Path(directory) / filename)
    return sorted(found, key=lambda path: path.as_posix())


def safety_check_command(python: str, requirement_file: Path) -> list[str]:
    """Build the Safety command for one requirement file."""
    return [
        python,
        "-m",
        "safety",
        "check",
        "-r",
        str(requirement_file),
        "--output",
        "text",
    ]


def run_safety_check(
    requirement_file: Path, python: str
) -> subprocess.CompletedProcess[str]:
    """Run Safety against one requirement file."""
    return subprocess.run(
        safety_check_command(python, requirement_file),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def scan_requirement_files(files: Sequence[Path], runner: Runner) -> int:
    """Scan every file. Return 1 if any scan failed, including a later file."""
    failed = False
    for path in files:
        completed = runner(path)
        print(f"===== {path.as_posix()} (exit {completed.returncode}) =====")
        sys.stdout.write(completed.stdout or "")
        sys.stderr.write(completed.stderr or "")
        if completed.returncode != 0:
            failed = True
    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Discover requirement files and scan each one."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Interpreter used to run safety.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = args.root.resolve()
    files = discover_dependency_files(root)
    return scan_requirement_files(
        files,
        lambda path: run_safety_check(path, args.python),
    )


if __name__ == "__main__":
    sys.exit(main())
