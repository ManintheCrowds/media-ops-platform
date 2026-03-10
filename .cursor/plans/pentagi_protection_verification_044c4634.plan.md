---
name: PentAGI Protection Verification
overview: Add a verification script for the PentAGI protection flow, update HITL_PLAYBOOK and DEANONYMIZATION_RISK with verification references, document exposure-check in AGENT_ENTRY_INDEX, and run critic on new docs. No backend logic changes.
todos: []
isProject: false
---

# PentAGI Protection Flow Verification and Docs Update

## Scope

- **In scope:** Verification script, doc updates (HITL_PLAYBOOK, DEANONYMIZATION_RISK, AGENT_ENTRY_INDEX), critic on new docs
- **Out of scope:** PentAGI backend logic changes

---

## 1. Verification Script

**Create:** [.cursor/scripts/verify_pentagi_protection.ps1](D:\portfolio-harness.cursor\scripts\verify_pentagi_protection.ps1)

Follow the pattern of [run_chaos_smoke.ps1](D:\portfolio-harness.cursor\scripts\run_chaos_smoke.ps1): file-existence and content checks, no backend invocation.

**Checks (per [pentagi_protection_implementation plan](D:\software.cursor\plans\pentagi_protection_implementation_2d26bd26.plan.md) Verification section):**


| Check                 | Path                                                 | Validation                                                                     |
| --------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------ |
| Protection preset     | `pentagi/.env.protection`                            | File exists                                                                    |
| Defensive org-intent  | `pentagi/examples/org-intent-defensive.json`         | Exists; contains `"mode": "defensive"` and `hb-3`                              |
| Scope example         | `pentagi/examples/scope/my-assets.example.txt`       | File exists                                                                    |
| Exposure prompt       | `pentagi/examples/prompts/exposure_check.md`         | Exists; contains "defensive" or "exposure"                                     |
| Starter template      | `pentagi/frontend/src/features/flows/flow-form.tsx`  | Contains `exposure_check` in STARTER_TEMPLATES                                 |
| Deanonymization check | `pentagi/backend/pkg/tools/deanonymization/check.go` | File exists; contains `CheckPreTool`                                           |
| Config vars           | `pentagi/.env.example`                               | Contains `DEANONYMIZATION_CHECK_ENABLED` and `PENTAGI_AUDIT_ALERT_WEBHOOK_URL` |


**Script behavior:** Accept optional `-RepoRoot`; default to parent of `.cursor`. Exit 0 if all pass, 1 otherwise. Output `[PASS]` / `[FAIL]` per check.

---

## 2. HITL_PLAYBOOK Update

**File:** [pentagi/docs/HITL_PLAYBOOK.md](D:\portfolio-harness\pentagi\docs\HITL_PLAYBOOK.md)

**Add new section (after §9 References):**

```markdown
## 10. Verification

Run the protection-flow verification script from repo root:

    .\.cursor\scripts\verify_pentagi_protection.ps1

Verifies: .env.protection, org-intent-defensive.json, scope example, exposure_check prompt, starter template, deanonymization check, config vars. See [DEANONYMIZATION_RISK.md §4a](DEANONYMIZATION_RISK.md#4a-protection-oriented-setup) for protection setup.
```

**Optional refinement:** In §7 (Exposure Check Flow Template), add one line: "Run `verify_pentagi_protection.ps1` to confirm all artifacts exist."

---

## 3. DEANONYMIZATION_RISK Update

**File:** [pentagi/docs/DEANONYMIZATION_RISK.md](D:\portfolio-harness\pentagi\docs\DEANONYMIZATION_RISK.md)

**In §4a (Protection-Oriented Setup):** Add a short "Verification" bullet:

- **Verification:** From repo root, run `.\\.cursor\\scripts\\verify_pentagi_protection.ps1` to confirm `.env.protection`, `org-intent-defensive.json`, scope example, exposure_check prompt, starter template, and deanonymization check are present.

**In §7 (Future Work):** Add "Verification script for protection flow" as completed (or move to a "Completed" subsection if preferred).

---

## 4. AGENT_ENTRY_INDEX Update

**File:** [.cursor/docs/AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md)

**Add row** (near line 37, with HITL/PentAGI entries):


| If you are …                                      | Then read …                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Running PentAGI exposure check or protection flow | [pentagi/docs/HITL_PLAYBOOK.md](../../pentagi/docs/HITL_PLAYBOOK.md) §7 Exposure Check, [DEANONYMIZATION_RISK.md](../../pentagi/docs/DEANONYMIZATION_RISK.md) §4a, [exposure_check.md](../../pentagi/examples/prompts/exposure_check.md); run `verify_pentagi_protection.ps1` to verify setup |


Use relative paths from `.cursor/docs/` to `pentagi/` (e.g. `../../pentagi/docs/`).

---

## 5. Critic on New Docs

Per [critic-loop-gate](c:\Users\schum.cursor\rules\critic-loop-gate.mdc), produce critic JSON before marking complete:

- **Domain:** docs
- **Artifacts:** HITL_PLAYBOOK §10, DEANONYMIZATION_RISK §4a update, AGENT_ENTRY_INDEX new row
- **Format:** `{ "pass": true|false, "score": 0.0-1.0, "issues": [...], "fixes": [...] }`
- **Process:** Run critic subagent (`mcp_task` with `subagent_type: "critic"`) on the updated doc content, or perform manual model-as-judge review. If `pass=false` or score below threshold, revise and re-run critic.

---

## Implementation Order

1. Create `verify_pentagi_protection.ps1`
2. Run script to confirm baseline passes (or fix any failing checks)
3. Update HITL_PLAYBOOK §10
4. Update DEANONYMIZATION_RISK §4a
5. Update AGENT_ENTRY_INDEX
6. Run critic on new/updated docs; revise if needed
7. Include final critic report in handoff/summary

---

## Files Touched


| File                                            | Action                         |
| ----------------------------------------------- | ------------------------------ |
| `.cursor/scripts/verify_pentagi_protection.ps1` | Create                         |
| `pentagi/docs/HITL_PLAYBOOK.md`                 | Add §10                        |
| `pentagi/docs/DEANONYMIZATION_RISK.md`          | Add verification bullet in §4a |
| `.cursor/docs/AGENT_ENTRY_INDEX.md`             | Add exposure-check row         |


---

## Out of Scope

- PentAGI backend logic (executor, deanonymization check, config)
- E2E tests requiring running backend (deanonymization block, webhook POST)
- Changes to flow-form.tsx, check.go, or other code

