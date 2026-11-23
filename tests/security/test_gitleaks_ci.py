"""Pull-request gitleaks loads ignore data from the base revision."""

from __future__ import annotations

import importlib.util
import json
import secrets
import string
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.security

_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "gitleaks_ci.py"
_spec = importlib.util.spec_from_file_location("gitleaks_ci", _SCRIPT)
assert _spec is not None and _spec.loader is not None
gitleaks_ci = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = gitleaks_ci
_spec.loader.exec_module(gitleaks_ci)


def _gitleaks() -> str:
    fallback = Path("/tmp/gl-bin/gitleaks")
    if fallback.is_file():
        return str(fallback)
    return "gitleaks"


def _git(repo: Path, *args: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "dev@example.invalid")
    _git(repo, "config", "user.name", "dev")
    (repo / ".gitleaks.toml").write_text(
        'title = "test"\n\n[extend]\nuseDefault = true\n',
        encoding="utf-8",
    )
    _git(repo, "add", ".gitleaks.toml")
    _git(repo, "commit", "-q", "-m", "config")


def _runtime_token() -> str:
    alphabet = string.ascii_uppercase + string.digits
    while True:
        body = "".join(secrets.choice(alphabet) for _ in range(16))
        token = "AKIA" + body
        if "EXAMPLE" not in token:
            return token


def _commit_file(repo: Path, name: str, content: str, message: str) -> str:
    (repo / name).write_text(content, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", message)
    sha = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    return sha


def test_missing_revision_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci.run_pull_request_scan(
            repo, base, "0123456789abcdef0123456789abcdef01234567", _gitleaks()
        )
    assert caught.value.code == 2
    assert "missing revision" in str(caught.value)


def test_empty_range_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    only = _commit_file(repo, "readme.txt", "ok\n", "base")
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci.run_pull_request_scan(repo, only, only, _gitleaks())
    assert caught.value.code == 3
    assert "empty range" in str(caught.value)


def test_runtime_built_secret_is_caught(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    head = _commit_file(repo, "secret.txt", f"token={token}\n", "add token")
    code = gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
    assert code == 1


def test_fingerprint_added_on_the_pull_request_still_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    head = _commit_file(repo, "secret.txt", f"token={token}\n", "add token")
    report = tmp_path / "report.json"
    listed = subprocess.run(
        [
            _gitleaks(),
            "detect",
            "--source",
            str(repo),
            "--config",
            str(repo / ".gitleaks.toml"),
            "--log-opts",
            f"{base}..{head}",
            "--ignore-gitleaks-allow",
            "--redact",
            "--no-banner",
            "--report-format",
            "json",
            "--report-path",
            str(report),
            "--exit-code",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert listed.returncode == 0
    findings = json.loads(report.read_text(encoding="utf-8"))
    fingerprints = [item["Fingerprint"] for item in findings if item.get("Fingerprint")]
    assert fingerprints
    (repo / ".gitleaksignore").write_text(
        "\n".join(fingerprints) + "\n", encoding="utf-8"
    )
    _git(repo, "add", ".gitleaksignore")
    _git(repo, "commit", "-q", "-m", "ignore on the pull request")
    head_with_ignore = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    suppressed = subprocess.run(
        [
            _gitleaks(),
            "detect",
            "--source",
            str(repo),
            "--config",
            str(repo / ".gitleaks.toml"),
            "--gitleaks-ignore-path",
            str(repo / ".gitleaksignore"),
            "--log-opts",
            f"{base}..{head_with_ignore}",
            "--ignore-gitleaks-allow",
            "--redact",
            "--no-banner",
            "--exit-code",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert suppressed.returncode == 0
    code = gitleaks_ci.run_pull_request_scan(repo, base, head_with_ignore, _gitleaks())
    assert code == 1


def test_pull_request_config_change_still_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / "secret.txt").write_text(f"token={token}\n", encoding="utf-8")
    (repo / ".gitleaks.toml").write_text('title = "no rules"\n', encoding="utf-8")
    _git(repo, "add", "secret.txt", ".gitleaks.toml")
    _git(repo, "commit", "-q", "-m", "empty config and token")
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    code = gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
    assert code == 1


def test_gitleaks_allow_comment_still_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    head = _commit_file(
        repo,
        "secret.txt",
        f"token={token} # gitleaks:allow\n",
        "allow comment",
    )
    code = gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
    assert code == 1


def test_scan_output_does_not_contain_the_canary(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    head = _commit_file(repo, "secret.txt", f"token={token}\n", "add token")
    policy = tmp_path / "policy"
    config, ignore = gitleaks_ci.materialize_policy(repo, base, policy)
    command = gitleaks_ci.gitleaks_command(
        _gitleaks(),
        repo,
        config,
        ignore,
        gitleaks_ci.revision_log_opts(base, head),
    )
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    leaked = token in completed.stdout or token in completed.stderr
    assert leaked is False
    assert completed.returncode == 1
