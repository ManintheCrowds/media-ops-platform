---
name: CircuitBreaker Critic Architect Brainstorm
overview: Critic evaluation passed; three minor improvements identified. Architect placement and brainstorming yield a prioritized to-do list and implementation steps.
todos: []
isProject: false
---

# CircuitBreaker: Critic, Architect, and Brainstorm Evaluation

## 1. Critic Report Summary

**Result:** Pass (threshold 18; scores: intent_alignment 5, safety 5, correctness 4, completeness 4, minimality 5)

**Verdict:** Artifacts meet the goal. CircuitBreaker is documented as complementary infra (not local-first), with correct placement and framing.

**Issues and fixes:**


| Issue                                                                                           | Type         | Fix                                                      |
| ----------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------------------- |
| Install script URL uses lowercase `circuitbreaker`; may break on case-sensitive systems         | correctness  | Use `CircuitBreaker` in URL                              |
| scope_circuitbreaker_eval.md has no inbound links; install path/constraints only in agent state | completeness | Add link from AGENT_ENTRY_INDEX (user chose this option) |
| docker-mcp SKILL uses `../../../../local-first/RESOURCES.md`; assumes sibling workspace         | structural   | Document assumption in workspace/README                  |


---

## 2. Architect / Tech-Lead Recommendations

**Layer:** Docs and state; no code changes.


| Fix                      | Path                                                                                                                                                                                | Rationale                                                                              |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Normalize install URL    | [.cursor/state/scope_circuitbreaker_eval.md](D:\portfolio-harness.cursor\state\scope_circuitbreaker_eval.md) L37                                                                    | Single source of truth for install; match GitHub casing for robustness                 |
| Add scope doc link       | [.cursor/docs/AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md) L66                                                                                      | Same-repo link; keeps Proxmox row self-contained; agents discover install path         |
| Document cross-repo link | [.cursor/skills/docker-mcp/SKILL.md](D:\portfolio-harness.cursor\skills\docker-mcp\SKILL.md) or [HARNESS_ARCHITECTURE.md](D:\portfolio-harness.cursor\docs\HARNESS_ARCHITECTURE.md) | Call out that `local-first` must be sibling of `portfolio-harness` for link to resolve |


**Conflict check:** None. All changes are additive or corrective.

---

## 3. Prioritized To-Dos


| Priority | ID   | Task                                                                                        | Risk |
| -------- | ---- | ------------------------------------------------------------------------------------------- | ---- |
| P1       | CB-1 | Normalize install URL in scope_circuitbreaker_eval.md (`circuitbreaker` → `CircuitBreaker`) | Low  |
| P2       | CB-2 | Add scope_circuitbreaker_eval.md link to AGENT_ENTRY_INDEX "Proxmox homelab visibility" row | Low  |
| P3       | CB-3 | Document docker-mcp cross-repo link assumption (local-first sibling of portfolio-harness)   | Low  |


**Deferred / optional:** No CircuitBreaker items in [pending_tasks.md](D:\portfolio-harness.cursor\state\pending_tasks.md). These can be added to PENDING_OTHER or executed as quick wins.

---

## 4. Implementation Design

### CB-1: Normalize install URL

**File:** [scope_circuitbreaker_eval.md](D:\portfolio-harness.cursor\state\scope_circuitbreaker_eval.md)

**Change:** L37 — replace:

```bash
curl -fsSL https://raw.githubusercontent.com/BlkLeg/circuitbreaker/main/install.sh | bash
```

with:

```bash
curl -fsSL https://raw.githubusercontent.com/BlkLeg/CircuitBreaker/main/install.sh | bash
```

### CB-2: Add scope doc link to AGENT_ENTRY_INDEX

**File:** [AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md)

**Current row (L66):**

```
| Proxmox homelab visibility, topology, or IPAM | [RESOURCES.md#infra--homelab](../../local-first/RESOURCES.md#infra--homelab) (CircuitBreaker); [docker-mcp SKILL](../skills/docker-mcp/SKILL.md) for container lifecycle |
```

**Proposed row:**

```
| Proxmox homelab visibility, topology, or IPAM | [RESOURCES.md#infra--homelab](../../local-first/RESOURCES.md#infra--homelab) (CircuitBreaker); [scope_circuitbreaker_eval.md](../state/scope_circuitbreaker_eval.md) for install path; [docker-mcp SKILL](../skills/docker-mcp/SKILL.md) for container lifecycle |
```

### CB-3: Document cross-repo link assumption

**Options:**

- **A (recommended):** Add one sentence to [docker-mcp/SKILL.md](D:\portfolio-harness.cursor\skills\docker-mcp\SKILL.md) "Additional resources" section: "Link assumes local-first is a sibling of portfolio-harness."
- **B:** Add to [HARNESS_ARCHITECTURE.md](D:\portfolio-harness.cursor\docs\HARNESS_ARCHITECTURE.md) workspace layout: "local-first and portfolio-harness are siblings for cross-repo doc links."

**Recommendation:** Option A — co-locate with the link; minimal change.

---

## 5. Verification

- Install URL: `curl -I` on normalized URL returns 200
- AGENT_ENTRY_INDEX: scope link resolves from portfolio-harness root
- docker-mcp: Assumption is documented

---

## 6. Critic JSON (Final)

```json
{
  "pass": true,
  "intent_alignment": 5,
  "safety": 5,
  "correctness": 4,
  "completeness": 4,
  "minimality": 5,
  "issues": [
    {"type": "correctness", "detail": "Install script URL casing"},
    {"type": "completeness", "detail": "scope doc not linked"},
    {"type": "structural", "detail": "docker-mcp cross-repo link assumption"}
  ],
  "fixes": ["CB-1", "CB-2", "CB-3"]
}
```

