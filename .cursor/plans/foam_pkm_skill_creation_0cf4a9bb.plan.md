---
name: Foam PKM Skill Creation
overview: Create a Cursor skill that teaches the agent to work with Foam (VS Code PKM) and Obsidian vaults, using obsidian-vault MCP when the vault is Obsidian and filesystem tools when the workspace is Foam. The skill encodes PKM conventions (wikilinks, tags, embeds, daily notes) and ensures agent-native parity.
todos: []
isProject: false
---

# Foam + Obsidian PKM Skill Creation Plan

## Product Scope (What We're Building)

**Skill name:** `foam-pkm` (or `pkm-vault`)

**Purpose:** Enables the agent to create, edit, search, and link notes in Foam workspaces (VS Code) and Obsidian vaults using the correct tools and conventions for each.

**Success criteria:**

- Agent can create notes with proper `[[wikilinks]]`, `![[embeds]]`, `#tags`
- Agent selects obsidian-vault MCP when vault is Obsidian; filesystem when Foam
- Agent follows Foam/Obsidian daily-note and template conventions
- MCP_CAPABILITY_MAP and AGENT_NATIVE_CHECKLIST updated

**Requirements:**

1. Skill encodes Foam conventions (wikilinks, embeds, tags, daily notes, templates)
2. Tool-selection logic: Obsidian vault path → obsidian-vault MCP; Foam workspace → filesystem + grep
3. Capability map: human actions → agent tools for both environments
4. Composes with handoff flow (session_save when vault work)

---

## Tech Lead: Placement and Structure

**Path:** `D:\portfolio-harness\.cursor\skills\foam-pkm\`

**Rationale:** Matches existing skill layout (browser-web, docs, tech-lead). Project skill since it's workspace-specific (ObsidianVault path, Arc_Forge).

**Structure:**

```
.cursor/skills/foam-pkm/
├── SKILL.md           # Main instructions, tool selection, conventions
├── reference.md       # Optional: Foam vs Obsidian syntax reference
└── (no scripts — uses existing MCP/filesystem)
```

**Conventions to follow:**

- YAML frontmatter with `name`, `description`, `triggers_any` (per create-skill)
- Capability map table (like browser-web)
- Guardrails: privacy, scope, human gate

---

## Agent-Native Audit Considerations

**Action parity:**

- Foam has no MCP (VS Code extension). Agent achieves via: `read_file`, `write_file`, `edit_file`, `grep`, `list_dir` (filesystem MCP).
- Obsidian: vault_search, apply_patch, note_context, session_save, etc. (obsidian-vault MCP).


| Human action        | Foam (agent)                      | Obsidian (agent)            |
| ------------------- | --------------------------------- | --------------------------- |
| Create note         | `write_file`                      | `apply_patch` (new file)    |
| Edit note           | `edit_file` / `write_file`        | `apply_patch`               |
| Search notes        | `grep` or search_files            | `vault_search`              |
| Create wikilink     | Write `[[Note Title]]`            | Same                        |
| Add backlink        | Create note that links to target  | Same                        |
| Daily note          | Use template, write to daily path | session_save or apply_patch |
| Graph visualization | N/A (UI only)                     | N/A (UI only)               |


**Tools as primitives:** All tools are primitives (read, write, search). No workflow tools.

**Shared workspace:** Agent and user work in same files (D:/Arc_Forge, D:/portfolio-harness). No sandbox.

**CRUD completeness:** Create (write_file/apply_patch), Read (read_file/vault_search), Update (edit_file/apply_patch), Delete (move_file to .trash or apply_patch empty).

**UI integration:** Agent writes to files; Foam/Obsidian UI auto-refreshes on file change (file watchers).

**Capability discovery:** Skill description + triggers_any enables discovery.

---

## Brainstorm: Key Decisions

1. **Vault detection:** Skill instructs agent to check workspace root for `.foam/templates` or `.vscode/settings.json` (Foam) vs `OBSIDIAN_VAULT_ROOT` env (Obsidian). If both, prefer Obsidian when path matches.
2. **Wikilink format:** Both use `[[Note Title]]` and `![[Note Title]]`. Foam uses `[[filename]]` or `[[filename#heading]]`. Standardize.
3. **Daily notes:** Foam: `YYYY-MM-DD.md` in configured folder. Obsidian: similar. Template from `.foam/templates/daily-note.md` if present.
4. **Composition:** Handoff flow already invokes session_save when "vault work" — skill should remind agent to use session_save when handing off Obsidian work.
5. **ObsidianVault path:** D:/Arc_Forge/ObsidianVault (from mcp.json). Foam workspace could be same folder or different (e.g. a foam-template repo).

---

## Implementation Steps

### Step 1: Create scope doc

Write to `.cursor/state/scope_foam_pkm_skill.md`:

- Requirements (numbered)
- Acceptance criteria (Given/When/Then)
- Tool selection logic
- Vault path constants

### Step 2: Create SKILL.md

```markdown
---
name: foam-pkm
description: Create, edit, search, and link notes in Foam (VS Code) or Obsidian vaults. Uses obsidian-vault MCP for Obsidian; filesystem for Foam. Use when working with PKM, wikilinks, knowledge graphs, daily notes, or Foam/Obsidian.
triggers_any: ["foam", "obsidian", "pkkm", "wikilink", "knowledge graph", "daily note", "vault", "note", "link notes"]
---
```

Sections:

- **Tool selection:** If ObsidianVault (D:/Arc_Forge/ObsidianVault) in scope → obsidian-vault; else → filesystem
- **Conventions:** wikilinks `[[Title]]`, embeds `![[Title]]`, tags `#tag`
- **Capability map:** Human action → Agent tool (both envs)
- **Daily notes:** Path pattern, template usage
- **Composes with:** handoff (session_save), docs

### Step 3: Update MCP_CAPABILITY_MAP.md

Add section for foam-pkm (or extend obsidian-vault with Foam note):


| User action | Foam (agent) | Obsidian (agent) |
| ----------- | ------------ | ---------------- |
| Create note | write_file   | apply_patch      |
| ...         | ...          | ...              |


### Step 4: Update role-routing / AGENT_ENTRY_INDEX

Add foam-pkm to skill index and role-routing if applicable.

### Step 5: Optional reference.md

Foam vs Obsidian syntax differences, template paths, common gotchas.

---

## Risk and Constraints

- **Low risk:** Skill is doc-only; no new MCP or scripts.
- **Path assumption:** ObsidianVault at D:/Arc_Forge/ObsidianVault. If Foam workspace is elsewhere, add to filesystem MCP allowed paths or document.
- **Scope:** Do not expose internal paths in public skill descriptions; use generic "vault root" language.

---

## Verification

- Agent can create a Foam-style note with wikilinks when given "create a note about X linking to Y"
- Agent uses vault_search when vault is Obsidian
- Agent uses grep/write_file when workspace is Foam
- Handoff with session_save invoked when Obsidian work done
- MCP_CAPABILITY_MAP and AGENT_NATIVE_CHECKLIST updated

