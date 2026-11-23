"""The gitleaks workflow executes the base revision's scan script."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
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
    assert "||  true" not in text
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


def _run_block(text: str, step_name: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.strip().endswith(f"name: {step_name}"):
            continue
        for cursor in range(index, min(index + 20, len(lines))):
            if lines[cursor].strip() != "run: |":
                continue
            indent = len(lines[cursor + 1]) - len(lines[cursor + 1].lstrip(" "))
            body: list[str] = []
            for raw in lines[cursor + 1 :]:
                if raw.strip() and (len(raw) - len(raw.lstrip(" "))) < indent:
                    break
                body.append(raw[indent:] if len(raw) >= indent else raw.lstrip(" "))
            return "\n".join(body) + "\n"
    raise AssertionError(step_name)


def test_gate_job_runs_no_checkout_tests() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    gate, tests = text.split("  gitleaks-tests:", 1)
    gate_job = gate.split("  gitleaks:", 1)[1]
    assert "pytest" not in gate_job
    assert "tests/security" not in gate_job
    assert "persist-credentials: false" in gate_job
    assert "GITLEAKS_BIN=" not in gate_job
    assert "GITLEAKS_BIN:" not in gate_job
    assert "/usr/local/bin/gitleaks" in gate_job
    assert "pytest==9.1.1" in tests


def test_materialize_executes_the_base_script(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.check_call(["git", "-C", str(repo), "init", "-q"])
    subprocess.check_call(
        ["git", "-C", str(repo), "config", "user.email", "dev@example.invalid"]
    )
    subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "dev"])
    script = repo / ".github" / "scripts"
    script.mkdir(parents=True)
    (script / "gitleaks_ci.py").write_text("print('base-script')\n", encoding="utf-8")
    (repo / ".gitleaks.toml").write_text('title = "base"\n', encoding="utf-8")
    subprocess.check_call(["git", "-C", str(repo), "add", "."])
    subprocess.check_call(["git", "-C", str(repo), "commit", "-q", "-m", "base"])
    base = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    (script / "gitleaks_ci.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    subprocess.check_call(["git", "-C", str(repo), "add", "."])
    subprocess.check_call(["git", "-C", str(repo), "commit", "-q", "-m", "head"])
    runner = tmp_path / "runner"
    runner.mkdir()
    body = _run_block(
        _WORKFLOW.read_text(encoding="utf-8"), "Materialize base scan gate"
    )
    completed = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", body],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GATE_SHA": base,
            "RUNNER_TEMP": str(runner),
        },
    )
    assert completed.returncode == 0, completed.stderr
    written = (runner / "scan" / "gitleaks_ci.py").read_text(encoding="utf-8")
    assert written == "print('base-script')\n"
    assert "raise SystemExit(0)" not in written


def test_run_step_checks_the_absolute_binary_before_scan(tmp_path: Path) -> None:
    fake_bin = tmp_path / "fakebin"
    fake_bin.mkdir()
    fake = fake_bin / "gitleaks"
    fake.write_text("#!/bin/sh\necho FAKE\n", encoding="utf-8")
    fake.chmod(0o755)
    runner = tmp_path / "runner"
    scan = runner / "scan"
    scan.mkdir(parents=True)
    (scan / "gitleaks_ci.py").write_text("print('scan')\n", encoding="utf-8")
    body = _run_block(_WORKFLOW.read_text(encoding="utf-8"), "Run gitleaks")
    completed = subprocess.run(
        ["bash", "-x", "-c", body],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        env={
            "PATH": f"{fake_bin}:/usr/bin:/bin",
            "RUNNER_TEMP": str(runner),
            "GITHUB_EVENT_NAME": "push",
            "PR_BASE_SHA": "",
            "PR_HEAD_SHA": "",
            "PUSH_BEFORE": "b" * 40,
            "PUSH_SHA": "c" * 40,
        },
    )
    trace = completed.stderr
    assert "FAKE" not in completed.stdout
    assert "+ sha256sum -c -" in trace
    assert "+ gitleaks version" not in trace
    assert "+ /usr/local/bin/gitleaks version" not in trace or trace.index(
        "+ sha256sum -c -"
    ) < trace.index("+ /usr/local/bin/gitleaks version")


def test_bootstrap_is_only_the_known_base(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.check_call(["git", "-C", str(repo), "init", "-q"])
    subprocess.check_call(
        ["git", "-C", str(repo), "config", "user.email", "dev@example.invalid"]
    )
    subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "dev"])
    script_dir = repo / ".github" / "scripts"
    script_dir.mkdir(parents=True)
    (script_dir / "gitleaks_ci.py").write_text("print('head-script')\n", encoding="utf-8")
    (repo / ".gitleaks.toml").write_text("title = \"head\"\n", encoding="utf-8")
    subprocess.check_call(["git", "-C", str(repo), "add", "."])
    subprocess.check_call(["git", "-C", str(repo), "commit", "-q", "-m", "head"])
    body = _run_block(_WORKFLOW.read_text(encoding="utf-8"), "Materialize base scan gate")
    other = tmp_path / "other"
    other.mkdir()
    refused = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", body],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GATE_SHA": "a" * 40, "RUNNER_TEMP": str(other)},
    )
    assert refused.returncode == 2
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    accepted = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", body],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GATE_SHA": "f3559cbb2677eb72088bec7c56d541f0aa78a41e",
            "RUNNER_TEMP": str(allowed),
        },
    )
    assert "bootstrap: base has no scan script" in accepted.stdout
    assert (allowed / "scan" / "gitleaks_ci.py").read_text(encoding="utf-8") == (
        "print('head-script')\n"
    )
    assert not (other / "scan" / "gitleaks_ci.py").exists()


def test_push_gate_sha_is_the_parent_not_the_pushed_commit() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert (
        "GATE_SHA: ${{ github.event_name == 'pull_request' && "
        "github.event.pull_request.base.sha || github.event.before }}"
    ) in text
    gate_lines = [
        line.strip()
        for line in text.split("  gitleaks-tests:", 1)[0].splitlines()
        if line.strip().startswith("GATE_SHA:")
    ]
    assert gate_lines
    assert all("github.sha" not in line for line in gate_lines)
    assert all("github.event.before" in line for line in gate_lines)


def test_binary_resolver_ignores_overrides(tmp_path: Path) -> None:
    scanner = _scanner()
    blob = tmp_path / "gitleaks"
    blob.write_bytes(b"synthetic-binary")
    digest = hashlib.sha256(blob.read_bytes()).hexdigest()
    resolved = scanner.verified_gitleaks_binary(
        blob, digest, {"GITLEAKS_BIN": "/bin/true", "PATH": "/tmp/fake"}
    )
    assert resolved == blob
    with pytest.raises(scanner.ScanError):
        scanner.verified_gitleaks_binary(blob, "0" * 64, {"GITLEAKS_BIN": "/bin/true"})


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
