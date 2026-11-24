"""Pull-request gitleaks loads ignore data from the base revision."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import io
import json
import random
import subprocess
import sys
import zipfile
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


def _pinned_gitleaks(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != gitleaks_ci.GITLEAKS_SHA256:
        return None
    return str(path)


def _gitleaks() -> str:
    for candidate in (Path("/usr/local/bin/gitleaks"), Path("/tmp/gl-bin/gitleaks")):
        pinned = _pinned_gitleaks(candidate)
        if pinned is not None:
            return pinned
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


@pytest.mark.parametrize(
    ("name", "payload"),
    [
        ("wide.txt", None),
        ("logo.png", b"\x89PNG\r\n\x1a\n"),
    ],
)
def test_prescan_ignores_gitleaks_allow(
    tmp_path: Path, name: str, payload: bytes | None
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    line = f'key = "{token}" # gitleaks:allow\n'
    if payload is None:
        (repo / name).write_bytes(line.encode("utf-16"))
    else:
        (repo / name).write_bytes(payload + line.encode("utf-8"))
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "allow comment")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


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


def _commit_tree(repo: Path, parents: list[str], message: str) -> str:
    tree = subprocess.check_output(
        ["git", "-C", str(repo), "write-tree"], text=True
    ).strip()
    command = ["git", "-C", str(repo), "commit-tree", tree, "-m", message]
    for parent in parents:
        command.extend(["-p", parent])
    return subprocess.check_output(command, text=True).strip()


def test_side_first_merge_ignore_does_not_hide_the_leak(tmp_path: Path) -> None:
    """Parents [leak, ignore]. A non-empty ignore fails closed on push and PR."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    _git(repo, "checkout", "-q", "-b", "side")
    token = _runtime_token()
    leak_commit = _commit_file(repo, "leak.txt", f'key = "{token}"\n', "leak")
    _git(repo, "checkout", "-q", base)
    note = _commit_file(repo, "note.txt", "hello\n", "note")
    _git(repo, "checkout", "-q", leak_commit)
    (repo / "note.txt").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "note.txt")
    control = _commit_tree(repo, [leak_commit, note], "control")
    assert gitleaks_ci.run_push_scan(repo, note, control, _gitleaks()) == 1
    assert gitleaks_ci.run_pull_request_scan(repo, note, control, _gitleaks()) == 1

    _git(repo, "checkout", "-q", base)
    fingerprint = f"{leak_commit}:leak.txt:github-pat:1\n"
    added = _commit_file(repo, ".gitleaksignore", fingerprint, "ignore")
    _git(repo, "checkout", "-q", leak_commit)
    (repo / ".gitleaksignore").write_text(fingerprint, encoding="utf-8")
    _git(repo, "add", ".gitleaksignore")
    merged = _commit_tree(repo, [leak_commit, added], "side first")
    for scan in (
        gitleaks_ci.run_push_scan,
        gitleaks_ci.run_pull_request_scan,
    ):
        with pytest.raises(gitleaks_ci.ScanError) as caught:
            scan(repo, added, merged, _gitleaks())
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


def test_replaced_slack_rule_fails_the_self_check(tmp_path: Path) -> None:
    config = _POLICY.read_text(encoding="utf-8") + (
        '\n[[rules]]\n'
        'id = "slack-bot-token"\n'
        'description = "replaced"\n'
        'regex = "NOMATCHSLACKTOKENNEVER"\n'
        'keywords = ["xoxb"]\n'
    )
    _expect_policy_failure(tmp_path, config)


def test_extra_rule_fails_the_default_rule_count(tmp_path: Path) -> None:
    config = _POLICY.read_text(encoding="utf-8") + (
        '\n[[rules]]\nid = "extra-dummy"\ndescription = "d"\nregex = "NOMATCHEXTRA"\n'
    )
    _expect_policy_failure(tmp_path, config)


def test_gate_script_calls_the_policy_self_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    head = _commit_file(repo, "note.txt", "hello\n", "note")
    seen: list[Path] = []
    real = gitleaks_ci.assert_policy_canaries

    def spy(gitleaks: str, config: Path, source: Path) -> None:
        seen.append(config)
        real(gitleaks, config, source)

    monkeypatch.setattr(gitleaks_ci, "assert_policy_canaries", spy)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 0
    assert seen


