---
name: Bitcoin Workflow Status
overview: "Verify workflow position for the Bitcoin-Chaos Convergence Integration plan and decompose the remaining steps: critic on merged plan (Step 4), per-artifact critic (Step 6), and optional agent-native re-audit v3 (Step 7) to capture post-Remaining-Gaps improvements."
todos: []
isProject: false
---

# Bitcoin-Chaos Workflow Status and Remaining Tasks

## Current Workflow Position


| Step | Description                                                                  | Status       | Evidence                                                                                                                                                              |
| ---- | ---------------------------------------------------------------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Deepen bitcoin_chaos_convergence_integration plan                            | **DONE**     | Plan has Research Insights, best practices, Agent-Native Audit summary; deepened 2026-03-09                                                                           |
| 2    | Run agent-native-audit on portfolio-harness + local-proto                    | **DONE**     | v1: 21/64; v2: 39/64 ([AGENT_NATIVE_BITCOIN_CHAOS_AUDIT_2026-03-10_v2.md](D:\portfolio-harness.cursor\state\adhoc\AGENT_NATIVE_BITCOIN_CHAOS_AUDIT_2026-03-10_v2.md)) |
| 3    | Merge audit findings into deepened plan                                      | **DONE**     | Plan includes A6, A7, B7, B8, C2 extended                                                                                                                             |
| 4    | Run critic on merged plan                                                    | **NOT DONE** | No critic report found                                                                                                                                                |
| 5    | Implement Phase A (A1–A5) + audit tasks (A6, A7) and Phase B (B1–B6, B7, B8) | **DONE**     | All artifacts exist; Agent-Native Remaining Gaps implemented                                                                                                          |
| 6    | Run critic after each artifact                                               | **NOT DONE** | No per-artifact critic evidence                                                                                                                                       |
| 7    | Re-run agent-native-audit after Phase B                                      | **PARTIAL**  | v2 run (39/64); v3 not run after Remaining Gaps (observation_log_append, org-intent.bitcoin-inspired)                                                                 |


---

## Artifact Completion Matrix

### Phase A (Observation)


| ID  | Task                          | Output                                                                                         | Status                 |
| --- | ----------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------- |
| A1  | Bitcoin observation template  | [BITCOIN_OBSERVATION_TEMPLATE.md](D:\portfolio-harness\docs\BITCOIN_OBSERVATION_TEMPLATE.md)   | Done                   |
| A2  | Chaos-Bitcoin mapping         | [CHAOS_BITCOIN_MAPPING.md](D:\portfolio-harness\docs\CHAOS_BITCOIN_MAPPING.md)                 | Done (Fedimint column) |
| A3  | Bitcoin community template    | org-intent.bitcoin-inspired.json                                                               | Done                   |
| A4  | Fedimint observation template | [FEDIMINT_OBSERVATION_TEMPLATE.md](D:\portfolio-harness\docs\FEDIMINT_OBSERVATION_TEMPLATE.md) | Done                   |
| A5  | Add Fedimint to mapping       | CHAOS_BITCOIN_MAPPING                                                                          | Done                   |
| A6  | observation_log_append MCP    | [observation_mcp.py](D:\portfolio-harness\local-proto\scripts\observation_mcp.py)              | Done                   |
| A7  | BITCOIN_AGENT_CAPABILITIES    | [BITCOIN_AGENT_CAPABILITIES.md](D:\portfolio-harness\docs\BITCOIN_AGENT_CAPABILITIES.md)       | Done                   |


### Phase B (Schema and Integration)


