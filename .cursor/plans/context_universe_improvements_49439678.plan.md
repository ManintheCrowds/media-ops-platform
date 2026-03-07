---
name: Context Universe Improvements
overview: Improve the Context Universe system with easy wins (link validation, Code Quality Auditor prompt, eval registry), gap closure (AI task evals for software, critic integration), and testing/audit mechanisms.
todos: []
isProject: false
---

# Context Universe Improvement Plan

## Current State Summary

You have implemented:

- [coding_standards_matrix.md](D:\software\docs\coding_standards_matrix.md) with Table 1 (standards) and Table 2 (pattern references)
- Retrieve-before-generate in [AI_PROMPT_LIBRARY.md](D:\software\docs\AI_PROMPT_LIBRARY.md) Prompt 9
- Pattern Extraction prompt (Prompt 15)
- Cross-references in AI_DOCUMENTATION_INDEX, .cursorrules

**Gaps identified:**

- No automated validation that agents follow retrieve-before-generate
- No link checker for matrix URLs (9 external links can go stale)
- No AI task evals for the software repo (portfolio-harness has [AI_TASK_EVALS.md](D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md))
- Article's Code Quality Auditor prompt not implemented
- No Matrix Generation prompt (auto-build matrix from repos)
- Critic-loop-gate applies to RAG but not explicitly to code-from-context

---

## Tier 1: Easy Wins (Low effort, high signal)

### 1.1 Add Code Quality Auditor Prompt

**File:** [docs/AI_PROMPT_LIBRARY.md](D:\software\docs\AI_PROMPT_LIBRARY.md)

**Action:** Add Prompt 16 after Pattern Extraction. Aligns with article's "Prompt 2" and complements existing Code Review prompt.

```
Act as a software architecture reviewer.

Compare the current code against:
- [coding_standards_matrix.md](coding_standards_matrix.md) Table 1 (PEP8, OpenAPI, OWASP, SQLAlchemy, etc.)
- [AI_PATTERNS.md](AI_PATTERNS.md) patterns

Return:
1. Violations (with standard/pattern reference)
2. Security risks (OWASP mapping)
3. Architectural smells
4. Suggested refactor
```

**Effort:** ~15 min. **Value:** Gives agents a structured audit prompt tied to your matrix.

---

### 1.2 Add Link Audit Section to coding_standards_matrix.md

**File:** [docs/coding_standards_matrix.md](D:\software\docs\coding_standards_matrix.md)

**Action:** Add footer:

```markdown
---

## Maintenance

- **Last link audit:** YYYY-MM-DD (run `markdown-link-check` or manual)
- **Update trigger:** New standards or reference repos; quarterly link check
```

**Effort:** 2 min. **Value:** Creates accountability for link freshness.

---

### 1.3 Add Matrix Generation Prompt

**File:** [docs/AI_PROMPT_LIBRARY.md](D:\software\docs\AI_PROMPT_LIBRARY.md)

**Action:** Add Prompt 17. Use when onboarding new reference repos to auto-extend the matrix.

```
Scan the following repositories and extract coding standards:
- formatting rules, architecture patterns, testing practices, security patterns

Produce a matrix linking: pattern | repository | documentation | example file

Output markdown table suitable for coding_standards_matrix.md Table 2.
```

**Effort:** ~10 min. **Value:** Reduces manual matrix maintenance when adding repos.

---

## Tier 2: Gap Closure (Medium effort)

### 2.1 Create AI Task Eval Registry for Software

**File:** Create `D:\software\docs\AI_TASK_EVALS.md` (or `.cursor\docs\AI_TASK_EVALS.md`)

**Action:** Adapt [portfolio-harness AI_TASK_EVALS.md](D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md) for software repo.


