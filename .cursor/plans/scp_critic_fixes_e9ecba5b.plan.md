---
name: SCP Critic Fixes
overview: "Address the four critic-identified issues: config path alignment, reversal false-positive documentation, create_foam_note SCP gate, and summarize_content path documentation."
todos: []
isProject: false
---

# SCP Critic Fixes Plan

Address the four issues from the critic report (score 0.88, pass) for the SCP + AI Trends integration.

---

## 1. Config Path Alignment

**Issue:** `scp_mcp._get_ai_trends_base()` uses a fixed path `_local_proto/ai_trends_config.json` and does not honour `AI_TRENDS_CONFIG` env. AI Trends MCP uses `AI_TRENDS_CONFIG` or `local-proto/scripts/ai_trends_config.json`.

**Fix:** Align [scp_mcp.py](D:\portfolio-harness\local-proto\scripts\scp_mcp.py) with AI Trends config resolution:

- In `_get_ai_trends_base()`, resolve config path via `os.environ.get("AI_TRENDS_CONFIG")` first; if unset, use `_local_proto / "ai_trends_config.json"` (scp_mcp lives in scripts/, so this = `scripts/ai_trends_config.json`).
- Update [AI_TRENDS_MCP.md](D:\portfolio-harness\local-proto\docs\AI_TRENDS_MCP.md) Configuration section: add note that `scp_analyze_ai_trends` uses the same config resolution (AI_TRENDS_CONFIG or `local-proto/scripts/ai_trends_config.json`) for base path.

---

## 2. Reversal False-Positive Documentation

**Issue:** `encoding_blocks` on newsletter URLs (e.g. TechCrunch links with hex-like path segments) triggers reversal tier. Content is still sanitized+contained; low risk but adds audit noise.

**Fix (doc-only, low priority for code):**

- Add to [AI_TRENDS_MCP.md](D:\portfolio-harness\local-proto\docs\AI_TRENDS_MCP.md) Security section:
  - "Known: encoding_blocks on newsletter URLs (hex-like path segments) may trigger reversal; content is sanitized+contained and persisted. No fix required unless audit noise is high."
- Add to [SKILL.md](D:\portfolio-harness.cursor\skills\secure-contain-protect\SKILL.md) AI Trends Integration:
  - Same known-issue note.

**Optional (defer):** If FP noise increases, add URL-context check in [sanitize_input.py](D:\portfolio-harness.cursor\scripts\sanitize_input.py) `scan_encoding_blocks`: when a match falls inside `http://` or `https://` URL, exclude from findings. Low priority.

---

## 3. create_foam_note SCP Gate

**Issue:** [create_foam_note](D:\portfolio-harness\local-proto\scripts\ai_trends_mcp.py) (lines 360-379) accepts user-provided `content` without SCP gate. Inconsistent with "contain all external content" policy.

**Fix:** Add SCP gate before writing:

- Import `run_pipeline` from `scp_utils` (or use existing `_scp_gate_for_summary` pattern).
- Before `note_path.write_text(body, ...)`, run `run_pipeline(content, sink="tool_output", options={"quarantine_on_block": False})`.
- If `blocked`, return error JSON; otherwise use `result` (contained content) for the note body.
- Fallback: if `scp_utils` import fails, pass through (same as current behavior for backward compat).

---

## 4. summarize_content Path Documentation

**Issue:** Path resolution logic (lines 324-328) not documented. Users may pass full path, relative path, or `YYYY-MM-DD/filename`.

**Current logic:**

```python
path = Path(content_path)
if not path.exists():
    base = _get_base_path()
    path = base / "raw" / path
```

So: full path works; if not found, treats `content_path` as `raw/<content_path>` (e.g. `2026-03-14/youtube_foo.txt` or just `youtube_foo.txt`).

**Fix:** Add "summarize_content" subsection under Tools in [AI_TRENDS_MCP.md](D:\portfolio-harness\local-proto\docs\AI_TRENDS_MCP.md):

- **Path format:** Full path to file, or path relative to `raw/` (e.g. `2026-03-14/youtube_David_Shapiro_xxx.txt` or `youtube_xxx.txt`). If path does not exist, resolved as `{base}/raw/{content_path}`.

---

## Summary of Changes


| File                                                                           | Change                                                       |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| [scp_mcp.py](D:\portfolio-harness\local-proto\scripts\scp_mcp.py)              | Add AI_TRENDS_CONFIG support in _get_ai_trends_base          |
| [ai_trends_mcp.py](D:\portfolio-harness\local-proto\scripts\ai_trends_mcp.py)  | Add SCP gate to create_foam_note                             |
| [AI_TRENDS_MCP.md](D:\portfolio-harness\local-proto\docs\AI_TRENDS_MCP.md)     | Config note, reversal FP note, summarize_content path format |
| [SKILL.md](D:\portfolio-harness.cursor\skills\secure-contain-protect\SKILL.md) | Reversal FP known-issue note                                 |


**Deferred:** encoding_blocks URL whitelist in sanitize_input.py (only if audit noise becomes high).