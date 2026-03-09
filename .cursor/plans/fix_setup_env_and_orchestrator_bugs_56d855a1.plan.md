---
name: Fix setup_env and orchestrator bugs
overview: "Verify and fix three bugs: (1) setup_env.py workspace root resolution returning .cursor instead of repo root, (2) PowerShell scripts passing byte array to Invoke-RestMethod instead of JSON string, and (3) orchestrator.py silently failing when fallback prompt is unavailable and not handling send_to_signal correctly."
todos: []
isProject: false
---

# Fix setup_env, PowerShell, and Orchestrator Bugs

## Bug Verification Summary


| Bug | Location                                                                                                                                                                                                                                                             | Verified | Notes                                                                                                                                                                                                                                              |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | [setup_env.py](D:\portfolio-harness.cursor\scripts\setup_env.py)                                                                                                                                                                                                     | Partial  | Current code uses `script_dir.parent.parent`; correct for `.cursor/scripts/` layout. Bug may manifest if script is run from different workspace root (e.g. `software`) where projects are siblings of portfolio-harness. Add defensive validation. |
| 2   | [generate_next_prompt.ps1](D:\portfolio-harness.cursor\scripts\generate_next_prompt.ps1), [verify_ollama_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_ollama_llm.ps1), [verify_nim_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_nim_llm.ps1) | Yes      | All use `$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)` and pass to `-Body`. PowerShell expects string for JSON; byte array can cause encoding issues in 5.1.                                                                          |
| 3   | [orchestrator.py](D:\portfolio-harness.cursor\scripts\orchestrator.py)                                                                                                                                                                                               | Yes      | When `_use_fallback_prompt()` returns False, no prompt is written and no warning is logged. `send_to_signal` is only called when we have a valid prompt (or inside fallback); but fallback does not validate prompt content before sending.        |


---

## Bug 1: `_workspace_root()` returns one level too shallow

**File:** [.cursor/scripts/setup_env.py](D:\portfolio-harness.cursor\scripts\setup_env.py) (lines 23–26)

**Current logic:**

```python
def _workspace_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent.parent
```

For script at `workspace/.cursor/scripts/setup_env.py`, `parent.parent` correctly yields the workspace root. If the script resolves to `.cursor` (e.g. different run context or symlinks), the result would be one level too shallow.

**Fix:**

1. Add a validation step: after computing `workspace`, verify that at least one project path exists (e.g. `(workspace / "pentagi" / ".env.example").exists()`).
2. If validation fails, try `workspace.parent` as an alternative root and re-validate.
3. If both fail, emit a clear error with the resolved path instead of failing later with ".env.example not found".

---

## Bug 2: Invoke-RestMethod -Body byte array

**Files:**

- [.cursor/scripts/generate_next_prompt.ps1](D:\portfolio-harness.cursor\scripts\generate_next_prompt.ps1) (lines 47–52)
- [local-proto/scripts/verify_ollama_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_ollama_llm.ps1) (lines 19–24)
- [local-proto/scripts/verify_nim_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_nim_llm.ps1) (lines 42–52)

**Current pattern:**

```powershell
$body = $bodyObj | ConvertTo-Json -Depth 4 -Compress
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
$response = Invoke-RestMethod ... -Body $bodyBytes -ContentType "application/json; charset=utf-8"
```

**Fix:** Pass the JSON string directly to `-Body`:

```powershell
$body = $bodyObj | ConvertTo-Json -Depth 4 -Compress
$response = Invoke-RestMethod ... -Body $body -ContentType "application/json; charset=utf-8"
```

Remove the `$bodyBytes` variable and the `GetBytes` call. This is simpler and avoids encoding issues in PowerShell 5.1.

---

## Bug 3: Fallback prompt failure and send_to_signal behavior

**File:** [.cursor/scripts/orchestrator.py](D:\portfolio-harness.cursor\scripts\orchestrator.py) (lines 206–247)

**Issues:**

1. When `_use_fallback_prompt()` returns False (e.g. `continue_prompt.txt` missing), the code returns without writing anything to `next_prompt.txt` and without logging a clear warning.
2. `send_to_signal()` is called inside `_use_fallback_prompt()` when fallback succeeds, but the fallback content is not validated (could be empty or invalid).
3. When fallback fails, the caller has no indication that handoff processing did not complete.

**Fixes:**

1. **Log when fallback fails:** In each branch where `_use_fallback_prompt()` returns False, add:

```python
   print("continue_prompt.txt not found or unreadable; no prompt written", file=sys.stderr)
   

```

1. **Optional: write a diagnostic placeholder** when fallback fails:

```python
   write_next_prompt(config["state_dir"], "[Handoff] No prompt available. Add .cursor/state/continue_prompt.txt or ensure Ollama is running.")
   

```

   (Debatable: may clutter state. Prefer logging only unless product explicitly wants a placeholder.)

1. **Validate fallback content before writing/sending:** In `_use_fallback_prompt()`, reject empty or too-short prompts:

```python
   prompt = continue_path.read_text(encoding="utf-8").strip()
   if len(prompt) < MIN_PROMPT_LEN or any(p in prompt for p in SYSTEM_PROMPT_LEAK_PATTERNS):
       return False
   

```

1. **Avoid duplicate send_to_signal:** When `_use_fallback_prompt()` returns True, it already calls `send_to_signal()`. The main path at line 247 also calls `send_to_signal()` after `write_next_prompt()`. Ensure we do not double-send when using fallback (current code returns before line 247, so no double-send).

---

## Implementation Order

1. **Bug 2** (PowerShell) — Low risk, straightforward string substitution.
2. **Bug 3** (orchestrator) — Add logging and validation in `_use_fallback_prompt()`.
3. **Bug 1** (setup_env) — Add validation and optional fallback for workspace root.

---

## Files to Modify


| File                                                                                     | Changes                                                                                     |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| [setup_env.py](D:\portfolio-harness.cursor\scripts\setup_env.py)                         | Add workspace validation; try `workspace.parent` if no project found; clearer error message |
| [generate_next_prompt.ps1](D:\portfolio-harness.cursor\scripts\generate_next_prompt.ps1) | Use `-Body $body` instead of `-Body $bodyBytes`                                             |
| [verify_ollama_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_ollama_llm.ps1)  | Same                                                                                        |
| [verify_nim_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_nim_llm.ps1)        | Same                                                                                        |
| [orchestrator.py](D:\portfolio-harness.cursor\scripts\orchestrator.py)                   | Log when fallback fails; validate fallback prompt in `_use_fallback_prompt()`               |


