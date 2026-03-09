---
name: Wire Identity to Org-Intent Decomposition
overview: Task decomposition for merging identity_context and community into org-intent. Prerequisites before implementation.
status: pending
priority: 1
phase: wire
todos: []
isProject: false
---

# Wire Identity to Org-Intent: Task Decomposition

Prerequisites and implementation order for `merge_identity_to_org_intent.ps1`. Ref: [criticism_remediation_plans](D:\software\.cursor\plans\criticism_remediation_plans_f26043cd.plan.md).

---

## Prerequisites (Before Implementation)

| Step | Task | Output | Dependency |
|------|------|--------|-------------|
| W1 | Define merge semantics | Doc: which fields from identity_context + community map to which org-intent fields; conflict resolution rules | None |
| W2 | Define output schema | Ensure org_intent_resolved.json validates against org-intent.v1.json | W1 |
| W3 | Define input validation | What if identity_context or community missing? Fallback to org-intent.example.json? | W1 |
| W4 | Define stakeholder_protection format | Optional org-intent extension or separate artifact for "who to protect" | W1 |
| W5 | Create merge script | merge_identity_to_org_intent.ps1 | W2, W3 |
| W6 | Create orientation doc | ALIGNMENT_STACK.md | None (can parallel W1) |
| W7 | Document ORG_INTENT_PATH usage | How ACE/local-proto points to resolved file | W5 |

**Implementation order:** W1, W6 (parallel) → W2, W3, W4 → W5 → W7.

---

## W1: Merge Semantics (Placeholder)

**identity_context → org-intent:**
- `values` → merge into org-intent `values` (dedupe)
- `value_hierarchy.conflicts` → inform hard_boundaries or delegation_rules
- `stakeholders` → optional stakeholder_protection

**community → org-intent:**
- `values` → merge into org-intent `values`
- `hard_boundaries` → merge into org-intent `hard_boundaries`
- `pro_social` → merge or override org-intent `pro_social`

**Conflict resolution:** identity_context overrides community when both present. Base org-intent.example.json provides defaults.

---

## W2–W4: Output Schema, Input Validation, Stakeholder Format

To be defined in W1 completion. Output must validate against [org-intent.v1.json](D:\portfolio-harness\org-intent-spec\schema\org-intent.v1.json).

---

## Output Location

- Script: `D:\alignment-seed\scripts\merge_identity_to_org_intent.ps1`
- Output: `D:\alignment-seed\data\org_intent_resolved.json` (or configurable via env)
