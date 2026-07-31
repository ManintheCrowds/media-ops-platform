# Public Repo Audit Results

**Date:** 2025-02-10  
**Scope:** portfolio-harness (root + obsidian_cursor_integration, WatchTower_main\WatchTower_main), software, Arc_Forge, moltbook-watchtower.  
**Checklist:** [PUBLIC_REPO_AUDIT_CHECKLIST.md](PUBLIC_REPO_AUDIT_CHECKLIST.md)

---

## 1. portfolio-harness (root)

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | N/A (no root requirements) |
| **Tests** | N/A (no tests at root) |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | See Summary |

---

## 2. obsidian_cursor_integration

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, MISSING .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | Skipped (pip-audit not installed) |
| **Tests** | **Pass** — 30 passed in 0.66s |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | None in this project |

---

## 3. WatchTower_main\WatchTower_main

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | Skipped (pip-audit not installed) |
| **Tests** | **Fail** — 14 errors during collection (import/env issues) |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | WatchTower_main: `docs/README.md` has "[Your License Here]" (lines 180, 407); `daggr_workflows/EVALUATION.md` has multiple "TBD" |

---

## 4. software

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | Skipped (pip-audit not installed) |
| **Tests** | **Fail** — 1 failed, 40 passed (unit); coverage gate 70% not reached (38%); full run aborted |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | None in project docs (only checklist/template references) |

---

## 5. Arc_Forge

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | N/A (no single root deps; optional per-component) |
| **Tests** | **Pass** — All suites passed (campaign_kb, workflow_ui, ObsidianVault scripts): 273 passed, 9 skipped |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | None in this project |

---

## 6. moltbook-watchtower

| Check | Result |
|-------|--------|
| **File check** | OK README.md, MISSING LICENSE, OK .gitignore *(Note: one run showed MISSING README.md; README.md was added in a prior task—verify on your FS.)* |
| **Gitleaks** | Skipped (not installed) |
| **pip audit** | Skipped (pip-audit not installed) |
| **Tests** | **Pass** — 58 passed in 2.53s |
| **Placeholder secrets (py)** | None |
| **Stale phrases** | None in this project |

---

## Summary

| Item | Count / status |
|------|-----------------|
| **MISSING LICENSE** | 6/6 roots (all) |
| **MISSING .gitignore** | 1 (obsidian_cursor_integration) |
| **Gitleaks** | Run locally 2026-06-05 (8.30.1, exit 0); see `run-gh-pf03-local-scan.ps1` |
| **pip audit** | Not run (pip-audit not installed); run `pip install pip-audit` then re-audit |
| **Test failures** | 2: WatchTower_main (collection errors), software (1 failing test + coverage gate) |
| **Stale "Your License Here" / TBD** | WatchTower_main: `docs/README.md` (2), `daggr_workflows/EVALUATION.md` (multiple TBD) |

### Recommended next steps

1. **Add LICENSE** to all six roots (MIT, Apache 2.0, or "Proprietary — All rights reserved").
2. **Add .gitignore** to `obsidian_cursor_integration` (include `.env`, `venv/`, `__pycache__/`, etc.).
3. **Fix WatchTower_main tests:** resolve 14 collection errors (imports or env); replace "[Your License Here]" in `docs/README.md` and add a real LICENSE at repo root.
4. **Fix software tests:** address failing test (`test_secret_key_min_length`) and optionally relax or meet coverage gate.
5. **Install and run gitleaks** (or rely on existing GitHub workflows) and **pip-audit** for a full security pass; re-run this checklist and update this report.

---

## 7. media-ops-platform (2026-06-23 partial re-run)

**Scope:** `ManintheCrowds/media-ops-platform` only (PF-REPO-4 partial). Other five pinned repos: backlog for PF-PR-16 quarterly ritual.

