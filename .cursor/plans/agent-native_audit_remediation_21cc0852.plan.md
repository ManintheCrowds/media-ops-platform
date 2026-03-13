---
name: Agent-Native Audit Remediation
overview: "Implement the top 5 recommendations from the agent-native architecture audit: add observation_list/observation_read, provenance_list, inject available capabilities into system prompt, document Agent→UI data flow for Daggr, and add empty-state/suggested prompts to handoff flow."
todos: []
isProject: false
---

# Agent-Native Audit Remediation Plan

Address the five highest-impact gaps from the critic's agent-native architecture audit.

---

## 1. Add observation_list / observation_read (CRUD completeness)

**Current state:** [observation_mcp.py](D:\portfolio-harness\local-proto\scripts\observation_mcp.py) has only `observation_log_append`. Observations are stored in `docs/bitcoin_observations/YYYY-MM-DD_observations.md` with schema `### {timestamp} | {source} | {obs_type}\n{content}\n`.

**Implementation:**

- **observation_list(date_from?, date_to?, limit?)** — List available observation files or entries. Options: (a) list file names in `bitcoin_observations/` filtered by date range, or (b) parse files and return structured entries (date, source, obs_type, content preview). Prefer (b) for agent reasoning; add `limit` (default 50) to cap output.
- **observation_read(date)** — Read full content of `{date}_observations.md`. Args: `date` (YYYY-MM-DD). Returns file content or error.

**Files to modify:**

- [local-proto/scripts/observation_mcp.py](D:\portfolio-harness\local-proto\scripts\observation_mcp.py)
- [.cursor/docs/MCP_CAPABILITY_MAP.md](D:\portfolio-harness.cursor\docs\MCP_CAPABILITY_MAP.md) — add rows for list/read
- [docs/BITCOIN_AGENT_CAPABILITIES.md](D:\portfolio-harness\docs\BITCOIN_AGENT_CAPABILITIES.md) — document new tools

**Note:** Update/Delete not recommended for append-only observation log (audit trail). Read + List completes agent's ability to reason over observations.

---

## 2. Add provenance_list (CRUD completeness)

**Current state:** [provenance_mcp.py](D:\portfolio-harness\local-proto\scripts\provenance_mcp.py) has `document_provenance_record` and `bitcoin_provenance_record` only. Logs are JSONL: `docs/provenance_log.jsonl`, `docs/bitcoin_provenance_log.jsonl`.

**Implementation:**

- **provenance_list(log_type?, limit?, url_filter?, txid_filter?)** — Read entries from provenance logs. Args: `log_type` ("document" | "bitcoin" | "both", default both), `limit` (default 50), optional `url_filter` or `txid_filter` for substring match. Returns JSON array of entries (most recent first via tail).

**Files to modify:**

- [local-proto/scripts/provenance_mcp.py](D:\portfolio-harness\local-proto\scripts\provenance_mcp.py)
- [.cursor/docs/MCP_CAPABILITY_MAP.md](D:\portfolio-harness.cursor\docs\MCP_CAPABILITY_MAP.md) — add row for provenance_list

---

## 3. Inject "available capabilities" from MCP_CAPABILITY_MAP into system prompt

**Current state:** MCP_CAPABILITY_MAP is in docs; agents discover it via AGENT_ENTRY_INDEX ("Checking MCP parity..."). No dynamic injection into Cursor's context.

**Options:**

- **A. Add to .cursorrules:** Insert a short "Available capabilities" block that summarizes MCP servers and key tools (e.g. "Observation: append, list, read. Provenance: record, list. Credentials: create, get, update, revoke..."). Risk: token bloat; .cursorrules is already large.
- **B. Create capability summary rule:** New file `.cursor/rules/capability-summary.mdc` with a condensed table (MCP server → tools). Cursor loads rules; this would be always-on. Keep it under ~500 words.
- **C. Add to continue_prompt / session_start_prompt:** Append one line: "Available capabilities: see .cursor/docs/MCP_CAPABILITY_MAP.md or run show_next_goals.ps1 for orientation."

**Recommendation:** B — Create [.cursor/rules/capability-summary.mdc](D:\portfolio-harness.cursor\rules\capability-summary.mdc) with a compact table derived from MCP_CAPABILITY_MAP (server name, tool names). Update via script or manually when adding tools. Reference in AGENT_ENTRY_INDEX.

