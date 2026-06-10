# TruffleHog baseline summary (2026-06-10)

Run locally from repo root (do **not** commit scan output — it may echo verified secrets):

```powershell
trufflehog filesystem . --results=verified,unknown
trufflehog filesystem . --results=verified,unknown --exclude-paths=config/trufflehog-exclude.txt
```

| Scan | verified | unverified | Notes |
|------|----------|------------|-------|
| No excludes | 1 | 25 | Observed 2026-06-10 on working tree |
| Narrow excludes | 1 | 25 | Path excludes do not remove history hits |

## Verified (Gate 1 blocker)

- **Detector:** Adzuna
- **Source:** `job-automation-service/.env.backup` (gitignored on main; present in git history and may exist locally)
- **Remediation:** rotate keys at https://developer.adzuna.com/ → `scripts/purge-adzuna-history.ps1 -Execute` → `git push --force-with-lease origin main`

## Unverified noise (Gate 2)

- Dev compose `${*_POSTGRES_PASSWORD:-changeme}` — excluded on **schedule** only via [`config/trufflehog-exclude.txt`](../../config/trufflehog-exclude.txt)
- Docs: five root `docs/*.md` URIs updated to `${POSTGRES_PASSWORD}` placeholders (2026-06-10)
- Remaining: `education-service/docs/DEPLOYMENT.md` example URI (optional follow-up)

Path excludes do **not** reduce verified Adzuna count; only history purge clears it.
