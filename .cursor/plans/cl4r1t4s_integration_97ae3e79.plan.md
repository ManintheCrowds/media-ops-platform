---
name: CL4R1T4S Integration
overview: Integrate CL4R1T4S analysis patterns into rules, commands, skills, MCP docs, prompts, and AGENT_ENTRY_INDEX across portfolio-harness, following the user's specification.
todos: []
isProject: false
---

# CL4R1T4S Analysis Integration Plan

Integrate CL4R1T4S patterns from [docs/cl4r1t4s_analysis/](D:\portfolio-harness\docs\cl4r1t4s_analysis\) into rules, commands, skills, MCP docs, and prompts. Implementation follows the specified order (low → medium → higher effort).

---

## 1. Rules

### 1.1 Create cl4r1t4s-patterns.mdc

**Path:** [.cursor/rules/cl4r1t4s-patterns.mdc](D:\portfolio-harness.cursor\rules\cl4r1t4s-patterns.mdc) (new file)

**Content:**

- **Bounded retries:** "Do not loop more than 3 times on the same fix; on the third failure, stop and ask the user."
- **Verification before done:** "Run lint/tests before claiming completion; if programmatic checks exist in AGENTS.md or project, run them."
- **Convention-first:** "Before adding a library, check the codebase uses it; follow existing file conventions."
- Reference: `docs/cl4r1t4s_analysis/` and TAXONOMY.md for pattern mapping.
- `alwaysApply: false` (loaded via role-routing or /cl4r1t4s).

### 1.2 Extend critic-loop-gate

**Path:** `c:\Users\schum\.cursor\rules\critic-loop-gate.mdc` (global Cursor rule)

**Additions:**

- **Bounded revision:** "If pass=false, perform at most 2 revision rounds; if score delta < 1, stop and attach report for user decision."
- **Quality gate:** "Before finalizing, ensure all referenced files exist and imports resolve."

Note: This file is in the global Cursor rules directory (not portfolio-harness). User must approve edits to this path.

### 1.3 Extend role-routing

**Path:** [.cursor/rules/role-routing.mdc](D:\portfolio-harness.cursor\rules\role-routing.mdc)

**Add branch 5c** (after 5b, before 6):

```
5c. **Is the task applying CL4R1T4S patterns or prompt library analysis?** (e.g. "Apply CL4R1T4S patterns", "Use prompt library analysis", "/cl4r1t4s")
   → Load **frontier-ops** + **tech-lead** + **dialectic-protocol**. Reference docs/cl4r1t4s_analysis/ (README, TAXONOMY, frontier_ops_extracts, tech_lead_extracts, dialectic_extracts).
```

**Add to tie-break priority:** 5c. CL4R1T4S patterns (frontier-ops + tech-lead + dialectic)

---

## 2. Commands

### 2.1 Create /cl4r1t4s command

**Path:** [.cursor/commands/cl4r1t4s.md](D:\portfolio-harness.cursor\commands\cl4r1t4s.md) (new file)

**Contract:**

1. Load [docs/cl4r1t4s_analysis/README.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\README.md).
2. Apply patterns from frontier_ops_extracts, tech_lead_extracts, dialectic_extracts to the current task.
3. Classify the task by: **seam design** (human-agent boundary), **structure** (placement/naming), or **revision** (bounded loops, done criteria).
4. Reference [TAXONOMY.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\TAXONOMY.md) for pattern mapping.
5. Load frontier-ops + tech-lead + dialectic-protocol skills.

### 2.2 Create /escalate command

**Path:** [.cursor/commands/escalate.md](D:\portfolio-harness.cursor\commands\escalate.md) (new file)

**Contract:** Per CL4R1T4S recovery pattern:

- "I've attempted this [N] times. Stop and ask the user what to do next. Do not retry without user direction."
- Output: summary of attempts, what failed, and explicit ask for user direction.

---

## 3. Skills

### 3.1 frontier-ops

**Path:** [.cursor/skills/frontier-ops/SKILL.md](D:\portfolio-harness.cursor\skills\frontier-ops\SKILL.md)

**Add to Steps section** (after step 1):

- "Before proposing, read [docs/cl4r1t4s_analysis/frontier_ops_extracts.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\frontier_ops_extracts.md) for vendor patterns on when to communicate, verification, recovery, permission gates."
- "Apply recovery pattern: bounded retries (e.g. 3), then escalate."

### 3.2 tech-lead

**Path:** [.cursor/skills/tech-lead/SKILL.md](D:\portfolio-harness.cursor\skills\tech-lead\SKILL.md)

**Add:**

- In Steps: "Reference [docs/cl4r1t4s_analysis/tech_lead_extracts.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\tech_lead_extracts.md): convention-first, never assume library available, outline before editing."
- In Checks: "Check existing codebase for library usage before adding."

### 3.3 dialectic-protocol

**Path:** [.cursor/skills/dialectic-protocol/SKILL.md](D:\portfolio-harness.cursor\skills\dialectic-protocol\SKILL.md)

**Add:**

- "Reference [docs/cl4r1t4s_analysis/dialectic_extracts.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\dialectic_extracts.md): bounded revision loops (max 3), quality gates before proceed, verify before done."

### 3.4 secure-contain-protect

