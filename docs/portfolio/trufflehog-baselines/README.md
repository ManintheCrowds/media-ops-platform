# TruffleHog baseline summary (2026-06-10)

## Scheduled known findings (2026-11-09)

The nightly job matches the known exposed credential to an expiring baseline instead of failing whenever verification returns a non-401. Entries expire 2026-11-23. After confirmed account closure they become revoked-history suppressions (`closed_on` plus an evidence link). Rewriting history is out of scope and needs separate owner approval. See [trufflehog-scheduled-known-findings.md](../../security/trufflehog-scheduled-known-findings.md).



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
- **Historical Gate 1 plan:** rotate the key, then rewrite history. That rewrite is not the nightly control. The scheduled job uses the expiring baseline described above. A history rewrite still needs separate owner approval.

## Unverified noise (Gate 2)

- Dev compose `${*_POSTGRES_PASSWORD:-changeme}` — excluded on **schedule** only via [`config/trufflehog-exclude.txt`](../../config/trufflehog-exclude.txt)
- Docs: five root `docs/*.md` URIs updated to `${POSTGRES_PASSWORD}` placeholders (2026-06-10)
- Remaining: `education-service/docs/DEPLOYMENT.md` example URI (optional follow-up)

Path excludes do **not** remove this credential from history. The scheduled matcher accepts only its baselined locations until they expire. A verified result still fails the job.
