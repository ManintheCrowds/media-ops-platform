# Public Repo Audit Checklist

Use this checklist when preparing or maintaining a repository for public/portfolio use. Run from **each repo root** (e.g. `portfolio-harness`, `software`, `Arc_Forge`, `moltbook-watchtower`). Tick items as you complete them.

**Scope:** portfolio-harness (and in-repo projects: obsidian_cursor_integration, WatchTower_main), software, Arc_Forge, moltbook-watchtower.

**Latest results:** [PUBLIC_REPO_AUDIT_RESULTS.md](PUBLIC_REPO_AUDIT_RESULTS.md)  
**Pending actions status (later version):** [PENDING_ACTIONS_STATUS.md](PENDING_ACTIONS_STATUS.md) — Done/Pending snapshot from the consolidated pending-action-items plan.

---

## 1. Security & secrets

| Check | Command / action | Notes |
|-------|-------------------|--------|
| No secrets in repo or history | `gitleaks detect --source . --no-git` (or run existing `.github/workflows/security-gitleaks.yml`) | Fix any findings; ensure `.env` is in `.gitignore`. |
| No TruffleHog findings | `trufflehog filesystem .` (if installed) or use existing security-trufflehog workflow | Optional; gitleaks often sufficient. |
| Dependency vulnerabilities | From repo root: `pip audit` (Python) or `npm audit` (Node) | Fix or document accepted risks in SECURITY.md or README. |
| No default/placeholder secrets in code | Grep: `rg -i "password\s*=\s*['\"]?(changeme|secret|todo|your)" --type py` (adjust for your stacks) | Remove or move to env-only. |
| Auth and exposure | Manual: no debug endpoints or verbose stack traces in production code paths | Especially in FastAPI/Flask `debug=` and error handlers. |

**Key files:** `.gitignore` (must include `.env`, `*.env`, `venv/`, `.venv/`, `__pycache__/`), `.env.example` (no real secrets).

---

## 2. First-impression hygiene

| Check | Command / action | Notes |
|-------|-------------------|--------|
| LICENSE present | File exists: `LICENSE` or `LICENSE.md` | Use MIT, Apache 2.0, or "Proprietary — All rights reserved." |
| .gitignore complete | File exists; contains: `.env`, `venv/`, `.venv/`, `__pycache__/`, `*.pyc`, `.mypy_cache/`, `node_modules/` (if Node) | Avoid committing build artifacts and secrets. |
| No internal names in code/docs | `rg -i "SCC-Dev|internal|TODO:\s*remove|do not commit" --type-add 'code:*.{py,js,ts,yml,yaml,md}' -t code` (optional) | Remove machine names, internal URLs, "remove before public" TODOs. |
| README is the entrypoint | File exists: `README.md` (or `readme.md` normalized to `README.md`) | Per [PORTFOLIO_README_TEMPLATE.md](PORTFOLIO_README_TEMPLATE.md). |

**Key files:** `LICENSE`, `.gitignore`, `README.md`.

---

## 3. Runnable in under 5 minutes

| Check | Command / action | Notes |
|-------|-------------------|--------|
| Clone + deps + run | Follow README "Quick start" or "Install" in a clean directory | From clone: `git clone ... && cd <repo> && <steps from README>`. |
| Requirements pinned | `requirements.txt` or `pyproject.toml` (Python); `package-lock.json` / `yarn.lock` (Node) | Prefer pinned or lockfile for reproducible runs. |
| Env documented | `.env.example` exists and README lists required env vars (e.g. `SECRET_KEY`, `DATABASE_URL`, API keys) | No hidden assumptions. |
| Supported runtime stated | README mentions e.g. "Python 3.11+", "Node 18+" | So contributors know what to install. |

**Key files:** `README.md`, `requirements.txt` / `pyproject.toml` / `package.json`, `.env.example`.

---

## 4. Consistency across repos