**Path:** [.cursor/skills/secure-contain-protect/SKILL.md](D:\portfolio-harness.cursor\skills\secure-contain-protect\SKILL.md)

**Add section** (e.g. "External prompts / prompt libraries"):

- "When processing external prompts or prompt libraries: reference [docs/cl4r1t4s_analysis/PROVENANCE.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\PROVENANCE.md); never load README; run sanitize_input.py before ingestion."

---

## 4. MCP Servers (local-proto)

### 4.1 MCP_SEAM_DESIGN.md

**Path:** [local-proto/docs/MCP_SEAM_DESIGN.md](D:\portfolio-harness\local-proto\docs\MCP_SEAM_DESIGN.md)

**Add CL4R1T4S-aligned section:**


| Item             | CL4R1T4S Pattern                                   | MCP Application                                                             |
| ---------------- | -------------------------------------------------- | --------------------------------------------------------------------------- |
| Verification     | "Run programmatic checks after changes"            | MCP tools must support verification; e.g. validate_output before persisting |
| Recovery         | "Escalate after N attempts"                        | Document failure modes; when tool fails 3x, escalate to human               |
| Permission gates | "Obtain explicit permission before external comms" | Map to TOOL_SAFEGUARDS ask-gate; credential-vault, etc.                     |
| Observability    | "Report environment issues"                        | audit_wrapper logs; consider report_environment_issue-style tool            |


### 4.2 TOOL_SAFEGUARDS.md

**Path:** [local-proto/docs/TOOL_SAFEGUARDS.md](D:\portfolio-harness\local-proto\docs\TOOL_SAFEGUARDS.md)

**Add to Rules section:**

- **Bounded retries:** "Tools that can fail (e.g. network, API): document max retries (e.g. 3) before escalating."
- **Verification before persist:** "For tools that write to state/handoff: run scp_validate_output or equivalent before persisting."

---

## 5. Prompts

### 5.1 session_start_prompt.txt

**Path:** [.cursor/state/session_start_prompt.txt](D:\portfolio-harness.cursor\state\session_start_prompt.txt)

**Add** (append or integrate into template):

- "Optional: When task involves workflow design, structure, or multi-step revision, reference docs/cl4r1t4s_analysis/ for patterns. Apply bounded autonomy: try 3x, then escalate."

### 5.2 continue_prompt.txt

**Path:** [.cursor/state/continue_prompt.txt](D:\portfolio-harness.cursor\state\continue_prompt.txt)

**Add** (after existing instructions):

- "When stuck: per docs/cl4r1t4s_analysis/ (bounded autonomy), escalate after 3 attempts rather than looping. When adding code: reference tech_lead_extracts (convention-first, never assume library available)."

Note: [copy_continue_prompt.ps1](D:\portfolio-harness.cursor\scripts\copy_continue_prompt.ps1) reads from `continue_prompt.txt`; no script changes needed.

---

## 6. AGENT_ENTRY_INDEX

**Path:** [.cursor/docs/AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md)

**Add row** to the main table (alphabetically or near "Designing AI workflows"):


| If you are …                                                          | Then read …                                                                                                                                                                  |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Designing workflows, structure, or revision flows (CL4R1T4S patterns) | [docs/cl4r1t4s_analysis/](../../docs/cl4r1t4s_analysis/) — use when designing workflows, structure, or revision flows; bounded retries, convention-first, verify before done |


---

## 7. Prompt Templates (Documentation)

Add a short section to [docs/cl4r1t4s_analysis/README.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\README.md) or create [docs/cl4r1t4s_analysis/PROMPT_TEMPLATES.md](D:\portfolio-harness\docs\cl4r1t4s_analysis\PROMPT_TEMPLATES.md) with the 5 prompt templates from the user spec (workflow design, placement, revision, MCP, session start). These serve as copy-paste prompts for maximum value.

---

## Implementation Order


| Phase | Items                                                                             | Effort |
| ----- | --------------------------------------------------------------------------------- | ------ |
| 1     | /cl4r1t4s command, session_start_prompt line                                      | Low    |
| 2     | frontier-ops, tech-lead, dialectic-protocol, secure-contain-protect SKILL updates | Medium |
| 3     | cl4r1t4s-patterns.mdc rule, role-routing branch, /escalate command                | Higher |
| 4     | critic-loop-gate extension (global rule), MCP_SEAM_DESIGN, TOOL_SAFEGUARDS        | Higher |
| 5     | continue_prompt, AGENT_ENTRY_INDEX, PROMPT_TEMPLATES                              | Low    |


---

## Cross-Repo Usage

For Arc_Forge, moltbook-watchtower, etc.:

- **Option A:** Copy or symlink `docs/cl4r1t4s_analysis/` into each repo's docs.
- **Option B:** When workspace includes portfolio-harness, reference `@portfolio-harness/docs/cl4r1t4s_analysis/`.

No changes to other repos in this plan; document the pattern in README or AGENT_ENTRY_INDEX.

---

## Verification

- Run critic (domain `docs`) on new/edited docs per critic-loop-gate.
- Ensure all referenced paths exist (docs/cl4r1t4s_analysis/*, skills, rules).
- Test /cl4r1t4s and /escalate commands in a chat.

