"""CODEOWNERS covers the secret-scan configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_ROOT = Path(__file__).resolve().parents[2]
_OWNERS = _ROOT / ".github" / "CODEOWNERS"
_PATHS = (
    ".gitleaksignore",
    ".gitleaks.toml",
    ".github/CODEOWNERS",
    ".github/scripts/gitleaks_ci.py",
    ".github/scripts/trufflehog_known_findings.py",
    ".github/trufflehog-known-findings.json",
    ".github/workflows/security-gitleaks.yml",
    ".github/workflows/security-trufflehog.yml",
    "config/trufflehog-exclude.txt",
    "tests/security/test_gitleaks_ci.py",
    "tests/unit/test_codeowners.py",
    "tests/unit/test_gitleaks_workflow.py",
    "tests/unit/test_trufflehog_known_findings.py",
)


def _parsed(text: str) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        rows.append((parts[0], parts[1:]))
    return rows


def _matches(pattern: str, path: str) -> bool:
    if pattern == "*":
        return True
    if pattern.endswith("/"):
        return path == pattern[:-1] or path.startswith(pattern)
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def _last_owners(rows: list[tuple[str, list[str]]], path: str) -> list[str]:
    owners: list[str] = []
    for pattern, pattern_owners in rows:
        if _matches(pattern, path):
            owners = pattern_owners
    return owners


def test_security_scan_files_are_owned_by_maninthecrowds() -> None:
    rows = _parsed(_OWNERS.read_text(encoding="utf-8"))
    assert all(pattern != "*" for pattern, _owners in rows)
    for path in _PATHS:
        assert _last_owners(rows, path) == ["@ManintheCrowds"]


def test_last_matching_pattern_wins_and_the_file_has_no_catchall() -> None:
    text = _OWNERS.read_text(encoding="utf-8") + "\n* @someone-else\n"
    rows = _parsed(text)
    assert _last_owners(rows, ".github/scripts/gitleaks_ci.py") == ["@someone-else"]
    assert all(
        pattern != "*"
        for pattern, _owners in _parsed(_OWNERS.read_text(encoding="utf-8"))
    )