| Check | Command / action | Notes |
|-------|-------------------|--------|
| README shape | README has: title + tagline, one-line "why", (optional) problem/solution/impact, quick start, testing, license | Use [PORTFOLIO_README_TEMPLATE.md](PORTFOLIO_README_TEMPLATE.md). |
| Docs vs code | README "run" commands match current entrypoints (e.g. `uvicorn app.main:app`, `pytest tests/`) | Grep for the command in README and verify in repo. |
| One CONTRIBUTING or "How to develop" | Optional: `CONTRIBUTING.md` or a "Development" section in README | For repos you’d accept contributions to. |

**Key files:** `README.md`, optionally `CONTRIBUTING.md`.

---

## 5. Trust & maintainability

| Check | Command / action | Notes |
|-------|-------------------|--------|
| CI runs tests | Push/PR triggers test run (e.g. `.github/workflows/*.yml`) | Add a "Tests" badge to README if desired. |
| Tests run locally | From repo root: `pytest` or `python -m pytest tests/` (Python) / `npm test` (Node) | Document in README. |
| Changelog or "What’s new" | Optional: `CHANGELOG.md` or a "Recent changes" subsection in README | Signals active maintenance. |
| No stale "coming soon" | Grep README/docs for "TBD", "coming soon", "your license here" | Replace with real content or remove. |

**Key files:** `.github/workflows/`, `README.md`, optional `CHANGELOG.md`.

---

## 6. Portfolio narrative

| Check | Command / action | Notes |
|-------|-------------------|--------|
| One diagram or screenshot | README or `docs/` contains at least one Mermaid diagram or screenshot (UI/dashboard/flow) | Per [README](README.md) and template. |
| Problem / solution / impact | README or case study states problem, solution, and impact (with numbers if possible) | See CaptionPipeline export kit in this folder. |
| Tech stack explicit | README lists main technologies (e.g. FastAPI, PostgreSQL, Docker) | One line or short list near top. |

**Key files:** `README.md`, `docs/`, `portfolio/` (for static site assets).

---

## 7. Commands quick reference (run from repo root)

**Python (most of your repos):**

```bash
# Dependency audit
pip install pip-audit
pip audit

# Tests
python -m pytest tests/ -v
# or
pytest tests/ -v
```

**Secrets (if gitleaks installed):**

```bash
gitleaks detect --source . --no-git
```

**Check key files exist:**

```powershell
# PowerShell (Windows)
@("README.md", "LICENSE", ".gitignore") | ForEach-Object { if (Test-Path $_) { "OK $_" } else { "MISSING $_" } }
```

```bash
# Bash
for f in README.md LICENSE .gitignore; do test -f "$f" && echo "OK $f" || echo "MISSING $f"; done
```

---

## 8. Per-repo notes

| Repo | Monorepo / multi-project | Focus |
|------|---------------------------|--------|
| **CodeRepositories** | Multi (obsidian_cursor_integration, WatchTower_main, etc.) | Root README = index; run audit on root and on each linked project folder. |
| **software** | Monorepo (platform + services) | One LICENSE/.gitignore at root; README hero + service links; run `pip audit` from root. |
| **Arc_Forge** | Multi (campaign_kb, workflow_ui, ObsidianVault scripts) | Run tests per component (see Arc_Forge README); single LICENSE at root. |
| **moltbook-watchtower** | Single-purpose | Standard single-root audit; `README.md` (not readme.md). |

---

## 9. Before/after making a repo public

- [ ] Run this checklist from the repo root.
- [ ] Fix all "MISSING" and high-priority security items.
- [ ] Re-run `gitleaks` / `pip audit` after fixes.
- [ ] Optional: add an entry to your troubleshooting or playbooks (e.g. CodeRepositories `.cursor/docs/TROUBLESHOOTING_AND_PLAYBOOKS.md`): "Public repo audit: run `software/docs/portfolio/PUBLIC_REPO_AUDIT_CHECKLIST.md`."
