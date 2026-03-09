---
name: Plan File Management
overview: Standardize plan frontmatter, create update_plans_index.ps1, and PLANS_INDEX.md for north star/priority labeling.
status: pending
priority: 1
phase: orient
todos: []
isProject: false
---

# Plan File Management

Labeling, automation, and north star/priority order for .cursor/plans. Ref: [criticism_remediation_plans](D:\software\.cursor\plans\criticism_remediation_plans_f26043cd.plan.md).

---

## Frontmatter Schema

```yaml
---
name: Plan Name
overview: One-line summary
status: pending | in_progress | resolved | superseded
priority: 1-5  # 1 = north star / highest
phase: orient | wire | extend | later
resolved_at: "YYYY-MM-DD"  # when status=resolved
superseded_by: "other_plan_id"  # when status=superseded
todos: []
isProject: false
---
```

---

## update_plans_index.ps1

**Location:** `D:\software\.cursor\scripts\update_plans_index.ps1`

**Behavior:**
1. Scans `D:\software\.cursor\plans\*.plan.md`
2. Parses frontmatter (status, priority, phase, name)
3. Writes `D:\software\.cursor\plans\PLANS_INDEX.md` with table: name, status, priority, phase, path

**Output format:** Markdown table. Resolved plans include "resolved" badge.

---

## North Star / Priority Order

| Priority | Phase | Plans |
|----------|-------|-------|
| 1 | orient, wire | alignment_stack_orientation, wire_identity_to_org_intent_decomposition, plan_file_management |
| 2 | extend | prime_enrichment, alignment_seed_local_first_gap |
| 3 | extend | bitcoin_chaos_convergence A1–A3 |
| 4+ | later | nim_*, docker, etc. |

---

## Resolved Labeling

When a plan is done: set `status: resolved` and `resolved_at: "YYYY-MM-DD"`. Script includes resolved plans in index with "resolved" badge.

---

## Artifacts

- [update_plans_index.ps1](D:\software\.cursor\scripts\update_plans_index.ps1)
- [PLANS_INDEX.md](D:\software\.cursor\plans\PLANS_INDEX.md)
