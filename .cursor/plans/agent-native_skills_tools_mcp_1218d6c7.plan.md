---
name: Agent-Native Skills Tools MCP
overview: Implement agent-native architecture improvements across skills (capability maps, parity, composability), MCP tools (CRUD audit, primitives, discovery), and MCP servers (capability maps, context injection), plus role-routing integration.
todos:
  - id: phase1-capability-maps
    content: Add capability map sections to docker-mcp, browser-web, price-deals, gws-workspace, lobster-university skills
    status: completed
  - id: phase1-composes-with
    content: Add agent-native-architecture to Composes with in tech-lead, frontier-ops, security-audit-rules, refactor-reuse
    status: completed
  - id: phase2-credential-update
    content: Implement credential_vault_update in vault.py and credential_vault_mcp.py
    status: completed
  - id: phase3-mcp-capability-map
    content: Create .cursor/docs/MCP_CAPABILITY_MAP.md with per-server capability tables
    status: completed
  - id: phase4-role-routing
    content: Add 5b agent-native-architecture branch to role-routing.mdc and tie-break priority
    status: completed
  - id: phase4-skill-exclusion
    content: Update SKILL_EXCLUSION_GRAPH.md with agent-native composition sequences
    status: completed
  - id: phase5-pr-checklist
    content: Add Agent-Native Checklist to PR template or .cursor/docs
    status: completed
  - id: phase5-org-intent
    content: Add credential_vault_update to org-intent escalation_tools when implemented
    status: completed
isProject: false
---

# Agent-Native Architecture Improvement Plan

## Current State Summary

**Skills:** 17 skills in `[.cursor/skills/](D:\portfolio-harness\.cursor\skills)`; 9 duplicated in [portable-skills](D:\portfolio-harness\portable-skills). Tool-using skills: browser-web, docker-mcp, price-deals, gws-workspace, lobster-university, qa-verifier.

**MCP servers:** 12 servers in `[.cursor/mcp.json](D:\portfolio-harness\.cursor\mcp.json)`. Custom scripts in [local-proto/scripts/](D:\portfolio-harness\local-proto\scripts): credential_vault_mcp, unhuman_deals_mcp, lobster_university_mcp, observation_mcp, provenance_mcp. Third-party: docker-mcp, filesystem, sqlite, git, playwright, scrapling, jcodemunch. Obsidian vault: [obsidian_cursor_integration/mcp_server/server.py](D:\portfolio-harness\obsidian_cursor_integration\mcp_server\server.py).

**CRUD gaps identified:**

- **Credential-vault:** Create, Read, Delete, Export exist. **Update missing** — `create` overwrites (rotate), but no `credential_vault_update(site, email?, password?)` for partial updates.
- **Obsidian-vault:** Create/Update via `apply_patch`. Read via `vault_search`, `note_context`. **Delete:** No explicit delete tool; filesystem MCP (D:/Arc_Forge) can delete files in vault — shared workspace covers this.
- **Filesystem MCP:** read_file, write_file, list_directory, move_file, edit_file. No explicit `delete_file` in standard server — verify and document workaround (move to trash or out-of-scope path) if needed.

---

## Phase 1: Skills — Capability Maps and Parity

### 1.1 Add capability map to tool-using skills

Add a `## Capability map (parity)` section to each skill that uses MCP tools. Template:

```markdown
## Capability map (parity)

| Human action | Agent achieves via |
|--------------|-------------------|
| [action] | [tool(s)] |
```

**Files to modify:**


| Skill              | Path                                                                                                         | Capability map content                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| docker-mcp         | [.cursor/skills/docker-mcp/SKILL.md](D:\portfolio-harness.cursor\skills\docker-mcp\SKILL.md)                 | Deploy stack, view logs, remove container, prune images (with APPROVAL_NEEDED) |
| browser-web        | [.cursor/skills/browser-web/SKILL.md](D:\portfolio-harness.cursor\skills\browser-web\SKILL.md)               | Navigate, screenshot, fill form, scrape (cursor-ide-browser / Playwright MCP)  |
| price-deals        | [.cursor/skills/price-deals/SKILL.md](D:\portfolio-harness.cursor\skills\price-deals\SKILL.md)               | Search products, get offers (search_products, get_offers)                      |
| gws-workspace      | [.cursor/skills/gws-workspace/SKILL.md](D:\portfolio-harness.cursor\skills\gws-workspace\SKILL.md)           | List Drive, create spreadsheet, etc. (gws CLI + credential_vault_get)          |
| lobster-university | [.cursor/skills/lobster-university/SKILL.md](D:\portfolio-harness.cursor\skills\lobster-university\SKILL.md) | Sign register, get attendance, get stats (lobster_* MCP tools)                 |


### 1.2 User vocabulary and exit criteria

