"""Matcher tests for the scheduled TruffleHog known-findings baseline."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import date
from io import StringIO
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.security]

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / ".github" / "scripts" / "trufflehog_known_findings.py"
_BASELINE = _ROOT / ".github" / "trufflehog-known-findings.json"
_WORKFLOW = _ROOT / ".github" / "workflows" / "security-trufflehog.yml"

_spec = importlib.util.spec_from_file_location("trufflehog_known_findings", _SCRIPT)
assert _spec is not None and _spec.loader is not None
known_findings = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = known_findings
_spec.loader.exec_module(known_findings)

_COMMIT = "7c07e7b78403ddfed05d76cb16f445407ae93e80"
_PATH = "job-automation-service/.env.backup"
_EXPIRES = "2026-11-23"
_FAKE_RAW = "example-raw-value-should-not-leak"


def _entry(**overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "detector": "Adzuna",
        "path": _PATH,
        "commit": _COMMIT,
        "line": 3,
        "expires": _EXPIRES,
        "reason": "known exposed credential",
    }
    entry.update(overrides)
    return entry


def _baseline(*entries: dict[str, object]) -> str:
    return json.dumps({"entries": list(entries)})


def _finding_json(
    *,
    verified: bool,
    commit: str = _COMMIT,
    detector: str = "Adzuna",
    line: int = 3,
) -> str:
    return json.dumps(
        {
            "DetectorName": detector,
            "Verified": verified,
            "Raw": _FAKE_RAW,
            "RawV2": _FAKE_RAW,
            "Redacted": _FAKE_RAW[:4] + "...",
            "SourceMetadata": {
                "Data": {
                    "Git": {
                        "file": _PATH,
                        "commit": commit,
                        "line": line,
                        "email": "person@example.invalid",
                    }
                }
            },
        }
    )


def _evaluate(
    findings_text: str,
    baseline_text: str,
    today: date,
) -> object:
    findings = known_findings.parse_findings(StringIO(findings_text))
    entries = known_findings.load_baseline(baseline_text)
    return known_findings.evaluate(findings, entries, today)


def test_unexpired_unverified_match_passes() -> None:
    result = _evaluate(
        _finding_json(verified=False),
        _baseline(_entry()),
        date(2026, 11, 9),
    )
    summary = known_findings.format_summary(result)

    assert result.ok is True
    assert result.matched_count == 1
    assert result.verified_count == 0
    assert "soonest_days_to_expiry: 14" in summary
    assert _FAKE_RAW not in summary
    assert "person@example.invalid" not in summary


def test_empty_findings_pass() -> None:
    result = _evaluate("", _baseline(_entry()), date(2026, 11, 9))

    assert result.ok is True
    assert result.finding_count == 0
    assert result.expired_count == 0
    assert result.matched_entries == ()


def test_same_commit_different_line_fails() -> None:
    result = _evaluate(
        _finding_json(verified=False, line=45),
        _baseline(_entry()),
        date(2026, 11, 9),
    )

    assert result.ok is False
    assert result.matched_count == 0
    assert result.unmatched_count == 1
    assert any("line=45" in item for item in result.failures)
    assert _FAKE_RAW not in "\n".join(result.failures)


def test_new_finding_fails() -> None:
    other_commit = "641d4f19dabfa807c70aad6fee312e8e3e0ae201"
    result = _evaluate(
        _finding_json(verified=False, commit=other_commit),
        _baseline(_entry()),
        date(2026, 11, 9),
    )

    assert result.ok is False
    assert result.unmatched_count == 1
    assert any("finding not in unexpired baseline" in item for item in result.failures)
    assert _FAKE_RAW not in "\n".join(result.failures)


def test_verified_fails_even_when_baselined() -> None:
    result = _evaluate(
        _finding_json(verified=True),
        _baseline(_entry()),
        date(2026, 11, 9),
    )

    assert result.ok is False
    assert result.verified_count == 1
    assert result.matched_count == 1
    assert any(item.startswith("verified result:") for item in result.failures)


def test_expired_baseline_fails_with_no_findings() -> None:
    day_before = _evaluate("", _baseline(_entry()), date(2026, 11, 22))
    expiry_day = _evaluate("", _baseline(_entry()), date(2026, 11, 23))

    assert day_before.ok is True
    assert day_before.soonest_days_to_expiry == 1
    assert expiry_day.ok is False
    assert expiry_day.expired_count == 1
    assert expiry_day.finding_count == 0
    assert any(
        item.startswith("expired baseline entry:") for item in expiry_day.failures
    )


def test_expired_baseline_fails_when_finding_matches_location() -> None:
    result = _evaluate(
        _finding_json(verified=False),
        _baseline(_entry()),
        date(2026, 11, 23),
    )

    assert result.ok is False
    assert result.matched_count == 0
    assert result.unmatched_count == 1
    assert result.expired_count == 1


def test_closed_on_replaces_expires() -> None:
    entry = _entry(closed_on="2026-11-15")
    still_open = _evaluate(
        _finding_json(verified=False), _baseline(entry), date(2026, 11, 14)
    )
    closed = _evaluate("", _baseline(entry), date(2026, 11, 15))

    assert still_open.ok is True
    assert still_open.soonest_days_to_expiry == 1
    assert closed.ok is False
    assert closed.expired_count == 1


def test_summary_and_parse_errors_omit_secret_material(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(_baseline(_entry()), encoding="utf-8")
    stdout = StringIO()
    stream = StringIO(_finding_json(verified=False) + "\n")
    real_stdout = known_findings.sys.stdout
    known_findings.sys.stdout = stdout
    try:
        code = known_findings.main(
            ["--baseline", str(baseline), "--today", "2026-11-09"],
            stdin=stream,
        )
    finally:
        known_findings.sys.stdout = real_stdout

    assert code == 0
    assert _FAKE_RAW not in stdout.getvalue()

    bad = StringIO(f"{_FAKE_RAW} is not json\n")
    with pytest.raises(ValueError, match="is not JSON") as caught:
        known_findings.parse_findings(bad)
    assert _FAKE_RAW not in str(caught.value)


_BASELINE_LOCATIONS = {
    (
        "job-automation-service/.env.backup",
        "726225a6c1939a4a199cea3de1b893e079193f90",
        3,
    ),
    (
        "job-automation-service/.env.backup",
        "7c07e7b78403ddfed05d76cb16f445407ae93e80",
        3,
    ),
    (
        "job-automation-service/ENV_FILE_FIX_SUMMARY.md",
        "641d4f19dabfa807c70aad6fee312e8e3e0ae201",
        71,
    ),
    (
        "job-automation-service/ENV_FILE_FIX_SUMMARY.md",
        "f708e4c85c471ef9af8817362b7ff14cc09bc6b7",
        71,
    ),
    (
        "job-automation-service/NEXT_STEPS_TO_FIX.md",
        "641d4f19dabfa807c70aad6fee312e8e3e0ae201",
        48,
    ),
    (
        "job-automation-service/NEXT_STEPS_TO_FIX.md",
        "f708e4c85c471ef9af8817362b7ff14cc09bc6b7",
        48,
    ),
    (
        "job-automation-service/SERVER_DEBUG_INSTRUCTIONS.md",
        "641d4f19dabfa807c70aad6fee312e8e3e0ae201",
        64,
    ),
    (
        "job-automation-service/SERVER_DEBUG_INSTRUCTIONS.md",
        "f708e4c85c471ef9af8817362b7ff14cc09bc6b7",
        64,
    ),
    (
        "job-automation-service/TEST_RESULTS_SUMMARY.md",
        "641d4f19dabfa807c70aad6fee312e8e3e0ae201",
        108,
    ),
    (
        "job-automation-service/TEST_RESULTS_SUMMARY.md",
        "f708e4c85c471ef9af8817362b7ff14cc09bc6b7",
        108,
    ),
    (
        "job-automation-service/fix_server_credentials.ps1",
        "641d4f19dabfa807c70aad6fee312e8e3e0ae201",
        25,
    ),
    (
        "job-automation-service/fix_server_credentials.ps1",
        "641d4f19dabfa807c70aad6fee312e8e3e0ae201",
        45,
    ),
    (
        "job-automation-service/fix_server_credentials.ps1",
        "f708e4c85c471ef9af8817362b7ff14cc09bc6b7",
        25,
    ),
    (
        "job-automation-service/fix_server_credentials.ps1",
        "f708e4c85c471ef9af8817362b7ff14cc09bc6b7",
        45,
    ),
}


def test_checked_in_baseline_shape() -> None:
    text = _BASELINE.read_text(encoding="utf-8")
    entries = known_findings.load_baseline(text)

    assert len(entries) == 14
    assert not re.search(r"\b[a-f0-9]{32}\b", text)
    assert "Raw" not in text
    assert "redacted" not in text.lower()
    for entry in entries:
        assert entry.detector == "Adzuna"
        assert entry.expires == date(2026, 11, 23)
        assert entry.closed_on is None
        assert entry.evidence is None
        assert entry.line is not None
    locations = {(entry.path, entry.commit, entry.line) for entry in entries}
    assert locations == _BASELINE_LOCATIONS


def test_evidence_link_is_accepted_and_non_urls_are_rejected() -> None:
    entry = _entry(evidence="https://example.invalid/closure")
    loaded = known_findings.load_baseline(_baseline(entry))
    assert loaded[0].evidence == "https://example.invalid/closure"
    with pytest.raises(ValueError, match="evidence must be an https URL"):
        known_findings.load_baseline(_baseline(_entry(evidence="not-a-link")))


def test_later_closed_on_is_rejected() -> None:
    with pytest.raises(ValueError, match="closed_on is after expires"):
        known_findings.load_baseline(_baseline(_entry(closed_on="2026-11-24")))


def test_scheduled_job_uses_baseline_and_strict_job_does_not() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    strict, scheduled = text.split("trufflehog-scheduled:", 1)

    assert "extra_args: --results=verified,unknown\n" in strict
    assert "trufflehog-known-findings.json" not in strict
    assert "trufflehog_known_findings.py" not in strict
    assert "--exclude-paths" not in strict
    assert "--results=verified,unknown" in scheduled
    assert "--exclude-paths=config/trufflehog-exclude.txt" in scheduled
    assert ".github/scripts/trufflehog_known_findings.py" in scheduled
    assert ".github/trufflehog-known-findings.json" in scheduled
    digest = (
        "ghcr.io/trufflesecurity/trufflehog:3.99.8"
        "@sha256:674b2f187620a19df77f44cf9a7d77efcc581a5662accef2f2739cbb46ba4a3a"
    )
    assert digest in scheduled
    assert digest not in strict
    assert "ghcr.io/trufflesecurity/trufflehog:3.99.8 \\" not in scheduled
