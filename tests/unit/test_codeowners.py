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
    ".github/trufflehog-known-findings.json",
    ".github/workflows/security-gitleaks.yml",
    ".github/workflows/security-trufflehog.yml",
)


def test_security_scan_files_are_owned_by_maninthecrowds() -> None:
    owners_for: dict[str, list[str]] = {}
    for raw_line in _OWNERS.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        owners_for[parts[0]] = parts[1:]
    for path in _PATHS:
        assert owners_for.get(path) == ["@ManintheCrowds"]