- **User vocabulary:** Ensure `triggers_any` and descriptions use phrases users say (e.g. "deploy stack", "container logs"). Most skills already do; audit price-deals, lobster-university for gaps.
- **Exit criteria:** Each skill has `exit_criteria` in frontmatter. Verify they are explicit (no heuristic completion). docker-mcp and browser-web already specify "verify" steps.

### 1.3 Composability and "Composes with"

- Add **agent-native-architecture** to "Composes with" in skills that design or audit tools: tech-lead, frontier-ops, security-audit-rules, refactor-reuse.
- Ensure docker-mcp, browser-web list composability with qa-verifier, tech-lead (already present).

### 1.4 Portable-skills sync

- portable-skills contains copies of docker-mcp, dialectic-protocol, docs, planning, product-scope, qa-verifier, refactor-reuse, security-audit-rules, tech-lead.
- **Decision:** Update `.cursor/skills` as source of truth. If portable-skills is consumed elsewhere, add a sync step or document that portable-skills should be updated when .cursor/skills changes. For this plan, focus on .cursor/skills; portable-skills can be updated in a follow-up if needed.

---

## Phase 2: MCP Tools — CRUD, Primitives, Discovery

### 2.1 Credential-vault: Add `credential_vault_update`

**Gap:** No way to update email or password without revoke + create.

**Implementation:**

1. **[local-proto/credential_vault/vault.py](D:\portfolio-harness\local-proto\credential_vault\vault.py):** Add `update(site: str, email: str | None = None, password: str | None = None) -> bool`. If email/password provided, merge into existing entry; return True if site existed.
2. **[local-proto/scripts/credential_vault_mcp.py](D:\portfolio-harness\local-proto\scripts\credential_vault_mcp.py):** Add tool `credential_vault_update(site: str, email: str | None = None, password: str | None = None) -> str`. Requires APPROVAL_NEEDED per TOOL_SAFEGUARDS (same as create/revoke).

### 2.2 Obsidian-vault: Document delete path

- Obsidian MCP has no `delete_file`. Filesystem MCP has access to `D:/Arc_Forge` (vault root). Verify filesystem MCP tools: if `delete_file` exists, document in capability map. If not, `move_file` to a trash path or document that delete is via filesystem primitives.
- Add capability map for obsidian-vault (see Phase 3).

### 2.3 CRUD audit summary


| Entity           | Create                  | Read                                             | Update                               | Delete                                |
| ---------------- | ----------------------- | ------------------------------------------------ | ------------------------------------ | ------------------------------------- |
| Credential       | credential_vault_create | credential_vault_get, credential_vault_list      | **credential_vault_update** (to add) | credential_vault_revoke               |
| Obsidian note    | apply_patch (new file)  | vault_search, note_context                       | apply_patch                          | filesystem move/delete (if available) |
| Docker container | docker_create_container | docker_inspect_container, docker_list_containers | restart (stop+start)                 | docker_remove_container               |
| Product offer    | N/A (read-only)         | search_products, get_offers                      | N/A                                  | N/A                                   |


### 2.4 Primitives and discovery

- **Docker:** Already primitive-based (docker-mcp). No changes.
- **Obsidian:** `vault_search` + `note_context` provide discovery; `index_health` gives index status. No static per-note-type tools — good.
- **SQLite:** Third-party `mcp-server-sqlite` provides catalog + execute. Verify it has `list_tables` or equivalent; document in capability map.
- **Input design:** Audit custom MCPs for `z.enum` overuse. unhuman-deals, lobster-university, credential-vault use string inputs — good.

### 2.5 Output richness

- Ensure tools return enough for agent to verify (e.g. "Deleted X. N items remaining."). credential_vault_revoke already returns `{"ok": true, "existed": true}`. Spot-check other custom MCPs.

---

## Phase 3: MCP Servers — Capability Maps and Context

### 3.1 Create MCP capability map document

Create `[.cursor/docs/MCP_CAPABILITY_MAP.md](D:\portfolio-harness\.cursor\docs\MCP_CAPABILITY_MAP.md)` with per-server capability tables:

```markdown
# MCP Capability Map

Per-server mapping of user/domain actions to agent tools. Update when adding tools.

## obsidian-vault
| User action | Agent tool | Status |
|-------------|------------|--------|
| Create note | apply_patch (new file) | Done |
| Edit note | apply_patch | Done |
| Search notes | vault_search | Done |
| Get note context | note_context | Done |
| Delete note | filesystem (if delete available) or move_file | Check |

## credential-vault
...

## docker
...

## unhuman-deals
...

## filesystem
...
```

Include all 12 servers. Mark gaps as "Check" or "Missing".

### 3.2 Context injection

- Skills already inject capability vocabulary (tool names, when to use). No new runtime injection mechanism needed.
- Ensure each tool-using skill documents "Available tools" or references the capability map. docker-mcp and browser-web do this implicitly via Steps. Add explicit "Tools" subsection where missing (price-deals, lobster-university).

### 3.3 Shared workspace verification

