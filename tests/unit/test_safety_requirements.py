"""Safety scans requirement files, including a planted vulnerable pin."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_planted_vulnerable_requirement_fails(tmp_path: Path) -> None:
    requirement = tmp_path / "requirements.txt"
    requirement.write_text("requests==2.19.1\n", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "safety",
            "check",
            "-r",
            str(requirement),
            "--output",
            "bare",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 and "No module named safety" in completed.stderr:
        pytest.skip("safety is installed in the security-scan job")
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "requests" in combined
    assert "filelock" not in combined.lower()
