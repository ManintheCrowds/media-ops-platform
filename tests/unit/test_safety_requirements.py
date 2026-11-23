"""Safety scans every requirement file, including a planted vulnerable pin."""

from __future__ import annotations

import importlib.util
import os
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


def _continuous_integration() -> bool:
    """Return whether this process is a CI run."""
    return any(
        os.environ.get(name, "").lower() == "true" for name in ("CI", "GITHUB_ACTIONS")
    )


def safety_missing_action(*, continuous_integration: bool) -> str:
    """Fail when CI has no Safety. Skip only outside CI."""
    if continuous_integration:
        return "fail"
    return "skip"


def _safety_installed() -> bool:
    return importlib.util.find_spec("safety") is not None


def _require_safety() -> None:
    if _safety_installed():
        return
    if (
        safety_missing_action(continuous_integration=_continuous_integration())
        == "fail"
    ):
        pytest.fail(
            "Safety is absent in CI; the planted-vulnerability test must fail, not skip"
        )
    pytest.skip("Safety is not installed outside CI")


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
        "pi-client/setup.py",
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
        return _completed(
            0,
            stdout='{"vulnerabilities": [], "ignored_vulnerabilities": []}\n',
        )

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


_CLEAN_JSON = '{"vulnerabilities": [], "ignored_vulnerabilities": []}\n'
_REPOSITORY_UNPINNED = {
    "education-service/requirements.txt": (
        "fastapi",
        "psycopg2-binary",
        "pydantic",
        "pydantic-settings",
    ),
    "home-cyber-risk/requirements.txt": ("psycopg2-binary",),
    "job-automation-service/requirements.txt": (
        "fastapi",
        "psycopg2-binary",
        "openai",
        "anthropic",
        "pydantic",
        "pydantic-settings",
    ),
    "monitoring/cursor-exporter/requirements.txt": ("prometheus-client",),
    "pi-client/requirements.txt": (
        "httpx",
        "aiofiles",
        "pyyaml",
        "pydantic",
        "fastapi",
        "uvicorn",
        "jinja2",
        "websockets",
        "cryptography",
        "pyjwt",
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
    ),
    "requirements.txt": (
        "fastapi",
        "psycopg2-binary",
        "arlo",
        "pydantic",
        "pydantic-settings",
    ),
    "security-service/requirements.txt": (
        "fastapi",
        "psycopg2-binary",
        "pydantic",
        "pydantic-settings",
    ),
}
_SETUP_UNPINNED = (
    "httpx",
    "aiofiles",
    "pyyaml",
    "pydantic",
    "fastapi",
    "uvicorn",
    "jinja2",
    "websockets",
    "cryptography",
    "pyjwt",
    "RPi.GPIO",
    "gpiozero",
    "picamera2",
    "pygame",
)


@pytest.mark.unit
def test_safety_command_checks_unpinned_requirements() -> None:
    command = safety_requirements_scan.safety_check_command(
        "python3",
        Path("requirements.txt"),
    )
    assert "--check-unpinned-requirements" in command
    assert command[command.index("--output") + 1] == "json"
    assert "--ignore" not in command


@pytest.mark.unit
def test_repository_unpinned_packages_are_explicit() -> None:
    for relative, expected in _REPOSITORY_UNPINNED.items():
        text = (_ROOT / relative).read_text(encoding="utf-8")
        problems = safety_requirements_scan.requirement_problems(text)
        assert problems.unsupported == ()
        assert problems.unpinned == expected
    pinned_sources = (
        "education-service/requirements.txt",
        "job-automation-service/requirements.txt",
        "requirements.txt",
    )
    for relative in pinned_sources:
        problems = safety_requirements_scan.requirement_problems(
            (_ROOT / relative).read_text(encoding="utf-8")
        )
        assert "python-jose" not in problems.unpinned
        assert "requests" not in problems.unpinned


@pytest.mark.unit
def test_setup_py_install_requires_and_extras_are_unpinned() -> None:
    source = (_ROOT / "pi-client" / "setup.py").read_text(encoding="utf-8")
    requirements = safety_requirements_scan.extract_setup_requirements(source)
    problems = safety_requirements_scan.requirement_problems("\n".join(requirements))
    assert problems.unsupported == ()
    assert problems.unpinned == _SETUP_UNPINNED


