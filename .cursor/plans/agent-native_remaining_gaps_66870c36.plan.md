---
name: Agent-Native Remaining Gaps
overview: "Address the two actionable remaining gaps from the agent-native audit v2: (1) add observation_log_append MCP tool, (2) switch provenance MCP to org-intent.bitcoin-inspired.json for Bitcoin-Chaos flows. Gaps 3 (capability tokens) and 4 (UI) are deferred."
todos: []
isProject: false
---

# Agent-Native Remaining Gaps Plan

Address the two actionable gaps from [AGENT_NATIVE_BITCOIN_CHAOS_AUDIT_2026-03-10_v2.md](D:\portfolio-harness.cursor\state\adhoc\AGENT_NATIVE_BITCOIN_CHAOS_AUDIT_2026-03-10_v2.md). Gaps 3 (capability tokens) and 4 (UI) remain out of scope for this plan.

---

## Gap 1: Add observation_log_append MCP Tool

**Current state:** Agent uses read_file + search_replace workflow documented in [BITCOIN_AGENT_CAPABILITIES.md](D:\portfolio-harness\docs\BITCOIN_AGENT_CAPABILITIES.md). Schema in [docs/bitcoin_observations/README.md](D:\portfolio-harness\docs\bitcoin_observations\README.md).

**Implementation:**

1. Create [local-proto/scripts/observation_mcp.py](D:\portfolio-harness\local-proto\scripts\observation_mcp.py) (or extend [provenance_mcp.py](D:\portfolio-harness\local-proto\scripts\provenance_mcp.py) with a second tool).
  **Recommendation:** New file `observation_mcp.py` to keep provenance and observation concerns separate. Both are Bitcoin-Chaos specific but different domains (document provenance vs. design/failure/community observations).
2. Tool signature:

```python
   @mcp.tool()
   def observation_log_append(
       content: str,
       source: str,
       obs_type: str,  # design_decision | failure_mode | community_norm
       date: str | None = None  # YYYY-MM-DD; default: today
   ) -> str
   

```

- Resolve target file: `docs/bitcoin_observations/{date}_observations.md`
- Append entry: `### {timestamp} | {source} | {obs_type}\n{content}\n`
- Create file with header if missing
- Path must be under `docs/bitcoin_observations/` (validate)

1. Register in [.cursor/mcp.json](D:\portfolio-harness.cursor\mcp.json) and [local-proto/config/mcp_server_tiers.json](D:\portfolio-harness\local-proto\config\mcp_server_tiers.json) (tier 1).
2. Update [BITCOIN_AGENT_CAPABILITIES.md](D:\portfolio-harness\docs\BITCOIN_AGENT_CAPABILITIES.md): replace "read_file + search_replace" workflow with "observation_log_append MCP tool" for the append action.

**Est. 2–4 hr.**

---

## Gap 2: Use org-intent.bitcoin-inspired.json for Bitcoin-Chaos MCPs

**Current state:** Provenance (and other MCPs) use `ORG_INTENT_PATH: org-intent-spec/examples/org-intent.example.json` in [.cursor/mcp.json](D:\portfolio-harness.cursor\mcp.json).

**Options:**


| Option | Change                                                                 | Pros                                            | Cons                              |
| ------ | ---------------------------------------------------------------------- | ----------------------------------------------- | --------------------------------- |
| A      | Set provenance (and observation) to `org-intent.bitcoin-inspired.json` | Bitcoin-Chaos flows get correct hard_boundaries | Other MCPs still use example.json |
| B      | Document override for Bitcoin-Chaos in PENTAGI_FEDIMINT_ACE_ROADMAP    | No mcp.json change                              | User must manually set env        |
| C      | Add `provenance-bitcoin` server with bitcoin-inspired; keep provenance | Clear separation                                | Two provenance-like servers       |


**Recommendation:** Option A for provenance and observation MCPs only. Provenance and observation were added specifically for Bitcoin-Chaos (CHAOS_BITCOIN_MAPPING, agent-native audit). Changing their ORG_INTENT_PATH to `org-intent.bitcoin-inspired.json` aligns them with Bitcoin flows.

**Implementation:**

1. In [.cursor/mcp.json](D:\portfolio-harness.cursor\mcp.json):
  - Set `provenance` env `ORG_INTENT_PATH` to `D:/portfolio-harness/org-intent-spec/examples/org-intent.bitcoin-inspired.json`
  - Set `observation` env (when added) to same
2. Add comment or note in [PENTAGI_FEDIMINT_ACE_ROADMAP.md](D:\portfolio-harness\docs\PENTAGI_FEDIMINT_ACE_ROADMAP.md) Section 5: "provenance and observation MCPs use org-intent.bitcoin-inspired.json by default."

**Est. 15 min.**

---

## Gaps 3 and 4 (Deferred)


| Gap               | Status     | Rationale                                                                                     |
| ----------------- | ---------- | --------------------------------------------------------------------------------------------- |
| Capability tokens | Phase C    | Per FEDIMINT_AUTHMODULE_CAPABILITY_RESEARCH; design target only. Implement in Phase C.        |
| UI Integration    | Doc-driven | Audit: "acceptable for current phase." No UI for observation/provenance; add later if needed. |


---

## Implementation Order

1. Create observation_mcp.py with observation_log_append
2. Register observation MCP in mcp.json (with org-intent.bitcoin-inspired.json)
3. Register observation in mcp_server_tiers.json
4. Update provenance ORG_INTENT_PATH to org-intent.bitcoin-inspired.json
5. Update BITCOIN_AGENT_CAPABILITIES.md
6. Update PENTAGI_FEDIMINT_ACE_ROADMAP.md note

---

## Verification

- Re-run agent-native-reviewer; expect Tools as Primitives 5→6 or 7, Action Parity 5→6.
- Manual: Agent given "append a Bitcoin observation" — should use observation_log_append tool.

