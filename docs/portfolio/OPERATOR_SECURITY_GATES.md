# Operator security gates — media-ops-platform

**Context:** [GH-PF-03-security-scan.md](GH-PF-03-security-scan.md) · [2026-06-23 audit](https://github.com/ManintheCrowds/MiscRepos/blob/main/local-proto/docs/adhoc/2026-06-23-media-ops-pf04-audit.md)

These steps require human approval. Agents must not force-push or rotate third-party keys without operator confirmation.

---

## Gate 1 — Adzuna history purge

**Status (2026-06-23):** Not executed. Local TruffleHog: `verified=1`. Nightly scheduled TruffleHog CI **failing**.

1. `REQUEST_HUMAN`: Rotate Adzuna API keys at https://developer.adzuna.com/
2. On `main`, from repo root:
   ```powershell
   .\scripts\purge-adzuna-history.ps1 -Execute
   ```
3. Local verify: TruffleHog `verified=0`
4. `git push --force-with-lease origin main`
5. Confirm GitHub Actions `trufflehog-strict` and scheduled job green

**Script:** [scripts/purge-adzuna-history.ps1](../../scripts/purge-adzuna-history.ps1)  
**Replacements:** [config/filter-repo-adzuna-replacements.txt](../../config/filter-repo-adzuna-replacements.txt)

---

## VirusTotal API key (active)

**Status:** **Done** — operator rotated 2026-06-23; continue using the new token locally.

**Paste the key here (never commit):**

```
C:\Users\Dell\Documents\GitHub\software\.env
```

Line in that file:

```
SECURITY_VIRUSTOTAL_API_KEY=<your-new-key>
```

If `.env` does not exist yet:

```powershell
cd C:\Users\Dell\Documents\GitHub\software
Copy-Item .env.example .env
# then edit .env and set SECURITY_VIRUSTOTAL_API_KEY
```

**How it flows:** root `.env` → `docker-compose.yml` → `security-service` (`SECURITY_` prefix → `virustotal_api_key` in [security_service/config.py](../../security-service/security_service/config.py)).

**Host-side DB tests** (scripts run on Windows, not in container) also need:

```
SECURITY_DATABASE_URL=postgresql://platform:changeme@localhost:5432/platform
```

Match `POSTGRES_PASSWORD` in `.env`. In-container services use `@postgres:5432` via compose `SECURITY_DATABASE_URL` (fixed 2026-06-24 in [docker-compose.yml](../../docker-compose.yml)).

**Full stack verify (2026-06-24):**

```powershell
cd C:\Users\Dell\Documents\GitHub\software
docker compose up -d postgres redis security-service
# Host test (set SECURITY_DATABASE_URL if not in .env):
$env:SECURITY_DATABASE_URL='postgresql://platform:changeme@localhost:5432/platform'
python scripts/test-virustotal-integration.py
Invoke-WebRequest http://localhost:8011/health -UseBasicParsing   # {"status":"healthy","service":"security-service"}
# OpenAPI: http://localhost:8011/docs
```

**Verify (API key only):**

```powershell
cd C:\Users\Dell\Documents\GitHub\software
python scripts/test-virustotal-integration.py
```

---

## Branch protection on `main`

**Status (2026-06-23):** Not configured (API returns 404).

GitHub → **Settings → Branches → Add rule** for `main`:

- Require status checks: **`trufflehog-strict`**, **`gitleaks`**
- (Optional) Require `Tests` workflow

Branch protection cannot be applied via API on this org tier; use GitHub UI.

---

## Optional — pip-audit

```powershell
pip install pip-audit
pip-audit -r requirements.txt
```

Document accepted risks in [docs/SECURITY.md](../SECURITY.md) if any remain.