@pytest.mark.unit
def test_setup_py_is_scanned_without_being_executed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = tmp_path / "executed"
    setup = tmp_path / "setup.py"
    setup.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('ran', encoding='utf-8')\n"
        "from setuptools import setup\n"
        "setup(\n"
        "    install_requires=['requests==2.19.1'],\n"
        "    extras_require={'hardware': ['pygame>=2.5.0']},\n"
        ")\n",
        encoding="utf-8",
    )
    seen: list[str] = []

    def runner(path: Path, python: str) -> subprocess.CompletedProcess[str]:
        seen.append(path.read_text(encoding="utf-8"))
        return _completed(0, stdout=_CLEAN_JSON)

    monkeypatch.setattr(safety_requirements_scan, "run_safety_check", runner)
    code = safety_requirements_scan.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert not marker.exists()
    assert code == 1
    assert any("pygame>=2.5.0" in text for text in seen)
    assert any("requests==2.19.1" in text for text in seen)
    assert "setup.py" in captured.out
    assert "UNPINNED pygame" in captured.out
    assert "UNPINNED requests" not in captured.out


@pytest.mark.unit
def test_non_literal_setup_requirements_fail_closed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "setup.py").write_text(
        "reqs = ['flask>=1']\n"
        "from setuptools import setup\n"
        "setup(install_requires=reqs)\n",
        encoding="utf-8",
    )

    def fail_if_called(path: Path, python: str) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"Safety should not scan an unreadable setup.py: {path}")

    monkeypatch.setattr(safety_requirements_scan, "run_safety_check", fail_if_called)
    code = safety_requirements_scan.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 1
    assert "not a literal list" in captured.err


@pytest.mark.unit
def test_unpinned_requirement_fails_without_stopping_the_next_file(
    capsys: pytest.CaptureFixture[str],
) -> None:
    targets = [
        safety_requirements_scan.DependencyTarget(
            display="first/requirements.txt",
            requirement_file=Path("first"),
            unpinned=("fastapi",),
        ),
        safety_requirements_scan.DependencyTarget(
            display="second/requirements.txt",
            requirement_file=Path("second"),
        ),
    ]
    seen: list[Path] = []

    def runner(path: Path) -> subprocess.CompletedProcess[str]:
        seen.append(path)
        return _completed(0, stdout=_CLEAN_JSON)

    code = safety_requirements_scan.scan_dependency_targets(targets, runner)
    captured = capsys.readouterr()
    assert seen == [Path("first"), Path("second")]
    assert code == 1
    assert "UNPINNED fastapi" in captured.out
    assert "second/requirements.txt (exit 0)" in captured.out


