---
name: Brain Map Gap Closure
overview: "Implement the gap closure workflow: create scope doc with priorities, add decision-log entry, produce WBS for Phase A/B, add G18 traceability gap to the gap analysis, and implement Phase A fixes (G1–G3, G6–G8)."
todos: []
isProject: false
---

# Brain Map Gap Closure Plan

## Scope

- **Must close:** G1–G3 (tool/credential), G6–G8 (process)
- **Explicitly accept:** G9, G10 (document as known limitations)
- **Defer:** G12–G17 (docs/repo)

---

## Phase 0: Scope and Decision

1. Create `D:\openharness\.cursor\state\scope_brain_map_gap_closure.md` with priorities, explicit acceptance list, and defer list
2. Append to `D:\openharness\.cursor\state\decision-log.md`: prioritization decision (Area, Decision, Rationale)

---

## Phase A: Tool/Credential (G1–G3)


| Gap | Closure                          | Task                                                                                                   |
| --- | -------------------------------- | ------------------------------------------------------------------------------------------------------ |
| G1  | Document tunnel or accept manual | Add tunnel setup note to BRAIN_MAP_E2E.md Step 8; or add "Accept: manual/staging only" to gap analysis |
| G2  | Fix credentials or accept manual | Document in scope: "Accept manual WCAG until credentials fixed"                                        |
| G3  | Update plan or add port check    | Add port fallback to plan (or note plan as reference-only); E2E already has fallback                   |


**Verification:** Scope doc exists; decision-log updated; G1–G3 closure documented.

---

## Phase B: Process (G6–G8)


| Gap | Closure                   | Task                                                                                      |
| --- | ------------------------- | ----------------------------------------------------------------------------------------- |
| G6  | Add stop steps            | Append to BRAIN_MAP_E2E.md: Step 9a (Stop HTTP server), Step 9b (Stop Med-Vis dev server) |
| G7  | Define screenshot path    | Add screenshot path/name convention to BRAIN_MAP_AUDIT.md Verification Checklist          |
| G8  | Document critic threshold | Add score threshold (e.g. ≥0.8) to BRAIN_MAP_AUDIT.md or gap analysis                     |


**Verification:** E2E has stop steps; Audit has screenshot convention; critic threshold documented.

---

## Phase C: Traceability (G18)

1. Add G18 to BRAIN_MAP_PROCESS_GAP_ANALYSIS.md §2.4 and §3
2. Implement Option A: Add "Post-audit checklist" to BRAIN_MAP_E2E.md (□ Update BRAIN_MAP_AUDIT.md Audit Findings row)

**Verification:** G18 in gap analysis; post-audit checklist in E2E.

---

## Artifacts


| Artifact     | Path                                           |
| ------------ | ---------------------------------------------- |
| Scope        | `.cursor/state/scope_brain_map_gap_closure.md` |
| Decision     | `.cursor/state/decision-log.md`                |
| Gap analysis | `docs/BRAIN_MAP_PROCESS_GAP_ANALYSIS.md`       |
| E2E playbook | `docs/BRAIN_MAP_E2E.md`                        |
| Audit        | `docs/BRAIN_MAP_AUDIT.md`                      |


---

## Human Gate

Before Phase B: confirm Phase A approach (document vs. fix). G1–G2 may be "accept" rather than "fix" depending on credential/tunnel availability.