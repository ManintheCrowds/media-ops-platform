#!/usr/bin/env python3
"""Check the scoped, expiring Safety ignore for python-jose.

Safety 3.8 `safety check` reads `.safety-policy.yml` (schema used by the
check command). This script checks that file and, with `--execute`, runs
`safety check` against a local database so the ignore can be shown to cover
one advisory and to fail after it expires.

Run trusted invocations with PYTHONSAFEPATH=1 and python3 -I.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence

ADVISORY_ID = "SFTY-20260903-64758"
PACKAGE = "python-jose"
GHSA_ID = "GHSA-3qf3-8w2g-rqmx"
PYSEC_ID = "PYSEC-2026-4298"
EXPIRES = datetime(2026, 12, 23)
OTHER_ADVISORY_ID = "999001"
REQUESTS_ADVISORY_ID = "90553"
_SECURITY_KEYS = frozenset(
    {
        "ignore-cvss-severity-below",
        "ignore-cvss-unknown-severity",
        "continue-on-vulnerability-error",
        "ignore-vulnerabilities",
    }
)
_ENTRY_KEYS = frozenset({"reason", "expires"})
_ROOT = Path(__file__).resolve().parents[2]
_POLICY_PATH = _ROOT / ".safety-policy.yml"


@dataclass(frozen=True)
class IgnoreEntry:
    """One Safety ignore-vulnerabilities entry."""

    advisory_id: str
    reason: str
    expires: datetime


@dataclass(frozen=True)
class Policy:
    """The subset of a Safety check policy this repo allows."""

    severity_below: int
    ignore_unknown_severity: bool
    continue_on_error: bool
    ignores: tuple[IgnoreEntry, ...]


@dataclass(frozen=True)
class Finding:
    """An advisory hit passed to the same ignore rule Safety applies."""

    advisory_id: str
    package: str


def ignore_is_active(expires: datetime, now: datetime) -> bool:
    """Return whether Safety would still apply an ignore at `now`.

    Safety compares the parsed expiry with `datetime.utcnow()` using `>`.
    A date-only expiry is midnight, so 2026-12-23 00:00:00 UTC is already expired.
    """

    return expires > now


def parse_policy(text: str) -> Policy:
    """Parse the repo's Safety check policy. Reject keys Safety would not use here."""

    security: dict[str, str] = {}
    ignores: dict[str, dict[str, str]] = {}
    section = "root"
    current_id: str | None = None

    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith(" ") and raw.replace(" ", "") == "":
            raise ValueError(f"line {line_number} is blank but indented")
        indent = len(raw) - len(raw.lstrip(" "))
        if "\t" in raw[:indent]:
            raise ValueError(f"line {line_number} uses tabs")
        content = raw.strip()
        if section == "root":
            if content != "security:":
                raise ValueError(f"line {line_number} is outside the security block")
            section = "security"
            continue
        if indent == 2 and content.endswith(":"):
            key = content[:-1]
            if key not in _SECURITY_KEYS:
                raise ValueError(
                    f"line {line_number} has unsupported security key {key}"
                )
            if key == "ignore-vulnerabilities":
                section = "ignores"
                current_id = None
                continue
            raise ValueError(f"line {line_number} is missing a value for {key}")
        if indent == 2 and ": " in content:
            key, value = content.split(": ", 1)
            if key not in _SECURITY_KEYS or key == "ignore-vulnerabilities":
                raise ValueError(
                    f"line {line_number} has unsupported security key {key}"
                )
            if key in security:
                raise ValueError(f"duplicate security key {key}")
            security[key] = value
            section = "security"
            current_id = None
            continue
        if indent == 4 and content.endswith(":") and section in {"ignores", "entry"}:
            advisory_id = content[:-1]
            if advisory_id in ignores:
                raise ValueError(f"duplicate ignore id {advisory_id}")
            ignores[advisory_id] = {}
            current_id = advisory_id
            section = "entry"
            continue
        if (
            indent == 6
            and section == "entry"
            and current_id is not None
            and ": " in content
        ):
            key, value = content.split(": ", 1)
            if key not in _ENTRY_KEYS:
                raise ValueError(f"line {line_number} has unsupported ignore key {key}")
            if key in ignores[current_id]:
                raise ValueError(f"duplicate {key} for {current_id}")
            ignores[current_id][key] = value
            continue
        raise ValueError(f"line {line_number} does not match the policy schema")

    present = set(security)
    if ignores:
        present.add("ignore-vulnerabilities")
    absent = _SECURITY_KEYS - present
    if absent:
        names = ", ".join(sorted(absent))
        raise ValueError(f"policy is missing {names}")

    entries: list[IgnoreEntry] = []
    for advisory_id, fields in ignores.items():
        absent_fields = _ENTRY_KEYS - set(fields)
        if absent_fields:
            names = ", ".join(sorted(absent_fields))
            raise ValueError(f"{advisory_id} is missing {names}")
        reason = _unquote(fields["reason"])
        expires = _parse_expiry(_unquote(fields["expires"]))
        entries.append(IgnoreEntry(advisory_id, reason, expires))
    return Policy(
        severity_below=_parse_severity(security["ignore-cvss-severity-below"]),
        ignore_unknown_severity=_parse_bool(security["ignore-cvss-unknown-severity"]),
        continue_on_error=_parse_bool(security["continue-on-vulnerability-error"]),
        ignores=tuple(entries),
    )