def _approved_plus(extra: str) -> str:
    return _POLICY.read_text(encoding="utf-8") + "\n" + extra


def test_same_id_stripe_rule_fails_the_pin(tmp_path: Path) -> None:
    extra = (
        '[[rules]]\nid = "stripe-access-token"\n'
        'description = "replaced"\nregex = \'\'\'zzneverzz\'\'\'\n'
    )
    _expect_policy_failure(tmp_path, _approved_plus(extra))


def test_same_id_pypi_rule_fails_the_pin(tmp_path: Path) -> None:
    extra = (
        '[[rules]]\nid = "pypi-upload-token"\n'
        'description = "replaced"\nregex = \'\'\'zzneverzz\'\'\'\n'
    )
    _expect_policy_failure(tmp_path, _approved_plus(extra))


def test_same_id_rule_path_fails_the_pin(tmp_path: Path) -> None:
    extra = (
        '[[rules]]\nid = "stripe-access-token"\n'
        'description = "replaced"\nregex = \'\'\'zzneverzz\'\'\'\n'
        "path = '''^never/'''\n"
    )
    _expect_policy_failure(tmp_path, _approved_plus(extra))


def test_allowlist_case_variant_before_the_real_table_fails_the_pin(
    tmp_path: Path,
) -> None:
    approved = _POLICY.read_text(encoding="utf-8")
    for index, name in enumerate(("AllowList", "Allowlist")):
        prefix = f"[{name}]\nregexTarget = \"line\"\nregexes = ['''^prod''']\n\n"
        repo = tmp_path / f"repo-{index}"
        _init_repo(repo, prefix + approved)
        base = _head(repo)
        head = _commit_file(repo, "note.txt", "hello\n", "note")
        with pytest.raises(gitleaks_ci.ScanError) as caught:
            gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
        assert caught.value.code == 2


def test_quoted_allowlist_keys_fail_the_pin(tmp_path: Path) -> None:
    extra = (
        '"allowlist.regexTarget" = "line"\n'
        "\"allowlist.regexes\" = ['''^prod''']\n"
    )
    _expect_policy_failure(tmp_path, _approved_plus(extra))


def test_bootstrap_checkout_must_match_the_pinned_config(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    approved = (repo / ".gitleaks.toml").read_bytes()
    assert gitleaks_ci.policy_config_bytes(repo, gitleaks_ci.BOOTSTRAP_SHA) == approved
    assert (
        __import__("hashlib").sha256(approved).hexdigest()
        == gitleaks_ci.APPROVED_CONFIG_SHA256
    )
    (repo / ".gitleaks.toml").write_text('title = "weak"\n', encoding="utf-8")
    weakened = tmp_path / "weak.toml"
    weakened.write_bytes(
        gitleaks_ci.policy_config_bytes(repo, gitleaks_ci.BOOTSTRAP_SHA) or b""
    )
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci.assert_approved_config(weakened)
    assert caught.value.code == 2
    assert gitleaks_ci.policy_config_bytes(repo, "a" * 40) is None


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


@pytest.mark.parametrize(
    "name",
    [
        "logo.png",
        "a.gif",
        "font.woff2",
        "go.sum",
        "poetry.lock",
        "package-lock.json",
    ],
)
def test_text_in_an_allowlisted_name_is_scanned(tmp_path: Path, name: str) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / name).write_text(f'key = "{token}"\n', encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "disguised text")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


@pytest.mark.parametrize(
    "encoding",
    ["utf-16-be", "utf-32-le", "utf-32-be"],
)
def test_wide_text_without_a_bom_is_scanned(tmp_path: Path, encoding: str) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / "wide.txt").write_bytes(f'key = "{token}"\n'.encode(encoding))
    _git(repo, "add", "wide.txt")
    _git(repo, "commit", "-q", "-m", "wide")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_c_quoted_path_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    name = "tab\tname.txt"
    (repo / name).write_bytes(f'key = "{token}"\n'.encode("utf-16-be"))
    _git(repo, "add", "--", name)
    _git(repo, "commit", "-q", "-m", "quoted name")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_unreadable_listed_path_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / "wide.txt").write_bytes(f'key = "{token}"\n'.encode("utf-16"))
    _git(repo, "add", "wide.txt")
    _git(repo, "commit", "-q", "-m", "wide")
    head = _head(repo)
    def hide_blob(repo_path: Path, blob_sha: str) -> bytes | None:
        del repo_path, blob_sha
        return None

    monkeypatch.setattr(gitleaks_ci, "git_cat_blob", hide_blob)
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
    assert caught.value.code == 2
    assert "prescan failed" in str(caught.value)


