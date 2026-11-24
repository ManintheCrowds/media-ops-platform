#!/usr/bin/env python3
"""Match scheduled TruffleHog JSON to an expiring known-findings baseline.

The scheduled job is the only caller. A run passes only when every finding
matches an unexpired baseline entry by detector, path, commit, and line. Any
verified result fails, including one whose location is in the baseline.
An expired baseline entry fails the run even when no finding matches it.
The 14 known Adzuna locations may omit expires when the reason is account
closed. A verified finding at one of those keys still fails. Every other
entry still needs an expiry, and that date cannot be more than 45 days out.

Scanner JSON includes secret material. This script reads detector name,
verified flag, file path, commit, and line, and never prints anything else.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Mapping, Sequence, TextIO

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_EXPIRY_DAYS = 45
_EVIDENCE_RE = re.compile(r"^https://\S+$")
_ENTRY_FIELDS = frozenset(
    {"detector", "path", "commit", "line", "expires", "closed_on", "reason", "evidence"}
)
# The 14 known Adzuna locations. They may omit expires only with the
# account-closed reason. A verified finding at one of these keys still fails.
_NO_EXPIRY_REASON = "account closed"
_NO_EXPIRY_FINGERPRINTS = frozenset(
    {
        ("Adzuna", "job-automation-service/.env.backup", "726225a6c1939a4a199cea3de1b893e079193f90", 3),
        ("Adzuna", "job-automation-service/.env.backup", "7c07e7b78403ddfed05d76cb16f445407ae93e80", 3),
        ("Adzuna", "job-automation-service/ENV_FILE_FIX_SUMMARY.md", "641d4f19dabfa807c70aad6fee312e8e3e0ae201", 71),
        ("Adzuna", "job-automation-service/ENV_FILE_FIX_SUMMARY.md", "f708e4c85c471ef9af8817362b7ff14cc09bc6b7", 71),
        ("Adzuna", "job-automation-service/NEXT_STEPS_TO_FIX.md", "641d4f19dabfa807c70aad6fee312e8e3e0ae201", 48),
        ("Adzuna", "job-automation-service/NEXT_STEPS_TO_FIX.md", "f708e4c85c471ef9af8817362b7ff14cc09bc6b7", 48),
        ("Adzuna", "job-automation-service/SERVER_DEBUG_INSTRUCTIONS.md", "641d4f19dabfa807c70aad6fee312e8e3e0ae201", 64),
        ("Adzuna", "job-automation-service/SERVER_DEBUG_INSTRUCTIONS.md", "f708e4c85c471ef9af8817362b7ff14cc09bc6b7", 64),
        ("Adzuna", "job-automation-service/TEST_RESULTS_SUMMARY.md", "641d4f19dabfa807c70aad6fee312e8e3e0ae201", 108),
        ("Adzuna", "job-automation-service/TEST_RESULTS_SUMMARY.md", "f708e4c85c471ef9af8817362b7ff14cc09bc6b7", 108),
        ("Adzuna", "job-automation-service/fix_server_credentials.ps1", "641d4f19dabfa807c70aad6fee312e8e3e0ae201", 25),
        ("Adzuna", "job-automation-service/fix_server_credentials.ps1", "641d4f19dabfa807c70aad6fee312e8e3e0ae201", 45),
        ("Adzuna", "job-automation-service/fix_server_credentials.ps1", "f708e4c85c471ef9af8817362b7ff14cc09bc6b7", 25),
        ("Adzuna", "job-automation-service/fix_server_credentials.ps1", "f708e4c85c471ef9af8817362b7ff14cc09bc6b7", 45),
    }
)


@dataclass(frozen=True)
class Finding:
    detector: str
    path: str
    commit: str
    verified: bool
    line: int | None
    verification_error: bool = False


@dataclass(frozen=True)
class BaselineEntry:
    detector: str
    path: str
    commit: str
    expires: date | None
    closed_on: date | None
    reason: str
    line: int | None
    evidence: str | None

    def effective_expiry(self) -> date | None:
        """Return the date this entry stops matching, or None when it does not."""
        if self.expires is None:
            return None
        if self.closed_on is not None:
            return self.closed_on
        return self.expires


@dataclass(frozen=True)
class MatchedEntry:
    detector: str
    path: str
    commit: str
    line: int | None
    days_to_expiry: int


@dataclass(frozen=True)
class Evaluation:
    ok: bool
    finding_count: int
    verified_count: int
    matched_count: int
    unmatched_count: int
    expired_count: int
    baseline_count: int
    soonest_days_to_expiry: int | None
    unverified_count: int
    unknown_count: int
    failures: tuple[str, ...]
    matched_entries: tuple[MatchedEntry, ...]


def _parse_date(value: object, label: str) -> date:
    if not isinstance(value, str) or _DATE_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be YYYY-MM-DD")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc


def _optional_date(value: object, label: str) -> date | None:
    if value is None:
        return None
    return _parse_date(value, label)


def _git_metadata(payload: Mapping[str, object]) -> Mapping[str, object]:
    source = payload.get("SourceMetadata")
    if not isinstance(source, dict):
        raise ValueError("finding missing git metadata")
    data = source.get("Data")
    if not isinstance(data, dict):
        raise ValueError("finding missing git metadata")
    git = data.get("Git")
    if not isinstance(git, dict):
        raise ValueError("finding missing git metadata")
    return git


def finding_from_payload(payload: Mapping[str, object], line_number: int) -> Finding:
    detector = payload.get("DetectorName")
    if not isinstance(detector, str) or not detector.strip():
        raise ValueError(f"finding on line {line_number} missing detector")
    verified = payload.get("Verified")
    if not isinstance(verified, bool):
        raise ValueError(f"finding on line {line_number} missing verified flag")
    git = _git_metadata(payload)
    path = git.get("file")
    commit = git.get("commit")
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"finding on line {line_number} missing path")
    if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit.lower()) is None:
        raise ValueError(f"finding on line {line_number} missing commit")
    line = git.get("line")
    if line is not None and not isinstance(line, int):
        raise ValueError(f"finding on line {line_number} has a non-integer line")
    verification_error = payload.get("VerificationError")
    return Finding(
        detector=detector,
        path=path,
        commit=commit.lower(),
        verified=verified,
        line=line,
        verification_error=isinstance(verification_error, str)
        and bool(verification_error.strip()),
    )


def parse_findings(stream: TextIO) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, raw_line in enumerate(stream, start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"scanner stdout line {line_number} is not JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"scanner stdout line {line_number} is not an object")
        findings.append(finding_from_payload(payload, line_number))
    return findings


def _entry_from_payload(payload: Mapping[str, object], index: int) -> BaselineEntry:
    extra = set(payload) - _ENTRY_FIELDS
    if extra:
        names = ", ".join(sorted(str(name) for name in extra))
        raise ValueError(f"baseline entry {index} has unsupported fields: {names}")
    detector = payload.get("detector")
    path = payload.get("path")
    commit = payload.get("commit")
    reason = payload.get("reason")
    if not isinstance(detector, str) or not detector.strip():
        raise ValueError(f"baseline entry {index} missing detector")
    if not isinstance(path, str) or not path.strip() or "\n" in path:
        raise ValueError(f"baseline entry {index} missing path")
    if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
        raise ValueError(f"baseline entry {index} missing commit")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"baseline entry {index} missing reason")
    line = payload.get("line")
    if line is not None and (not isinstance(line, int) or isinstance(line, bool)):
        raise ValueError(f"baseline entry {index} line must be an integer")
    line_value = line if isinstance(line, int) else None
    fingerprint = (detector, path, commit, line_value)
    closed_on = _optional_date(
        payload.get("closed_on"), f"baseline entry {index} closed_on"
    )
    if "expires" not in payload:
        if fingerprint not in _NO_EXPIRY_FINGERPRINTS:
            raise ValueError(f"baseline entry {index} missing expires")
        if reason.strip() != _NO_EXPIRY_REASON:
            raise ValueError(f"baseline entry {index} missing account-closed reason")
        if closed_on is not None:
            raise ValueError(f"baseline entry {index} closed_on requires expires")
        expires = None
    else:
        expires = _parse_date(payload.get("expires"), f"baseline entry {index} expires")
        if closed_on is not None and closed_on > expires:
            raise ValueError(f"baseline entry {index} closed_on is after expires")
    evidence = payload.get("evidence")
    if evidence is not None:
        if (
            not isinstance(evidence, str)
            or _EVIDENCE_RE.fullmatch(evidence) is None
            or len(evidence) > 200
        ):
            raise ValueError(f"baseline entry {index} evidence must be an https URL")
    return BaselineEntry(
        detector=detector,
        path=path,
        commit=commit,
        expires=expires,
        closed_on=closed_on,
        reason=reason.strip(),
        line=line if isinstance(line, int) else None,
        evidence=evidence if isinstance(evidence, str) else None,
    )


def load_baseline(text: str) -> list[BaselineEntry]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("baseline is not JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"entries"}:
        raise ValueError("baseline must be an object with an entries array")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("baseline entries must be an array")
    parsed: list[BaselineEntry] = []
    seen: set[tuple[str, str, str, int | None]] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"baseline entry {index} is not an object")
        parsed_entry = _entry_from_payload(entry, index)
        identity = (
            parsed_entry.detector,
            parsed_entry.path,
            parsed_entry.commit,
            parsed_entry.line,
        )
        if identity in seen:
            raise ValueError(f"baseline entry {index} is a duplicate")
        seen.add(identity)
        parsed.append(parsed_entry)
    return parsed


def finding_kind(finding: Finding) -> str:
    """Classify a finding without reading verification-error text."""
    if finding.verified:
        return "verified"
    if finding.verification_error:
        return "unknown"
    return "unverified"


def evaluate(
    findings: Sequence[Finding],
    entries: Sequence[BaselineEntry],
    today: date,
) -> Evaluation:
    days_by_entry: list[tuple[BaselineEntry, int | None]] = []
    for entry in entries:
        expiry = entry.effective_expiry()
        days_by_entry.append(None if expiry is None else (expiry - today).days)
    dated = tuple(
        (entry, days)
        for entry, days in zip(entries, days_by_entry, strict=True)
        if days is not None
    )
    expired = tuple(entry for entry, days in dated if days <= 0)
    allowed: dict[tuple[str, str, str, int | None], int] = {}
    for entry, days in zip(entries, days_by_entry, strict=True):
        if days is not None and days <= 0:
            continue
        key = (entry.detector, entry.path, entry.commit, entry.line)
        previous = allowed.get(key)
        remaining = days if days is not None else _MAX_EXPIRY_DAYS + 1
        if previous is None or remaining < previous:
            allowed[key] = remaining

    failures: list[str] = []
    limit = today + timedelta(days=_MAX_EXPIRY_DAYS)
    for entry, _days in dated:
        if entry.expires is not None and entry.expires > limit:
            failures.append(
                "baseline expiry past upper limit: "
                f"{entry.detector} {entry.path} {entry.commit} line={entry.line} "
                f"expires={entry.expires.isoformat()}"
            )
    for entry, days in dated:
        if days <= 0:
            effective = entry.effective_expiry()
            assert effective is not None
            failures.append(
                "expired baseline entry: "
                f"{entry.detector} {entry.path} {entry.commit} line={entry.line} "
                f"effective_expiry={effective.isoformat()} "
                f"days_to_expiry={days}"
            )

    matched_count = 0
    unmatched_count = 0
    verified_count = 0
    unknown_count = 0
    unverified_count = 0
    matched: dict[tuple[str, str, str, int | None], int] = {}
    for finding in findings:
        key = (finding.detector, finding.path, finding.commit, finding.line)
        kind = finding_kind(finding)
        if kind == "verified":
            verified_count += 1
            failures.append(
                "verified result: "
                f"{finding.detector} {finding.path} {finding.commit} "
                f"line={finding.line}"
            )
        elif kind == "unknown":
            unknown_count += 1
        elif kind == "unverified":
            unverified_count += 1
        else:
            raise AssertionError(f"unhandled finding kind: {kind}")
        days = allowed.get(key)
        if days is None:
            unmatched_count += 1
            if kind != "unverified":
                failures.append(
                    "finding not in unexpired baseline: "
                    f"{finding.detector} {finding.path} {finding.commit} "
                    f"line={finding.line}"
                )
            continue
        matched_count += 1
        matched[key] = days

    soonest = min((days for days in days_by_entry if days is not None), default=None)
    matched_entries = tuple(
        MatchedEntry(detector, path, commit, line, days)
        for (detector, path, commit, line), days in sorted(
            matched.items(),
            key=lambda item: (
                item[0][0],
                item[0][1],
                item[0][2],
                item[0][3] is None,
                item[0][3] or 0,
            ),
        )
    )
    return Evaluation(
        ok=not failures,
        finding_count=len(findings),
        verified_count=verified_count,
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        expired_count=len(expired),
        baseline_count=len(entries),
        soonest_days_to_expiry=soonest,
        unverified_count=unverified_count,
        unknown_count=unknown_count,
        failures=tuple(failures),
        matched_entries=matched_entries,
    )


_NIGHTLY_RE = re.compile(
    r"^trufflehog_nightly total=(?P<total>\d+) verified=(?P<verified>\d+) "
    r"unverified=(?P<unverified>\d+) unknown=(?P<unknown>\d+) "
    r"baselined=(?P<baselined>\d+) new=(?P<new>\d+)$"
)


def nightly_count_line(result: Evaluation) -> str:
    """Return the single machine-readable nightly total."""
    return (
        "trufflehog_nightly "
        f"total={result.finding_count} "
        f"verified={result.verified_count} "
        f"unverified={result.unverified_count} "
        f"unknown={result.unknown_count} "
        f"baselined={result.matched_count} "
        f"new={result.unmatched_count}"
    )


def parse_nightly_counts(text: str) -> dict[str, int]:
    """Parse the one nightly total line from a matcher report."""
    matches = [
        line for line in text.splitlines() if line.startswith("trufflehog_nightly ")
    ]
    if len(matches) != 1:
        raise ValueError("expected one nightly count line")
    match = _NIGHTLY_RE.fullmatch(matches[0])
    if match is None:
        raise ValueError("nightly count line is not parseable")
    return {key: int(value) for key, value in match.groupdict().items()}


def format_summary(result: Evaluation) -> str:
    soonest = (
        "none"
        if result.soonest_days_to_expiry is None
        else str(result.soonest_days_to_expiry)
    )
    lines = [
        f"status: {'pass' if result.ok else 'fail'}",
        f"findings: {result.finding_count}",
        f"verified: {result.verified_count}",
        f"matched: {result.matched_count}",
        f"unmatched: {result.unmatched_count}",
        f"baseline_entries: {result.baseline_count}",
        f"expired_entries: {result.expired_count}",
        f"soonest_days_to_expiry: {soonest}",
    ]
    if result.failures:
        lines.append("failures:")
        lines.extend(f"- {item}" for item in result.failures)
    lines.append("matched_entries:")
    if result.matched_entries:
        lines.extend(
            f"- {item.detector} {item.path} {item.commit} "
            f"line={item.line} days={item.days_to_expiry}"
            for item in result.matched_entries
        )
    else:
        lines.append("- none")
    lines.append(nightly_count_line(result))
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None, stdin: TextIO | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument(
        "--today",
        help="UTC calendar date YYYY-MM-DD. Defaults to today's UTC date.",
    )
    args = parser.parse_args(argv)
    stream = sys.stdin if stdin is None else stdin
    try:
        if args.today is None:
            today = datetime.now(timezone.utc).date()
        else:
            today = _parse_date(args.today, "today")
        with open(args.baseline, encoding="utf-8") as baseline_file:
            entries = load_baseline(baseline_file.read())
        findings = parse_findings(stream)
        result = evaluate(findings, entries, today)
    except (OSError, ValueError) as exc:
        print(f"status: fail\nbaseline_or_scanner_error: {exc}", file=sys.stdout)
        return 1
    print(format_summary(result), end="")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
