---
name: Quick Wins Link Resolution
overview: Fix plans links (404), remove absolute paths from shared docs, and add fallbacks for fragile cross-references per critic audit.
todos: []
isProject: false
---

# Quick Wins: Link Resolution and Path Portability

## Summary

Address 6 prioritized quick wins from critic audit: plans links 404, absolute paths in shared docs, and fragile cross-references. Risk: Low (docs only). Verification: `grep -E "D:\\\\|D:/"` on modified files.

---

## 1. WAVED_PENDING_TASKS.md — Plans Links

**File:** [local-proto/docs/WAVED_PENDING_TASKS.md](D:\portfolio-harness\local-proto\docs\WAVED_PENDING_TASKS.md)

**Issue:** Links use `../../.cursor/plans/` but plans submodule lives at `plans/` per [.gitmodules](D:\portfolio-harness.gitmodules). All referenced plan files exist in `plans/` (quick_wins_security_audit_b334a41b.plan.md, continue_aider_eval.plan.md, playwright_skills_audit_prep.plan.md, integration_points_verification_763e7765.plan.md).

**Fix:** Replace `../../.cursor/plans/` with `../../plans/` (6 occurrences).


| Line | Current                                                                | Change to                                                      |
| ---- | ---------------------------------------------------------------------- | -------------------------------------------------------------- |
| 5    | `../../.cursor/plans/quick_wins_security_audit_b334a41b.plan.md`       | `../../plans/quick_wins_security_audit_b334a41b.plan.md`       |
| 47   | `../../.cursor/plans/quick_wins_security_audit_b334a41b.plan.md`       | `../../plans/quick_wins_security_audit_b334a41b.plan.md`       |
| 72   | `../../.cursor/plans/continue_aider_eval.plan.md`                      | `../../plans/continue_aider_eval.plan.md`                      |
| 74   | `../../.cursor/plans/playwright_skills_audit_prep.plan.md`             | `../../plans/playwright_skills_audit_prep.plan.md`             |
| 101  | `../../.cursor/plans/integration_points_verification_763e7765.plan.md` | `../../plans/integration_points_verification_763e7765.plan.md` |
| 210  | `../../.cursor/plans/quick_wins_security_audit_b334a41b.plan.md`       | `../../plans/quick_wins_security_audit_b334a41b.plan.md`       |


---

## 2. CONTEXT_ENGINEERING_TECH_DEMO_PLAN.md — Root Path

**File:** [.cursor/docs/CONTEXT_ENGINEERING_TECH_DEMO_PLAN.md](D:\portfolio-harness.cursor\docs\CONTEXT_ENGINEERING_TECH_DEMO_PLAN.md)

**Line 17:** `Root: D:/portfolio-harness` in prerequisites table.

**Fix:** Change to `Root: <repo root> or %CD%` (or `$PWD` for Unix).

---

## 3. HANDOFF_FLOW.md — Plans Path and Local-First Ref

**File:** [.cursor/HANDOFF_FLOW.md](D:\portfolio-harness.cursor\HANDOFF_FLOW.md)

**Fixes:**

1. **Lines 36–37 (Plans submodule):** Change "at `.cursor/plans/`" to "at `plans/`" to match .gitmodules. Update: "Paths like `plan_ref` and `dependency_links` (e.g. `../plans/foo.plan.md`) resolve to the Planswithinplans submodule at `plans/`."
2. **Line 50 (Sync decisions):** Change `[D:\local-first\AGENTS.md](D:\local-first\AGENTS.md)` to `[.cursor/state/decision-log.md](state/decision-log.md)` (the actual target for logging) or add fallback: "per [local-first skill](skills/local-first/SKILL.md) or [decision-log.md](state/decision-log.md)".

---

## 4. pending_tasks.md — Plan Links

**File:** [.cursor/state/pending_tasks.md](D:\portfolio-harness.cursor\state\pending_tasks.md)

**Fix:** Replace `D:\software\.cursor\plans\` with `../../plans/` for plan links. From .cursor/state/, `../../plans/` = portfolio-harness/plans/.


| Row  | Current                                                                                                                                                    | Change to                                                                                                                                                                            |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AL2  | `D:\software\.cursor\plans\bitcoin_chaos_convergence_a219e7b9.plan.md`, `D:\software\.cursor\plans\bitcoin_chaos_convergence_integration_827d4828.plan.md` | `[bitcoin_chaos_convergence plan](../../plans/bitcoin_chaos_convergence_a219e7b9.plan.md)`, `[integration plan](../../plans/bitcoin_chaos_convergence_integration_827d4828.plan.md)` |
| AL2a | `D:\software\.cursor\plans\bitcoin_chaos_convergence_a219e7b9.plan.md`                                                                                     | `[bitcoin_chaos_convergence_a219e7b9](../../plans/bitcoin_chaos_convergence_a219e7b9.plan.md)`                                                                                       |
| B6   | `D:\software\.cursor\plans\bitcoin_chaos_convergence_integration_827d4828.plan.md`                                                                         | `[integration plan](../../plans/bitcoin_chaos_convergence_integration_827d4828.plan.md)`                                                                                             |


**Exclude:** AL1 (D:\alignment-seed — external), V2 (D:/Arc_Forge — done task describing fix). Add note if desired: "AL1, V2 reference external workspaces."

---

## 5. AGENT_ENTRY_INDEX.md — Local-First Fallback

**File:** [.cursor/docs/AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md)

**Line 39:** `[local-first README](../../../local-first/README.md)` — 404 if local-first not in workspace.

**Fix:** Add fallback: "Learning local-first or choosing sync engines | [LOCAL_FIRST_STACK_CHOICE.md](../../local-proto/docs/LOCAL_FIRST_STACK_CHOICE.md) or [local-first skill](../skills/local-first/SKILL.md). If local-first workspace is open: [local-first README](../../../local-first/README.md)."

Or simpler: replace with `[LOCAL_FIRST_STACK_CHOICE.md](../../local-proto/docs/LOCAL_FIRST_STACK_CHOICE.md)` and `[local-first skill](../skills/local-first/SKILL.md)` as primary; drop fragile ../../../local-first link.

---

## 6. secure-contain-protect README — Placeholder

**File:** [.cursor/skills/secure-contain-protect/README.md](D:\portfolio-harness.cursor\skills\secure-contain-protect\README.md)

**Line 17:** "Replace `D:/portfolio-harness` (or your install path) with your actual path."

**Fix:** Change to "Replace `<REPO_ROOT>` (or your install path) with your actual path." The mcp.json template below already uses `<REPO_ROOT>`.

---

## Implementation Order

1. WAVED_PENDING_TASKS.md (6 replacements)
2. CONTEXT_ENGINEERING_TECH_DEMO_PLAN.md (1 replacement)
3. HANDOFF_FLOW.md (2 edits)
4. pending_tasks.md (4 link groups: AL2, AL2a, B6)
5. AGENT_ENTRY_INDEX.md (1 row edit)
6. secure-contain-protect README (1 replacement)

---

## Verification

- Run `grep -E "D:\\\\|D:/"` on modified files; expect no matches in shared docs (decision-log historical entries acceptable).
- Click-through: plans links resolve to files in `plans/` submodule.
- Run critic on modified docs; expect pass.

---

## Out of Scope (Lower Priority)

- decision-log.md: D:/ in historical entries — keep as audit trail.
- pending_tasks AL1, V2: External paths — leave as-is or add "(external workspace)" note.