**Files to create/modify:**

- Create `.cursor/rules/capability-summary.mdc` (condensed table)
- [.cursor/docs/AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md) — add row for "Quick capability reference" → capability-summary rule

---

## 4. Document Agent→UI data flow for Daggr/Gradio

**Current state:** [STACK_OVERVIEW.md](D:\portfolio-harness) (Daggr MCP) describes data flow at a high level. No explicit "Agent writes X → UI shows Y" documentation.

**Data flow (from stack overview):**

- WatchTower: Flask API (5000), RAG, Daggr workflows → Gradio (7860)
- campaign_kb: ingest → SQLite → Daggr search/merge → Gradio (7860)
- workflow_ui (5001): redirects to campaign_kb Daggr

**Agent actions that affect UI:**

- Agent edits campaign_kb config, ingest paths, or SQLite → Daggr reads these on next request or reload
- Agent edits workflow config files → workflow_ui may need restart
- Gradio typically does not hot-reload; restart or explicit reload required

**Implementation:**

- Add new doc [.cursor/docs/AGENT_UI_DATA_FLOW.md](D:\portfolio-harness.cursor\docs\AGENT_UI_DATA_FLOW.md) with:
  - Diagram: Agent (write_file, sqlite_write_query) → Files/SQLite → Daggr/Gradio (reads on request or startup)
  - Table: Agent action | Data store | UI component | Update mechanism (restart, next request, file watch)
  - "Silent actions" note: Agent changes to config/DB may not appear until Gradio restarted or workflow re-run
- Link from [MCP_CAPABILITY_MAP.md](D:\portfolio-harness.cursor\docs\MCP_CAPABILITY_MAP.md) UI Integration section and [HARNESS_ARCHITECTURE.md](D:\portfolio-harness.cursor\docs\HARNESS_ARCHITECTURE.md)

---

## 5. Add empty-state and suggested prompts in handoff/continue flow

**Current state:** [continue_prompt.txt](D:\portfolio-harness.cursor\state\continue_prompt.txt) is instruction-heavy; no "What can I do?" or suggested prompts. [session_start_prompt.txt](D:\portfolio-harness.cursor\state\session_start_prompt.txt) has "[fill in]" placeholders but no suggestions.

**Implementation:**

- **Empty-state block:** Add to end of [continue_prompt.txt](D:\portfolio-harness.cursor\state\continue_prompt.txt): "If handoff is empty or you're unsure what to do: see .cursor/docs/MCP_CAPABILITY_MAP.md and .cursor/docs/COMMANDS_README.md for capabilities. Run .cursor/scripts/show_next_goals.ps1 for next goals."
- **Suggested prompts file:** Create [.cursor/state/suggested_prompts.md](D:\portfolio-harness.cursor\state\suggested_prompts.md) with 5–7 example prompts (e.g. "Summarize today", "Run handoff flow", "Check MCP parity", "Run meta-review"). Reference in continue_prompt and state/README.
- **Session start:** Add to [session_start_prompt.txt](D:\portfolio-harness.cursor\state\session_start_prompt.txt): "Suggested starters: see .cursor/state/suggested_prompts.md"

**Files to create/modify:**

- [.cursor/state/continue_prompt.txt](D:\portfolio-harness.cursor\state\continue_prompt.txt) — append empty-state line
- Create `.cursor/state/suggested_prompts.md`
- [.cursor/state/session_start_prompt.txt](D:\portfolio-harness.cursor\state\session_start_prompt.txt) — add suggested starters ref
- [.cursor/state/README.md](D:\portfolio-harness.cursor\state\README.md) — document suggested_prompts.md in schema

---

## Implementation order


| Step | Task                               | Effort |
| ---- | ---------------------------------- | ------ |
| 1    | observation_list, observation_read | Low    |
| 2    | provenance_list                    | Low    |
| 3    | capability-summary.mdc             | Low    |
| 4    | AGENT_UI_DATA_FLOW.md              | Low    |
| 5    | Empty-state + suggested_prompts    | Low    |


All are documentation or small MCP additions. No breaking changes.

---

## Verification

- Run agent-native-reviewer subagent after implementation
- Test: "List recent Bitcoin observations" → agent uses observation_list
- Test: "What provenance records exist for URL X?" → agent uses provenance_list
- Test: New session with empty handoff → agent finds suggested_prompts or show_next_goals

