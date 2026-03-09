---
name: Criticism Remediation Plans
overview: "Address alignment stack criticisms: task decomposition for wire implementation, TODO integration, PRIME enrichment, local-first gap analysis, plan file management, and scale-mismatch spectrum exploration."
status: in_progress
priority: 1
phase: orient
todos: []
isProject: false
---

# Criticism Remediation: Task Decompositions and Plans

Address the six criticisms from [alignment_stack_orientation_cef9c3be.plan.md](D:\software.cursor\plans\alignment_stack_orientation_cef9c3be.plan.md) with concrete task decompositions, plan files, and automation proposals.

---

## 1. Wire Implementation: Task Decomposition (Before Implementation)

**Plan file:** [D:\softwarecursor\plans\wire_identity_to_org_intent_decomposition.plan.md](D:\software.cursor\plans\wire_identity_to_org_intent_decomposition.plan.md) (to create)

**Prerequisites before any implementation:**


| Step | Task                                 | Output                                                                                                        | Dependency             |
| ---- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ---------------------- |
| W1   | Define merge semantics               | Doc: which fields from identity_context + community map to which org-intent fields; conflict resolution rules | None                   |
| W2   | Define output schema                 | Ensure org_intent_resolved.json validates against org-intent.v1.json                                          | W1                     |
| W3   | Define input validation              | What if identity_context or community missing? Fallback to org-intent.example.json?                           | W1                     |
| W4   | Define stakeholder_protection format | Optional org-intent extension or separate artifact for "who to protect"                                       | W1                     |
| W5   | Create merge script                  | merge_identity_to_org_intent.ps1                                                                              | W2, W3                 |
| W6   | Create orientation doc               | ALIGNMENT_STACK.md                                                                                            | None (can parallel W1) |
| W7   | Document ORG_INTENT_PATH usage       | How ACE/local-proto points to resolved file                                                                   | W5                     |


**Implementation order:** W1, W6 (parallel) → W2, W3, W4 → W5 → W7.

---

## 2. TODO List Integration

**Update:** [D:\portfolio-harness\local-proto\TODO.md](D:\portfolio-harness\local-proto\TODO.md)

**Changes:**

- Mark 18 (Alignment Analysis Seed) done
- Mark 20 (Identity/Cultural Context) done
- Add new item: **22. Wire alignment-seed to org-intent:** Task decomposition in [wire_identity_to_org_intent_decomposition.plan.md](D:\software.cursor\plans\wire_identity_to_org_intent_decomposition.plan.md). Prereqs: W1–W4. Implement: merge_identity_to_org_intent.ps1; ORG_INTENT_PATH to resolved file. Ref: ALIGNMENT_STACK.

---

## 3. PRIME Enrichment (Both org-intent and identity_context)

**Plan file:** [D:\softwarecursor\plans\prime_enrichment.plan.md](D:\software.cursor\plans\prime_enrichment.plan.md) (to create)

**PRIME's five dimensions:** Deontology, Teleology, Operational, Alignment, Coordination.

**identity_context enrichment:**


| Dimension    | Schema addition                               | Purpose                                           |
| ------------ | --------------------------------------------- | ------------------------------------------------- |
| Deontology   | `philosophical_stance.deontological_notes`    | "Immediate duty" framing; what I must do now      |
| Teleology    | `philosophical_stance.teleological_notes`     | "What end state"; cosmic picture; maximal scope   |
| Operational  | Already in values + value_hierarchy           | Heuristics; conflict rules                        |
| Alignment    | `temporal.evolving_toward` + `evolving_notes` | Value propagation; corrigibility                  |
| Coordination | `contexts` + `stakeholders`                   | Multi-context cooperation; who to coordinate with |


**org-intent enrichment:**


| Dimension    | Schema addition                         | Purpose                         |
| ------------ | --------------------------------------- | ------------------------------- |
| Deontology   | `prime.deontological` (optional string) | "Immediate duty" for agents     |
| Teleology    | `prime.teleological` (optional string)  | "Ultimate end state" for agents |
| Operational  | Already in pro_social, delegation_rules | Adequate                        |
| Alignment    | `prime.alignment` (optional string)     | "Replicate more aligned"        |
| Coordination | Already in pro_social                   | Adequate                        |


**Artifacts:**

- identity_context.v2.json: add `deontological_notes`, `teleological_notes` to philosophical_stance
- org-intent.v1.json: add optional `prime` object with `deontological`, `teleological`, `alignment`
- PRIME_REFERENCE.md: One-pager linking to PRIME.md; agents load for context

---

## 4. Local-First Gap: Analysis and Task Decomposition

**Plan file:** [D:\softwarecursor\plans\alignment_seed_local_first_gap.plan.md](D:\software.cursor\plans\alignment_seed_local_first_gap.plan.md) (to create)

**Gap analysis (alignment-seed vs [local-first AI_SECURITY](D:\local-first\AI_SECURITY.md)):**


