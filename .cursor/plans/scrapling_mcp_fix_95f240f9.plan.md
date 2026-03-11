---
name: Scrapling MCP Fix
overview: Fix the Scrapling MCP server startup failure caused by using `python -m scrapling mcp`, which fails because the scrapling package has no `__main__.py`. The package exposes its CLI via a console script `scrapling` that must be invoked directly.
todos: []
isProject: false
---

# Scrapling MCP Error Fix

## Root Cause

The error log shows two cascading failures:

1. **Primary:** `No module named scrapling.__main__; 'scrapling' is a package and cannot be directly executed`
  - Current config runs: `python -m scrapling mcp`
  - `python -m <package>` requires the package to have a `__main__.py` module
  - The scrapling package does **not** define `__main__.py`; it exposes its CLI via a [console script](https://github.com/D4Vinci/Scrapling/blob/main/pyproject.toml) `scrapling = "scrapling.cli:main"`
2. **Secondary:** `OSError: [Errno 22] Invalid argument` in `audit_wrapper.py` line 239 (`dst.write(line)`)
  - Occurs when the relay thread writes to the child process stdout after the child has exited (because scrapling failed immediately)
  - Fixing the primary error will prevent this cascade

## Correct Invocation

From scrapling's [pyproject.toml](https://github.com/D4Vinci/Scrapling/blob/main/pyproject.toml):

- Entry point: `scrapling = "scrapling.cli:main"`
- MCP subcommand exists: `main.add_command(mcp)` in [cli.py](https://github.com/D4Vinci/Scrapling/blob/main/scrapling/cli.py)

The correct way to run the MCP server is `**scrapling mcp`** (the installed console script), not `python -m scrapling mcp`.

## Implementation Options


| Option | Command                                                                                        | Pros                                                  | Cons                                                                                       |
| ------ | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| A      | `scrapling` with args `["mcp"]`                                                                | Native CLI                                            | `scrapling` must be in PATH; on Windows, Scripts may not be in Cursor's PATH               |
| B      | `python -c "import sys; sys.argv=['scrapling','mcp']; from scrapling.cli import main; main()"` | Uses same Python as audit_wrapper; no PATH dependency | Slightly verbose                                                                           |
| C      | `uvx scrapling-fetch-mcp`                                                                      | Dedicated MCP package                                 | Different package (scrapling-fetch-mcp); different feature set; security concerns with uvx |


**Recommendation: Option B** — Most reliable on Windows, uses the same Python environment, and invokes the same scrapling MCP server. Option A may fail if Cursor's MCP spawn doesn't include Python Scripts in PATH.

## Files to Change

1. **[.cursor/mcp.json](D:\portfolio-harness.cursor\mcp.json)** (lines 22–36)
  - Replace args from `["--", "python", "-m", "scrapling", "mcp"]` to `["--", "python", "-c", "import sys; sys.argv=['scrapling','mcp']; from scrapling.cli import main; main()"]`
2. **[.cursor/state/known-issues.md](D:\portfolio-harness.cursor\state\known-issues.md)** (line 59)
  - Update the documented command from `python -m scrapling mcp` to the correct invocation for future reference

## Prerequisites

- **scrapling[ai]** must be installed (includes `mcp>=1.26.0` and fetchers). The `ai` extra is required for MCP support.
- If not already installed: `pip install "scrapling[ai]"` or `pip install "scrapling[all]"`

## Optional: Audit Wrapper Relay Hardening

The `OSError: [Errno 22]` in `_relay` when writing to a closed pipe could be hardened with a try/except around `dst.write(line)` to catch `OSError`/`BrokenPipeError` and break the loop gracefully. This is a defensive improvement, not required for the fix.

## Verification

After applying the fix:

1. Restart Cursor or reload MCP servers
2. Confirm scrapling MCP server starts (no "No module named scrapling.**main**" in logs)
3. If scrapling tools appear in the agent's tool list, the fix is successful

