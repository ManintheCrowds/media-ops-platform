# AI Task Eval Registry (Software)

Define recurring AI tasks and how to verify them. Per specification engineering: 3–5 test cases with known-good outputs; run periodically, especially after model updates.

**See also:** [AI_PROMPT_LIBRARY.md](AI_PROMPT_LIBRARY.md), [coding_standards_matrix.md](coding_standards_matrix.md). For harness-wide evals (handoff, Daggr, calibration), see [portfolio-harness AI_TASK_EVALS](D:\portfolio-harness\.cursor\docs\AI_TASK_EVALS.md).

---

## Registry

| Task | Test cases / verification | When to run |
|------|---------------------------|-------------|
| **Retrieve-before-generate** | Agent output includes "Standards applied" and "Reference code used" sections before Implementation | Spot-check after code gen; quarterly sample |
| **Code Quality Auditor** | Output has Violations, Security risks, Architectural smells, Suggested refactor | After audit runs |
| **Pattern Extraction** | Output has pattern, structure, principles, checklist | After Pattern Extraction runs |
| **Matrix link validity** | All URLs in coding_standards_matrix.md return 2xx | Quarterly; CI or manual |

---

## Retrieve-Before-Generate Spot-Check Procedure

1. Ask agent: "Add a new service client for [fictional service]. Use Prompt 9."
2. Verify output order: Standards applied → Reference code used → Design plan → Implementation
3. Verify at least one standard from matrix and one internal reference path cited
4. Record pass/fail; add to eval registry

---

## Running evals

- **Retrieve-before-generate:** Manual spot-check; use procedure above when generating code.
- **Code Quality Auditor:** Run Prompt 16 on code; verify output structure.
- **Pattern Extraction:** Run Prompt 15 on repo; verify output has required fields.
- **Matrix links:** Run `.\scripts\check_docs_links.ps1` from repo root (or manual) on docs/coding_standards_matrix.md.

---

## Model-update trigger

After a Cursor or model update: run retrieve-before-generate spot-check; verify matrix links.

---

## Adding new tasks

For each recurring AI task:

1. Define 3–5 test cases with known-good outputs.
2. Add to this registry.
3. Run periodically; after model updates.
4. Document failures in known-issues or decision-log.
