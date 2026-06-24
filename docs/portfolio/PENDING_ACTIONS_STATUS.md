# Pending Action Items — Status (2026-06-24)

**Source checklist:** [PUBLIC_REPO_AUDIT_CHECKLIST.md](PUBLIC_REPO_AUDIT_CHECKLIST.md)  
**Security report:** [GH-PF-03-security-scan.md](GH-PF-03-security-scan.md)  
**Last verified:** 2026-06-23 — [GH-PF-04 audit](https://github.com/ManintheCrowds/MiscRepos/blob/main/local-proto/docs/adhoc/2026-06-23-media-ops-pf04-audit.md) (repo PUBLIC; trackers reconciled)

---

## 1. Public repo audit

| Status | Action | Where |
|--------|--------|--------|
| Done | MIT **LICENSE** aligned with README | Root `LICENSE` |
| Done | Operator paths **gitignore** + untrack | `plans/`, `.cursor/plans/`, `.cursor/state/`, hazard dirs |
| Done | Rebrand Archivist → **CaptionPipeline**; neutral narrative | README, `docs/portfolio/`, `portfolio/` |
| Done | **PRE_PUBLIC_INVENTORY.md** | `docs/portfolio/` |
| Done | Operator **GitHub rename** → `media-ops-platform` | `gh repo rename` 2026-06-04 |
| Done | **GH-PF-04** public visibility | Public since 2026-06-04; verified 2026-06-23 via `gh repo view` |

---

## 2. Security remediation

| Status | Priority | Action |
|--------|----------|--------|
| Done | P0 | LICENSE/README alignment |
| Done | P0 | Untrack operator-only trees with harness paths |
| Done | P1 | gitleaks/trufflehog — local CLI installed 2026-06-05; `run-gh-pf03-local-scan.ps1`; untrack `job-automation-service/.env.backup` |
| Pending | P2 | Coverage 58% → 70% | ROADMAP |
| Pending | P3 | Refresh stale per-repo security_audit docs if re-added |
| Pending | **Operator** | Adzuna Gate 1, branch protection | [OPERATOR_SECURITY_GATES.md](OPERATOR_SECURITY_GATES.md) |
| Done | P1 | VirusTotal API key rotated; active key in local `.env` only | `SECURITY_VIRUSTOTAL_API_KEY` — see [OPERATOR_SECURITY_GATES.md](OPERATOR_SECURITY_GATES.md) § VirusTotal |

---

## 3. Naming

| Status | Action |
|--------|--------|
| Done | [NAMING_BRAINSTORM.md](NAMING_BRAINSTORM.md) — **CaptionPipeline** + **Platform API** + **media-ops-platform** |
| Done | Operator sign-off 2026-06-24 — **CaptionPipeline** + **Platform API** + **media-ops-platform** + **MIT** (implemented 2026-06-04) |

---

## Summary

- **Done this pass:** MIT license, gitignore/untrack operator dirs, rebrand, README rewrite, portfolio case study rename, security markdown report.
- **Still pending:** optional pip-audit locally, coverage gate, Grafana reliability screenshot (PF-REPO-2 — Branch B until homelab stack runs), Adzuna Gate 1 history purge, branch protection on `main`.
