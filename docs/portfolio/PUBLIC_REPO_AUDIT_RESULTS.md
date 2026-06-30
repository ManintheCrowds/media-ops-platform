# Public Repo Audit Results

**Date:** 2025-02-10  
**Scope:** portfolio-harness (root + obsidian_cursor_integration, WatchTower_main\WatchTower_main), software, Arc_Forge, moltbook-watchtower.  
**Checklist:** [PUBLIC_REPO_AUDIT_CHECKLIST.md](PUBLIC_REPO_AUDIT_CHECKLIST.md)

---

## 1. portfolio-harness (root)

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | N/A (no root requirements) |
| **Tests** | N/A (no tests at root) |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | See Summary |

---

## 2. obsidian_cursor_integration

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, MISSING .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | Skipped (pip-audit not installed) |
| **Tests** | **Pass** — 30 passed in 0.66s |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | None in this project |

---

## 3. WatchTower_main\WatchTower_main

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | Skipped (pip-audit not installed) |
| **Tests** | **Fail** — 14 errors during collection (import/env issues) |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | WatchTower_main: `docs/README.md` has "[Your License Here]" (lines 180, 407); `daggr_workflows/EVALUATION.md` has multiple "TBD" |

---

## 4. software

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | Skipped (pip-audit not installed) |
| **Tests** | **Fail** — 1 failed, 40 passed (unit); coverage gate 70% not reached (38%); full run aborted |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | None in project docs (only checklist/template references) |

---

## 5. Arc_Forge

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | N/A (no single root deps; optional per-component) |
| **Tests** | **Pass** — All suites passed (campaign_kb, workflow_ui, ObsidianVault scripts): 273 passed, 9 skipped |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | None in this project |

---

## 6. moltbook-watchtower

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore *(Note: one run showed MISSING README.md; README.md was added in a prior task—verify on your FS.)* |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | Skipped (pip-audit not installed) |
| **Tests** | **Pass** — 58 passed in 2.53s |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | None in this project |

---

## Summary

| Item | Count / status |
|------|-----------------|
| **MISSING LICENSE** | 6/6 roots (all) |
| **MISSING .gitignore** | 1 (obsidian_cursor_integration) |
| **Gitleaks** | Run locally 2026-06-05 (8.30.1, exit 0); see `run-gh-pf03-local-scan.ps1` |
| **pip audit** | Not run (pip-audit not installed); run `pip install pip-audit` then re-audit |
| **Test failures** | 2: WatchTower_main (collection errors), software (1 failing test + coverage gate) |
| **Stale "Your License Here" / TBD** | WatchTower_main: `docs/README.md` (2), `daggr_workflows/EVALUATION.md` (multiple TBD) |

### Recommended next steps

1. **Add LICENSE** to all six roots (MIT, Apache 2.0, or "Proprietary — All rights reserved").
2. **Add .gitignore** to `obsidian_cursor_integration` (include `.env`, `venv/`, `__pycache__/`, etc.).
3. **Fix WatchTower_main tests:** resolve 14 collection errors (imports or env); replace "[Your License Here]" in `docs/README.md` and add a real LICENSE at repo root.
4. **Fix software tests:** address failing test (`test_secret_key_min_length`) and optionally relax or meet coverage gate.
5. **Install and run gitleaks** (or rely on existing GitHub workflows) and **pip-audit** for a full security pass; re-run this checklist and update this report.

---

## 7. media-ops-platform (2026-06-23 partial re-run)

**Scope:** `ManintheCrowds/media-ops-platform` only (PF-REPO-4 partial). Other five pinned repos: backlog for PF-PR-16 quarterly ritual.

**Evidence:** [2026-06-23-media-ops-pf04-audit](https://github.com/ManintheCrowds/MiscRepos/blob/main/local-proto/docs/adhoc/2026-06-23-media-ops-pf04-audit.md)

| Section | Result |
|---------|--------|
| 1 Security & secrets | **Partial pass** — gitleaks exit 0; TruffleHog verified=1 (Adzuna Gate 1 pending); scheduled TruffleHog CI failing nightly |
| 2 First-impression hygiene | **Pass** — MIT LICENSE, README, .gitignore, .env.example |
| 3 Runnable in 5 min | **Partial** — documented; full compose not agent-verified (Docker daemon off on audit host) |
| 4 Consistency | **Pass** — README matches portfolio template |
| 5 Trust & maintainability | **Partial** — CI workflows active; branch protection not configured |
| 6 Portfolio narrative | **Pass** — CaptionPipeline snapshot honest; Grafana screenshot deferred |

**Recommended next steps (media-ops):**

1. Execute [OPERATOR_SECURITY_GATES.md](OPERATOR_SECURITY_GATES.md) Gate 1 + branch protection.
2. Complete PF-REPO-2 when Grafana reachable; PF-REPO-8 live metrics export.
3. Re-run checklist on remaining five pinned repos under PF-PR-16.
