# PURPOSE: Import-smoke a service requirements.txt after isolated pip install (PF-REPO-11 CI).
# DEPENDENCIES: Run with cwd = service directory that contains requirements.txt.
# MODIFICATION NOTES: 2026-07-20 — extracted from inline workflow heredoc for YAML safety.

from __future__ import annotations

import importlib
import pathlib
import re
import sys


def main() -> int:
    req_path = pathlib.Path("requirements.txt")
    if not req_path.is_file():
        print("requirements.txt missing", file=sys.stderr)
        return 1
    req = req_path.read_text(encoding="utf-8")
    mapping = {
        "psycopg2-binary": "psycopg2",
        "python-dotenv": "dotenv",
        "python-dateutil": "dateutil",
        "python-multipart": "multipart",
        "python-telegram-bot": "telegram",
        "pyyaml": "yaml",
        "beautifulsoup4": "bs4",
        "Pillow": "PIL",
    }
    skip = {
        "pytest",
        "pytest-asyncio",
        "pytest-mock",
        "pytest-cov",
        "black",
        "flake8",
        "mypy",
    }
    names: list[str] = []
    for line in req.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = re.split(r"[<>=!\[]", line, maxsplit=1)[0].strip()
        if pkg.lower() in skip:
            continue
        names.append(mapping.get(pkg, pkg.replace("-", "_")))
    if "aiosmtplib" in req:
        importlib.import_module("aiosmtplib")
        print("aiosmtplib: OK")
    failed: list[str] = []
    for name in sorted(set(names)):
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 — report all import gaps
            failed.append(f"{name}: {exc}")
    if failed:
        print("Import failures:\n" + "\n".join(failed), file=sys.stderr)
        return 1
    print(f"Import smoke OK ({len(set(names))} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
