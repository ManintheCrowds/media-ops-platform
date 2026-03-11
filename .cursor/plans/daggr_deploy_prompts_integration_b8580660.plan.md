---
name: Daggr Deploy Prompts Integration
overview: Integrate the Daggr deployment prompts (discovery, deploy, single "deploy best") into the docs and add copy scripts plus an optional discovery-report script that renders structured outputs using Daggr MCP.
todos: []
isProject: false
---

# Daggr Deploy Prompts Integration Plan

## Goal

Make the Daggr deployment prompts (discovery, deploy, single "deploy best") usable so an AI system can render the outputs: discovery list, deployment status, and prioritized workflow recommendations.

---

## Deliverables

### 1. Extend DAGGR_GRADIO_AI_ACTION_PROMPTS.md

Add three new action items to [.cursor/docs/DAGGR_GRADIO_AI_ACTION_PROMPTS.md](D:\portfolio-harness.cursor\docs\DAGGR_GRADIO_AI_ACTION_PROMPTS.md):

- **Action D — Discovery:** Prompt to identify 3–5 most important functional areas for Daggr visualization (user impact, data-flow centrality, debugging value, gaps). Output: ranked list with rationale.
- **Action E — Deploy:** Prompt to deploy visualizations for priorities (verify existing, implement missing, ensure entry points). Output: per-workflow status.
- **Action F — Single "deploy best":** Combined 4-step prompt (discovery → prioritize → deploy → document) for one-shot execution.

Reference Daggr MCP tools: `list_workflows`, `get_stack_overview`, `get_graph_schema`, `run_verification`, `run_playwright_smoke`.

### 2. Create Copy-Paste Prompt File

Create [.cursor/state/daggr_deploy_prompt.txt](D:\portfolio-harness.cursor\state\daggr_deploy_prompt.txt) containing the full Action F prompt (single "deploy best"). This is the canonical prompt for "deploy Daggr visualizations for most important functionality."

### 3. Create Copy Script

Create [.cursor/scripts/copy_daggr_deploy_prompt.ps1](D:\portfolio-harness.cursor\scripts\copy_daggr_deploy_prompt.ps1) that copies `daggr_deploy_prompt.txt` to clipboard. Follows the pattern of [copy_session_start_prompt.ps1](D:\portfolio-harness.cursor\scripts\copy_session_start_prompt.ps1).

### 4. Create Discovery Report Script (Optional)

Create [.cursor/scripts/run_daggr_discovery_report.py](D:\portfolio-harness.cursor\scripts\run_daggr_discovery_report.py) that:

- Calls Daggr MCP tools (or imports from `daggr_mcp`) to get `list_workflows("all")`, `get_stack_overview()`, `run_verification("all")`
- Produces a structured markdown report: `DAGGR_DISCOVERY_REPORT.md` (or stdout) with:
  - Workflow registry (from list_workflows)
  - Stack components and data flow (from get_stack_overview)
  - Verification status per stack
  - Suggested priority order (hardcoded or from a small config)

This "renders" the discovery output programmatically without an LLM. The report can be used as input for the deploy prompt or for human review.

### 5. Update COMMANDS_README.md

Add a row to the Handoff and Session Flow table (or a new "Daggr" section):


| Command                                             | When                                                                   |
| --------------------------------------------------- | ---------------------------------------------------------------------- |
| `.\\.cursor\\scripts\\copy_daggr_deploy_prompt.ps1` | New chat: deploy Daggr visualizations for most important functionality |


---

## File Summary


| Action | File                                                                                                                                         |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Modify | [.cursor/docs/DAGGR_GRADIO_AI_ACTION_PROMPTS.md](D:\portfolio-harness.cursor\docs\DAGGR_GRADIO_AI_ACTION_PROMPTS.md) — add Action D, E, F    |
| Create | [.cursor/state/daggr_deploy_prompt.txt](D:\portfolio-harness.cursor\state\daggr_deploy_prompt.txt) — full deploy prompt                      |
| Create | [.cursor/scripts/copy_daggr_deploy_prompt.ps1](D:\portfolio-harness.cursor\scripts\copy_daggr_deploy_prompt.ps1) — copy to clipboard         |
| Create | [.cursor/scripts/run_daggr_discovery_report.py](D:\portfolio-harness.cursor\scripts\run_daggr_discovery_report.py) — render discovery report |
| Modify | [.cursor/docs/COMMANDS_README.md](D:\portfolio-harness.cursor\docs\COMMANDS_README.md) — add command row                                     |


---

## Usage Flow

1. **Quick deploy (AI chat):** Run `copy_daggr_deploy_prompt.ps1`, open new chat, paste. AI runs discovery, prioritizes, deploys, documents.
2. **Discovery only (no LLM):** Run `python .cursor/scripts/run_daggr_discovery_report.py` to produce `DAGGR_DISCOVERY_REPORT.md`.
3. **Phased (A/B/C + D/E):** Use Action A, B, C from existing doc; add D (discovery) or E (deploy) for targeted steps.

---

## Verification

- `copy_daggr_deploy_prompt.ps1` copies non-empty content to clipboard
- `run_daggr_discovery_report.py` runs without error and produces valid markdown
- DAGGR_GRADIO_AI_ACTION_PROMPTS.md includes D, E, F with correct references to Daggr MCP

