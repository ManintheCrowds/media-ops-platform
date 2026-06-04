# GH-PF-03 security scan — media-ops-platform (2026-06-04)

**Repo:** `ManintheCrowds/media-ops-platform` (rename from `software`; operator confirms in GitHub Settings)  
**Verdict:** **GO with conditions** — no P0 secrets in tracked public tree; coverage/test debt documented; operator completes GitHub rename (if `gh` not run) + **GH-PF-04** (public).

## Tooling

| Tool | Version / status | Result |
|------|------------------|--------|
| gitleaks | Not installed locally | Rely on [`.github/workflows/security-gitleaks.yml`](../.github/workflows/security-gitleaks.yml) on push |
| trufflehog | Not run locally | Rely on [`.github/workflows/security-trufflehog.yml`](../.github/workflows/security-trufflehog.yml) |
| rg placeholder passwords (`changeme`, etc.) | ripgrep | **0** matches in `*.py` |
| rg high-entropy tokens | ripgrep | **1** doc example in `API.md` (`eyJ...` truncated JWT sample) — **false positive** |
| pip audit | See pytest run section | Run in CI / operator env if needed |
| Operator trees removed from index | git rm --cached | `plans/`, `.cursor/plans/`, `.cursor/state/`, hazard dirs |

## P0 triage

| ID | Finding | Severity | Action |
|----|---------|----------|--------|
| P0-1 | `SECURITY_AUDIT_REPORT.md` not present in repo | — | Superseded by this scan + checklist |
| P0-2 | Secrets in removed operator paths | — | **Mitigated** — paths gitignored and untracked |
| P0-3 | LICENSE was Proprietary vs README MIT | P0 | **Fixed** — MIT `LICENSE` committed |
| P0-4 | Harness paths in tracked docs | P1 | **Mitigated** — operator dirs untracked; `docs/research` not linked from README |

## 5-minute clone verification

| Step | Status | Notes |
|------|--------|-------|
| `git clone` + `cp .env.example .env` | Documented | Requires operator-generated `SECRET_KEY` / `JWT_SECRET_KEY` |
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
| 1 Security & secrets | Conditional — CI workflows; local gitleaks N/A |
| 2 First-impression hygiene | Pass — MIT LICENSE, README, .gitignore |
| 3 Runnable in 5 min | Partial — compose documented; full stack not agent-verified |
| 4 Consistency | Pass — README matches template |
| 5 Trust & maintainability | Pass — CI workflows present |
| 6 Portfolio narrative | Pass — CaptionPipeline neutral narrative |

## Recommendations before public

1. Operator: GitHub **Settings → Repository name** → `media-ops-platform`
2. Push this branch; confirm gitleaks/trufflehog Actions green on `main`
3. Review diff for any remaining city/employer identifiers in **tracked** files
4. **GH-PF-04:** Settings → Change visibility → Public

## Historical log

Binary log (prior run): [GH-PF-03-security-scan.log](GH-PF-03-security-scan.log) — treat as supplemental only.
