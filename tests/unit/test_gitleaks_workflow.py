"""The gitleaks workflow executes the base revision's scan script."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shlex
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
    assert "gitleaks_8.30.1_linux_x64.tar.gz" in text


_TARBALL_SHA = "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"
_BINARY_SHA = "88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509"


def _gate_and_tests(text: str) -> tuple[str, str]:
    gate, tests = text.split("  gitleaks-tests:", 1)
    return gate.split("  gitleaks:", 1)[1], tests


def test_gate_job_pins_tarball_and_both_binary_hashes() -> None:
    """The pin checks have to match the gate job, not the tests job's copy."""
    gate, tests = _gate_and_tests(_WORKFLOW.read_text(encoding="utf-8"))
    assert gate.count(_TARBALL_SHA) == 1
    assert gate.count(_BINARY_SHA) == 2
    assert f"{_BINARY_SHA}  /usr/local/bin/gitleaks" in gate
    assert tests.count(_TARBALL_SHA) == 1
    assert tests.count(_BINARY_SHA) == 1
    assert f"{_BINARY_SHA}  /usr/local/bin/gitleaks" in tests


def test_find_and_loop_step_cannot_be_skipped() -> None:
    """The scan step that walks commits cannot be skipped or ignored."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    gate, _tests = _gate_and_tests(text)
    assert "continue-on-error" not in gate
    start = gate.index("      - name: Run gitleaks\n")
    step = gate[start:]
    assert "\n    if:" not in step
    assert "|| true" not in step
    run = _run_block(text, "Run gitleaks")
    assert "set -euo pipefail" in run
    assert 'python3 -I "${RUNNER_TEMP}/scan/gitleaks_ci.py"' in run
    script = (
        _WORKFLOW.parents[2] / ".github" / "scripts" / "gitleaks_ci.py"
    ).read_text(encoding="utf-8")
    loop = script.split("def prescan_opaque_files", 1)[1].split("\ndef ", 1)[0]
    assert '"-z"' in script
    assert "--diff-filter=AMR" in script
    assert "for commit, path in blobs:" in loop
    assert "|| true" not in loop


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


def test_gitleaks_pytest_install_is_hash_locked() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    tests = text.split("  gitleaks-tests:", 1)[1]
    assert "--require-hashes" in tests
    assert "--only-binary=:all:" in tests
    requirements = (
        _WORKFLOW.parents[2] / ".github" / "gitleaks-tests-requirements.txt"
    ).read_text(encoding="utf-8")
    assert "pytest==9.1.1" in requirements
    for line in requirements.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        assert "--hash=sha256:" in stripped or stripped.endswith("\\")


def test_orphan_gitlink_is_not_in_the_tree() -> None:
    root = _WORKFLOW.parents[2]
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-s", "--", "reference/CL4R1T4S"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert listed.returncode == 0
    assert listed.stdout.strip() == ""
    modules = (root / ".gitmodules").read_text(encoding="utf-8")
    assert "media-ops-platform-unfetched-gitlink" not in modules
    assert "reference/CL4R1T4S must never be created" in modules


def test_checkout_can_list_submodules() -> None:
    """Credential cleanup lists submodules. reference/CL4R1T4S must not be a gitlink."""
    completed = subprocess.run(
        ["git", "submodule", "foreach", "--recursive", ":"],
        cwd=_WORKFLOW.parents[2],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_gate_job_runs_no_checkout_tests() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    gate, tests = text.split("  gitleaks-tests:", 1)
    gate_job = gate.split("  gitleaks:", 1)[1]
    assert "pytest" not in gate_job
    assert "tests/security" not in gate_job
    assert gate_job.count("persist-credentials: false") == 1
    assert gate_job.count("submodules: false") == 1
    assert tests.count("submodules: false") == 1
    assert "GITLEAKS_BIN=" not in gate_job
    assert "GITLEAKS_BIN:" not in gate_job
    assert "/usr/local/bin/gitleaks" in gate_job
    assert "--require-hashes" in tests
    assert ".github/gitleaks-tests-requirements.txt" in tests


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
    # A trailing `|| true` would keep going after the checksum fails.
    assert "+ /usr/local/bin/gitleaks version" not in trace
    assert "python3" not in trace


def _run_in_mount_namespace(script: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    command = ["unshare", "--user", "--map-root-user", "--mount", "bash", "-c", script]
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 and "uid_map" in completed.stderr:
        completed = subprocess.run(
            ["sudo", "-n", "unshare", "--mount", "bash", "-c", script],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    return completed


def test_trusted_python_is_isolated_from_the_checkout() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    gate, tests = text.split("  gitleaks-tests:", 1)
    run = _run_block(text, "Run gitleaks")
    forwarded = run.split("env -i", 1)[1]
    assert "env -i" in run
    assert "PATH=/usr/bin:/bin" in run
    assert 'HOME="$HOME"' in run
    assert "PYTHONSAFEPATH=1" in run
    assert 'python3 -I "${RUNNER_TEMP}/scan/gitleaks_ci.py"' in run
    assert "PYTHONPATH" not in forwarded
    assert "LD_PRELOAD" not in forwarded
    assert "GIT_DIR" not in forwarded
    assert "python3 -I" in tests
    assert "PYTHONSAFEPATH=1" in tests
    assert 'cd "${RUNNER_TEMP}"' in tests
    assert "pytest" not in gate.split("  gitleaks:", 1)[1]


def test_run_step_executes_the_materialized_script(tmp_path: Path) -> None:
    """Import-time checkout code must not replace the script the gate runs."""
    runner = tmp_path / "runner"
    scan = runner / "scan"
    scan.mkdir(parents=True)
    (scan / "gitleaks_ci.py").write_text(
        "print('materialized-scan')\n", encoding="utf-8"
    )
    checkout = tmp_path / ".github" / "scripts"
    checkout.mkdir(parents=True)
    (checkout / "gitleaks_ci.py").write_text(
        "print('checkout-scan')\n", encoding="utf-8"
    )
    evil = tmp_path / "tests" / "security"
    evil.mkdir(parents=True)
    (evil / "overwrite.py").write_text(
        "from pathlib import Path\n"
        "import os\n"
        "Path(os.environ['RUNNER_TEMP'], 'scan', 'gitleaks_ci.py').write_text("
        "'print(\"overwritten\")\\n')\n",
        encoding="utf-8",
    )
    body = _run_block(_WORKFLOW.read_text(encoding="utf-8"), "Run gitleaks")
    sha_stub = tmp_path / "sha256sum"
    leaks_stub = tmp_path / "gitleaks"
    sha_stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    leaks_stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    sha_stub.chmod(0o755)
    leaks_stub.chmod(0o755)
    exports = "\n".join(
        [
            f"export RUNNER_TEMP={shlex.quote(str(runner))}",
            "export GITHUB_EVENT_NAME=push",
            "export PR_BASE_SHA=",
            "export PR_HEAD_SHA=",
            f"export PUSH_BEFORE={shlex.quote('b' * 40)}",
            f"export PUSH_SHA={shlex.quote('c' * 40)}",
            f"export HOME={shlex.quote(str(tmp_path))}",
        ]
    )
    script = "\n".join(
        [
            "set -euo pipefail",
            exports,
            f"mount --bind {shlex.quote(str(sha_stub))} /usr/bin/sha256sum",
            "mount -t tmpfs tmpfs /usr/local",
            "mkdir -p /usr/local/bin",
            f"cp {shlex.quote(str(leaks_stub))} /usr/local/bin/gitleaks",
            "chmod +x /usr/local/bin/gitleaks",
            body,
        ]
    )
    completed = _run_in_mount_namespace(script, tmp_path)
    assert completed.returncode == 0, completed.stderr
    assert "materialized-scan" in completed.stdout
    assert "checkout-scan" not in completed.stdout
    assert "overwritten" not in completed.stdout


def test_checkout_json_module_cannot_exit_zero_or_replace_the_binary(
    tmp_path: Path,
) -> None:
    """A repo-root or script-dir json.py must not run inside the gate."""
    runner = tmp_path / "runner"
    scan = runner / "scan"
    scan.mkdir(parents=True)
    marker = tmp_path / "shadowed"
    note = tmp_path / "binary-note"
    (scan / "gitleaks_ci.py").write_text(
        "import json\n"
        "import os\n"
        "print('materialized-scan')\n"
        "print('GIT_DIR=' + os.environ.get('GIT_DIR', ''))\n"
        "print('PYTHONPATH=' + os.environ.get('PYTHONPATH', ''))\n"
        "print('LD_PRELOAD=' + os.environ.get('LD_PRELOAD', ''))\n"
        "print('PYTHONSAFEPATH=' + os.environ.get('PYTHONSAFEPATH', ''))\n",
        encoding="utf-8",
    )
    shadow = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('shadowed\\n')\n"
        "target = Path('/usr/local/bin/gitleaks')\n"
        "try:\n"
        "    target.write_text('overwritten\\n')\n"
        f"    Path({str(note)!r}).write_text('overwritten\\n')\n"
        "except OSError:\n"
        f"    Path({str(note)!r}).write_text('blocked\\n')\n"
        "raise SystemExit(0)\n"
    )
    (tmp_path / "json.py").write_text(shadow, encoding="utf-8")
    (scan / "json.py").write_text(shadow, encoding="utf-8")
    sha_stub = tmp_path / "sha256sum"
    leaks_stub = tmp_path / "gitleaks"
    sha_stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    leaks_stub.write_text("#!/bin/sh\nprintf sentinel\nexit 0\n", encoding="utf-8")
    sha_stub.chmod(0o755)
    leaks_stub.chmod(0o755)
    body = _run_block(_WORKFLOW.read_text(encoding="utf-8"), "Run gitleaks")
    exports = "\n".join(
        [
            f"export RUNNER_TEMP={shlex.quote(str(runner))}",
            "export GITHUB_EVENT_NAME=push",
            "export PR_BASE_SHA=",
            "export PR_HEAD_SHA=",
            f"export PUSH_BEFORE={shlex.quote('b' * 40)}",
            f"export PUSH_SHA={shlex.quote('c' * 40)}",
            f"export HOME={shlex.quote(str(tmp_path))}",
            "export GIT_DIR=/tmp/evil-git",
            f"export PYTHONPATH={shlex.quote(str(tmp_path))}",
            "export LD_PRELOAD=/tmp/evil.so",
            "export PYTHONSAFEPATH=0",
        ]
    )
    script = "\n".join(
        [
            "set -euo pipefail",
            exports,
            f"mount --bind {shlex.quote(str(sha_stub))} /usr/bin/sha256sum",
            "mount -t tmpfs tmpfs /usr/local",
            "mkdir -p /usr/local/bin",
            f"cp {shlex.quote(str(leaks_stub))} /usr/local/bin/gitleaks",
            "chmod +x /usr/local/bin/gitleaks",
            body,
        ]
    )
    completed = _run_in_mount_namespace(script, tmp_path)
    assert completed.returncode == 0, completed.stderr
    assert "materialized-scan" in completed.stdout
    assert "GIT_DIR=\n" in completed.stdout
    assert "PYTHONPATH=\n" in completed.stdout
    assert "LD_PRELOAD=\n" in completed.stdout
    assert "PYTHONSAFEPATH=1" in completed.stdout
    assert not marker.exists()
    assert not note.exists()


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
    assert accepted.returncode != 0
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


def test_bootstrap_sha_reads_the_checkout_config(tmp_path: Path) -> None:
    scanner = _scanner()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitleaks.toml").write_text('title = "checkout"\n', encoding="utf-8")
    assert scanner.policy_config_bytes(repo, scanner.BOOTSTRAP_SHA) == (
        b'title = "checkout"\n'
    )
    assert scanner.policy_config_bytes(repo, "a" * 40) is None


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