def policy_problems(policy: Policy) -> tuple[str, ...]:
    """Return shape problems. An empty tuple means the ignore is the one approved entry."""

    problems: list[str] = []
    if policy.severity_below != 0:
        problems.append("ignore-cvss-severity-below must stay 0")
    if policy.ignore_unknown_severity:
        problems.append("ignore-cvss-unknown-severity must stay false")
    if policy.continue_on_error:
        problems.append("continue-on-vulnerability-error must stay false")
    if len(policy.ignores) != 1:
        problems.append(f"expected one ignore, found {len(policy.ignores)}")
        return tuple(problems)
    entry = policy.ignores[0]
    if entry.advisory_id != ADVISORY_ID:
        problems.append(f"ignore id must be {ADVISORY_ID}")
    if entry.expires != EXPIRES:
        problems.append("expires must be 2026-12-23")
    reason = entry.reason
    for needle in (PACKAGE, GHSA_ID, PYSEC_ID, "PyJWT"):
        if needle not in reason:
            problems.append(f"reason must name {needle}")
    return tuple(problems)


def classify(
    policy: Policy, findings: Sequence[Finding], now: datetime
) -> tuple[tuple[Finding, ...], tuple[Finding, ...]]:
    """Split findings into ignored and still-reported using Safety's id-and-expiry rule."""

    active = {
        entry.advisory_id: entry
        for entry in policy.ignores
        if ignore_is_active(entry.expires, now)
    }
    ignored: list[Finding] = []
    reported: list[Finding] = []
    for finding in findings:
        if finding.advisory_id in active:
            ignored.append(finding)
        else:
            reported.append(finding)
    return tuple(ignored), tuple(reported)


def load_policy(path: Path = _POLICY_PATH) -> Policy:
    """Load the checked-in policy file."""

    return parse_policy(path.read_text(encoding="utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the policy and, when asked, run Safety against a fixture database."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-policy",
        action="store_true",
        help="Fail when the checked-in ignore is missing, too wide, or expired.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run safety check against a local database and the checked-in policy.",
    )
    parser.add_argument(
        "--now",
        help="UTC timestamp YYYY-MM-DDTHH:MM:SS used by --check-policy. Default: current UTC.",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=_POLICY_PATH,
        help="Policy file to read. Default: the repo root .safety-policy.yml.",
    )
    args = parser.parse_args(argv)
    check_policy = args.check_policy or not args.execute
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError) as exc:
        print(f"policy error: {exc}", file=sys.stderr)
        return 1
    problems = policy_problems(policy)
    if problems:
        for problem in problems:
            print(f"policy error: {problem}", file=sys.stderr)
        return 1
    if args.execute:
        code = _execute(policy)
        if code != 0:
            return code
    if check_policy:
        now = _parse_now(args.now) if args.now else datetime.utcnow()
        entry = policy.ignores[0]
        if not ignore_is_active(entry.expires, now):
            print(
                f"python-jose ignore {ADVISORY_ID} expired at {entry.expires.date().isoformat()}",
                file=sys.stderr,
            )
            return 1
    return 0


