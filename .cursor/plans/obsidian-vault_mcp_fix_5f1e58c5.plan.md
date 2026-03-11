---
name: Obsidian-vault MCP Fix
overview: Fix the obsidian-vault MCP server failure caused by ModuleNotFoundError for mcp_server and the subsequent OSError in the audit_wrapper relay when the subprocess exits immediately.
todos: ["Verify obsidian-vault MCP loads after Cursor restart; call a tool (e.g. list notes) to confirm end-to-end"]
status: closed
isProject: false
---

# Obsidian-vault MCP Fix Plan

## Problem Summary

The obsidian-vault MCP server fails to start with two cascading errors:

1. **Primary:** `ModuleNotFoundError: No module named 'mcp_server'` — Python cannot find the `mcp_server` module when running `python -m mcp_server.server`.
2. **Secondary:** `OSError: [Errno 22] Invalid argument` at [audit_wrapper.py](D:\portfolio-harness\local-proto\scripts\audit_wrapper.py) line 239 — the relay thread tries to write to stdout after Cursor has closed the connection (because the subprocess exited immediately).

## Root Cause

- The `mcp_server` package lives at `D:/portfolio-harness/obsidian_cursor_integration/mcp_server/`.
- The MCP config sets `cwd: "D:/portfolio-harness/obsidian_cursor_integration"`, but:
  - **audit_wrapper** does not pass `cwd` to the subprocess it spawns; the child inherits the parent's cwd.
  - Cursor may spawn the MCP process from the workspace root (e.g. `D:/portfolio-harness` or `D:/software`), so the subprocess runs with the wrong cwd.
- With the wrong cwd, `sys.path[0]` (current directory) does not contain `obsidian_cursor_integration`, so `mcp_server` is not found.

## Solution

### 1. Add PYTHONPATH to obsidian-vault MCP env (primary fix)

In [.cursor/mcp.json](D:\portfolio-harness.cursor\mcp.json), add `PYTHONPATH` to the obsidian-vault server's `env` so the module is found regardless of cwd:

```json
"obsidian-vault": {
  ...
  "env": {
    "PYTHONPATH": "D:/portfolio-harness/obsidian_cursor_integration",
    "OBSIDIAN_VAULT_ROOT": "D:/Arc_Forge/ObsidianVault",
    ...
  },
  ...
}
```

This ensures `python -m mcp_server.server` finds both `mcp_server` and sibling packages (`index`, `context`, `safety`, `session`, `automation`).

### 2. Harden audit_wrapper relay against closed pipe (optional but recommended)

In [audit_wrapper.py](D:\portfolio-harness\local-proto\scripts\audit_wrapper.py), wrap the `dst.write(line)` / `dst.flush()` calls in `_relay` with a try/except for `OSError` (and `BrokenPipeError`), breaking the loop gracefully when the client has closed the connection. This prevents noisy tracebacks when the subprocess exits early.

```python
# Around lines 183-184 and 239-240
try:
    dst.write(line)
    dst.flush()
except OSError:
    break  # Client closed; exit relay gracefully
```

Apply to both write sites in `_relay` (the JSON-decode continue path and the main path).

### 3. Document in known-issues (optional)

Add an entry to [.cursor/state/known-issues.md](D:\portfolio-harness.cursor\state\known-issues.md) under "local-proto (MCP, first-install)" describing the obsidian-vault PYTHONPATH requirement and the fix, so future agents/users can diagnose similar issues.

## Verification

After applying the fix:

1. Restart Cursor or reload the MCP servers.
2. Confirm obsidian-vault MCP loads (no "Server not yet created, returning empty offerings").
3. Optionally call an obsidian-vault tool (e.g. list notes) to verify end-to-end.

## Dependencies

- The obsidian_cursor_integration package requires `mcp>=1.2.0` (optional extra). If not installed, a different error will appear after the ModuleNotFoundError is fixed. User may need: `pip install -e D:/portfolio-harness/obsidian_cursor_integration[mcp]` from the appropriate environment.

