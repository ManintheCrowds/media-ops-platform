"""Pull-request gitleaks loads ignore data from the base revision."""

from __future__ import annotations

import importlib.util
import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.security

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / ".github" / "scripts" / "gitleaks_ci.py"
_POLICY = _ROOT / ".gitleaks.toml"
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


def _init_repo(repo: Path, config: str | None = None) -> None:
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "dev@example.invalid")
    _git(repo, "config", "user.name", "dev")
    text = _POLICY.read_text(encoding="utf-8") if config is None else config
    (repo / ".gitleaks.toml").write_text(text, encoding="utf-8")
    _git(repo, "add", ".gitleaks.toml")
    _git(repo, "commit", "-q", "-m", "config")


def _head(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()


def _expect_policy_failure(tmp_path: Path, config: str) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo, config)
    base = _head(repo)
    head = _commit_file(repo, "note.txt", "hello\n", "note")
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
    assert caught.value.code == 2
    assert "policy canary failed" in str(caught.value)


def _runtime_token() -> str:
    rng = random.Random(20261123)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "AKIA" + "".join(rng.choice(alphabet) for _ in range(16))


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


def test_utf16_and_nul_and_node_modules_are_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / "wide.txt").write_bytes(f"token={token}\n".encode("utf-16"))
    (repo / "nul.bin").write_bytes(b"\x00token=" + token.encode("ascii") + b"\n")
    nested = repo / "node_modules" / "pkg"
    nested.mkdir(parents=True)
    (nested / "index.js").write_text(f"token={token}\n", encoding="utf-8")
    _git(repo, "add", "wide.txt", "nul.bin", "node_modules")
    _git(repo, "commit", "-q", "-m", "opaque")
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    code = gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
    assert code == 1


def test_path_only_base_fingerprint_does_not_suppress(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / ".gitleaksignore").write_text(
        "secret.txt:generic-api-key:1\n", encoding="utf-8"
    )
    _git(repo, "add", ".gitleaksignore")
    _git(repo, "commit", "-q", "-m", "path-only ignore")
    base = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    token = _runtime_token()
    head = _commit_file(repo, "secret.txt", f"token={token}\n", "add token")
    code = gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
    assert code == 1


def test_push_ignore_on_the_pushed_commit_still_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    before = _commit_file(repo, "readme.txt", "ok\n", "base")
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
            gitleaks_ci.revision_log_opts(before, head),
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
    (repo / ".gitleaks.toml").write_text('title = "no rules"\n', encoding="utf-8")
    _git(repo, "add", ".gitleaksignore", ".gitleaks.toml")
    _git(repo, "commit", "-q", "-m", "push ignore and empty config")
    pushed = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    code = gitleaks_ci.run_push_scan(repo, before, pushed, _gitleaks())
    assert code == 1


def test_push_all_zero_before_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    head = _commit_file(repo, "readme.txt", "ok\n", "base")
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci.run_push_scan(repo, "0" * 40, head, _gitleaks())
    assert caught.value.code == 2


def test_push_unfetchable_before_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    head = _commit_file(repo, "readme.txt", "ok\n", "base")
    missing = "0123456789abcdef0123456789abcdef01234567"
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci.run_push_scan(repo, missing, head, _gitleaks())
    assert caught.value.code == 2


def _extend_only() -> str:
    return 'title = "weak"\n\n[extend]\nuseDefault = true\n'


def test_root_path_allowlist_fails_the_self_check(tmp_path: Path) -> None:
    config = _extend_only() + "\n[allowlist]\npaths = ['''^[^/]''']\n"
    _expect_policy_failure(tmp_path, config)


def test_line_regex_allowlist_fails_the_self_check(tmp_path: Path) -> None:
    config = (
        _extend_only()
        + "\n[allowlist]\nregexTarget = \"line\"\nregexes = ['''^t=''']\n"
    )
    _expect_policy_failure(tmp_path, config)


def test_disabled_slack_rule_fails_the_self_check(tmp_path: Path) -> None:
    config = _extend_only().replace(
        "useDefault = true\n",
        'useDefault = true\ndisabledRules = ["slack-bot-token"]\n',
    )
    _expect_policy_failure(tmp_path, config)


def test_dummy_rules_without_defaults_fail_the_self_check(tmp_path: Path) -> None:
    rules = "\n".join(
        f'[[rules]]\nid = "dummy-{index}"\ndescription = "d"\nregex = "NOMATCH{index:04d}"\n'
        for index in range(200)
    )
    _expect_policy_failure(tmp_path, 'title = "dummy"\n\n' + rules + "\n")


def test_stopwords_allowlist_without_paths_fails_the_self_check(tmp_path: Path) -> None:
    config = _extend_only() + '\n[allowlist]\nstopwords = ["example"]\n'
    _expect_policy_failure(tmp_path, config)


def test_write_nofollow_refuses_a_symlinked_directory(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("untouched\n", encoding="utf-8")
    (root / "nested").symlink_to(outside, target_is_directory=True)
    with pytest.raises(gitleaks_ci.ScanError):
        gitleaks_ci._write_nofollow(root, "nested/github-canary.txt", 'key = "x"\n')
    assert secret.read_text(encoding="utf-8") == "untouched\n"
    assert not (outside / "github-canary.txt").exists()


def test_canary_tree_does_not_follow_symlinks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("untouched\n", encoding="utf-8")
    (repo / "nested").symlink_to(outside, target_is_directory=True)
    (repo / "aws-canary.txt").symlink_to(secret)
    base = _head(repo)
    policy = tmp_path / "policy"
    config, _ignore = gitleaks_ci.materialize_policy(repo, base, policy)
    gitleaks_ci.assert_policy_canaries(_gitleaks(), config, repo)
    assert secret.read_text(encoding="utf-8") == "untouched\n"
    assert (repo / "aws-canary.txt").is_symlink()