def _execute(policy: Policy) -> int:
    safety = shutil.which("safety")
    if safety is None:
        print("safety is not on PATH", file=sys.stderr)
        return 1
    now = datetime.utcnow()
    active = ignore_is_active(policy.ignores[0].expires, now)
    with tempfile.TemporaryDirectory(prefix="jose-safety-") as tmp:
        root = Path(tmp)
        db = root / "db"
        db.mkdir()
        _write_database(db)
        jose_req = root / "jose.txt"
        jose_req.write_text("python-jose==3.5.0\n", encoding="utf-8")
        old_req = root / "requests-old.txt"
        old_req.write_text("requests==2.32.4\n", encoding="utf-8")
        new_req = root / "requests-new.txt"
        new_req.write_text("requests==2.33.0\n", encoding="utf-8")
        one_db = root / "db-one"
        one_db.mkdir()
        _write_database(one_db, include_other_jose=False)
        expired = root / "expired.yml"
        expired.write_text(
            _POLICY_PATH.read_text(encoding="utf-8").replace(
                'expires: "2026-12-23"', 'expires: "2020-01-01"'
            ),
            encoding="utf-8",
        )
        checks = (
            _SafetyCase(
                "unexpired policy ignores only the python-jose advisory",
                db=one_db,
                requirements=jose_req,
                policy=_POLICY_PATH,
                expected_code=0 if active else 64,
                ignored=(ADVISORY_ID,) if active else (),
                reported=() if active else (ADVISORY_ID,),
            ),
            _SafetyCase(
                "expired policy reports the python-jose advisory",
                db=one_db,
                requirements=jose_req,
                policy=expired,
                expected_code=64,
                ignored=(),
                reported=(ADVISORY_ID,),
            ),
            _SafetyCase(
                "a second python-jose advisory is not ignored",
                db=db,
                requirements=jose_req,
                policy=_POLICY_PATH,
                expected_code=64,
                ignored=(ADVISORY_ID,) if active else (),
                reported=(
                    (OTHER_ADVISORY_ID,) if active else (ADVISORY_ID, OTHER_ADVISORY_ID)
                ),
            ),
            _SafetyCase(
                "requests 2.32.4 advisory stays unignored",
                db=db,
                requirements=old_req,
                policy=_POLICY_PATH,
                expected_code=64,
                ignored=(),
                reported=(REQUESTS_ADVISORY_ID,),
            ),
            _SafetyCase(
                "requests 2.33.0 is outside Safety 90553",
                db=db,
                requirements=new_req,
                policy=_POLICY_PATH,
                expected_code=0,
                ignored=(),
                reported=(),
            ),
        )
        for case in checks:
            error = _run_safety_case(safety, case)
            if error:
                print(error, file=sys.stderr)
                return 1
    return 0


@dataclass(frozen=True)
class _SafetyCase:
    label: str
    db: Path
    requirements: Path
    policy: Path
    expected_code: int
    ignored: tuple[str, ...]
    reported: tuple[str, ...]


