---
name: Scale Mismatch Spectrum
overview: Spectrum and matrix of personal vs swarm alignment; identity_context, org-intent, PRIME, MISSION relationship.
status: pending
priority: 2
phase: extend
todos: []
isProject: false
---

# Scale Mismatch: Spectrum and Matrix

Explore the relationship between personal alignment (alignment-seed) and swarm alignment (GATO MISSION). Ref: [criticism_remediation_plans](D:\software\.cursor\plans\criticism_remediation_plans_f26043cd.plan.md).

---

## Spectrum: Personal ↔ Swarm

| Scale | Exemplar | identity_context | org-intent | MISSION/PRIME |
|-------|----------|------------------|------------|---------------|
| **Personal** | alignment-seed | Primary | Fed by merge | Values only |
| **Household** | Family agents | stakeholders (family) | — | — |
| **Community** | Bitcoin culture, Glitch | communities | community template | — |
| **Organization** | portfolio-harness | — | Primary | Values |
| **Ecosystem** | Moltbook, agent platforms | communities (ecosystem ref) | — | Coordination |
| **Swarm** | 150k agents | — | — | MISSION primary |

---

## Matrix: What Each System Optimizes For

| System | Scope | Primary question | Secondary |
|--------|-------|------------------|-----------|
| identity_context | Who am I? | Personal alignment | Community membership |
| org-intent | What does the org value? | Agent constitution | Escalation |
| PRIME | What should any agent value? | Universal imperatives | Five dimensions |
| MISSION | What is this swarm for? | Ecosystem alignment | Heuristic Imperatives propagation |

---

## Reflection

The "mismatch" is not a bug. Personal identity (alignment-seed) is the **anchor**; org-intent is the **bridge** to agents; PRIME is the **universal layer**; MISSION is **ecosystem-scale**. They form a ladder: personal → org → universal → swarm.

identity_context.communities can add `scale` or `ecosystem_ref` to link "I am part of Bitcoin culture" to "that ecosystem has swarm-scale dynamics."

---

## Schema Addition (identity_context)

Optional `communities[].scale` enum: `personal`, `household`, `community`, `ecosystem`, `swarm`. Enables explicit positioning.

**Location:** [identity_context.v2.json](D:\alignment-seed\schema\identity_context.v2.json) — add to communities items.

---

## Artifacts

- [docs/SCALE_SPECTRUM.md](D:\alignment-seed\docs\SCALE_SPECTRUM.md) or portfolio-harness equivalent — doc for agents/humans
- identity_context schema update (optional)