@pytest.mark.unit
def test_ignored_safety_advisory_fails_the_scan(
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = (
        '{"vulnerabilities": [], "ignored_vulnerabilities": '
        '[{"package_name": "pyjwt", "vulnerability_id": "SFTY-20260930-08546"}]}\n'
    )
    target = safety_requirements_scan.DependencyTarget(
        display="pi-client/requirements.txt",
        requirement_file=Path("pi-client/requirements.txt"),
    )
    code = safety_requirements_scan.scan_dependency_targets(
        [target],
        lambda path: _completed(0, stdout=payload),
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "IGNORED pyjwt SFTY-20260930-08546" in captured.out


@pytest.mark.unit
def test_editable_requirement_is_not_silently_ignored(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "requirements.txt").write_text("-e .\n", encoding="utf-8")
    monkeypatch.setattr(
        safety_requirements_scan,
        "run_safety_check",
        lambda path, python: _completed(0, stdout=_CLEAN_JSON),
    )
    code = safety_requirements_scan.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 1
    assert "UNSUPPORTED -e ." in captured.out


def _locked_packages(text: str) -> dict[str, tuple[str, tuple[str, ...]]]:
    packages: dict[str, tuple[str, tuple[str, ...]]] = {}
    name: str | None = None
    version = ""
    hashes: list[str] = []

    def finish() -> None:
        if name is not None:
            packages[name.lower()] = (version, tuple(hashes))

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        continued = stripped.endswith("\\")
        body = stripped[:-1].strip() if continued else stripped
        if body.startswith("--hash="):
            hashes.append(body.split("=", 1)[1])
        else:
            finish()
            parsed_name, version = body.split("==")
            name = parsed_name.strip()
            hashes = []
        if not continued:
            finish()
            name = None
            hashes = []
    finish()
    return packages


def _assert_every_distribution_is_hash_locked(
    packages: dict[str, tuple[str, tuple[str, ...]]],
) -> None:
    assert packages
    for package_name, (version, hashes) in packages.items():
        assert version
        assert hashes, package_name
        for digest in hashes:
            assert digest.startswith("sha256:")
            assert len(digest) == len("sha256:") + 64


@pytest.mark.unit
def test_safety_tooling_is_hash_locked() -> None:
    pip_packages = _locked_packages(
        (_ROOT / "ci" / "pip-requirements.txt").read_text(encoding="utf-8")
    )
    safety_packages = _locked_packages(
        (_ROOT / "ci" / "safety-requirements.txt").read_text(encoding="utf-8")
    )
    pytest_packages = _locked_packages(
        (_ROOT / "ci" / "safety-pytest-requirements.txt").read_text(encoding="utf-8")
    )
    _assert_every_distribution_is_hash_locked(pip_packages)
    _assert_every_distribution_is_hash_locked(safety_packages)
    _assert_every_distribution_is_hash_locked(pytest_packages)
    assert pip_packages["pip"][0] == "26.3"
    assert safety_packages["safety"][0] == "3.6.2"
    assert safety_packages["filelock"][0] == "3.32.7"
    assert "pytest" not in safety_packages
    assert pytest_packages["pytest"][0] == "9.1.1"
    assert "safety" not in pytest_packages


@pytest.mark.unit
def test_scanner_lockfiles_are_not_application_manifests(tmp_path: Path) -> None:
    tooling = tmp_path / "ci"
    tooling.mkdir()
    (tooling / "safety-requirements.txt").write_text(
        "filelock==3.32.7\n",
        encoding="utf-8",
    )
    (tooling / "pip-requirements.txt").write_text("pip==26.3\n", encoding="utf-8")
    application = tmp_path / "requirements.txt"
    application.write_text("requests==2.32.4\n", encoding="utf-8")
    found = safety_requirements_scan.discover_dependency_files(tmp_path)
    assert found == [application]
    repo_files = {
        path.relative_to(_ROOT).as_posix()
        for path in safety_requirements_scan.discover_dependency_files(_ROOT)
    }
    assert "ci/safety-requirements.txt" not in repo_files
    assert "ci/pip-requirements.txt" not in repo_files
    assert "ci/safety-pytest-requirements.txt" not in repo_files


@pytest.mark.unit
def test_self_test_is_outside_the_scan_environment() -> None:
    job = _workflow_job("security-scan")
    assert "--require-hashes" in job
    assert "--only-binary=:all:" in job
    assert "--no-deps" in job
    assert "--upgrade pip" not in job
    assert "install safety==" not in job
    assert "ci/safety-requirements.txt" in job
    assert "ci/pip-requirements.txt" in job
    scan_at = job.index("Check requirement files for vulnerabilities")
    self_test_at = job.index("Run Safety self-test")
    assert scan_at < self_test_at
    scan_step = job[scan_at:self_test_at]
    assert "pytest" not in scan_step
    assert "safety_requirements_scan.py" in scan_step
    assert "RUNNER_TEMP/safety/bin/python" in scan_step
    self_test = job[self_test_at:]
    assert "safety-self-test" in self_test
    assert "pytest" in self_test
    assert "!cancelled()" in self_test
    assert "safety_requirements_scan.py" not in self_test


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
    assert "aaa/requirements.txt (exit 0)" in combined
    assert "zzz/requirements.txt" in combined
    assert "ADVISORY requests" in combined
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
    assert "aaa/requirements.txt" in combined
    assert "zzz/requirements.txt (exit 0)" in combined
    assert "ADVISORY requests" in combined
    assert "filelock" not in combined.lower()


@pytest.mark.unit
def test_absent_safety_fails_in_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys.modules[__name__], "_safety_installed", lambda: False)
    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.fail.Exception, match="must fail, not skip"):
        _require_safety()


@pytest.mark.unit
def test_absent_safety_skips_outside_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys.modules[__name__], "_safety_installed", lambda: False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(pytest.skip.Exception):
        _require_safety()


@pytest.mark.unit
def test_github_actions_counts_as_ci_for_a_missing_safety(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys.modules[__name__], "_safety_installed", lambda: False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert safety_missing_action(continuous_integration=True) == "fail"
    with pytest.raises(pytest.fail.Exception, match="must fail, not skip"):
        _require_safety()


@pytest.mark.safety_cli
def test_planted_vulnerable_requirement_fails(tmp_path: Path) -> None:
    _require_safety()
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
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "requests" in combined
    assert "filelock" not in combined.lower()