def _run_safety_case(safety: str, case: _SafetyCase) -> str | None:
    completed = subprocess.run(
        [
            safety,
            "--disable-optional-telemetry",
            "check",
            "-r",
            str(case.requirements),
            "--db",
            str(case.db),
            "--policy-file",
            str(case.policy),
            "--output",
            "json",
            "--disable-audit-and-monitor",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != case.expected_code:
        return (
            f"{case.label}: safety exited {completed.returncode}, "
            f"expected {case.expected_code}"
        )
    try:
        report = _first_json_object(completed.stdout)
    except ValueError as exc:
        return f"{case.label}: {exc}"
    ignored = _ids(report.get("ignored_vulnerabilities"))
    reported = _ids(report.get("vulnerabilities"))
    if ignored != set(case.ignored) or reported != set(case.reported):
        return f"{case.label}: ignored {sorted(ignored)} reported {sorted(reported)}"
    for item in report.get("ignored_vulnerabilities") or []:
        if item.get("package_name") != PACKAGE:
            return f"{case.label}: ignored package {item.get('package_name')}"
    return None


def _ids(items: object) -> set[str]:
    if not isinstance(items, list):
        return set()
    found: set[str] = set()
    for item in items:
        if isinstance(item, dict) and item.get("vulnerability_id") is not None:
            found.add(str(item["vulnerability_id"]))
    return found


def _first_json_object(text: str) -> Mapping[str, object]:
    start = text.find("{")
    if start < 0:
        raise ValueError("safety stdout had no JSON object")
    payload, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(payload, dict):
        raise ValueError("safety JSON report was not an object")
    return payload


def _write_database(directory: Path, include_other_jose: bool = True) -> None:
    meta = {
        "schema_version": "2.0.0",
        "base_domain": "https://getsafety.com",
        "packages": {
            PACKAGE: {
                "insecure_versions": ["3.5.0"],
                "secure_versions": [],
                "latest_version": "3.5.0",
                "latest_secure_version": "",
                "more_info_path": "/p/pypi/python-jose/",
            },
            "requests": {
                "insecure_versions": ["2.32.4"],
                "secure_versions": ["2.33.0"],
                "latest_version": "2.33.0",
                "latest_secure_version": "2.33.0",
                "more_info_path": "/p/pypi/requests/",
            },
        },
    }
    jose_entries = [
        {
            "advisory": "algorithm confusion via DER-encoded public keys",
            "ids": [
                {"type": "pyup", "id": ADVISORY_ID},
                {"type": "cve", "id": "CVE-2026-85394"},
            ],
            "specs": ["<=3.5.0"],
            "more_info_path": f"/v/{ADVISORY_ID}/97c",
        }
    ]
    if include_other_jose:
        jose_entries.append(
            {
                "advisory": "synthetic second python-jose advisory",
                "ids": [{"type": "pyup", "id": int(OTHER_ADVISORY_ID)}],
                "specs": ["<=3.5.0"],
                "more_info_path": f"/v/{OTHER_ADVISORY_ID}/97c",
            }
        )
    full = {
        "meta": meta,
        "vulnerable_packages": {
            PACKAGE: jose_entries,
            "requests": [
                {
                    "advisory": "extract_zipped_paths temporary file reuse",
                    "ids": [
                        {"type": "pyup", "id": int(REQUESTS_ADVISORY_ID)},
                        {"type": "cve", "id": "CVE-2026-25645"},
                    ],
                    "specs": [">=2.19.0,<2.33.0"],
                    "more_info_path": f"/v/{REQUESTS_ADVISORY_ID}/97c",
                }
            ],
        },
    }
    short = {
        "meta": meta,
        "vulnerable_packages": {
            PACKAGE: ["<=3.5.0"],
            "requests": [">=2.19.0,<2.33.0"],
        },
    }
    (directory / "insecure.json").write_text(json.dumps(short), encoding="utf-8")
    (directory / "insecure_full.json").write_text(json.dumps(full), encoding="utf-8")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"expected true or false, got {value}")


def _parse_severity(value: str) -> int:
    if value != "0":
        raise ValueError("ignore-cvss-severity-below must be 0")
    return 0


def _parse_expiry(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"expires {value} is not YYYY-MM-DD") from exc


def _parse_now(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    except ValueError as exc:
        raise SystemExit(
            f"policy error: --now must be YYYY-MM-DDTHH:MM:SS ({exc})"
        ) from exc


if __name__ == "__main__":
    sys.exit(main())
