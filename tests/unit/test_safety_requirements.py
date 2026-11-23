"""Safety scans every requirement file, including a planted vulnerable pin."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / ".github" / "scripts" / "safety_requirements_scan.py"
_WORKFLOW = _ROOT / ".github" / "workflows" / "tests.yml"

_spec = importlib.util.spec_from_file_location("safety_requirements_scan", _SCRIPT)
assert _spec is not None and _spec.loader is not None
safety_requirements_scan = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = safety_requirements_scan
_spec.loader.exec_module(safety_requirements_scan)


def _workflow_job(name: str) -> str:
    text = _WORKFLOW.read_text(encoding="utf-8")
    marker = f"  {name}:\n"
    start = text.index(marker)
    rest = text[start + len(marker) :]
    match = re.search(r"\n  [A-Za-z0-9-]+:\n", rest)
    end = start + len(marker) + (match.start() if match else len(rest))
    return text[start:end]


def _completed(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _require_safety() -> None:
    if importlib.util.find_spec("safety") is None:
        pytest.skip("safety is installed in the security-scan job")


@pytest.mark.unit
def test_scan_continues_after_the_first_file_fails(
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = Path("education-service/requirements.txt")
    second = Path("requirements.txt")
    seen: list[Path] = []

    def runner(path: Path) -> subprocess.CompletedProcess[str]:
        seen.append(path)
        if path == first:
            return _completed(64, stdout="vuln-first\n")
        return _completed(0, stdout="clean-second\n")

    code = safety_requirements_scan.scan_requirement_files([first, second], runner)
    captured = capsys.readouterr()
    assert seen == [first, second]
    assert code == 1
    assert "vuln-first" in captured.out
    assert "clean-second" in captured.out
    assert second.as_posix() in captured.out


@pytest.mark.unit
def test_scan_reports_a_failure_in_the_second_file(
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = Path("aaa/requirements.txt")
    second = Path("zzz/requirements.txt")
    seen: list[Path] = []

    def runner(path: Path) -> subprocess.CompletedProcess[str]:
        seen.append(path)
        if path == second:
            return _completed(64, stdout="vuln-second\n")
        return _completed(0, stdout="clean-first\n")

    code = safety_requirements_scan.scan_requirement_files([first, second], runner)
    captured = capsys.readouterr()
    assert seen == [first, second]
    assert code == 1
    assert "clean-first" in captured.out
    assert "vuln-second" in captured.out


@pytest.mark.unit
def test_scan_succeeds_only_when_every_file_succeeds() -> None:
    files = [Path("a/requirements.txt"), Path("b/requirements.txt")]
    code = safety_requirements_scan.scan_requirement_files(
        files,
        lambda path: _completed(0, stdout="ok\n"),
    )
    assert code == 0


@pytest.mark.unit
def test_discovery_includes_requirement_variants_and_lockfiles(tmp_path: Path) -> None:
    nested = tmp_path / "service"
    nested.mkdir()
    exact = nested / "requirements.txt"
    exact.write_text("requests==2.32.4\n", encoding="utf-8")
    development = tmp_path / "requirements-dev.txt"
    development.write_text("pytest==9.1.1\n", encoding="utf-8")
    constraints = tmp_path / "constraints.txt"
    constraints.write_text("urllib3==2.8.0\n", encoding="utf-8")
    lockfile = tmp_path / "poetry.lock"
    lockfile.write_text("# lock\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not a manifest\n", encoding="utf-8")
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "requirements.txt").write_text("requests==2.19.1\n", encoding="utf-8")
    venv_dir = tmp_path / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    (venv_dir / "requirements.txt").write_text("filelock==3.32.7\n", encoding="utf-8")

    found = safety_requirements_scan.discover_dependency_files(tmp_path)
    assert found == [constraints, lockfile, development, exact]


@pytest.mark.unit
def test_repository_requirement_files_are_discovered() -> None:
    found = {
        path.relative_to(_ROOT).as_posix()
        for path in safety_requirements_scan.discover_dependency_files(_ROOT)
    }
    assert found == {
        "education-service/requirements.txt",
        "home-cyber-risk/requirements.txt",
        "job-automation-service/requirements.txt",
        "monitoring/cursor-exporter/requirements.txt",
        "pi-client/requirements.txt",
        "requirements.txt",
        "security-service/requirements.txt",
    }


@pytest.mark.unit
def test_empty_dependency_list_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "README.md").write_text("no dependencies\n", encoding="utf-8")
    code = safety_requirements_scan.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 1
    assert "no dependency files found" in captured.err


@pytest.mark.unit
def test_lockfile_is_not_silently_skipped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    lockfile = tmp_path / "uv.lock"
    lockfile.write_text("# lock\n", encoding="utf-8")

    def fail_if_called(path: Path, python: str) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"Safety should not be asked to ignore {path}")

    monkeypatch.setattr(safety_requirements_scan, "run_safety_check", fail_if_called)
    code = safety_requirements_scan.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 1
    assert "refusing to skip unscanned dependency file" in captured.err
    assert "uv.lock" in captured.err


@pytest.mark.unit
def test_variant_requirement_file_is_scanned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    requirement = tmp_path / "requirements-dev.txt"
    requirement.write_text("pytest==9.1.1\n", encoding="utf-8")
    seen: list[Path] = []

    def runner(path: Path, python: str) -> subprocess.CompletedProcess[str]:
        seen.append(path)
        return _completed(0, stdout="ok\n")

    monkeypatch.setattr(safety_requirements_scan, "run_safety_check", runner)
    code = safety_requirements_scan.main(["--root", str(tmp_path)])
    assert code == 0
    assert seen == [requirement.resolve()]


@pytest.mark.unit
def test_security_scan_uses_the_collector_script() -> None:
    job = _workflow_job("security-scan")
    assert "safety_requirements_scan.py" in job
    assert "for req in" not in job
    scan_step = job.split("Check requirement files for vulnerabilities", 1)[1]
    assert "|| true" not in scan_step
    assert "safety_requirements_scan.py" in scan_step


@pytest.mark.safety_cli
def test_second_planted_file_is_scanned_when_only_it_is_vulnerable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _require_safety()
    clean = tmp_path / "aaa" / "requirements.txt"
    vulnerable = tmp_path / "zzz" / "requirements.txt"
    clean.parent.mkdir()
    vulnerable.parent.mkdir()
    clean.write_text("certifi==2026.11.20\n", encoding="utf-8")
    vulnerable.write_text("requests==2.19.1\n", encoding="utf-8")

    code = safety_requirements_scan.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert code == 1
    assert clean.as_posix() in combined
    assert "(exit 0)" in combined
    assert vulnerable.as_posix() in combined
    assert "requests" in combined
    assert "filelock" not in combined.lower()


@pytest.mark.safety_cli
def test_scan_continues_after_a_real_vulnerability(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _require_safety()
    vulnerable = tmp_path / "aaa" / "requirements.txt"
    clean = tmp_path / "zzz" / "requirements.txt"
    vulnerable.parent.mkdir()
    clean.parent.mkdir()
    vulnerable.write_text("requests==2.19.1\n", encoding="utf-8")
    clean.write_text("certifi==2026.11.20\n", encoding="utf-8")

    code = safety_requirements_scan.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert code == 1
    assert vulnerable.as_posix() in combined
    assert clean.as_posix() in combined
    assert f"{clean.as_posix()} (exit 0)" in combined
    assert "requests" in combined
    assert "filelock" not in combined.lower()


@pytest.mark.safety_cli
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
