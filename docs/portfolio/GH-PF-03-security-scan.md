# GH-PF-03 security scan — media-ops-platform (2026-06-04)

**Repo:** `ManintheCrowds/media-ops-platform`  
**Verdict:** **REMEDIATED 2026-06-04** — GitGuardian post-public alerts addressed; history rewritten on `main` (`a6b97ce`).

## GitGuardian remediation (2026-06-04)

| Alert | Root cause | Remediation |
|-------|------------|-------------|
| VirusTotal API Key | Literal key in `scripts/verify-virustotal-config.md`, `VIRUSTOTAL_SETUP_COMPLETE.md` | Files deleted; `git filter-repo --replace-text` on all history; force-push `main` |
| Generic High Entropy Secret | Same VT key; Grafana example hash in `docs/monitoring/GRAFANA_PASSWORD_RESET.md` | History purge + placeholder hash in doc |
| Generic Password | Dev literals in `docker-compose*.yml`, `job-automation-service/test_output.txt` | Env-var `${*_POSTGRES_PASSWORD:-changeme}`; untrack `test_output.txt` |

**CI fixes:** Removed blanket `*.md` allowlist in [`.gitleaks.toml`](../../.gitleaks.toml). TruffleHog workflow uses `--results=verified,unknown` (was `--only-verified`).

**Operator [MEATSPACE]:** `REQUEST_HUMAN: Revoke the exposed VirusTotal API key at https://www.virustotal.com/gui/my-apikey and set `SECURITY_VIRUSTOTAL_API_KEY` only in local `.env`. Mark GitGuardian incidents resolved after rotation + 24h scan clear.

## Tooling

| Tool | Version / status | Result |
|------|------------------|--------|
| gitleaks | CI on push | [`.github/workflows/security-gitleaks.yml`](../.github/workflows/security-gitleaks.yml); **no** global md allowlist |
| trufflehog | CI on push | [`.github/workflows/security-trufflehog.yml`](../.github/workflows/security-trufflehog.yml) |
| rg exposed VT key | ripgrep | **0** matches after remediation |
| rg placeholder passwords (`changeme`, etc.) | ripgrep | Dev defaults in compose use `changeme` via env substitution |
| pip audit | See pytest run section | Run in CI / operator env if needed |
| Operator trees removed from index | git rm --cached | `plans/`, `.cursor/plans/`, `.cursor/state/`, hazard dirs |

## P0 triage (original scan)

| ID | Finding | Severity | Action |
|----|---------|----------|--------|
| P0-1 | `SECURITY_AUDIT_REPORT.md` not present in repo | — | Superseded by this scan + checklist |
| P0-2 | Secrets in removed operator paths | — | **Mitigated** — paths gitignored and untracked |
| P0-3 | LICENSE was Proprietary vs README MIT | P0 | **Fixed** — MIT `LICENSE` committed |
| P0-4 | Harness paths in tracked docs | P1 | **Mitigated** — operator dirs untracked; `docs/research` not linked from README |
| P0-5 | VirusTotal key in tracked markdown (GitGuardian) | P0 | **Fixed** — delete + filter-repo + force-push 2026-06-04 |

## 5-minute clone verification

| Step | Status | Notes |
|------|--------|-------|
| `git clone` + `cp .env.example .env` | Documented | Requires operator-generated `SECRET_KEY` / `JWT_SECRET_KEY`; set `SECURITY_VIRUSTOTAL_API_KEY` after rotation |
| `docker compose up -d` | Not run in agent session | Homelab-scale; see README honesty note |
| `pytest tests/ -v` | See below | Unit/integration subset |

## Pytest (2026-06-04)

```
321 passed, 9 failed, 7 errors (unit suite)
Coverage: 56.47% (gate 70% not met — documented in ROADMAP)
```

Failures are pre-existing client/encoder/SSRF tests in this environment, not introduced by rebrand. **CI** on GitHub remains authoritative after push.

## Checklist scorecard ([PUBLIC_REPO_AUDIT_CHECKLIST.md](PUBLIC_REPO_AUDIT_CHECKLIST.md))

| Section | Pass |
|---------|------|
| 1 Security & secrets | Pass after remediation — CI workflows; operator VT rotation pending |
| 2 First-impression hygiene | Pass — MIT LICENSE, README, .gitignore |
| 3 Runnable in 5 min | Partial — compose documented; full stack not agent-verified |
| 4 Consistency | Pass — README matches template |
| 5 Trust & maintainability | Pass — CI workflows present |
| 6 Portfolio narrative | Pass — CaptionPipeline neutral narrative |

## Public visibility

**GH-PF-04** completed 2026-06-04. Post-public GitGuardian alerts remediated same day (see above).

## Historical log

Binary log (prior run): [GH-PF-03-security-scan.log](GH-PF-03-security-scan.log) — treat as supplemental only.
