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
    assert len(rules) == 222


def test_runtime_canaries_match_default_rules(tmp_path: Path) -> None:
    aws = "AKIA" + "".join(["M7NP", "Q2RS", "T4VW", "X5YZ"])
    pat = "ghp_" + "".join(
        ["Ab3Cd", "Ef7Gh", "Jk2Lm", "Np5Qr", "St8Vw", "Xy1Za", "Bc4De", "F"]
    )
    slack = "".join(
        ["xoxb-", "2468013579", "-", "135792468013", "-", "Ab9Cd8Ef7Gh6Ij5Kl4Mn3"]
    )
    source = tmp_path / "src"
    source.mkdir()
    (source / "aws.txt").write_text(f'key = "{aws}"\n', encoding="utf-8")
    (source / "pat.txt").write_text(f'key = "{pat}"\n', encoding="utf-8")
    (source / "slack.txt").write_text(f'key = "{slack}"\n', encoding="utf-8")
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
    assert "aws-access-token" in rules
    assert "slack-bot-token" in rules
    leaked = aws in completed.stdout or aws in completed.stderr
    leaked = leaked or pat in completed.stdout or pat in completed.stderr
    leaked = leaked or slack in completed.stdout or slack in completed.stderr
    assert leaked is False


def test_current_worktree_has_no_gitleaks_findings(tmp_path: Path) -> None:
    findings = _detect(_ROOT, tmp_path / "report.json")
    assert len(findings) == 0, f"gitleaks reported {len(findings)} findings"
