"""The gitleaks workflow executes the base revision's scan script."""

from __future__ import annotations

import importlib.util
import sys
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


def _scanner():
    script = (
        Path(__file__).resolve().parents[2] / ".github" / "scripts" / "gitleaks_ci.py"
    )
    spec = importlib.util.spec_from_file_location("gitleaks_ci_workflow", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_log_opts_are_first_parent_text_and_not_all() -> None:
    scanner = _scanner()
    opts = scanner.revision_log_opts("a" * 40, "b" * 40)
    assert opts == (
        "--diff-merges=first-parent --text " + ("a" * 40) + ".." + ("b" * 40)
    )
    assert "--all" not in opts.split()
    command = scanner.gitleaks_command(
        "gitleaks",
        Path("."),
        Path(".gitleaks.toml"),
        Path(".gitleaksignore"),
        opts,
    )
    assert "--ignore-gitleaks-allow" in command
    assert "--redact" in command
    assert "--all" not in command


def test_ignore_entries_must_be_exact_commit_fingerprints() -> None:
    scanner = _scanner()
    raw = "\n".join(
        [
            "# note",
            "README.md:generic-api-key:1",
            "a" * 40 + ":job-automation-service/.env.backup:generic-api-key:6",
            "not-a-fingerprint",
        ]
    )
    kept = scanner.exact_ignore_text(raw.encode("utf-8")).decode("utf-8").splitlines()
    assert kept == ["a" * 40 + ":job-automation-service/.env.backup:generic-api-key:6"]
