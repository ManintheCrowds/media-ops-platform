---
name: README Repo Sync Update
overview: "Fix READMEs that are out of sync with their repository contents: correct software platform→app references and run commands, fix portfolio-harness PORTFOLIO.md link, and expand prusa_XL_soft README with structure, dependencies, and missing features."
todos: []
isProject: false
---

# README Repo Sync Update

## Audit Summary

An explore-agent audit compared each README to its repository. Findings:


| Repo                    | Critical issues                                                  | Minor issues                                                    |
| ----------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------- |
| **software**            | platform→app mismatch; run command fails                         | Project structure diagram wrong                                 |
| **portfolio-harness**   | PORTFOLIO.md links `readme.md` (lowercase)                       | —                                                               |
| **prusa_XL_soft**       | No requirements.txt; install steps vague; structure undocumented | Redis, Flask-Limiter, Flask-Caching, monitoring/ not documented |
| **Arc_Forge**           | None                                                             | —                                                               |
| **moltbook-watchtower** | None                                                             | —                                                               |
| **local-first**         | None                                                             | AGENTS.md not in contents table                                 |


---

## Phase 1: software — Fix platform→app Mismatch

**Problem:** Code lives in `app/`, not `platform/`. README and Dockerfile disagree; run command fails.

**Files:** [software/README.md](D:\software\README.md)

**Edits:**

1. **Project structure (lines 305–331):** Replace `platform/` with `app/`:
  - `platform/` → `app/`
  - `platform/main.py` → `app/main.py`
  - `platform/config.py` → `app/config.py`
  - etc.
2. **Run command (line 360):**
  - From: `uvicorn platform.main:app --reload`
  - To: `uvicorn app.main:app --reload`
3. **Adding New Services (line 367):**
  - From: `platform/api/gateway.py`
  - To: `app/api/gateway.py`

**Verification:** Dockerfile uses `app.main:app`; `app/main.py` exists.

---

## Phase 2: portfolio-harness — Fix PORTFOLIO.md Link

**Problem:** `docs/PORTFOLIO.md` links to `moltbook-watchtower/readme.md` (lowercase). Actual file is `README.md`; fails on case-sensitive systems.

**File:** [portfolio-harness/docs/PORTFOLIO.md](D:\portfolio-harness\docs\PORTFOLIO.md)

**Edit (line 17):**

- From: `../moltbook-watchtower/readme.md`
- To: `../moltbook-watchtower/README.md`

**Note:** Main [portfolio-harness/README.md](D:\portfolio-harness\README.md) was already updated to `README.md` in the prior identity plan.

---

## Phase 3: prusa_XL_soft — Expand README

**Problem:** No `requirements.txt` or `pyproject.toml`; install steps vague; structure and features undocumented. Code uses Redis, Flask-Limiter, Flask-Caching, `monitoring/`, `alembic/`, `services/`.

**File:** [prusa_XL_soft/README.md](D:\prusa_XL_soft\README.md)

**Edits:**

1. **Add requirements.txt** (create file): Extract deps from `app/` imports: flask, flask-limiter, flask-caching, sqlalchemy, etc. Check `app/__init__.py`, `app/api/`, `app/cli/` for imports.
2. **Update Quick start:** Add explicit install step:

```markdown
   pip install -r requirements.txt
   

```

   (Or document `pip install -e .` if adding pyproject.toml instead.)

1. **Add Project structure section:**

```markdown
   ## Project structure
   - `app/` — Flask app, API, CLI (kb seed, troubleshoot)
   - `services/` — PrusaLink, OctoPrint, collector, knowledge_base
   - `alembic/` — DB migrations
   - `monitoring/` — Grafana dashboards, alerts
   - `scripts/` — Smoke test, utilities
   

```

1. **Update Tech stack line:** Add Redis, Flask-Limiter, Flask-Caching.
2. **Document optional components:** Redis (for caching), `monitoring/` (Grafana).

**Pre-requisite:** Create `requirements.txt` from actual imports. If the project uses a different dependency mechanism (e.g. only in Docker), document that instead.

---

## Phase 4: local-first — Optional AGENTS.md

**File:** [local-first/README.md](D:\local-first\README.md)

**Edit:** Add `AGENTS.md` to the Contents table if it exists and is relevant for AI agents.

---

## Implementation Order

1. software: platform→app fixes (3 edits)
2. portfolio-harness: PORTFOLIO.md link fix (1 edit)
3. prusa_XL_soft: Create requirements.txt (if missing), then expand README
4. local-first: Add AGENTS.md to table (optional)

---

## Verification

- Run `uvicorn app.main:app --reload` from software root — should start
- Click PORTFOLIO.md moltbook link — should resolve
- Run `pip install -r requirements.txt` and `flask run` from prusa_XL_soft — should work (after requirements.txt exists)

