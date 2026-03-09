---
name: Alignment Analysis Seed
overview: Create a sibling repo at D:\alignment-seed as a minimal local app for capturing and analyzing identity, goals, and community alignment. Data stays private (local-only, encrypted at rest, gitignored). Add a to-do entry to local-proto.
status: resolved
priority: 1
phase: orient
resolved_at: "2026-03-08"
todos: []
isProject: false
---

# Alignment Analysis Seed

Create a secondary project at `D:\alignment-seed` for analyzing identity, goals, and community alignment. Data is private by design: local-only storage, encryption at rest, and gitignored. The seed includes a minimal CLI app to capture and persist alignment data.

---

## 1. Project Structure

```
D:\alignment-seed\
├── README.md                 # Purpose, privacy model, usage
├── .gitignore                # data/, *.key, secrets
├── schema/
│   ├── identity.v1.json      # JSON Schema for identity
│   ├── goals.v1.json         # Extends portfolio-harness goals schema
│   └── community.v1.json     # Community norms, boundaries
├── data/                     # Gitignored; holds actual data
│   └── .gitkeep
├── scripts/
│   ├── capture_identity.ps1  # Interactive capture for identity
│   ├── capture_goals.ps1     # Interactive capture for goals
│   ├── capture_community.ps1 # Interactive capture for community
│   └── analyze_alignment.ps1 # Read-only report (no PII in output)
├── templates/
│   ├── identity.example.json
│   ├── goals.example.json
│   └── community.example.json
└── docs/
    ├── PRIVACY.md            # What stays local; encryption; no sync
    ├── AGENTS.md             # Instructions for AI agents
    └── AGENTS_OF_CHAOS_REF.md # Links to mitigation checklist from analysis
```

---

## 2. Schema Design

**Identity** (`schema/identity.v1.json`): Owner attributes, verified identity mechanism, preferences categories. Aligns with [ALIGNMENT_SURFACE.md](D:\portfolio-harness.cursor\docs\ALIGNMENT_SURFACE.md) and [preferences.json](D:\portfolio-harness.cursor\state\preferences.json) categories (workflow, handoff, scope, tools, alignment, vision, etc.). No PII in schema; PII only in `data/` (gitignored).

**Goals** (`schema/goals.v1.json`): Reuse or extend [goals.v1.json](D:\portfolio-harness.cursor\state\schemas\goals.v1.json). Add optional `community_ref` for community-aligned goals.

**Community** (`schema/community.v1.json`): Shared values, hard boundaries, community context. Extends [org-intent.example.json](D:\portfolio-harness\org-intent-spec\examples\org-intent.example.json) `values`, `hard_boundaries`, `pro_social` for personal/community scope.

---

## 3. Minimal CLI App (PowerShell)

- **capture_identity.ps1**: Prompts for identity fields (owner name, verification mechanism, preference categories). Writes to `data/identity.json`. Uses `Read-Host -AsSecureString` for sensitive fields if any.
- **capture_goals.ps1**: Prompts for goals (id, goal, status, priority). Writes to `data/goals.json`. Can import from `portfolio-harness/.cursor/state/goals.json` as optional source.
- **capture_community.ps1**: Prompts for community name, values, hard boundaries. Writes to `data/community.json`.
- **analyze_alignment.ps1**: Reads `data/*.json`, produces a summary report (e.g. "Identity configured: yes; Goals: 3 active; Community: 2 boundaries"). No PII in report output; suitable for handoff context.

All scripts: no network calls, no cloud, no sync. Data path: `$PSScriptRoot/../data/` or configurable via env.

---

## 4. Privacy Model


| Aspect         | Implementation                                                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Storage**    | `data/` directory; gitignored                                                                                                                    |
| **Encryption** | Optional: encrypt `data/*.json` with user key (e.g. DPAPI or password-derived). MVP: document in PRIVACY.md; implement encryption in later phase |
| **No sync**    | No Electric, PowerSync, or cloud. Local-only                                                                                                     |
| **AI access**  | AGENTS.md instructs: do not read `data/` contents; use templates only. Analyze script outputs summary only                                       |
| **Backup**     | User responsibility; document in README                                                                                                          |


---

## 5. Cross-References

- Link to [Agents of Chaos mitigation checklist](D:\portfolio-harness.cursor\docs\ALIGNMENT_SURFACE.md) and the analysis summary in `docs/AGENTS_OF_CHAOS_REF.md`
- Link to [local-first AI_SECURITY.md](D:\local-first\AI_SECURITY.md) for encryption/traceability patterns
- Link to [org-intent-spec](D:\portfolio-harness\org-intent-spec) for values/boundaries schema

---

## 6. To-Do Entry

Add to [local-proto/TODO.md](D:\portfolio-harness\local-proto\TODO.md):

```markdown
N. **Alignment Analysis Seed:** Create D:\alignment-seed — minimal local app for identity, goals, community alignment. Private data (gitignored, local-only). CLI capture scripts; analyze_alignment.ps1 for summary. Ref: Agents of Chaos mitigation; ALIGNMENT_SURFACE.
```

And optionally to [pending_tasks.md](D:\portfolio-harness.cursor\state\pending_tasks.md) under a new section (e.g. PENDING_ALIGNMENT) or append to existing PENDING_ASYNC.

---

## 7. Implementation Order

1. Create `D:\alignment-seed` directory and `.gitignore`
2. Add README.md, docs/PRIVACY.md, docs/AGENTS.md, docs/AGENTS_OF_CHAOS_REF.md
3. Add schema files and templates
4. Add PowerShell capture scripts (stub or minimal working)
5. Add analyze_alignment.ps1 (reads data, outputs summary)
6. Add to-do to local-proto/TODO.md and pending_tasks.md
7. Initialize git repo in alignment-seed (optional; user may do manually)

---

## 8. Out of Scope (Phase 1)

- Encryption at rest (document only; implement later)
- Sync to portfolio-harness (explicitly excluded)
- Web UI (CLI only for seed)
- Integration with Cursor/agents (AGENTS.md provides boundaries; no MCP or tooling)

