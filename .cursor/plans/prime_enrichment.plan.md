---
name: PRIME Enrichment
overview: Enrich identity_context and org-intent with PRIME's five dimensions (deontology, teleology, operational, alignment, coordination).
status: pending
priority: 2
phase: extend
todos: []
isProject: false
---

# PRIME Enrichment Plan

Enrich both identity_context and org-intent with PRIME's five dimensions. Ref: [GATO PRIME.md](https://github.com/daveshap/GATO_Framework); [criticism_remediation_plans](D:\software\.cursor\plans\criticism_remediation_plans_f26043cd.plan.md).

---

## PRIME's Five Dimensions

| Dimension | Question | Function |
|-----------|----------|----------|
| Deontology | What should I do now? | Immediate moral guidance |
| Teleology | What are we building toward? | Ultimate orientation |
| Operational | What rules should I follow? | Practical heuristics |
| Alignment | How do values propagate? | Temporal stability |
| Coordination | How do we work together? | Multi-agent cooperation |

---

## identity_context Enrichment

| Dimension | Schema addition | Purpose |
|-----------|------------------|---------|
| Deontology | `philosophical_stance.deontological_notes` | "Immediate duty" framing; what I must do now |
| Teleology | `philosophical_stance.teleological_notes` | "What end state"; cosmic picture; maximal scope |
| Operational | Already in values + value_hierarchy | Heuristics; conflict rules |
| Alignment | `temporal.evolving_toward` + `evolving_notes` | Value propagation; corrigibility |
| Coordination | `contexts` + `stakeholders` | Multi-context cooperation; who to coordinate with |

**Artifacts:**
- [identity_context.v2.json](D:\alignment-seed\schema\identity_context.v2.json): add `deontological_notes`, `teleological_notes` to philosophical_stance
- [templates/identity_context.example.json](D:\alignment-seed\templates\identity_context.example.json): add example values
- [capture_identity_context.ps1](D:\alignment-seed\scripts\capture_identity_context.ps1): add prompts for v2 capture

---

## org-intent Enrichment

| Dimension | Schema addition | Purpose |
|-----------|------------------|---------|
| Deontology | `prime.deontological` (optional string) | "Immediate duty" for agents |
| Teleology | `prime.teleological` (optional string) | "Ultimate end state" for agents |
| Operational | Already in pro_social, delegation_rules | Adequate |
| Alignment | `prime.alignment` (optional string) | "Replicate more aligned" |
| Coordination | Already in pro_social | Adequate |

**Artifacts:**
- [org-intent.v1.json](D:\portfolio-harness\org-intent-spec\schema\org-intent.v1.json): add optional `prime` object
- [org-intent.example.json](D:\portfolio-harness\org-intent-spec\examples\org-intent.example.json): add example prime block

---

## PRIME_REFERENCE.md

One-pager linking to PRIME.md; agents load for context. Location: `D:\alignment-seed\docs\PRIME_REFERENCE.md` or `D:\portfolio-harness\.cursor\docs\PRIME_REFERENCE.md`.

---

## Implementation Order

1. identity_context schema + template + capture script
2. org-intent schema + example
3. PRIME_REFERENCE.md
