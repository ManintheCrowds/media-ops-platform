#!/usr/bin/env python3
"""Match scheduled TruffleHog JSON to an expiring known-findings baseline.

The scheduled job is the only caller. A run passes only when every finding
matches an unexpired baseline entry by detector, path, and commit. Any
verified result fails, including one whose location is in the baseline.
An expired baseline entry fails the run even when no finding matches it.

Scanner JSON includes secret material. This script reads detector name,
verified flag, file path, commit, and line, and never prints anything else.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Mapping, Sequence, TextIO

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_EVIDENCE_RE = re.compile(r"^https://\S+$")
_ENTRY_FIELDS = frozenset(
    {"detector", "path", "commit", "line", "expires", "closed_on", "reason", "evidence"}
)


@dataclass(frozen=True)
class Finding:
    detector: str
    path: str
    commit: str
    verified: bool
    line: int | None


@dataclass(frozen=True)
class BaselineEntry:
    detector: str
    path: str
    commit: str
    expires: date
    closed_on: date | None
    reason: str
    line: int | None
    evidence: str | None

    def effective_expiry(self) -> date:
        if self.closed_on is not None:
            return self.closed_on
        return self.expires


@dataclass(frozen=True)
class MatchedEntry:
    detector: str
    path: str
    commit: str
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
    return Finding(
        detector=detector,
        path=path,
        commit=commit.lower(),
        verified=verified,
        line=line,
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
    if "expires" not in payload:
        raise ValueError(f"baseline entry {index} missing expires")
    expires = _parse_date(payload.get("expires"), f"baseline entry {index} expires")
    closed_on = _optional_date(
        payload.get("closed_on"), f"baseline entry {index} closed_on"
    )
    if closed_on is not None and closed_on > expires:
        raise ValueError(f"baseline entry {index} closed_on is after expires")
    line = payload.get("line")
    if line is not None and (not isinstance(line, int) or isinstance(line, bool)):
        raise ValueError(f"baseline entry {index} line must be an integer")
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


def evaluate(
    findings: Sequence[Finding],
    entries: Sequence[BaselineEntry],
    today: date,
) -> Evaluation:
    days_by_entry = tuple(
        (entry, (entry.effective_expiry() - today).days) for entry in entries
    )
    expired = tuple(entry for entry, days in days_by_entry if days <= 0)
    allowed: dict[tuple[str, str, str], int] = {}
    for entry, days in days_by_entry:
        if days <= 0:
            continue
        key = (entry.detector, entry.path, entry.commit)
        previous = allowed.get(key)
        if previous is None or days < previous:
            allowed[key] = days

    failures: list[str] = []
    for entry, days in days_by_entry:
        if days <= 0:
            failures.append(
                "expired baseline entry: "
                f"{entry.detector} {entry.path} {entry.commit} "
                f"effective_expiry={entry.effective_expiry().isoformat()} "
                f"days_to_expiry={days}"
            )

    matched_count = 0
    unmatched_count = 0
    verified_count = 0
    matched: dict[tuple[str, str, str], int] = {}
    for finding in findings:
        key = (finding.detector, finding.path, finding.commit)
        if finding.verified:
            verified_count += 1
            failures.append(
                f"verified result: {finding.detector} {finding.path} {finding.commit}"
            )
        days = allowed.get(key)
        if days is None:
            unmatched_count += 1
            failures.append(
                "finding not in unexpired baseline: "
                f"{finding.detector} {finding.path} {finding.commit}"
            )
            continue
        matched_count += 1
        matched[key] = days

    soonest = min((days for _, days in days_by_entry), default=None)
    matched_entries = tuple(
        MatchedEntry(detector, path, commit, days)
        for (detector, path, commit), days in sorted(matched.items())
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
        failures=tuple(failures),
        matched_entries=matched_entries,
    )


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
            f"- {item.detector} {item.path} {item.commit} days={item.days_to_expiry}"
            for item in result.matched_entries
        )
    else:
        lines.append("- none")
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
