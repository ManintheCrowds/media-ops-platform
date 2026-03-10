---
name: Bitcoin Chaos Convergence Workflow Checklist
overview: "Concrete workflow for using deepen-plan, agent-native-audit, and critic to prepare and implement Bitcoin-related content. Run in sequence before and during Phase A/B implementation."
todos: []
isProject: false
---

# Bitcoin Chaos Convergence: Workflow Checklist

Use this checklist when preparing Bitcoin values content for portfolio-harness, local-proto, and ACE-first. The sequence ensures plans are grounded, architecture is agent-native, and outputs pass quality gates.

**Scope:** *Bitcoin Chaos Convergence* = the plan mapping Agents of Chaos failures to Bitcoin design patterns and Fedimint/ACE mitigations. *Bitcoin values content* = org-intent templates, observation logs, Chaos–Bitcoin mappings, and ACE–harness documentation.

---

## Prerequisites

- [ ] Plans available: `plans/bitcoin_chaos_convergence_a219e7b9.plan.md`, `plans/bitcoin_chaos_convergence_integration_827d4828.plan.md`
- [ ] Workspace: `D:\portfolio-harness`, `D:\local-proto`, `D:\ACE-first` accessible
- [ ] Commands available: `/deepen-plan`, `/agent-native-audit`, critic subagent (via Task tool)

---

## Phase 0: Plan Deepening (Before Implementation)

### Step 0.1 — Deepen Integration Plan

- [ ] Run `/deepen-plan` with plan path: `plans/bitcoin_chaos_convergence_integration_827d4828.plan.md`
- [ ] Wait for all research agents (skills, learnings, Context7, review agents)
- [ ] Verify plan has `### Research Insights` sections per major block
- [ ] Run **critic** on deepened plan (domain: `docs`)
  - [ ] `pass: true` and score ≥ threshold
  - [ ] If fail: revise per critic fixes, re-run critic

### Step 0.2 — (Optional) Deepen Core Plan

- [ ] Run `/deepen-plan` on `plans/bitcoin_chaos_convergence_a219e7b9.plan.md` if keeping separate
- [ ] Run critic on deepened core plan

### Step 0.3 — Save Deepened Plan

- [ ] Update plan in place or save as `*-deepened.md` per preference
- [ ] Note Enhancement Summary (key improvements, new considerations)

---

## Phase 1: Agent-Native Audit (Architecture Alignment)

### Step 1.1 — Run Full Audit

- [ ] Run `/agent-native-audit` on `D:\portfolio-harness`
- [ ] Run `/agent-native-audit` on `D:\local-proto` (or combined scope)
- [ ] Capture: Overall Agent-Native Score, per-principle scores, Top 10 recommendations

### Step 1.2 — Merge Audit Findings into Plan

- [ ] Add tasks for Action Parity gaps (e.g. MCP tools for observation logs, org-intent)
- [ ] Add tasks for CRUD completeness (observation logs, mappings, templates)
- [ ] Add tasks for Context Injection (org-intent, session_brief in system prompt)
- [ ] Add tasks for Shared Workspace (agent writes to same docs as user)
- [ ] Run **critic** on updated plan (domain: `docs`)

### Step 1.3 — (Optional) Single-Principle Deep Dive

- [ ] If one principle is critical, run audit with argument: `action parity`, `tools`, `context`, `shared`, `crud`, `ui`, `discovery`, or `prompt`

---

## Phase 2: Implementation — Phase A (Observation)

| ID | Task | Output | Critic After? |
|----|------|--------|---------------|
| A1 | Create Bitcoin observation log template | `D:\portfolio-harness\docs\BITCOIN_OBSERVATION_TEMPLATE.md` | ✅ |
| A2 | Document Chaos-to-Bitcoin mapping | `D:\portfolio-harness\docs\CHAOS_BITCOIN_MAPPING.md` | ✅ |
| A3 | Add Bitcoin community template | `org-intent-spec\examples\org-intent.bitcoin-inspired.json` | ✅ |
| A4 | Document Fedimint observation template | `D:\portfolio-harness\docs\FEDIMINT_OBSERVATION_TEMPLATE.md` | ✅ |
| A5 | Add Fedimint to Chaos-Bitcoin mapping | Extend CHAOS_BITCOIN_MAPPING.md | ✅ |

**Per-task critic rule:** Before marking any task complete, produce critic JSON. If `pass=false`, revise and re-run.

---

## Phase 3: Implementation — Phase B (Schema and Integration)

| ID | Task | Output | Critic After? |
|----|------|--------|---------------|
| B1 | Extend identity schema for signed identity | `org-intent-spec\schema\` or doc | ✅ |
| B2 | Add Bitcoin-inspired hard boundaries to org-intent | `org-intent.bitcoin-inspired.json` | ✅ |
| B3 | Document observation sources | `D:\portfolio-harness\docs\BITCOIN_OBSERVATION_SOURCES.md` | ✅ |
| B4 | Create PENTAGI_FEDIMINT_ACE_ROADMAP | `D:\portfolio-harness\docs\PENTAGI_FEDIMINT_ACE_ROADMAP.md` | ✅ |
| B5 | Map ACE layers to harness components | Section in roadmap or `ACE_HARNESS_MAPPING.md` | ✅ |
| B6 | Add Fedimint to observation sources | Extend BITCOIN_OBSERVATION_SOURCES | ✅ |

---

## Phase 4: Post-Implementation Audit

- [ ] Re-run `/agent-native-audit` on portfolio-harness
- [ ] Compare scores to Phase 1 baseline
- [ ] Document improvements in handoff or decision-log

---

## Critic JSON Template (Copy Before Each Gate)

```json
{
  "pass": true,
  "score": 0.0,
  "issues": [],
  "fixes": []
}
```

**Domains:** `docs` (plans, markdown, templates), `workflow_ui` (UI changes), `code` (scripts, MCP, schemas).

---

## Quick Reference: Tool Order

```
1. deepen-plan (integration plan) → Research Insights
2. critic (deepened plan)
3. agent-native-audit (portfolio-harness, local-proto)
4. Merge audit findings into plan
5. critic (merged plan)
6. Implement Phase A → critic per artifact
7. Implement Phase B → critic per artifact
8. agent-native-audit (post-implementation)
```

---

## Cross-References

| Artifact | Purpose |
|----------|---------|
| [bitcoin_chaos_convergence_a219e7b9.plan.md](../../plans/bitcoin_chaos_convergence_a219e7b9.plan.md) | Core plan |
| [bitcoin_chaos_convergence_integration_827d4828.plan.md](../../plans/bitcoin_chaos_convergence_integration_827d4828.plan.md) | Integration plan |
| [critic-loop-gate.mdc](c:\Users\schum\.cursor\rules\critic-loop-gate.mdc) | Critic rule |
| agent-native-architecture skill (compound-engineering plugin) | Agent-native principles |
| [AGENT_ENTRY_INDEX.md](D:\portfolio-harness\.cursor\docs\AGENT_ENTRY_INDEX.md) | Agent entry |
