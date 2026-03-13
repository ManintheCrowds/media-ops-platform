---
name: Foam Plan Critic Fixes
overview: "Apply three critic fixes to the Foam PKM Skill Testing plan: correct malformed markdown link paths, add \"if not yet done\" to implementation steps (Steps 1–2 are already complete), and clarify checksum run context."
todos: []
isProject: false
---

# Foam Plan Critic Fixes

## CL4R1T4S Classification

- **Structure** (tech-lead): Link path convention, placement clarity
- **Revision** (dialectic): Bounded edits per critic report; verify before done

Per [tech_lead_extracts](D:\portfolio-harness\docs\cl4r1t4s_analysis\tech_lead_extracts.md): follow existing conventions. Per [TAXONOMY](D:\portfolio-harness\docs\cl4r1t4s_analysis\TAXONOMY.md): convention-first, verify before done.

---

## Target File

[foam_pkm_skill_testing_e9bee968.plan.md](D:\software.cursor\plans\foam_pkm_skill_testing_e9bee968.plan.md)

---

## Fix 1: Link Targets

**Problem:** `portfolio-harness.cursor` (missing path separator before `.cursor`) — links resolve incorrectly.

**Convention:** Other plans use `D:\portfolio-harness\docs\...` (correct). Use forward slashes for portability per tech-lead guidance.

**Replacements (4 occurrences):**


| Line | Current                                                       | Replacement                                                    |
| ---- | ------------------------------------------------------------- | -------------------------------------------------------------- |
| 12   | `D:\portfolio-harness.cursor\skills\foam-pkm\TEST_PROMPTS.md` | `D:/portfolio-harness/.cursor/skills/foam-pkm/TEST_PROMPTS.md` |
| 16   | `D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md`           | `D:/portfolio-harness/.cursor/docs/AI_TASK_EVALS.md`           |
| 24   | `D:\portfolio-harness.cursor\docs\AGENT_NATIVE_CHECKLIST.md`  | `D:/portfolio-harness/.cursor/docs/AGENT_NATIVE_CHECKLIST.md`  |
| 69   | `D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md`           | `D:/portfolio-harness/.cursor/docs/AI_TASK_EVALS.md`           |


**Note:** Same bug exists in [matt_corallo_video_digest_d17d691d.plan.md](D:\software.cursor\plans\matt_corallo_video_digest_d17d691d.plan.md) and [scp_obliteratus_assimilation_9415fc2b.plan.md](D:\software.cursor\plans\scp_obliteratus_assimilation_9415fc2b.plan.md). This plan scopes to the foam plan only; consider a follow-up to fix all plans.

---

## Fix 2: Implementation Steps (Steps 1–2)

**Problem:** Steps 1–2 read as pre-implementation; both artifacts already exist:

- [TEST_PROMPTS.md](D:\portfolio-harness.cursor\skills\foam-pkm\TEST_PROMPTS.md) exists
- [AI_TASK_EVALS.md](D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md) has foam-pkm row (line 51)

**Change:** Add conditional wording so the plan is valid whether implementation is done or not.

**Step 1 (line 59):** Prepend:

```markdown
### Step 1: Create TEST_PROMPTS.md (if not yet done)
```

**Step 2 (line 68):** Prepend:

```markdown
### Step 2: Add AI_TASK_EVALS registry entry (if not yet done)
```

**Optional:** Add a short note after the Implementation Steps heading:

> **Status:** Steps 1–2 are implemented in portfolio-harness. Re-run when creating a new skill or cloning to another repo.

---

## Fix 3: Checksum Context

**Problem:** Plan lives in `D:\software` (plans submodule); `checksum_integrity.py` is in `D:\portfolio-harness`. Running the command from software root would fail.

**Change:** In Step 3 (lines 79–81), replace:

```markdown
### Step 3: Run checksum_integrity

Before commit: `python .cursor/scripts/checksum_integrity.py --verify --strict`
```

With:

```markdown
### Step 3: Run checksum_integrity

Before commit, from portfolio-harness root:
```powershell
python .cursor/scripts/checksum_integrity.py --verify --strict
```

```

Aligns with [COMMANDS_README](D:\portfolio-harness\.cursor\docs\COMMANDS_README.md) "Before committing rules/skills" section, which implies portfolio-harness root.

---

## Verification

- [ ] All 4 link targets use `D:/portfolio-harness/.cursor/...` (forward slashes)
- [ ] Steps 1–2 include "(if not yet done)"
- [ ] Step 3 includes "from portfolio-harness root" and code block
- [ ] Plan renders correctly; no broken links

---

## Out of Scope

- Fixing link targets in matt_corallo or scp_obliteratus plans (separate task)
- Changing plan content beyond the three critic fixes
```