| Requirement         | alignment-seed status             | Gap       | Task                                                                                           |
| ------------------- | --------------------------------- | --------- | ---------------------------------------------------------------------------------------------- |
| Encryption at rest  | data/ not encrypted               | High      | L1: Document in PRIVACY.md; L2: Implement DPAPI or password-derived encryption for data/*.json |
| No cloud / no sync  | Compliant                         | None      | —                                                                                              |
| Traceability        | analyze_alignment outputs summary | Partial   | L3: Add optional audit log for capture script invocations (timestamp, script name, no PII)     |
| HITL                | Capture scripts are human-run     | Compliant | —                                                                                              |
| Micro-segmentation  | data/ isolated                    | Compliant | —                                                                                              |
| Tool registry / JIT | N/A (no AI tools)                 | —         | —                                                                                              |


**Task decomposition:**

- L1: PRIVACY.md update (document encryption plan; cross-ref AI_SECURITY)
- L2: Encryption implementation (later phase; depends on key management decision)
- L3: Capture audit log (optional; low priority)

---

## 5. Plan File Management: Labeling and Automation

**Plan file:** [D:\softwarecursor\plans\plan_file_management.plan.md](D:\software.cursor\plans\plan_file_management.plan.md) (to create)

**Frontmatter schema (standardize):**

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

**Automation options:**


| Approach                     | Mechanism                                                                                            | Pros                                             | Cons                       |
| ---------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------ | -------------------------- |
| **A. Frontmatter + script**  | PowerShell script scans .cursor/plans/*.plan.md; outputs PLANS_INDEX.md with status, priority, phase | Single source of truth; script regenerates index | Manual frontmatter updates |
| **B. PLANS_INDEX.md manual** | Human maintains index; links to plans; status column                                                 | Simple                                           | Drift risk                 |
| **C. GitHub-style labels**   | Use status/priority in frontmatter; script or Cursor rule enforces on plan creation                  | Consistent                                       | Requires discipline        |


**Recommended:** A. Create `scripts/update_plans_index.ps1` that:

1. Scans D:\softwarecursor\plans.plan.md
2. Parses frontmatter (status, priority, phase, name)
3. Writes D:\softwarecursor\plans\PLANS_INDEX.md with table: name, status, priority, phase, path

**North star / priority order:**

- priority 1: orientation, wire (align with alignment stack)
- priority 2: PRIME enrichment, local-first gap
- priority 3: bitcoin_chaos A1–A3
- priority 4+: other plans

**Resolved labeling:** When a plan is done, set `status: resolved` and `resolved_at: "YYYY-MM-DD"`. Script includes resolved plans in index with "resolved" badge; optional filter to hide them.

---

## 6. Scale Mismatch: Spectrum and Matrix

**Plan file:** [D:\softwarecursor\plans\scale_mismatch_spectrum.plan.md](D:\software.cursor\plans\scale_mismatch_spectrum.plan.md) (to create)

**Spectrum: Personal ↔ Swarm**


| Scale            | Exemplar                  | identity_context            | org-intent         | MISSION/PRIME   |
| ---------------- | ------------------------- | --------------------------- | ------------------ | --------------- |
| **Personal**     | alignment-seed            | Primary                     | Fed by merge       | Values only     |
| **Household**    | Family agents             | stakeholders (family)       | —                  | —               |
| **Community**    | Bitcoin culture, Glitch   | communities                 | community template | —               |
| **Organization** | portfolio-harness         | —                           | Primary            | Values          |
| **Ecosystem**    | Moltbook, agent platforms | communities (ecosystem ref) | —                  | Coordination    |
| **Swarm**        | 150k agents               | —                           | —                  | MISSION primary |


**Matrix: What each system optimizes for**


| System           | Scope                        | Primary question      | Secondary                         |
| ---------------- | ---------------------------- | --------------------- | --------------------------------- |
| identity_context | Who am I?                    | Personal alignment    | Community membership              |
| org-intent       | What does the org value?     | Agent constitution    | Escalation                        |
| PRIME            | What should any agent value? | Universal imperatives | Five dimensions                   |
| MISSION          | What is this swarm for?      | Ecosystem alignment   | Heuristic Imperatives propagation |


**Reflection:** The "mismatch" is not a bug. Personal identity (alignment-seed) is the **anchor**; org-intent is the **bridge** to agents; PRIME is the **universal layer**; MISSION is **ecosystem-scale**. They form a ladder: personal → org → universal → swarm. identity_context.communities can add `scale` or `ecosystem_ref` to link "I am part of Bitcoin culture" to "that ecosystem has swarm-scale dynamics."

**Schema addition (identity_context):** Optional `communities[].scale` enum: `personal`, `household`, `community`, `ecosystem`, `swarm`. Enables explicit positioning.

---

## 7. Artifacts Summary


| #   | Artifact                     | Location                                                        |
| --- | ---------------------------- | --------------------------------------------------------------- |
| 1   | Wire task decomposition plan | .cursor/plans/wire_identity_to_org_intent_decomposition.plan.md |
| 2   | PRIME enrichment plan        | .cursor/plans/prime_enrichment.plan.md                          |
| 3   | Local-first gap plan         | .cursor/plans/alignment_seed_local_first_gap.plan.md            |
| 4   | Plan file management plan    | .cursor/plans/plan_file_management.plan.md                      |
| 5   | Scale mismatch spectrum plan | .cursor/plans/scale_mismatch_spectrum.plan.md                   |
| 6   | TODO update                  | local-proto/TODO.md                                             |
| 7   | update_plans_index.ps1       | portfolio-harness or software .cursor/scripts/                  |
| 8   | PLANS_INDEX.md               | .cursor/plans/PLANS_INDEX.md                                    |


---

## 8. Implementation Order

1. Create the five plan files (wire, PRIME, local-first gap, plan management, scale spectrum)
2. Create update_plans_index.ps1 and initial PLANS_INDEX.md
3. Update local-proto TODO with item 22
4. Add status/priority/phase to existing plan frontmatter (batch update)
5. Execute wire decomposition (W1–W7) when ready
6. Execute PRIME enrichment when wire is stable
7. Execute local-first gap L1 (doc only) early; L2/L3 later

