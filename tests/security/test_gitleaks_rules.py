"""Gitleaks default rules load, and the worktree has no current findings."""

from __future__ import annotations

import json
import secrets
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
    assert len(rules) >= 200


def test_runtime_canaries_match_default_rules(tmp_path: Path) -> None:
    upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    mixed = upper + "abcdefghijklmnopqrstuvwxyz"
    aws = "AKIA" + "".join(secrets.choice(upper) for _ in range(16))
    while "EXAMPLE" in aws:
        aws = "AKIA" + "".join(secrets.choice(upper) for _ in range(16))
    pat = "ghp_" + "".join(secrets.choice(mixed) for _ in range(36))
    source = tmp_path / "src"
    source.mkdir()
    (source / "aws.txt").write_text(f"token={aws}\n", encoding="utf-8")
    (source / "pat.txt").write_text(f"github={pat}\n", encoding="utf-8")
    findings = _detect(source, tmp_path / "canary.json")
    # Re-run with captured logs so a dropped --redact would show the canary.
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
            "--exit-code",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    rules = {item.get("RuleID") for item in findings}
    assert "github-pat" in rules
    assert "aws-access-token" in rules or "generic-api-key" in rules
    assert len(rules) >= 2
    leaked = aws in completed.stdout or aws in completed.stderr
    leaked = leaked or pat in completed.stdout or pat in completed.stderr
    assert leaked is False


def test_current_worktree_has_no_gitleaks_findings(tmp_path: Path) -> None:
    findings = _detect(_ROOT, tmp_path / "report.json")
    assert len(findings) == 0, f"gitleaks reported {len(findings)} findings"