def test_utf16_secret_added_then_deleted_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / "wide.txt").write_bytes(f'key = "{token}"\n'.encode("utf-16"))
    _git(repo, "add", "wide.txt")
    _git(repo, "commit", "-q", "-m", "add wide")
    _git(repo, "rm", "-q", "wide.txt")
    _git(repo, "commit", "-q", "-m", "delete wide")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_merge_only_utf16_file_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    _git(repo, "checkout", "-q", "-b", "side")
    _commit_file(repo, "side.txt", "side\n", "side")
    _git(repo, "checkout", "-q", "-")
    merge = subprocess.run(
        ["git", "-C", str(repo), "merge", "--no-ff", "--no-commit", "side"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert merge.returncode == 0, merge.stderr
    token = _runtime_token()
    (repo / "app.py").write_bytes(f'key = "{token}"\n'.encode("utf-16-le"))
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-q", "-m", "merge")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_prescan_nonzero_exit_fails_when_the_report_is_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        report = Path(command[command.index("--report-path") + 1])
        report.write_text("[]", encoding="utf-8")
        return subprocess.CompletedProcess(command, 2, "", "")

    monkeypatch.setattr(gitleaks_ci.subprocess, "run", fake_run)
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci._scan_sample(tmp_path, "gitleaks", tmp_path / "config", "text")
    assert caught.value.code == 2


def test_unparseable_diff_tree_record_fails() -> None:
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci._parse_diff_tree(b"not a raw record\x00")
    assert caught.value.code == 1


def test_root_file_named_like_a_commit_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    name = "0123456789abcdef0123456789abcdef01234567"
    (repo / name).write_bytes(f'key = "{token}"\n'.encode("utf-16"))
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    _git(repo, "add", "--", name, "later.txt")
    _git(repo, "commit", "-q", "-m", "hex name")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1
    assert gitleaks_ci.run_push_scan(repo, base, head, _gitleaks()) == 1


def test_rename_onto_a_commit_named_file_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "a.txt", "ok\n", "base")
    base = _head(repo)
    token = _runtime_token()
    name = "fedcba9876543210fedcba9876543210fedcba98"
    _git(repo, "mv", "a.txt", name)
    (repo / name).write_bytes(f'key = "{token}"\n'.encode("utf-16"))
    _git(repo, "add", "--", name)
    _git(repo, "commit", "-q", "-m", "rename to hex")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_path_that_looks_like_a_raw_diff_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    name = ":100644 100644 aaaa bbbb M"
    (repo / name).write_bytes(f'key = "{token}"\n'.encode("utf-16"))
    added = subprocess.run(
        ["git", "--literal-pathspecs", "-C", str(repo), "add", "--", name],
        check=False,
        capture_output=True,
        text=True,
    )
    assert added.returncode == 0, added.stderr
    _git(repo, "commit", "-q", "-m", "colon path")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_symlink_replaced_by_utf16_file_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "README").write_text("readme\n", encoding="utf-8")
    (repo / "app.py").symlink_to("README")
    _git(repo, "add", "README", "app.py")
    _git(repo, "commit", "-q", "-m", "symlink")
    base = _head(repo)
    (repo / "app.py").unlink()
    token = _runtime_token()
    (repo / "app.py").write_bytes(f'key = "{token}"\n'.encode("utf-16"))
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-q", "-m", "replace symlink")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_renamed_and_edited_utf16_file_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    (repo / "plain.txt").write_bytes(f'key = "{token}"\n'.encode("utf-16"))
    _git(repo, "add", "plain.txt")
    _git(repo, "commit", "-q", "-m", "add wide")
    base = _head(repo)
    _git(repo, "mv", "plain.txt", "nested.txt")
    (repo / "nested.txt").write_bytes(
        f'key = "{token}"\nnote=1\n'.encode("utf-16")
    )
    _git(repo, "add", "nested.txt")
    _git(repo, "commit", "-q", "-m", "rename and edit")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_renamed_utf16_secret_deleted_later_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "plain.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / "nested").mkdir()
    (repo / "plain.txt").write_bytes(f'key = "{token}"\n'.encode("utf-16"))
    _git(repo, "add", "plain.txt")
    _git(repo, "mv", "plain.txt", "nested/hidden.txt")
    _git(repo, "commit", "-q", "-m", "rename wide")
    _git(repo, "rm", "-q", "nested/hidden.txt")
    _git(repo, "commit", "-q", "-m", "delete renamed")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