| ID  | Task                         | Output                                                                                                             | Status                  |
| --- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------- |
| B1  | Schema extensions (identity) | org-intent-spec                                                                                                    | Done (bitcoin-inspired) |
| B2  | org-intent Bitcoin-inspired  | [org-intent.bitcoin-inspired.json](D:\portfolio-harness\org-intent-spec\examples\org-intent.bitcoin-inspired.json) | Done                    |
| B3  | Observation sources          | [BITCOIN_OBSERVATION_SOURCES.md](D:\portfolio-harness\docs\BITCOIN_OBSERVATION_SOURCES.md)                         | Done (Fedimint)         |
| B4  | PENTAGI_FEDIMINT_ACE_ROADMAP | [PENTAGI_FEDIMINT_ACE_ROADMAP.md](D:\portfolio-harness\docs\PENTAGI_FEDIMINT_ACE_ROADMAP.md)                       | Done                    |
| B5  | ACE-harness mapping          | Section 2 in PENTAGI_FEDIMINT_ACE_ROADMAP                                                                          | Done                    |
| B6  | Fedimint observation sources | BITCOIN_OBSERVATION_SOURCES                                                                                        | Done                    |
| B7  | org-intent injection         | continue_prompt.txt, .cursorrules                                                                                  | Done                    |
| B8  | ACE/OpenClaw alignment       | [OPENCLAW.md](D:\portfolio-harness\local-proto\docs\OPENCLAW.md) SOUL section                                      | Done                    |


---

## Remaining Tasks (Decomposed)

### Task 4.1: Run critic on merged plan (retrospective)

**Input:** [bitcoin_chaos_convergence_integration_827d4828.plan.md](D:\software\plans\bitcoin_chaos_convergence_integration_827d4828.plan.md)

**Action:** Invoke critic subagent (domain: docs) on the plan. Produce critic JSON per critic-loop-gate. Fix any issues (e.g. broken links, missing cross-refs, inconsistent task IDs).

**Output:** `AGENT_NATIVE_BITCOIN_CHAOS_CRITIC_PLAN_YYYYMMDD.json` or similar; plan edits if needed.

**Est:** 15–30 min

---

### Task 6.1: Run critic on Phase A artifacts (retrospective)

**Artifacts (domain: docs):** A1, A2, A3, A4, A5, A7 (all markdown/docs)

**Artifacts (domain: code):** A6 (observation_mcp.py)

**Action:** For each artifact, run critic subagent. Domain: docs for markdown; code for scripts. Produce critic JSON; fix issues if score below threshold.

**Order:** A1 → A2 → A3 → A4 → A5 → A6 → A7 (or batch docs, then code)

**Output:** Per-artifact critic reports; fixes if needed.

**Est:** 1–2 hr (7 artifacts)

---

### Task 6.2: Run critic on Phase B artifacts (retrospective)

**Artifacts (domain: docs):** B2 (org-intent JSON), B3, B4, B5 (roadmap sections), B6 (sources), B7 (continue_prompt, .cursorrules), B8 (OPENCLAW)

**Action:** Same as 6.1. Domain: docs for markdown; code for .cursorrules/continue_prompt if treated as config.

**Output:** Per-artifact critic reports; fixes if needed.

**Est:** 1–2 hr

---

### Task 7.1: Run agent-native-audit v3 (optional but recommended)

**Rationale:** v2 (39/64) was run before Agent-Native Remaining Gaps. Since then: observation_log_append MCP added, provenance/observation ORG_INTENT_PATH switched to org-intent.bitcoin-inspired.json. v3 would confirm Tools as Primitives and Action Parity improvements.

**Action:** Invoke agent-native-reviewer subagent on portfolio-harness + local-proto. Compare to v2 baseline (39/64). Expect Tools as Primitives 5→6 or 7, Action Parity 5→6 per [agent-native_remaining_gaps plan](D:\software.cursor\plans\agent-native_remaining_gaps_66870c36.plan.md) verification.

**Output:** `AGENT_NATIVE_BITCOIN_CHAOS_AUDIT_2026-03-XX_v3.md`

**Est:** 30–45 min

---

## Implementation Order

1. **4.1** — Critic on merged plan (fix plan if needed)
2. **6.1** — Critic on Phase A artifacts (A1–A7)
3. **6.2** — Critic on Phase B artifacts (B2–B8)
4. **7.1** — Agent-native audit v3 (confirm post-Remaining-Gaps score)

---

## Verification

- Plan critic: pass=true, score ≥ threshold
- Per-artifact critics: all pass or issues documented and fixed
- v3 audit: score ≥ 39/64; Tools as Primitives and Action Parity improved vs v2

