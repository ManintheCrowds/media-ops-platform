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
| **Gitleaks** | Not run (gitleaks not installed); use CI workflows or install locally |
| **pip audit** | Not run (pip-audit not installed); run `pip install pip-audit` then re-audit |
| **Test failures** | 2: WatchTower_main (collection errors), software (1 failing test + coverage gate) |
| **Stale "Your License Here" / TBD** | WatchTower_main: `docs/README.md` (2), `daggr_workflows/EVALUATION.md` (multiple TBD) |

### Recommended next steps

1. **Add LICENSE** to all six roots (MIT, Apache 2.0, or "Proprietary — All rights reserved").
2. **Add .gitignore** to `obsidian_cursor_integration` (include `.env`, `venv/`, `__pycache__/`, etc.).
3. **Fix WatchTower_main tests:** resolve 14 collection errors (imports or env); replace "[Your License Here]" in `docs/README.md` and add a real LICENSE at repo root.
4. **Fix software tests:** address failing test (`test_secret_key_min_length`) and optionally relax or meet coverage gate.
5. **Install and run gitleaks** (or rely on existing GitHub workflows) and **pip-audit** for a full security pass; re-run this checklist and update this report.