**Evidence:** [2026-06-23-media-ops-pf04-audit](https://github.com/ManintheCrowds/MiscRepos/blob/main/local-proto/docs/adhoc/2026-06-23-media-ops-pf04-audit.md)

| Section | Result |
|---------|--------|
| 1 Security & secrets | **Partial pass** — gitleaks exit 0; TruffleHog verified=1 (Adzuna Gate 1 pending); scheduled TruffleHog CI failing nightly |
| 2 First-impression hygiene | **Pass** — MIT LICENSE, README, .gitignore, .env.example |
| 3 Runnable in 5 min | **Partial** — documented; full compose not agent-verified (Docker daemon off on audit host) |
| 4 Consistency | **Pass** — README matches portfolio template |
| 5 Trust & maintainability | **Partial** — CI workflows active; branch protection not configured |
| 6 Portfolio narrative | **Pass** — CaptionPipeline snapshot honest; Grafana screenshot deferred |

**Recommended next steps (media-ops):**

1. Execute [OPERATOR_SECURITY_GATES.md](OPERATOR_SECURITY_GATES.md) Gate 1 + branch protection.
2. Complete PF-REPO-2 when Grafana reachable; PF-REPO-8 live metrics export.
3. Re-run checklist on remaining five pinned repos under PF-PR-16.

## 8. ManintheCrowds public portfolio (2026-07-18 full re-run)

**Scope:** All **14** public repositories owned by `ManintheCrowds`, plus profile README. Checklist: [PUBLIC_REPO_AUDIT_CHECKLIST.md](PUBLIC_REPO_AUDIT_CHECKLIST.md). Closes/refreshes **PF-REPO-4** evidence base (prior: 2025-02-10 historic roots + 2026-06-23 media-ops partial).

**Pinned (GitHub UI, live):** OpenHarness, moltbook_watchtower, media-ops-platform, OpenGrimoire, SCP (**5** pins). Profile README table still lists **7** "Pinned work" rows (adds T3MP3ST_BLU3H4T + arc-forge-wiki) — **drift**. Plan: pin **scp-mycelium-registry** as 6th (no removal required).

### Inventory

| Repo | Fork | GH description | README / LICENSE | Copy / narrative notes |
|------|------|----------------|------------------|------------------------|
| ManintheCrowds | no | GitHub profile README | OK / MIT | Banner-first; dense PSI; "Pinned work" vs actual pins mismatch; mycelium in "Other" only |
| OpenHarness | no | Handoffs, Context & Intent Engineering… | OK / GPL-3.0 | Strong proof-set member |
| SCP | no | Content safety for AI… | OK / MIT | Strong; pairs with registry |
| scp-mycelium-registry | no | SCP mycelium shared threat registry (data) | OK / MIT | Banner before thesis; stale "v0.2.0 draft" (tag published 2026-07-11); AI service entry undocumented |
| media-ops-platform | no | CaptionPipeline + FastAPI… | OK / MIT | Partial PF-REPO-4 already; Grafana / live metrics still deferred |
| OpenGrimoire | no | Local-first context graph… | OK / MIT | Default branch `master` (called out on profile) |
| arc-forge-wiki | no | Public sterile extract… | OK / MIT | Profile table lists as pin; not actually pinned |
| moltbook_watchtower | no | Passive monitoring… | OK / MIT | Actually pinned |
| T3MP3ST_BLU3H4T | yes | autonomous blue teaming… | OK / other | Profile table pin; not actually pinned; banner-first preference conflict |
| LangChainChatBot | no | Local-first RAG… | OK / MIT | Other projects; fine |
| PrusaXL_Monitor | no | Observability… | OK / MIT | Other projects; fine |
| ENTHEA | yes | Forked real-time psychedelic… | OK / AGPL-3.0 | Identical to upstream; no fork-purpose note on public README; EEG I/O lives in MiscRepos vendored tree |
| Understand-Anything | yes | Graphs that teach… | OK / MIT | Upstream fork; no portfolio narrative |
| jobsync | yes | Self-hosted job tracker… | OK / MIT | Upstream fork; career ops; keep out of proof-set |

### Checklist summary (portfolio hygiene)

| Section | Result |
|---------|--------|
| 1 Security & secrets | **Not re-scanned this pass** — rely on per-repo CI (gitleaks/trufflehog where present). No new secret findings from README/docs review. |
| 2 First-impression hygiene | **Pass** — LICENSE + README present on all 14. |
| 3 Runnable in 5 min | **Mixed** — proof-set repos document quick starts; ENTHEA/jobsync/Understand-Anything are forks with upstream docs; registry is data-only (fetch URL). |
| 4 Consistency | **Fail / drift** — `MiscRepos/docs/PORTFOLIO.md` still points at legacy `software`, Arc_Forge TTRPG framing, `moltbook-watchtower` hyphen vs underscore; profile "Pinned work" ≠ GitHub pins; registry description thinner than README one-liner. |
| 5 Trust & maintainability | **Partial** — CI badges on proof set; PF-REPO-6 billing historically blocked some Actions; ENTHEA public fork has no fork-specific CI. |
| 6 Portfolio narrative | **Partial** — Guard–Guide–Defend–Build story clear but jargon-heavy; ENTHEA/EEG experiment and mycelium registry under-explained on profile. |

### Copy recommendations (implement in this session)

1. Profile: plain-language groups; thesis before metrics; list actual pins + planned 6th (mycelium); ENTHEA as experiment under Other.
2. Registry: thesis before banner; fix v0.2.0 published wording; add AI service entry barriers doc.
3. ENTHEA: "About this fork" + AGPL notes sync; update GH description to EEG I/O focus.
4. MiscRepos `docs/PORTFOLIO.md`: refresh to current public repo map.
5. Track `eeg-connection-hub` beta locally (not public yet).

### Out of scope this pass

- Full `pip audit` / `npm audit` across all 14.
- Grafana screenshot (PF-REPO-2) / WER caption audit (PF-CAP-AUDIT-*).
- Public creation of `eeg-connection-hub` (human gate).
- Silent merge of registry patterns or live Muse hardware claims.