| Task                         | Test cases / verification                                                                          | When to run                                 |
| ---------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| **Retrieve-before-generate** | Agent output includes "Standards applied" and "Reference code used" sections before Implementation | Spot-check after code gen; quarterly sample |
| **Code Quality Auditor**     | Output has Violations, Security risks, Architectural smells, Suggested refactor                    | After audit runs                            |
| **Pattern Extraction**       | Output has pattern, structure, principles, checklist                                               | After Pattern Extraction runs               |
| **Matrix link validity**     | All URLs in coding_standards_matrix.md return 2xx                                                  | Quarterly; CI or manual                     |


**Effort:** ~30 min. **Value:** Makes compliance testable and creates a model-update trigger.

---

### 2.2 Integrate Critic with Code Generation

**Action:** Add to Prompt 9 (Code Generation) or to critic-loop-gate rule:

- When generating code from context universe, produce critic JSON (pass, score, issues, fixes) before finalizing.
- Domains: code. Check: "Did agent cite standards and references before implementation?"

**Options:**

- **A:** Extend [critic-loop-gate.mdc](C:\Users\schum.cursor\rules\critic-loop-gate.mdc) to include "code from context" (broader scope)
- **B:** Add critic step inside Prompt 9 template (software-only)

**Effort:** ~20 min. **Value:** Aligns code gen with existing RAG critic discipline.

---

### 2.3 Add Link Check to CI or Script

**Action:** Add markdown link check for `docs/*.md` (especially coding_standards_matrix.md).

- **Option A:** Use [markdown-link-check](https://github.com/tcort/markdown-link-check) in a GitHub Action or local script
- **Option B:** Add `scripts/check_docs_links.sh` (or `.ps1`) that validates key URLs

**Effort:** ~30 min. **Value:** Catches broken links before they mislead agents.

---

## Tier 3: Testing and Observability

### 3.1 Retrieve-Before-Generate Spot-Check Procedure

**Action:** Document in AI_TASK_EVALS or AI_VALIDATION_CHECKLIST:

1. Ask agent: "Add a new service client for [fictional service]. Use Prompt 9."
2. Verify output order: Standards applied → Reference code used → Design plan → Implementation
3. Verify at least one standard from matrix and one internal reference path cited
4. Record pass/fail; add to eval registry

**Effort:** ~15 min (doc). **Value:** Concrete test for the core mechanism.

---

### 3.2 Cross-Link Software to Portfolio-Harness Evals

**Action:** In [AI_DOCUMENTATION_INDEX.md](D:\software\docs\AI_DOCUMENTATION_INDEX.md) or a new "Evals" section:

- Add: "For AI task evals and calibration, see [portfolio-harness AI_TASK_EVALS](D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md)"
- Add software-specific eval tasks to portfolio-harness registry (or keep in software with pointer)

**Effort:** ~10 min. **Value:** Single place to find all eval procedures.

---

## Implementation Order


| Priority | Item                                  | Effort | Impact |
| -------- | ------------------------------------- | ------ | ------ |
| 1        | Code Quality Auditor prompt           | 15 min | High   |
| 2        | Matrix Generation prompt              | 10 min | Medium |
| 3        | Link audit footer in matrix           | 2 min  | Low    |
| 4        | AI_TASK_EVALS.md for software         | 30 min | High   |
| 5        | Retrieve-before-generate spot-check   | 15 min | High   |
| 6        | Critic integration (Prompt 9 or rule) | 20 min | Medium |
| 7        | Link check script/CI                  | 30 min | Medium |
| 8        | Cross-link to portfolio-harness evals | 10 min | Low    |


---

## Quick Wins Summary

**Do first (under 30 min total):**

1. Code Quality Auditor prompt
2. Matrix Generation prompt
3. Link audit footer in coding_standards_matrix.md

**Do next (under 1 hr):**
4. AI_TASK_EVALS.md with Retrieve-before-generate, Pattern Extraction, Matrix links
5. Retrieve-before-generate spot-check procedure
6. Critic integration for code-from-context

**Do when automating:**
7. Link check script or CI step