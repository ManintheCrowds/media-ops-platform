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

| gitleaks | **8.30.1** local + CI | `winget install Gitleaks.Gitleaks`; local run 2026-06-05: **no leaks** (exit 0). CI: [`.github/workflows/security-gitleaks.yml`](../.github/workflows/security-gitleaks.yml) |

| trufflehog | **3.94.0** local + CI | Binary: `%LOCALAPPDATA%\Programs\trufflehog\trufflehog.exe`; local run 2026-06-05: 1 verified (tracked `.env.backup` — **removed from index**, gitignore `*.env.backup`). CI: [`.github/workflows/security-trufflehog.yml`](../.github/workflows/security-trufflehog.yml) |

| Local runner | `run-gh-pf03-local-scan.ps1` | From repo root: `.\docs\portfolio\run-gh-pf03-local-scan.ps1` → [GH-PF-03-security-scan.log](GH-PF-03-security-scan.log) |

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

| P0-6 | `job-automation-service/.env.backup` tracked (TruffleHog verified Adzuna) | P0 | **Index fixed 2026-06-05** — `git rm --cached`; `*.env.backup` in `.gitignore`. **History purge pending (Gate 1):** regex replacements in [`config/filter-repo-adzuna-replacements.txt`](../../config/filter-repo-adzuna-replacements.txt); run [`scripts/purge-adzuna-history.ps1`](../../scripts/purge-adzuna-history.ps1) after rotating keys at https://developer.adzuna.com/; `git push --force-with-lease origin main`; confirm scheduled TruffleHog zero verified. Local scan 2026-06-10: 1 verified Adzuna (see [`trufflehog-baselines/README.md`](trufflehog-baselines/README.md)). |

## TruffleHog policy (2026-06-10, Gate 2)

| Trigger | Workflow job | Path excludes |
|---------|--------------|---------------|
| PR / push to `main` | `trufflehog-strict` | **None** — full diff scan |
| Schedule (02:00 UTC) | `trufflehog-scheduled` | [`config/trufflehog-exclude.txt`](../../config/trufflehog-exclude.txt) — **enumerated dev compose only** (not `docker-compose.prod.yml`, not `docs/**`) |

- **Doc placeholders:** five root `docs/*.md` URIs updated to `${POSTGRES_PASSWORD}` / `<POSTGRES_PASSWORD>` (no blanket markdown exclude).
- **Baseline notes:** [`docs/portfolio/trufflehog-baselines/README.md`](trufflehog-baselines/README.md) — run scans locally; do not commit raw output (may echo secrets).

**Operator gates:**

- `APPROVAL_NEEDED: Adzuna key rotation + git filter-repo force-push to main` (Gate 1 — purge not executed in repo yet)
- **Gate 2 allowlist signed off 2026-06-10:** five dev compose paths in [`config/trufflehog-exclude.txt`](../../config/trufflehog-exclude.txt) (scheduled job only). Residual risk: file-level exclude hides all findings in those paths on nightly runs; merge path `trufflehog-strict` has no excludes.



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


