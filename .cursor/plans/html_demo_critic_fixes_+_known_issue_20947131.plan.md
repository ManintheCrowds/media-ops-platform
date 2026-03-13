---
name: HTML Demo Critic Fixes + Known Issue
overview: Implement critic feedback on the HTML walkthrough demo, record the agent Korean-language-switch known issue, add to pending_tasks, and update AGENTS.md via continual-learning.
todos: []
isProject: false
---

# HTML Demo Critic Fixes + Korean-Language Known Issue

## Context

- **Critic report (2026-03-13):** Pass (18/25); 8 issues, 7 actionable fixes for [docs/demo/context-engineering-walkthrough.html](D:\portfolio-harness\docs\demo\context-engineering-walkthrough.html).
- **Known issue:** Agent unexpectedly switches to Korean when user sends a prompt (e.g. "do it") after previous English context. User requests this be recorded and added to todo.
- **Continual-learning:** Add language preference to AGENTS.md.

---

## Phase 1: Record Known Issue and Todo

### 1.1 Add to known-issues.md

**File:** [.cursor/state/known-issues.md](D:\portfolio-harness.cursor\state\known-issues.md)

**New section (append before ## Archive or at end):**

```markdown
## Agent behavior (Cursor / AI)

- **Symptom:** Agent switches to Korean unexpectedly when user sends a short prompt (e.g. "do it", "and do it") after previous English context. **Location:** Cursor AI responses. **Issue:** Response language drifts to Korean without explicit user request. **Status:** open. **Note:** Investigate: .cursorrules "Always respond in Korean" rule, workspace rules, or model context. User preference: English unless explicitly requested otherwise.
```

### 1.2 Add to pending_tasks.md

**File:** [.cursor/state/pending_tasks.md](D:\portfolio-harness.cursor\state\pending_tasks.md)

**Add row to PENDING_OTHER (or new PENDING_AGENT_BEHAVIOR):**


| ID  | Status  | Task                                                                                                                                                                                                                  | Spec / Link                                        |
| --- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| H5  | pending | **Agent Korean-language switch:** Investigate and fix unexpected Korean responses when user sends short prompts (e.g. "do it") in English context. Check .cursorrules, workspace rules, language-preference handling. | [known-issues.md](known-issues.md) §Agent behavior |


---

## Phase 2: Implement Critic Fixes (HTML Walkthrough)

**File:** [docs/demo/context-engineering-walkthrough.html](D:\portfolio-harness\docs\demo\context-engineering-walkthrough.html)

### 2.1 Content gaps (cheatsheet alignment)


| Fix                  | Location                      | Action                                                                                                       |
| -------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Block 3 note         | Block 3 demo prompt area      | Add note: "Use fetch_craigslist_search or audit_wrapper; fetch_captions_ytdlp doesn't exist in local-proto." |
| Block 7 Bitcoin note | Block 7 note section          | Append: "Bitcoin-capable: observation, provenance (see BITCOIN_AGENT_CAPABILITIES.md)."                      |
| Block 5 pre-commit   | Block 5 pre-demo verification | Add hook names: sanitize_input, validate_output, mask_secrets, checksum_integrity                            |
| Block 5 tense        | SCP future vision text        | Align "will submit" with cheatsheet "will be able to submit"                                                 |


### 2.2 Accessibility


| Fix               | Location                 | Action                                                                                                                  |
| ----------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Table headers     | All `<th>` elements      | Add `scope="col"`                                                                                                       |
| Diagram fallbacks | Each `.diagram-wrap`     | Add `aria-label` describing the diagram (e.g. "Flowchart: Aspirational layer governing harness mycelium")               |
| Viewport          | `<meta name="viewport">` | Change from `width=1280` to `width=device-width, initial-scale=1`                                                       |
| Main landmark     | Body structure           | Wrap `.container` in `<main>`; add skip link: `<a href="#block-1" class="skip-link">Skip to content</a>` at top of body |


### 2.3 Verification

- Serve: `npx serve docs/demo -p 3333` (from portfolio-harness root)
- Open [http://localhost:3333/context-engineering-walkthrough.html](http://localhost:3333/context-engineering-walkthrough.html)
- Spot-check Block 3, 5, 7 content; verify tables and diagrams render; test skip link and keyboard nav

---

## Phase 3: Continual-Learning (AGENTS.md)

**File:** [.cursor/state/AGENTS.md](D:\portfolio-harness.cursor\state\AGENTS.md)

**Add to ## Learned User Preferences:**

- Prefer English for agent responses unless user explicitly requests another language (e.g. Korean). Do not switch to Korean based on short prompts like "do it" or implicit context.

**Note:** If `.cursorrules` or a workspace rule contains "Always respond in Korean", that may conflict; document in known-issues and consider rule override for this workspace.

---

## Phase 4: Critic Re-run (Optional)

After implementing fixes, run critic again to verify:

- `mcp_task` with `subagent_type="critic"` on the updated HTML file
- Or manual review per critic-loop-gate

---

## Summary


| Phase | Deliverable                                            |
| ----- | ------------------------------------------------------ |
| 1     | known-issues.md entry; pending_tasks.md H5             |
| 2     | 7 critic fixes in context-engineering-walkthrough.html |
| 3     | AGENTS.md Learned User Preferences update              |
| 4     | Optional: critic re-run for verification               |


