---
name: Foam PKM Skill Testing
overview: Define a test approach for the foam-pkm skill using natural-language prompts (per AGENT_NATIVE_CHECKLIST), a test matrix doc, optional AI_TASK_EVALS registry entry, and checksum_integrity verification. Placement follows existing patterns (daggr_test_matrix, MORAL_BOUNDARY_TESTS).
todos: []
isProject: false
---

# Foam PKM Skill Testing Plan

## Tech-lead: Placement

**Test prompts doc:** [.cursor/skills/foam-pkm/TEST_PROMPTS.md](D:\portfolio-harness.cursor\skills\foam-pkm\TEST_PROMPTS.md)

**Rationale:** Co-locate with the skill (like reference.md). Keeps foam-pkm self-contained. Alternative: `.cursor/docs/FOAM_PKM_TEST_PROMPTS.md` if you prefer docs-centralized (like MORAL_BOUNDARY_TESTS). Skill folder is simpler for a single-skill test set.

**AI_TASK_EVALS registry:** Add foam-pkm row to [.cursor/docs/AI_TASK_EVALS.md](D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md) Registry table.

**Checksum:** Run `python .cursor/scripts/checksum_integrity.py --verify --strict` before committing (per COMMANDS_README).

---

## Test Approach

Per [AGENT_NATIVE_CHECKLIST.md](D:\portfolio-harness.cursor\docs\AGENT_NATIVE_CHECKLIST.md): "Tested with natural language request." No pytest; manual paste-and-verify.

### Test categories


| Category            | Purpose                                                |
| ------------------- | ------------------------------------------------------ |
| **Skill discovery** | Prompts that should trigger foam-pkm (role-routing 4f) |
| **Tool selection**  | Agent picks obsidian-vault vs filesystem correctly     |
| **Conventions**     | Output uses `[[wikilinks]]`, `#tags` correctly         |
| **Parity**          | Agent achieves create, search, link per capability map |


---

## Test Prompts (5 cases)


| #   | Prompt                                                                                                                                          | Expected                                                                                      | Vault             |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------- |
| 1   | "Create a note in the Obsidian vault about Bitcoin-Chaos mapping, linking to CHAOS_BITCOIN_MAPPING"                                             | Uses obsidian-vault `apply_patch`; note has `[[CHAOS_BITCOIN_MAPPING]]`                       | Obsidian          |
| 2   | "Search the vault for notes mentioning 'handoff'"                                                                                               | Uses `vault_search`                                                                           | Obsidian          |
| 3   | "Create a Foam-style note in portfolio-harness/docs about agent-native testing with wikilinks to AGENT_NATIVE_CHECKLIST and MCP_CAPABILITY_MAP" | Uses filesystem `write_file`; note has `[[AGENT_NATIVE_CHECKLIST]]`, `[[MCP_CAPABILITY_MAP]]` | Foam (filesystem) |
| 4   | "Add a daily note for today in the Obsidian vault with a one-line session summary"                                                              | Uses `apply_patch` or `session_save`; path `daily/YYYY-MM-DD.md` or similar                   | Obsidian          |
| 5   | "What can the agent do with Foam and Obsidian vaults?"                                                                                          | References foam-pkm skill, capability map; no tool calls                                      | Discovery         |


**Note:** Test 3 assumes portfolio-harness/docs is in filesystem MCP allowed paths (D:/portfolio-harness). If ObsidianVault is the only vault in scope, test 3 may need a Foam workspace path or skip.

---

## Implementation Steps

### Step 1: Create TEST_PROMPTS.md

Path: `.cursor/skills/foam-pkm/TEST_PROMPTS.md`

Content:

- Table of 5 prompts with Expected and Vault columns
- Procedure: paste prompt in new chat, verify behavior, record pass/fail
- When to run: after skill/rules changes; after model updates (optional)

### Step 2: Add AI_TASK_EVALS registry entry

In [AI_TASK_EVALS.md](D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md) Registry table:


| Task               | Test cases / verification                                                                                                               | When to run                                                   | Model floor |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ----------- |
| **foam-pkm skill** | [TEST_PROMPTS.md](../skills/foam-pkm/TEST_PROMPTS.md): 5 natural-language prompts; pass = correct tool selection + wikilink conventions | After skill/role-routing changes; optional after model update | 3B–7B       |


### Step 3: Run checksum_integrity

Before commit: `python .cursor/scripts/checksum_integrity.py --verify --strict`

### Step 4 (optional): Copy-prompts script

If you want one-click copy like moral boundary: create `.cursor/scripts/copy_foam_pkm_test_prompts.ps1` that outputs the 5 prompts (or first N) for paste. Low priority; manual copy from TEST_PROMPTS.md is sufficient.

---

## Verification Checklist

- TEST_PROMPTS.md exists and lists 5 prompts
- AI_TASK_EVALS registry has foam-pkm row
- checksum_integrity passes
- Manual run: paste prompt 1, verify obsidian-vault used and wikilink present
- Manual run: paste prompt 3 (if Foam workspace available), verify filesystem used

---

## Edge Cases

- **No ObsidianVault access:** Tests 1, 2, 4 require obsidian-vault MCP and D:/Arc_Forge/ObsidianVault. If unavailable, document "skip Obsidian tests" in TEST_PROMPTS.md.
- **No Foam workspace:** Test 3 uses portfolio-harness/docs. If workspace is only ObsidianVault, agent may use obsidian-vault for that path too (if it's under Arc_Forge). Clarify in TEST_PROMPTS.md: "Test 3: use a path outside ObsidianVault (e.g. D:/portfolio-harness/docs) to force filesystem."

