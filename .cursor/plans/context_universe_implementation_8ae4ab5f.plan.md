---
name: Context Universe Implementation
overview: "Implement the four \"context universe\" components: (1) coding standards matrix with two lookup tables, (2) explicit \"retrieve before generate\" in the Code Generation prompt, (3) external reference repos as curated links, and (4) Pattern Extraction prompt. All changes are in D:\\software."
status: pending
priority: 4
phase: later
todos: []
isProject: false
---

# Context Universe Implementation Plan

## Summary

Add a structured coding standards matrix and enforce "retrieve before generate" in the Code Generation prompt. Integrate external reference repos and a Pattern Extraction prompt for internalizing new repositories into reusable pattern docs.

---

## 1. Create `docs/coding_standards_matrix.md`

**New file.** Purpose: single lookup table for AI agents to find standards and reference implementations before writing code.

### Table 1: Standards by Domain


| Domain             | Standard             | Description                | Reference                                                                                  |
| ------------------ | -------------------- | -------------------------- | ------------------------------------------------------------------------------------------ |
| Python style       | PEP 8                | Formatting rules           | [https://peps.python.org/pep-0008/](https://peps.python.org/pep-0008/)                     |
| Python typing      | PEP 484              | Type hints                 | [https://peps.python.org/pep-0484/](https://peps.python.org/pep-0484/)                     |
| API design         | OpenAPI 3.1          | REST schema design         | [https://spec.openapis.org/oas/v3.1.0](https://spec.openapis.org/oas/v3.1.0)               |
| Web security       | OWASP Top 10         | Web security risks         | [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/)           |
| Container security | CIS Docker Benchmark | Secure container configs   | [https://www.cisecurity.org/benchmark/docker](https://www.cisecurity.org/benchmark/docker) |
| Database design    | PostgreSQL docs      | Indexing, normalization    | [https://www.postgresql.org/docs/current/](https://www.postgresql.org/docs/current/)       |
| Python linting     | Ruff rules           | Static analysis            | [https://docs.astral.sh/ruff/](https://docs.astral.sh/ruff/)                               |
| SQL migrations     | Alembic              | Schema migration practices | [https://alembic.sqlalchemy.org/](https://alembic.sqlalchemy.org/)                         |
| Async Python       | asyncio / httpx      | Async patterns             | [https://www.python.org/dev/peps/pep-0492/](https://www.python.org/dev/peps/pep-0492/)     |


### Table 2: Pattern to Reference Implementation


| Pattern          | Internal Reference                                                                                                         | External Reference                                                                                                       |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Service Client   | [AI_PATTERNS.md](AI_PATTERNS.md) §1; `services/file_storage/seafile_client.py`, `services/media_server/jellyfin_client.py` | [encode/httpx](https://github.com/encode/httpx)                                                                          |
| FastAPI + Auth   | [AI_PATTERNS.md](AI_PATTERNS.md) §2; `app/api/gateway.py`, `app/auth/oauth2.py`                                            | [tiangolo/full-stack-fastapi-postgresql](https://github.com/tiangolo/full-stack-fastapi-postgresql)                      |
| API design       | [AI_PATTERNS.md](AI_PATTERNS.md) §2                                                                                        | [encode/starlette](https://github.com/encode/starlette)                                                                  |
| Database models  | [AI_PATTERNS.md](AI_PATTERNS.md) §3; `app/models/`                                                                         | [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy), [alembic/alembic](https://github.com/alembic/alembic) |
| Configuration    | [AI_PATTERNS.md](AI_PATTERNS.md) §6; `app/config.py`, `services/*/config.py`                                               | [pydantic/pydantic-settings](https://github.com/pydantic/pydantic-settings)                                              |
| Testing          | [AI_PATTERNS.md](AI_PATTERNS.md) §4; `tests/`                                                                              | [pytest-dev/pytest](https://github.com/pytest-dev/pytest)                                                                |
| Docker / Compose | `docker-compose.yml`, `nginx/`                                                                                             | [docker/awesome-compose](https://github.com/docker/awesome-compose)                                                      |


### Document structure

- **Purpose** section: "Lookup table for AI agents. Consult before generating code."
- **Related Documents**: AI_PATTERNS.md, AI_CODEBASE_MAP.md, AI_PROMPT_LIBRARY.md
- **Usage**: "Before writing code, identify relevant domain(s), look up standards and reference implementations, then generate."

---

## 2. Update Code Generation Prompt (Prompt 9)

**File:** [docs/AI_PROMPT_LIBRARY.md](D:\software\docs\AI_PROMPT_LIBRARY.md) (lines 434–486)

**Change:** Add a mandatory "Retrieve Before Generate" block at the top of the template, before "Generate code for the following:".

Insert after the opening backticks:

```
RETRIEVE BEFORE GENERATE (required):
1. Consult docs/coding_standards_matrix.md for relevant domain standards
2. Identify applicable patterns and reference implementations (internal + external)
3. Read AI_PATTERNS.md Section(s) for the pattern(s) you will use
4. Locate similar code in codebase via AI_CODEBASE_MAP.md
5. Summarize: Standards applied | Reference code used | Design plan
6. Only then proceed to implementation

Output sections (in order):
- Standards applied (from matrix)
- Reference code used (internal paths + external links if consulted)
- Design plan (brief)
- Implementation
```

**Also:** Add `docs/coding_standards_matrix.md` to the Reference Documents list in Prompt 9.

---

## 3. Add Pattern Extraction Prompt (Prompt 15)

**File:** [docs/AI_PROMPT_LIBRARY.md](D:\software\docs\AI_PROMPT_LIBRARY.md)

**Location:** After Prompt 14 (Emergency Rollback), before "Section: Prompt Usage Guidelines".

**Content:**

```
## Prompt 15: Pattern Extraction Prompt

**When to Use**: When internalizing a new repository into reusable engineering pattern docs.

**Template**:

```

Analyze the following repository and extract a reusable engineering pattern document.

Repository: {repo_path_or_url}
Target output: Add to docs/ or update AI_PATTERNS.md

Extract:

1. Directory structure
2. Architecture pattern (e.g., layered, modular, gateway)
3. Dependency management (requirements.txt, pyproject.toml)
4. Testing approach (framework, fixtures, mocking)
5. Security patterns (auth, validation, rate limiting)
6. API conventions (REST, OpenAPI, error codes)

Output format:

- pattern: {short_name}
- structure: {directory tree}
- principles: [list]
- benefits: [list]
- reference_files: [paths or URLs]
- checklist: [items for new implementations]

Convert output into a markdown document suitable for AI_PATTERNS.md or a new docs/coding_standards_matrix.md row.

```

**Integration:** Add row to "When to Use Each Prompt" table and "Prompt Combination Strategies" (e.g., "Pattern Extraction + Code Generation: Extract pattern from new repo, then use for future code").
```

---

## 4. Update AI_DOCUMENTATION_INDEX.md

**File:** [docs/AI_DOCUMENTATION_INDEX.md](D:\software\docs\AI_DOCUMENTATION_INDEX.md)

- Add row to Document Overview table: **coding_standards_matrix.md** | Standards and reference lookup | Before generating code | AI agents | 2–5 min
- Add to "I need to write code" path: "Consult [coding_standards_matrix.md](coding_standards_matrix.md) for standards and references"
- Add to Maintenance "Update Triggers": "New standards or reference repos → Update coding_standards_matrix.md"
- Add to See Also section

---

## 5. Update .cursorrules (optional but recommended)

**File:** [.cursorrules](D:\software.cursorrules)

Add one line to "See Also" or "Code Style & Practices":

- Before generating code, consult `docs/coding_standards_matrix.md` for standards and reference implementations.

---

## File Change Summary


| File                              | Action                                                 |
| --------------------------------- | ------------------------------------------------------ |
| `docs/coding_standards_matrix.md` | Create (new)                                           |
| `docs/AI_PROMPT_LIBRARY.md`       | Edit: Prompt 9 retrieval block, Prompt 15, usage table |
| `docs/AI_DOCUMENTATION_INDEX.md`  | Edit: add matrix to overview, paths, maintenance       |
| `.cursorrules`                    | Edit: add matrix reference (optional)                  |


---

## Validation

- All links in coding_standards_matrix.md resolve
- Prompt 9 explicitly requires retrieval before implementation
- Prompt 15 follows existing prompt structure (When to Use, Template, Integration)
- AI_DOCUMENTATION_INDEX cross-references updated

