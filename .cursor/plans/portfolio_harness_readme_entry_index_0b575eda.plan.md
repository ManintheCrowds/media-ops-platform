---
name: Portfolio Harness README Entry Index
overview: "Make the harness itself a clear portfolio piece by adding Portfolio Highlights and Skills in action sections to README.md, refreshing AGENT_ENTRY_INDEX with links to these highlights, and establishing the portfolio angle: \"Multi-project AI harness: skills, role-routing, handoff, critic gates.\""
todos: []
isProject: false
---

# Portfolio Harness README and Entry Index Refresh

## Current State

- [README.md](D:\portfolio-harness\README.md): Lists portfolio projects (Obsidian, WatchTower, Berserk B.I.T.S., software, Arc Forge, moltbook-watchtower) and Cursor plans. No harness-specific highlights.
- [AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md): Routing table for agents; has one Bitcoin-Chaos row (line 45). No dedicated "Portfolio Highlights" section or Skills-in-action mapping.

## Target Structure

### 1. README.md — Add Portfolio Angle and Highlights

**Opening (after title):** Add one-line tagline:

> Multi-project AI harness: skills, role-routing, handoff, critic gates.

**New section: Portfolio Highlights** (insert after tagline, before "Portfolio projects"):


| Highlight                     | What it is                                                                                                                                          | Links                                                                                                                                      |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Bitcoin-Chaos alignment**   | Chaos failure modes mapped to Bitcoin design patterns; agent capabilities for observation logs, provenance, org-intent hard_boundaries (hb-1..hb-5) | [BITCOIN_AGENT_CAPABILITIES.md](docs/BITCOIN_AGENT_CAPABILITIES.md), [CHAOS_BITCOIN_MAPPING.md](docs/CHAOS_BITCOIN_MAPPING.md)             |
| **PentAGI protection**        | Human-gated autonomy, pre-tool deanonymization checks, HITL gates, audit alerts; defensive org-intent and exposure-check flows                      | [pentagi/README.md](pentagi/README.md), [INTEGRATED_HITL_ASYNC_ROADMAP](.cursor/plans/INTEGRATED_HITL_ASYNC_ROADMAP.md)                    |
| **org-intent spec**           | Machine-readable org alignment: values, mission, roles, escalation; ACE integration; Bitcoin-inspired example with hard_boundaries                  | [org-intent-spec/README.md](org-intent-spec/README.md)                                                                                     |
| **Agent-native architecture** | Agent parity: any user action can be agent action; MCP tools (observation, provenance), role-routing, critic gates                                  | [HARNESS_ARCHITECTURE.md](.cursor/docs/HARNESS_ARCHITECTURE.md), [USER_GUIDE_AGENT_FEATURES.md](.cursor/docs/USER_GUIDE_AGENT_FEATURES.md) |


**New section: Skills in action** (after Portfolio Highlights, before Portfolio projects):


| Skill                | Projects / use                                                   |
| -------------------- | ---------------------------------------------------------------- |
| planning             | WBS, decompose, plan-first; Arc Forge arcs, Bitcoin-Chaos phases |
| product-scope        | Requirements, AC; Arc Forge, scope elicitation                   |
| tech-lead            | Architecture, placement; harness structure, local-proto          |
| docs                 | README, API docs, runbooks; all portfolio projects               |
| refactor-reuse       | Redundancy scan, reuse vs. new; WatchTower, software             |
| qa-verifier          | Tests, verification; WatchTower, berserk_custom_bit              |
| frontier-ops         | AI workflows, seams; PentAGI gates, handoff chains               |
| security-audit-rules | Rules/skills audit; critic-loop-gate, role-routing               |
| browser-web          | Web automation; Obsidian MCP, DeFlock                            |
| docker-mcp           | Containers, compose; PentAGI, WatchTower                         |


### 2. AGENT_ENTRY_INDEX.md — Refresh with Highlight Links

**Add new row** (after "Understanding harness and golden principles" or in a logical spot):


| If you are …                                                                      | Then read …                                       |
| --------------------------------------------------------------------------------- | ------------------------------------------------- |
| Exploring portfolio highlights (Bitcoin-Chaos, PentAGI, org-intent, agent-native) | [README.md](../../README.md#portfolio-highlights) |


**Add "Portfolio Highlights" subsection** under Quick routing or as a short block:

- **Bitcoin-Chaos:** [BITCOIN_AGENT_CAPABILITIES.md](../../docs/BITCOIN_AGENT_CAPABILITIES.md)
- **PentAGI protection:** [pentagi/README.md](../../pentagi/README.md), [INTEGRATED_HITL_ASYNC_ROADMAP](../plans/INTEGRATED_HITL_ASYNC_ROADMAP.md)
- **org-intent spec:** [org-intent-spec/README.md](../../org-intent-spec/README.md)
- **Agent-native:** [HARNESS_ARCHITECTURE.md](HARNESS_ARCHITECTURE.md), [USER_GUIDE_AGENT_FEATURES.md](USER_GUIDE_AGENT_FEATURES.md)

**Update existing Bitcoin-Chaos row** (line 45) to cross-link:

- Current: `[BITCOIN_AGENT_CAPABILITIES.md](../../docs/BITCOIN_AGENT_CAPABILITIES.md)`
- Add note: "See also [README#portfolio-highlights](../../README.md#portfolio-highlights) for harness highlights."

### 3. File Edit Summary


| File                                                                          | Changes                                                                                                             |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [README.md](D:\portfolio-harness\README.md)                                   | Add tagline; add Portfolio Highlights table; add Skills in action table                                             |
| [AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md) | Add "Exploring portfolio highlights" row; add Portfolio Highlights subsection; optionally enhance Bitcoin-Chaos row |


### 4. Risk and Reversibility

- **Risk:** Low (docs only, no code or config)
- **Rollback:** Revert README and AGENT_ENTRY_INDEX edits via git

