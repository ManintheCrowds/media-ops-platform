"""Pin checks for the requests 2.33.0 security bump."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.security]

_ROOT = Path(__file__).resolve().parents[2]
_ROOT_REQUIREMENTS = _ROOT / "requirements.txt"
_VULNERABLE_PIN = "requests==2.32.4"
_FIXED_PIN = "requests==2.33.0"
_FIXED_VERSION = (2, 33, 0)


def _requirement_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        code = raw.split("#", 1)[0].strip()
        if code:
            lines.append(code)
    return lines


def _version_tuple(spec: str) -> tuple[int, ...]:
    version = spec.split("==", 1)[1]
    version = version.split(";", 1)[0].strip()
    return tuple(int(part) for part in version.split("."))


def test_root_requirements_pin_requests_2_33_0() -> None:
    """The root manifest pins the release that fixes Safety 90553."""
    pins = [
        line
        for line in _requirement_lines(_ROOT_REQUIREMENTS)
        if line.startswith("requests==")
    ]
    assert pins == [_FIXED_PIN]


def test_no_requirements_file_pins_vulnerable_requests() -> None:
    """requests 2.32.4 is the vulnerable pin; no manifest may keep it."""
    offenders = [
        str(path.relative_to(_ROOT))
        for path in _ROOT.rglob("requirements*.txt")
        if _VULNERABLE_PIN in _requirement_lines(path)
    ]
    assert offenders == []


def test_other_requests_pins_are_at_least_2_33_0() -> None:
    """Service manifests that already moved past 2.32.4 stay on a fixed release."""
    below: list[str] = []
    for path in _ROOT.rglob("requirements*.txt"):
        for line in _requirement_lines(path):
            if not line.startswith("requests=="):
                continue
            if _version_tuple(line) < _FIXED_VERSION:
                below.append(f"{path.relative_to(_ROOT)}: {line}")
    assert below == []


def test_root_requirements_do_not_require_arlo_distribution() -> None:
    """PyPI arlo pins urllib3==1.24, which pip cannot resolve with requests 2.33.0."""
    names = []
    for line in _requirement_lines(_ROOT_REQUIREMENTS):
        name = line.split("[", 1)[0].split("=", 1)[0].split(">", 1)[0].split("<", 1)[0]
        names.append(name.strip().lower())
    assert "arlo" not in names
    text = _ROOT_REQUIREMENTS.read_text(encoding="utf-8")
    assert "urllib3==1.24" in text
    assert "arlo>=1.2.62 is omitted" in text
