# Pending Action Items — Status (later version)

**Status as of:** 2025-02-10 (post-implementation pass)  
**Source (canonical list):** [Pending Action Items plan](D:\CodeRepositories\.cursor\plans\pending_action_items_35faf7f5.plan.md) in CodeRepositories `.cursor/plans/`.  
This doc is a **later snapshot** of that plan with Done / Pending applied after the implementation run. Re-run the checklist or update this file when you complete more items.

---

## 1. Public repo audit (all roots)

| Status  | Action | Where |
|---------|--------|--------|
| Done    | Add **LICENSE** (Proprietary — All rights reserved) | All six roots |
| Done    | Add **.gitignore** | obsidian_cursor_integration |
| Pending | Fix **WatchTower_main tests** (14 collection errors) | WatchTower_main\WatchTower_main |
| Done    | Fix **software tests** (`test_secret_key_min_length` / Pydantic v2) | software |
| Done    | Replace "[Your License Here]" in WatchTower docs | docs/README.md |
| Pending | Fill or remove **TBD** placeholders | daggr_workflows/EVALUATION.md |
| Pending | Install and run **gitleaks** and **pip-audit**; re-run audit | Per PUBLIC_REPO_AUDIT_CHECKLIST.md |

---

## 2. Security remediation (CodeRepositories / software)

| Status  | Priority | Action |
|---------|----------|--------|
| Pending | P0 | Review CRITICAL in SECURITY_AUDIT_REPORT.md; remove/sanitize credentials; rotate if exposed |
| Pending | P1 | Secrets scanning workflow; CodeQL; .github/dependabot.yml |
| Pending | P2 | Normalize .gitignore; document placeholder patterns |
| Pending | P3 | Clean up debug prints/TODOs from scans |

---

## 3. Known issues (fixes / follow-ups)

| Status  | Project | Issue | Action |
|---------|---------|--------|--------|
| Done    | Cross-repo | .pytest-tmp/ in .gitignore | Already present in all four repos |
| Done    | WatchTower_main | Flask-Session `save_session` request | Pass `request` into `_is_daggr_run_complete_path(request)` in redis_session.py |
| Done    | WatchTower_main | run-complete middleware | Already wraps `app.wsgi_app` |
| Done    | workflow_ui | "Error: [object Object]" | formatErr in app.js and utils.js (msg + "[object Object]" → "Unknown error") |
| Done    | workflow_ui | rag_pipeline path | _VAULT / _SCRIPTS already on sys.path before imports |
| —       | Arc_Forge | Folder rename "Folder In Use" | Workaround in known-issues; no code change |

---

## 4. Upload readiness (first push / after push)

| Status  | Phase | Action |
|---------|--------|--------|
| Pending | Before first push | Review allowlists; run gitleaks/trufflehog locally per root |
| Pending | Phase4 | Remediation backlog after first push |
| Pending | After first push | Branch protection on main; validate workflows on GitHub |

---

## 5. Arc_Forge

| Status  | Item | Notes |
|---------|------|--------|
| Done    | Doc path cleanup (wrath_and_glory → Arc_Forge) | ROADMAP_STATUS, RUNBOOK, INTEGRATION_POINTS, Sources, gui_audit_tasks; ingest_config, rag_pipeline, extract_character_sheets, ingest_pdf_cache, alembic.ini |
| Done    | Terminal cwd | .vscode/settings.json already had `terminal.integrated.cwd` |
| Pending | Optional P2/P3 | In-context help, manual I/O alignment, E2E, path traversal, rate-limit docs |
| Pending | workflow_ui remaining | Per DEVELOPMENT_PLAN_REMAINING.md |

---

## 6. Software (platform)

| Status  | Item | Notes |
|---------|------|--------|
| Done    | test_secret_key_min_length | Assertion updated for Pydantic v2 `string_too_short` |
| Pending | Coverage 58% → 70% | COVERAGE_GAPS_SUMMARY.md |
| Pending | strengthen_debug_security plan | DEVELOPMENT.md, SECURITY.md |
| Pending | project_status / codebase_audit plans | Per plan action items |

---

## 7. Local gitleaks and repo mappings

| Status  | Action |
|---------|--------|
| Pending | Run gitleaks from prusa_XL_soft, moltbook-watchtower, Arc_Forge before first push |
| Pending | Document/confirm Git remote mappings |

---

## Summary

- **Done this pass:** LICENSE (6), .gitignore (obsidian_cursor_integration), WatchTower docs "[Your License Here]", WatchTower redis_session save_session, workflow_ui formatErr + path, Arc_Forge doc/config path cleanup, software test_secret_key_min_length.
- **Still pending:** WatchTower test collection errors; TBD in EVALUATION.md; gitleaks/pip-audit run; security P0–P3; upload phases; coverage and other software plans; local gitleaks per root; optional Arc_Forge P2/P3 and workflow_ui remaining.

Update this file when you complete more items or re-run the [PUBLIC_REPO_AUDIT_CHECKLIST](PUBLIC_REPO_AUDIT_CHECKLIST.md).
