---
name: Bitcoin-Chaos Skill Sequence
overview: "Skill-driven development sequence for Phase C and beyond: product-scope → planning → tech-lead → local-first → frontier-ops → refactor-reuse → TDD."
todos: []
isProject: false
---

# Bitcoin-Chaos Skill Sequence Plan

Execute skills in order to develop Phase C (capability tokens, Fedimint testnet, sync boundary) and related work.

---

## Sequence

| Step | Skill | Input | Output |
|------|-------|-------|--------|
| 1 | **product-scope** | Phase C: capability tokens, testnet, client integration, sync boundary | scope_phase_c_bitcoin_chaos.md (requirements, AC) |
| 2 | **planning** | scope_phase_c_bitcoin_chaos.md | Phase C WBS with dependencies, approval gates |
| 3 | **tech-lead** | Scope + WBS | Structure: where capability schema, AuthModule design, sync boundary docs live |
| 4 | **local-first** | Sync boundary task | Document local-proto ↔ Fedimint client boundary |
| 5 | **frontier-ops** | Bitcoin-Chaos agent flows | Review observation/provenance seams, escalation paths |
| 6 | **refactor-reuse** | Before C5 implementation | Scan for existing token/auth patterns |
| 7 | **TDD** | Capability token schema (C5) | Tests for validation, scope checks before implementation |

---

## Dependencies

- Step 1 must complete before step 2 (planning needs scope).
- Step 2 must complete before step 3 (tech-lead needs WBS).
- Steps 4–5 can run in parallel after step 3.
- Step 6 runs before C5 implementation.
- Step 7 runs before C5 implementation (TDD).

---

## Handoff Between Steps

Per product-scope skill: handoff includes Done, Next (self-contained), Paths, Decisions. Goal-constraint conflict: escalate by default.
