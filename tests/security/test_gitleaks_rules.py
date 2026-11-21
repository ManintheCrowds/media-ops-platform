"""Gitleaks default rules load, and the worktree has no current findings."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.security

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG = _ROOT / ".gitleaks.toml"


def _gitleaks() -> str:
    found = shutil.which("gitleaks")
    if found:
        return found
    fallback = Path("/tmp/gl-bin/gitleaks")
    if fallback.is_file():
        return str(fallback)
    pytest.fail("gitleaks is not installed")
    return ""


def _detect(source: Path, report: Path) -> list[dict[str, object]]:
    completed = subprocess.run(
        [
            _gitleaks(),
            "detect",
            "--no-git",
            "--source",
            str(source),
            "--config",
            str(_CONFIG),
            "--redact",
            "--no-banner",
            "--ignore-gitleaks-allow",
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
    assert completed.returncode == 0, "gitleaks did not finish"
    if not report.is_file() or report.stat().st_size == 0:
        return []
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    return payload


def test_use_default_loads_a_nonzero_rule_count(tmp_path: Path) -> None:
    text = _CONFIG.read_text(encoding="utf-8")
    assert "[extend]" in text
    assert "useDefault = true" in text
    sarif = tmp_path / "rules.sarif"
    empty = tmp_path / "empty"
    empty.mkdir()
    completed = subprocess.run(
        [
            _gitleaks(),
            "detect",
            "--no-git",
            "--source",
            str(empty),
            "--config",
            str(_CONFIG),
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
    assert completed.returncode == 0, "gitleaks did not finish"
    report = json.loads(sarif.read_text(encoding="utf-8"))
    rules = report["runs"][0]["tool"]["driver"].get("rules") or []
    assert len(rules) > 0


def test_current_worktree_has_no_gitleaks_findings(tmp_path: Path) -> None:
    findings = _detect(_ROOT, tmp_path / "report.json")
    assert len(findings) == 0, f"gitleaks reported {len(findings)} findings"
