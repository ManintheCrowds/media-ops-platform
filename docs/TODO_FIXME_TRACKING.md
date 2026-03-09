# TODO/FIXME Tracking Document

This document tracks all TODO, FIXME, and HACK comments found in the codebase.

**Last Updated:** 2025-03-07  
**Total Items Found:** 6

## Summary

| Priority | Count | Status |
|----------|-------|--------|
| Low | 4 | Open |
| Medium | 2 | Open |
| High | 0 | - |

## Items

### 1. Arlo Module - Threading Hack
- **File:** `services/camera/arlo_module.py:306`
- **Type:** HACK
- **Context:** Comment about using a thread for asynchronous EventStream interface
- **Description:** "Since this interface is asynchronous, and this is a quick and dirty hack to get this working, I'm using a thread to listen to the EventStream."
- **Priority:** Medium
- **Estimated Effort:** 2-3 hours (refactor to proper async/await)
- **Status:** Open
- **Notes:** This is in the Subscribe() method. Consider refactoring to use proper async/await patterns instead of threads.

### 2. Arlo Module - Sleep Hack
- **File:** `services/camera/arlo_module.py:477`
- **Type:** HACK
- **Context:** Sleep to allow Ping() thread to process queued event
- **Description:** `# HACK: Take a quick nap here to give the Ping() method's thread a chance to get the queued event.`
- **Priority:** Medium
- **Estimated Effort:** 1-2 hours (proper event synchronization)
- **Status:** Open
- **Notes:** This is a race condition workaround. Should use proper event synchronization mechanisms.

### 3. Arlo Module - HandleEvents No-op
- **File:** `services/camera/arlo_module.py:501`
- **Type:** NOTE (mentions hack)
- **Context:** HandleEvents() calls Subscribe() again as a no-op
- **Description:** `# NOTE: Calling HandleEvents() calls Subscribe() again, which basically turns into a no-op. Hackie I know, but it cleans up the code a bit.`
- **Priority:** Low
- **Estimated Effort:** 30 min (documentation/clarification)
- **Status:** Open
- **Notes:** This is intentional design but could be better documented. Consider renaming or adding clearer documentation.

### 4. Arlo Module - Python 2.x Nonlocal Hack (StartStream)
- **File:** `services/camera/arlo_module.py:1677`
- **Type:** HACK
- **Context:** Workaround for Python 2.x lack of nonlocal keyword
- **Description:** `# nonlocal variable hack for Python 2.x.`
- **Priority:** Low
- **Estimated Effort:** 15 min (remove if Python 2.x support not needed)
- **Status:** Open
- **Notes:** Python 2.x is EOL. If we don't need Python 2.x support, this can be refactored to use proper `nonlocal` keyword.

### 5. Arlo Module - Python 2.x Nonlocal Hack (StopStream)
- **File:** `services/camera/arlo_module.py:1694`
- **Type:** HACK
- **Context:** Workaround for Python 2.x lack of nonlocal keyword
- **Description:** `# nonlocal variable hack for Python 2.x.`
- **Priority:** Low
- **Estimated Effort:** 15 min (remove if Python 2.x support not needed)
- **Status:** Open
- **Notes:** Python 2.x is EOL. If we don't need Python 2.x support, this can be refactored to use proper `nonlocal` keyword.

### 6. Pip Dependency Conflict Warnings
- **File:** `requirements.txt` (D:\software root)
- **Type:** TODO
- **Context:** Installing requirements alongside chromadb, daggr, gradio, mcp, ollama, theharvester, etc. causes pip dependency conflict warnings
- **Description:** Pip reports conflicts (e.g. httpx, uvicorn, aiohttp version mismatches) but install completes. See [DEPENDENCY_CONFLICTS.md](DEPENDENCY_CONFLICTS.md) for proposed solutions.
- **Priority:** Low
- **Estimated Effort:** 30 min (venv setup + README doc)
- **Status:** Open
- **Notes:** Recommendation: use virtual environment for D:\software and document in README.

## Quick Wins (Can be fixed immediately)

1. **Items 4 & 5** - Python 2.x hacks: If Python 2.x support is not required, these can be quickly refactored to use `nonlocal` keyword.
2. **Item 3** - Documentation: Add clearer comments explaining the intentional design.
3. **Item 6** - Dependency conflicts: Create venv and document activation in README (see [DEPENDENCY_CONFLICTS.md](DEPENDENCY_CONFLICTS.md)).

## Medium Priority (Require investigation)

1. **Item 1** - Threading hack: Requires understanding the Arlo API event stream and refactoring to async/await.
2. **Item 2** - Sleep hack: Requires proper event synchronization mechanism.

## Notes

- Most HACK comments are in the Arlo module, which appears to be a third-party integration that may have been adapted.
- The Python 2.x hacks (items 4 & 5) are likely safe to remove if Python 3.x+ is the minimum requirement.
- The threading-related hacks (items 1 & 2) would benefit from proper async/await refactoring but require more careful testing.