@pytest.mark.parametrize(
    ("name", "prefix"),
    [
        ("logo.png", b"\x89PNG\r\n\x1a\n"),
        ("a.gif", b"GIF89a"),
        ("photo.jpg", b"\xff\xd8\xff\xe0"),
    ],
)
def test_plaintext_after_image_magic_is_scanned(
    tmp_path: Path, name: str, prefix: bytes
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / name).write_bytes(prefix + f'key = "{token}"\n'.encode("utf-8"))
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "magic plus text")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


@pytest.mark.parametrize("name", ["data.bin", "font.woff2"])
def test_high_byte_padding_is_scanned(tmp_path: Path, name: str) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    padding = bytes(range(128, 256)) * 8
    (repo / name).write_bytes(padding + f'key = "{token}"\n'.encode("utf-8"))
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "padded")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


@pytest.mark.parametrize(
    ("name", "prefix"),
    [
        ("data.bin", b"PK\x03\x04"),
        ("logo.png", b"PK\x03\x04"),
        ("note.pdf", b"PK\x03\x04"),
        ("data.bin", b"\x7fELF"),
        ("logo.png", b"\x7fELF"),
        ("note.pdf", b"\x7fELF"),
        ("data.bin", b"%PDF-1.4\n"),
        ("logo.png", b"%PDF-1.4\n"),
        ("note.pdf", b"%PDF-1.4\n"),
    ],
)
def test_token_after_archive_magic_is_scanned(
    tmp_path: Path, name: str, prefix: bytes
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / name).write_bytes(prefix + f'key = "{token}"\n'.encode("utf-8"))
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "magic plus token")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def _zip_with_token(token: str, compression: int) -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=compression) as archive:
        archive.writestr("secret.txt", f'key = "{token}"\n')
    return payload.getvalue()


@pytest.mark.parametrize(
    ("name", "compression"),
    [
        ("doc.docx", zipfile.ZIP_STORED),
        ("doc.docx", zipfile.ZIP_DEFLATED),
        ("book.xlsx", zipfile.ZIP_DEFLATED),
        ("a.zip", zipfile.ZIP_DEFLATED),
    ],
)
def test_zip_member_token_is_scanned(
    tmp_path: Path, name: str, compression: int
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    token = _runtime_token()
    (repo / name).write_bytes(_zip_with_token(token, compression))
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "zip member")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def _commit_bytes(repo: Path, name: str, payload: bytes) -> tuple[str, str]:
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    (repo / name).write_bytes(payload)
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "blob")
    return base, _head(repo)


def _expect_prescan_exit_one(repo: Path, base: str, head: str) -> None:
    with pytest.raises(gitleaks_ci.ScanError) as caught:
        gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks())
    assert caught.value.code == 1


def test_zip_member_past_the_count_cap_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index in range(32):
            archive.writestr(f"pad{index}.txt", "pad")
        archive.writestr("secret.txt", f'key = "{token}"\n')
    base, head = _commit_bytes(repo, "data.bin", payload.getvalue())
    _expect_prescan_exit_one(repo, base, head)


def test_zip_member_over_one_mebibyte_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("big.bin", b"\x00" * (1024 * 1024 + 1) + f'key = "{token}"\n'.encode())
    base, head = _commit_bytes(repo, "data.bin", payload.getvalue())
    _expect_prescan_exit_one(repo, base, head)


