"""The python-jose Safety ignore covers one advisory and fails after it expires."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.security]

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / ".github" / "scripts" / "safety_python_jose_ignore.py"
_POLICY = _ROOT / ".safety-policy.yml"

_spec = importlib.util.spec_from_file_location("safety_python_jose_ignore", _SCRIPT)
assert _spec is not None and _spec.loader is not None
policy_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = policy_mod
_spec.loader.exec_module(policy_mod)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONSAFEPATH"] = "1"
    return subprocess.run(
        ["python3", "-I", str(_SCRIPT), *args],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_checked_in_policy_ignores_only_the_python_jose_advisory() -> None:
    policy = policy_mod.load_policy(_POLICY)
    assert policy_mod.policy_problems(policy) == ()
    assert [entry.advisory_id for entry in policy.ignores] == [policy_mod.ADVISORY_ID]
    entry = policy.ignores[0]
    assert entry.expires == datetime(2026, 12, 23)
    assert entry.reason.count(policy_mod.PACKAGE) == 1
    assert policy_mod.GHSA_ID in entry.reason
    assert policy_mod.PYSEC_ID in entry.reason
    assert "PyJWT" in entry.reason
    assert policy.continue_on_error is False


def test_other_advisories_stay_reported_until_expiry_and_fail_after_it() -> None:
    policy = policy_mod.load_policy(_POLICY)
    jose = policy_mod.Finding(policy_mod.ADVISORY_ID, policy_mod.PACKAGE)
    other = policy_mod.Finding(policy_mod.OTHER_ADVISORY_ID, policy_mod.PACKAGE)
    requests = policy_mod.Finding(policy_mod.REQUESTS_ADVISORY_ID, "requests")
    before = datetime(2026, 12, 22, 23, 59, 59)
    ignored, reported = policy_mod.classify(policy, (jose, other, requests), before)
    assert ignored == (jose,)
    assert reported == (other, requests)

    at_expiry = datetime(2026, 12, 23, 0, 0, 0)
    ignored, reported = policy_mod.classify(policy, (jose,), at_expiry)
    assert ignored == ()
    assert reported == (jose,)
    assert policy_mod.ignore_is_active(policy.ignores[0].expires, at_expiry) is False


def test_a_second_ignore_is_rejected() -> None:
    text = _POLICY.read_text(encoding="utf-8")
    extra = text.replace(
        "    SFTY-20260903-64758:\n",
        "    90553:\n"
        "      reason: This must not be ignored. Migrate nothing.\n"
        '      expires: "2026-12-23"\n'
        "    SFTY-20260903-64758:\n",
    )
    policy = policy_mod.parse_policy(extra)
    assert policy_mod.policy_problems(policy) == ("expected one ignore, found 2",)


def test_check_policy_cli_accepts_the_day_before_expiry() -> None:
    completed = _run("--check-policy", "--now", "2026-12-22T23:59:59")
    assert completed.returncode == 0, completed.stderr


def test_check_policy_cli_fails_once_expired() -> None:
    completed = _run("--check-policy", "--now", "2026-12-23T00:00:00")
    assert completed.returncode == 1
    assert "expired" in completed.stderr
    assert policy_mod.ADVISORY_ID in completed.stderr


def test_check_policy_cli_is_active_on_the_approval_date() -> None:
    completed = _run("--check-policy", "--now", "2026-11-23T02:41:00")
    assert completed.returncode == 0, completed.stderr


def test_security_scan_runs_the_policy_gate() -> None:
    text = (_ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    command = (
        "PYTHONSAFEPATH=1 python3 -I "
        ".github/scripts/safety_python_jose_ignore.py --check-policy --execute"
    )
    assert command in text
    assert "safety check --policy-file .safety-policy.yml" in text


@pytest.mark.skipif(
    shutil.which("safety") is None, reason="safety CLI is not installed"
)
def test_safety_check_honors_the_scoped_expiring_ignore() -> None:
    completed = _run("--check-policy", "--execute", "--now", "2026-11-23T02:41:00")
    assert completed.returncode == 0, completed.stderr
