---
name: Post-Rename Path Audit Fix
overview: Audit found 50+ references to `CodeRepositories` or `D:\CodeRepositories` across 6 workspaces. This plan fixes broken paths by replacing them with `portfolio-harness` or `D:\portfolio-harness`.
status: pending
priority: 4
phase: later
todos: []
isProject: false
---

# Post-Rename Path Audit and Fix Plan

## Audit Summary

The rename from `CodeRepositories` to `portfolio-harness` broke references in **6 workspaces**. Generic phrases like "code repositories" (Gitea description) are unchanged.

---

## Workspaces Requiring Updates

### 1. portfolio-harness (this repo)


| File                                                                                                                             | Action                                                                                                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [.cursor/mcp.json](.cursor/mcp.json)                                                                                             | Replace `D:/CodeRepositories` with `D:/portfolio-harness` in all path entries                                                                                                         |
| [.cursor/state/README.md](.cursor/state/README.md)                                                                               | Update org-intent path                                                                                                                                                                |
| [.cursor/state/known-issues.md](.cursor/state/known-issues.md)                                                                   | Git MCP `--repository` path                                                                                                                                                           |
| [.cursor/state/rename_instructions.md](.cursor/state/rename_instructions.md)                                                     | Update or archive (rename done)                                                                                                                                                       |
| [local-proto/scripts/check_intent_checksum.ps1](local-proto/scripts/check_intent_checksum.ps1)                                   | `$IntentPath`                                                                                                                                                                         |
| [local-proto/scripts/pre_install_check.ps1](local-proto/scripts/pre_install_check.ps1)                                           | `$RepoRoot`                                                                                                                                                                           |
| [local-proto/docs/*](local-proto/docs/)                                                                                          | INTENT_CHECKSUM, MCP_TEST_TROUBLESHOOTING, FIRST_INSTALL_RUNBOOK, INSTALL_READINESS_AUDIT, SECURITY_AUDIT_INSTALL_GATE, MCP_SERVERS, OBSERVABILITY_LAYER, PLAYWRIGHT_MCP_CONFIG, TODO |
| [.github/workflows/mcp_tests.yml](.github/workflows/mcp_tests.yml)                                                               | `sed` replacement target                                                                                                                                                              |
| [obsidian_cursor_integration/docs/*](obsidian_cursor_integration/docs/)                                                          | MCP_SETUP, OLLAMA_TETHER, RUNBOOK; [obsidian_cursor_integration/mcp.json](obsidian_cursor_integration/mcp.json)                                                                       |
| [docs/cognitive-ergonomics-seed/GAP_DOCS_IMPLEMENTATION_SPEC.md](docs/cognitive-ergonomics-seed/GAP_DOCS_IMPLEMENTATION_SPEC.md) | Path refs                                                                                                                                                                             |


**Plans and archives** (lower priority; historical): `.cursor/plans/*.plan.md`, `.cursor/state/handoff_archive/`*, `.cursor/state/adhoc/`*, `.cursor/state/security_audit_*.md`, `.cursor/docs/SECURITY_*.md`, `.cursor/docs/UPLOAD_READINESS.md` — update if you want plans to reflect current paths.

---

### 2. software


| File                                                                                             | Action                                                                         |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| [job-automation-service/app/main.py](D:\software\job-automation-service\app\main.py)             | `LOG_PATH = Path(r"d:\portfolio-harness\.cursor\debug.log")`                   |
| [job-automation-service/app/database.py](D:\software\job-automation-service\app\database.py)     | Same                                                                           |
| [job-automation-service/app/api/jobs.py](D:\software\job-automation-service\app\api\jobs.py)     | Same (2 occurrences)                                                           |
| [job-automation-service/test_*.py](D:\software\job-automation-service/)                          | verify_jobs_saved, test_other_sources, test_server_startup, install_*, debug_* |
| [scripts/setup_camera_env.ps1](D:\software\scripts\setup_camera_env.ps1)                         | `$storagePath = "D:\portfolio-harness\software\camera_recordings"`             |
| [darktide_ssl_timeout_debug.ps1](D:\software\darktide_ssl_timeout_debug.ps1)                     | `$logPath`                                                                     |
| [SSL_TIMEOUT_HYPOTHESES.md](D:\software\SSL_TIMEOUT_HYPOTHESES.md)                               | Log path                                                                       |
| [docs/AI_DOCUMENTATION_INDEX.md](D:\software\docs\AI_DOCUMENTATION_INDEX.md)                     | Multi-workspace link                                                           |
| [docs/portfolio/*.md](D:\software\docs\portfolio\)                                               | PENDING_ACTIONS_STATUS, PUBLIC_REPO_AUDIT_*, README                            |
| [docs/CAMERA_MIGRATION*.md](D:\software\docs\)                                                   | ARLO_STORAGE_PATH                                                              |
| [docs/OAUTH2_FIX_AND_SETUP.md](D:\software\docs\OAUTH2_FIX_AND_SETUP.md)                         | ARLO_STORAGE_PATH                                                              |
| [job-automation-service/DEBUG_COMPLETE.md](D:\software\job-automation-service\DEBUG_COMPLETE.md) | Log path                                                                       |


**Note:** `D:\portfolio-harness\software\camera_recordings` assumes `software` is a sibling of `portfolio-harness`. If `software` is a separate repo at `D:\software`, the path may need to be `D:\software\camera_recordings` instead. Check intent.

---

### 3. Arc_Forge


| File                                                                                              | Action                                                       |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| [ObsidianVault/scripts/rag_pipeline.py](D:\Arc_Forge\ObsidianVault\scripts\rag_pipeline.py)       | `RAG_DEBUG_LOG_PATH`                                         |
| [ObsidianVault/scripts/ai_summarizer.py](D:\Arc_Forge\ObsidianVault\scripts\ai_summarizer.py)     | `DEBUG_LOG_PATH`                                             |
| [ObsidianVault/Vehicle_Recovery_Riverview_Tower.md](D:\Arc_Forge\ObsidianVault\)                  | Links to local-proto, .cursor                                |
| [ObsidianVault/scripts/docs/*.md](D:\Arc_Forge\ObsidianVault\scripts\docs\)                       | ERROR_MONITORING, RAG_VERIFICATION, RAG_FEATURE_COMPLETENESS |
| [ObsidianVault/scripts/TROUBLESHOOTING.md](D:\Arc_Forge\ObsidianVault\scripts\TROUBLESHOOTING.md) | known-issues                                                 |
| [ObsidianVault/workflow_ui/docs/*.md](D:\Arc_Forge\ObsidianVault\workflow_ui\docs\)               | DEVELOPMENT_PLAN, GUI_AUDIT                                  |
| [campaign_kb/daggr_workflows/README.md](D:\Arc_Forge\campaign_kb\daggr_workflows\README.md)       | "CodeRepositories workspace" text                            |


---

### 4. ACE-first


| File                                                         | Action                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------- |
| [ACE_Framework-main/.../org_intent/README.md](D:\ACE-first\) | Links to org-intent-spec                                |
| [ACE_Framework-main/.../org_intent/config.py](D:\ACE-first\) | Default path `D:/portfolio-harness/org-intent-spec/...` |


---

### 5. local-first


| File                                            | Action                                    |
| ----------------------------------------------- | ----------------------------------------- |
| [AI_SECURITY.md](D:\local-first\AI_SECURITY.md) | Links to local-proto, OBSERVABILITY_LAYER |
| [AGENTS.md](D:\local-first\AGENTS.md)           | decision-log path                         |


---

### 6. moltbook-watchtower


| File                                                                                                     | Action                                |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| [.github/workflows/security-gitleaks.yml](D:\moltbook-watchtower.github\workflows\security-gitleaks.yml) | Comment "Copy from portfolio-harness" |


---

## No Changes Needed

- **dashboard.html**, **SERVICE_HELP.md**, **DASHBOARD_USER_GUIDE.md**, **education-service/docs/INTEGRATION.md** — "code repositories" refers to Gitea, not the folder name.

---

## Implementation Order

1. **portfolio-harness** — `.cursor/mcp.json`, `local-proto/scripts/*.ps1`, `local-proto/docs/`*, `obsidian_cursor_integration`
2. **software** — job-automation-service (LOG_PATH), camera/storage paths
3. **Arc_Forge** — RAG scripts, ObsidianVault links
4. **ACE-first** — org_intent config
5. **local-first** — AI_SECURITY, AGENTS
6. **moltbook-watchtower** — workflow comment

---

## Verification

After updates:

- Run `job-automation-service` and confirm logs write to the new path
- Run `local-proto` pre_install_check and check_intent_checksum
- Run MCP tests (`.github/workflows/mcp_tests.yml`)
- Open Arc_Forge RAG scripts and confirm they resolve the debug log path

