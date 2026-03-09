# Pip Dependency Conflict Warnings

When installing D:\software requirements alongside other tools (chromadb, daggr, gradio, mcp, ollama, theharvester, etc.), pip may report dependency conflicts. The install still completes; these are warnings, not blockers.

## Proposed Solutions

| Solution | Effort | Trade-off |
|----------|--------|-----------|
| **A. Virtual environment** | Low | `python -m venv .venv` then `pip install -r requirements.txt`. Isolates D:\software from global packages. Recommended for development. |
| **B. Project-specific venv** | Low | Add `.venv/` to `.gitignore`, document `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows) in README. |
| **C. Relax version pins** | Medium | Loosen D:\software pins (e.g. `httpx>=0.25.2`, `uvicorn>=0.24.0`) to allow newer versions. Risk: may break compatibility with older code. |
| **D. Ignore warnings** | None | If conflicting tools still work, no action. Pip does not block install. |
| **E. Separate envs per tool** | High | Use `uv`, `poetry`, or `conda` with per-project lockfiles. Best isolation, more setup. |

**Recommendation**: A + B — use a venv for D:\software and document it.