def test_zip_members_past_four_mebibytes_fail(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    payload = io.BytesIO()
    chunk = b"\x00" * (1024 * 1024)
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index in range(4):
            archive.writestr(f"pad{index}.bin", chunk)
        archive.writestr("secret.txt", f'key = "{token}"\n')
    base, head = _commit_bytes(repo, "data.bin", payload.getvalue())
    _expect_prescan_exit_one(repo, base, head)


def test_unreadable_zip_member_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("secret.txt", f'key = "{token}"\n')
    raw = bytearray(payload.getvalue())
    raw[8:10] = (99).to_bytes(2, "little")
    central = raw.find(b"PK\x01\x02")
    raw[central + 10 : central + 12] = (99).to_bytes(2, "little")
    base, head = _commit_bytes(repo, "data.bin", bytes(raw))
    _expect_prescan_exit_one(repo, base, head)


def _deflated_zip(name: str, payload: bytes) -> bytes:
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, payload)
    return raw.getvalue()


@pytest.mark.parametrize(
    ("name", "prefix"),
    [
        ("data.bin", b"XXXX"),
        ("note.pdf", b"%PDF-1.4\n"),
        ("data.bin", b"\x7fELF"),
    ],
)
def test_zip_after_a_prefix_is_unpacked(
    tmp_path: Path, name: str, prefix: bytes
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    inner = _zip_with_token(token, zipfile.ZIP_DEFLATED)
    base, head = _commit_bytes(repo, name, prefix + inner)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_gzip_member_is_unpacked(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    payload = io.BytesIO()
    with gzip.GzipFile(fileobj=payload, mode="wb") as handle:
        handle.write(f'key = "{token}"\n'.encode())
    base, head = _commit_bytes(repo, "data.bin", payload.getvalue())
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_nested_zip_member_is_unpacked(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    inner = _zip_with_token(token, zipfile.ZIP_DEFLATED)
    base, head = _commit_bytes(repo, "data.bin", _deflated_zip("inner.zip", inner))
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_zip_nested_past_the_depth_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    inner = _zip_with_token(token, zipfile.ZIP_DEFLATED)
    middle = _deflated_zip("inner.zip", inner)
    outer = _deflated_zip("middle.zip", middle)
    base, head = _commit_bytes(repo, "data.bin", outer)
    _expect_prescan_exit_one(repo, base, head)


def test_ustar_magic_at_offset_257_is_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    token = _runtime_token()
    payload = bytearray(257)
    payload += b"ustar"
    payload += f'\nkey = "{token}"\n'.encode()
    base, head = _commit_bytes(repo, "data.bin", bytes(payload))
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 1


def test_image_magic_without_a_token_is_not_a_finding(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    (repo / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(128, 256)))
    _git(repo, "add", "logo.png")
    _git(repo, "commit", "-q", "-m", "image only")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 0


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


def test_gitleaks_pin_rejects_a_different_file(tmp_path: Path) -> None:
    fake = tmp_path / "gitleaks"
    fake.write_bytes(b"not-the-pinned-binary")
    assert _pinned_gitleaks(fake) is None


def test_wide_decoder_names_stay_in_the_script() -> None:
    """ASCII wide text also survives NUL stripping. The codecs stay anyway."""
    source = _SCRIPT.read_text(encoding="utf-8")
    body = source.split("def _decode_opaque", 1)[1].split("\ndef ", 1)[0]
    for name in ("utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be"):
        assert f'"{name}"' in body
    assert 'replace(b"\\x00"' in body


def test_checkout_directory_at_a_canary_path_does_not_fail_the_scan(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    base = _commit_file(repo, "readme.txt", "ok\n", "base")
    blocked = repo / "nested" / "deep" / "slack-canary.txt"
    blocked.mkdir(parents=True)
    (blocked / "keep.txt").write_text("ok\n", encoding="utf-8")
    _git(repo, "add", "nested")
    _git(repo, "commit", "-q", "-m", "directory at canary path")
    head = _head(repo)
    assert gitleaks_ci.run_pull_request_scan(repo, base, head, _gitleaks()) == 0


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