- Filesystem: `D:/portfolio-harness`, `D:/Arc_Forge` — shared.
- Obsidian vault: `D:/Arc_Forge/ObsidianVault` — under Arc_Forge, so filesystem can access.
- SQLite: `D:/Arc_Forge/campaign_kb/data/kb.sqlite3` — shared.
- No agent sandbox; workspace is shared. Document in MCP_CAPABILITY_MAP or a short "Workspace" section.

---

## Phase 4: Integration — Role-Routing and References

### 4.1 Add agent-native-architecture to role-routing

**File:** [.cursor/rules/role-routing.mdc](D:\portfolio-harness.cursor\rules\role-routing.mdc)

**Insert** after step 5a (frontier-ops), as new step **5b**:

```markdown
5b. **Is the task designing agent tools, MCP servers, or action parity?** (e.g. "improve MCP", "agent tools", "parity", "capability map", "agent-native")  
   → Load **agent-native-architecture** skill (compound-engineering plugin). Apply Architecture Checklist; read mcp-tool-design, action-parity-discipline references.
```

**Tie-break priority:** Add `5b. Agent tools / MCP / parity (agent-native-architecture)` after 5a.

**Note:** The agent-native-architecture skill lives in the compound-engineering Cursor plugin. Role-routing should reference it by description; the agent will load it when the plugin is available. If the plugin path is known, document it. Otherwise, the trigger phrases suffice.

### 4.2 Update SKILL_EXCLUSION_GRAPH

**File:** [.cursor/docs/SKILL_EXCLUSION_GRAPH.md](D:\portfolio-harness.cursor\docs\SKILL_EXCLUSION_GRAPH.md)

- Add agent-native-architecture to composition sequences: `tech-lead → agent-native-architecture` (when designing tools), `refactor-reuse → agent-native-architecture` (when adding MCP tools).
- No mutual exclusions needed.

### 4.3 Org-intent and escalation_tools

**File:** [org-intent-spec/examples/org-intent.example.json](D:\portfolio-harness\org-intent-spec\examples\org-intent.example.json)

- `escalation_tools` already lists credential_vault_*, docker_* tools. Add `credential_vault_update` to the hb-1 tools list when implemented.
- Document in plan or MCP_CAPABILITY_MAP that each escalation tool should have a clear user action in the capability map.

---

## Phase 5: Parity Workflow and Maintenance

### 5.1 PR checklist addition

Add to project PR template or [.cursor/docs/](D:\portfolio-harness.cursor\docs/) a checklist:

```markdown
## Agent-Native Checklist (when adding UI or MCP tools)

- [ ] Every new UI action has a corresponding agent tool
- [ ] MCP_CAPABILITY_MAP.md updated
- [ ] Skill capability map updated (if skill uses new tools)
- [ ] Tested with natural language request
```

### 5.2 agent-native-reviewer subagent

- When adding UI features or new MCP tools, invoke `agent-native-reviewer` subagent to verify parity.
- Document in HANDOFF_FLOW or agent docs when to run this (e.g. after feature-complete, before merge).

---

## Implementation Order


| Phase | Tasks                                    | Dependencies             |
| ----- | ---------------------------------------- | ------------------------ |
| 1     | Skills: capability maps, Composes with   | None                     |
| 2     | credential_vault_update (vault.py + MCP) | None                     |
| 3     | MCP_CAPABILITY_MAP.md                    | Phase 1 (for tool names) |
| 4     | role-routing 5b, SKILL_EXCLUSION_GRAPH   | None                     |
| 5     | PR checklist, agent-native-reviewer doc  | Phase 3                  |


**Suggested sequence:** Phase 1 (skills) → Phase 2 (credential_vault_update) → Phase 3 (capability map doc) → Phase 4 (routing) → Phase 5 (maintenance).

---

## Files Changed Summary


| Category   | Files                                                                                                                                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skills     | .cursor/skills/docker-mcp/SKILL.md, browser-web/SKILL.md, price-deals/SKILL.md, gws-workspace/SKILL.md, lobster-university/SKILL.md; optionally tech-lead, frontier-ops, security-audit-rules, refactor-reuse |
| MCP        | local-proto/credential_vault/vault.py, local-proto/scripts/credential_vault_mcp.py                                                                                                                            |
| Docs       | .cursor/docs/MCP_CAPABILITY_MAP.md (new), .cursor/docs/SKILL_EXCLUSION_GRAPH.md                                                                                                                               |
| Routing    | .cursor/rules/role-routing.mdc                                                                                                                                                                                |
| Org-intent | org-intent-spec/examples/org-intent.example.json (add credential_vault_update to escalation_tools when implemented)                                                                                           |


---

## Out of Scope / Deferred

- **Obsidian delete:** If filesystem MCP lacks delete_file, document workaround or defer to filesystem server upgrade.
- **Portable-skills sync:** Update portable-skills copies only if sync process exists; otherwise defer.
- **New agent-native SKILL.md in portfolio-harness:** Use compound-engineering plugin skill; no local copy unless plugin unavailable.

