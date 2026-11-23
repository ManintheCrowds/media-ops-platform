"""The gitleaks workflow executes the base revision's scan script."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_WORKFLOW = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "security-gitleaks.yml"
)


def test_pull_request_gate_is_materialized_from_the_base() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert 'git show "${GATE_SHA}:.github/scripts/gitleaks_ci.py"' in text
    assert 'git show "${GATE_SHA}:.gitleaks.toml"' in text
    assert 'git show "${GATE_SHA}:.gitleaksignore"' in text
    assert 'git show "${GATE_SHA}:.github/trufflehog-known-findings.json"' in text
    assert "${RUNNER_TEMP}/scan/gitleaks_ci.py" in text
    assert "bootstrap: base has no scan script" in text
    assert "python3 .github/scripts/gitleaks_ci.py" not in text
    assert "|| true" not in text
    assert "continue-on-error" not in text
    assert "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb" in text
    assert "gitleaks_8.30.1_linux_x64.tar.gz" in text
