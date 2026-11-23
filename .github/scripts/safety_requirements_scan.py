#!/usr/bin/env python3
"""Scan dependency files with Safety and fail closed on gaps.

The security-scan job runs this script. It scans every discovered file before
it fails, treats an empty discovery list as a failure, and reports unpinned
requirements instead of letting Safety skip them.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, Sequence


class CommandResult(Protocol):
    """The fields of a completed command this scanner reads."""

    returncode: int
    stdout: str
    stderr: str


class SetupRequirementsError(ValueError):
    """setup.py dependencies could not be read without executing the file."""


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
_REQUIREMENT_FILENAME = re.compile(r"^(requirements.*|constraints.*)\.txt$")
_LOCK_FILENAMES = frozenset(
    {
        "Pipfile.lock",
        "pdm.lock",
        "poetry.lock",
        "pylock.toml",
        "uv.lock",
    }
)
_REQUIREMENT_NAME = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?P<extras>\[[^\]]*\])?\s*(?P<spec>.*)$"
)
_DIRECTIVE_OPTIONS = frozenset(
    {
        "-c",
        "-f",
        "-r",
        "--constraint",
        "--extra-index-url",
        "--find-links",
        "--index-url",
        "--no-binary",
        "--no-index",
        "--only-binary",
        "--prefer-binary",
        "--requirement",
        "--trusted-host",
    }
)


@dataclass(frozen=True)
class ParsedRequirement:
    """One non-blank requirement line."""

    kind: str
    name: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class RequirementProblems:
    """Unpinned names and lines that could not be classified."""

    unpinned: tuple[str, ...]
    unsupported: tuple[str, ...]


@dataclass(frozen=True)
class DependencyTarget:
    """A file Safety should scan, plus pins this script checks itself."""

    display: str
    requirement_file: Path
    unpinned: tuple[str, ...] = ()
    unsupported: tuple[str, ...] = ()


def discover_dependency_files(root: Path) -> list[Path]:
    """Return requirement files, setup.py, and known lockfiles under ``root``.

    Matches ``requirements*.txt``, ``constraints*.txt``, and ``setup.py``, plus
    the lockfiles this repository would treat as pinned dependency manifests.
    ``.git`` and local virtualenv directories are skipped. An empty result is a
    failure at the command entrypoint.
    """
    found: list[Path] = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in _EXCLUDED_DIRECTORIES]
        for filename in filenames:
            if (
                _REQUIREMENT_FILENAME.match(filename)
                or filename in _LOCK_FILENAMES
                or filename == "setup.py"
            ):
                found.append(Path(directory) / filename)
    return sorted(found, key=lambda path: path.as_posix())


def requirement_files_for_safety(files: Sequence[Path]) -> list[Path]:
    """Return requirement files Safety can scan directly."""
    return [
        path
        for path in files
        if path.name not in _LOCK_FILENAMES and path.name != "setup.py"
    ]


def unscanned_lockfiles(files: Sequence[Path]) -> list[Path]:
    """Return lockfiles that must fail the scan instead of being ignored."""
    return [path for path in files if path.name in _LOCK_FILENAMES]


def setup_files(files: Sequence[Path]) -> list[Path]:
    """Return setup.py files whose install requirements must be scanned."""
    return [path for path in files if path.name == "setup.py"]


def _logical_lines(text: str) -> list[str]:
    lines: list[str] = []
    pending = ""
    for raw in text.splitlines():
        if raw.rstrip().endswith("\\"):
            pending += raw.rstrip()[:-1] + " "
            continue
        lines.append(pending + raw)
        pending = ""
    if pending:
        lines.append(pending)
    return lines


def _is_exact_pin(spec: str) -> bool:
    parts = [part.strip() for part in spec.split(",") if part.strip()]
    if len(parts) != 1:
        return False
    token = parts[0]
    if token.startswith("==="):
        version = token[3:].strip()
    elif token.startswith("=="):
        version = token[2:].strip()
    else:
        return False
    return bool(version) and "*" not in version


def parse_requirement_line(raw: str) -> ParsedRequirement | None:
    """Classify one requirement line. Blank lines and comments return None."""
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if " #" in stripped:
        stripped = stripped.split(" #", 1)[0].strip()
    if not stripped:
        return None
    if stripped.startswith("-"):
        option = stripped.split("=", 1)[0].split()[0]
        if option in _DIRECTIVE_OPTIONS:
            return ParsedRequirement(kind="directive")
        return ParsedRequirement(kind="unsupported", detail=stripped)
    body = stripped.split(";", 1)[0].strip()
    match = _REQUIREMENT_NAME.match(body)
    if match is None:
        return ParsedRequirement(kind="unsupported", detail=stripped)
    name = match.group("name")
    spec = match.group("spec").strip()
    if spec.startswith("@") or "://" in spec or not _is_exact_pin(spec):
        return ParsedRequirement(kind="unpinned", name=name)
    return ParsedRequirement(kind="pinned", name=name)


def requirement_problems(text: str) -> RequirementProblems:
    """Return unpinned packages and requirement lines that are not understood."""
    unpinned: list[str] = []
    unsupported: list[str] = []
    seen: set[str] = set()
    for line in _logical_lines(text):
        parsed = parse_requirement_line(line)
        if parsed is None or parsed.kind in {"directive", "pinned"}:
            continue
        if parsed.kind == "unpinned" and parsed.name is not None:
            if parsed.name not in seen:
                seen.add(parsed.name)
                unpinned.append(parsed.name)
            continue
        detail = parsed.detail or line.strip()
        unsupported.append(detail)
    return RequirementProblems(unpinned=tuple(unpinned), unsupported=tuple(unsupported))


def _is_setup_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "setup"
    if isinstance(func, ast.Attribute):
        return func.attr == "setup"
    return False


def _literal_strings(node: ast.AST, label: str) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        raise SetupRequirementsError(f"{label} is not a literal list")
    values: list[str] = []
    for element in node.elts:
        if isinstance(element, ast.Constant) and isinstance(element.value, str):
            values.append(element.value)
            continue
        raise SetupRequirementsError(f"{label} contains a non-literal requirement")
    return values


def extract_setup_requirements(source: str) -> list[str]:
    """Read ``install_requires`` and ``extras_require`` without executing setup.py."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise SetupRequirementsError(f"setup.py could not be parsed: {exc}") from exc
    found = False
    requirements: list[str] = []
    for node in ast.walk(tree):
        if not _is_setup_call(node):
            continue
        found = True
        assert isinstance(node, ast.Call)
        for keyword in node.keywords:
            if keyword.arg == "install_requires":
                requirements.extend(_literal_strings(keyword.value, "install_requires"))
            elif keyword.arg == "extras_require":
                if not isinstance(keyword.value, ast.Dict):
                    raise SetupRequirementsError("extras_require is not a literal dict")
                for value in keyword.value.values:
                    requirements.extend(_literal_strings(value, "extras_require"))
    if not found:
        raise SetupRequirementsError("setup() call not found")
    return requirements


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def safety_check_command(python: str, requirement_file: Path) -> list[str]:
    """Build the Safety command for one requirement file.

    ``--check-unpinned-requirements`` reports vulnerabilities in version
    ranges. Unpinned names are still a separate failing check, because a range
    with no advisory would otherwise pass silently.
    """
    return [
        python,
        "-m",
        "safety",
        "check",
        "-r",
        str(requirement_file),
        "--check-unpinned-requirements",
        "--output",
        "json",
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


def first_json_object(text: str) -> dict[str, object] | None:
    """Return the first JSON object in Safety's banner-wrapped stdout."""
    start = text.find("{")
    if start < 0:
        return None
    try:
        value, _end = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    return value


def _advisory_pairs(items: object) -> list[tuple[str, str]]:
    if not isinstance(items, list):
        return []
    pairs: list[tuple[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        package = item.get("package_name")
        vulnerability_id = item.get("vulnerability_id")
        if isinstance(package, str) and isinstance(vulnerability_id, str):
            pairs.append((package, vulnerability_id))
    return pairs


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


def scan_dependency_targets(targets: Sequence[DependencyTarget], runner: Runner) -> int:
    """Scan every target, then fail if any target is vulnerable or unpinned."""
    failed = False
    for target in targets:
        completed = runner(target.requirement_file)
        print(f"===== {target.display} (exit {completed.returncode}) =====")
        sys.stderr.write(completed.stderr or "")
        payload = first_json_object(completed.stdout or "")
        if payload is None:
            sys.stdout.write(completed.stdout or "")
            print(
                f"error: Safety output for {target.display} was not JSON",
                file=sys.stderr,
            )
            failed = True
            reported: list[tuple[str, str]] = []
            ignored: list[tuple[str, str]] = []
        else:
            reported = _advisory_pairs(payload.get("vulnerabilities"))
            ignored = _advisory_pairs(payload.get("ignored_vulnerabilities"))
        for package, vulnerability_id in reported:
            print(f"ADVISORY {package} {vulnerability_id}")
        for package, vulnerability_id in ignored:
            print(f"IGNORED {package} {vulnerability_id}")
        for package in target.unpinned:
            print(f"UNPINNED {package}")
        for detail in target.unsupported:
            print(f"UNSUPPORTED {detail}")
        if (
            completed.returncode != 0
            or payload is None
            or ignored
            or target.unpinned
            or target.unsupported
        ):
            failed = True
    return 1 if failed else 0


def _targets_for_requirement_files(
    files: Sequence[Path], root: Path
) -> list[DependencyTarget]:
    targets: list[DependencyTarget] = []
    for path in files:
        problems = requirement_problems(path.read_text(encoding="utf-8"))
        targets.append(
            DependencyTarget(
                display=_display_path(path, root),
                requirement_file=path,
                unpinned=problems.unpinned,
                unsupported=problems.unsupported,
            )
        )
    return targets


def _targets_for_setup_files(
    files: Sequence[Path], root: Path, directory: Path
) -> tuple[list[DependencyTarget], int]:
    targets: list[DependencyTarget] = []
    code = 0
    for index, path in enumerate(files):
        display = _display_path(path, root)
        try:
            requirements = extract_setup_requirements(path.read_text(encoding="utf-8"))
        except SetupRequirementsError as exc:
            print(f"error: {display}: {exc}", file=sys.stderr)
            code = 1
            continue
        rendered = directory / f"setup-{index}-requirements.txt"
        rendered.write_text("\n".join(requirements) + "\n", encoding="utf-8")
        problems = requirement_problems("\n".join(requirements) + "\n")
        targets.append(
            DependencyTarget(
                display=display,
                requirement_file=rendered,
                unpinned=problems.unpinned,
                unsupported=problems.unsupported,
            )
        )
    return targets, code


def main(argv: Sequence[str] | None = None) -> int:
    """Discover dependency files, scan each one, and fail closed."""
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
    if not files:
        print(f"error: no dependency files found under {root}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="safety-setup-") as temporary:
        setup_targets, setup_code = _targets_for_setup_files(
            setup_files(files),
            root,
            Path(temporary),
        )
        targets = _targets_for_requirement_files(
            requirement_files_for_safety(files),
            root,
        )
        targets.extend(setup_targets)
        code = scan_dependency_targets(
            targets,
            lambda path: run_safety_check(path, args.python),
        )
    for lockfile in unscanned_lockfiles(files):
        print(
            f"error: refusing to skip unscanned dependency file {lockfile.as_posix()}",
            file=sys.stderr,
        )
        code = 1
    if setup_code != 0:
        return 1
    return code


if __name__ == "__main__":
    sys.exit(main())
