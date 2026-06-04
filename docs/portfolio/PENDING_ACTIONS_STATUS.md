# Pending Action Items — Status (2026-06-04)

**Source checklist:** [PUBLIC_REPO_AUDIT_CHECKLIST.md](PUBLIC_REPO_AUDIT_CHECKLIST.md)  
**Security report:** [GH-PF-03-security-scan.md](GH-PF-03-security-scan.md)

---

## 1. Public repo audit

| Status | Action | Where |
|--------|--------|--------|
| Done | MIT **LICENSE** aligned with README | Root `LICENSE` |
| Done | Operator paths **gitignore** + untrack | `plans/`, `.cursor/plans/`, `.cursor/state/`, hazard dirs |
| Done | Rebrand Archivist → **CaptionPipeline**; neutral narrative | README, `docs/portfolio/`, `portfolio/` |
| Done | **PRE_PUBLIC_INVENTORY.md** | `docs/portfolio/` |
| Done | Operator **GitHub rename** → `media-ops-platform` | `gh repo rename` 2026-06-04 |
| Pending | **GH-PF-04** public visibility | [MEATSPACE] after scan review |

---

## 2. Security remediation

| Status | Priority | Action |
|--------|----------|--------|
| Done | P0 | LICENSE/README alignment |
| Done | P0 | Untrack operator-only trees with harness paths |
| Conditional | P1 | gitleaks/trufflehog — use CI on push (local CLI not installed) |
| Pending | P2 | Coverage 58% → 70% | ROADMAP |
| Pending | P3 | Refresh stale per-repo security_audit docs if re-added |

---

## 3. Naming

| Status | Action |
|--------|--------|
| Done | [NAMING_BRAINSTORM.md](NAMING_BRAINSTORM.md) — **CaptionPipeline** + **Platform API** + **media-ops-platform** |
| Pending | Operator sign-off checkbox in brainstorm doc |

---

## Summary

- **Done this pass:** MIT license, gitignore/untrack operator dirs, rebrand, README rewrite, portfolio case study rename, security markdown report.
- **Still pending:** GitHub repo rename, public flip (GH-PF-04), optional pip-audit locally, coverage gate, operator Grafana screenshots.
