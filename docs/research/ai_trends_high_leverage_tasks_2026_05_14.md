# AI trends high-leverage task proposal

**Date:** 2026-05-14  
**Source context:** [Local-first AI trend scan](local_first_news_2026_05_14_ai_trends.md), [local-first follow-up report](local_first_followup_report_2026_05_14.md), and [local-first pilot audit](local_first_pilot_audit_2026_05_14.md).  
**Purpose:** Capture high-leverage follow-up work suggested by the AI/local-first trend research so it can be promoted into the user's task system.

## Obsidian migration flag

`OBSIDIAN_PENDING_TASKS_MIGRATION_FLAG: migrate-ai-trends-local-first-tasks-2026-05-14`

Future AI instruction:

> If you have access to the user's Obsidian Vault pending-tasks system, migrate the tasks in this document into that system. Preserve the task IDs, sequencing, source links, and "why this matters" notes. After migration, update this section with the destination note/path and mark the migration complete. If you do not have Obsidian access, leave this flag in place.

Migration status: **pending**. This repository session cannot access the Obsidian Vault.

## Executive proposal

The highest-leverage work is not to adopt a local-first stack immediately. The trend research and code audit show that the compounding path is:

1. Stabilize one narrow local-first pilot (`pi-client` + `education-service`).
2. Protect sensitive local data before expanding pilots.
3. Make agent/research tooling repeatable.
4. Convert local-first lessons into reusable checklists and policies.

## Proposed task sequence

| ID | Priority | Task | Why this matters | Acceptance |
|---|---|---|---|---|
| HL-1 | P0 | Write the Pi local-first pilot brief | The audit found `pi-client` + `education-service` is the best strategic pilot, but not implementation-ready. A brief prevents a vague "local-first rewrite" and narrows scope to read-only package sync and offline content listing. | A brief exists that defines scope, non-goals, local entities, trust boundary, sync lifecycle, encryption stance, rollback, and acceptance gates. |
| HL-2 | P0 | Add Pi sync contract tests | The client/server sync contract currently disagrees on package download and `sync/complete`. Contract tests should fail before implementation and protect against future drift. | Tests prove package download response shape and `sync/complete` request binding across client and FastAPI server. |
| HL-3 | P0 | Define Pi device-scoped auth and org authorization | The current Pi client uses a bearer human token and server sync methods fetch devices by ID without user/org enforcement in the service layer. Local-first edge devices need a clear trust boundary. | A design note or tests specify device credentials, org scoping, revocation/wipe behavior, and negative authorization cases. |
| HL-4 | P1 | Write home-cyber privacy and data-retention policy | `home-cyber-risk` is a strong local-data candidate, but identifier disclosure, raw payload retention, logs, and Loki/Grafana exposure need explicit consent and policy. | A policy decides `raw_data` retention/redaction/encryption, identifier disclosure, log redaction, backup/encryption, and observability exposure. |
| HL-5 | P1 | Draft local storage encryption policy | Multiple pilots will store sensitive local data. The research recommends random DEKs with explicit wraps and no support decryption bypass. | A reusable policy separates account recovery from data recovery, defines DEK/wrap/recovery-key language, and bans support bypasses. |
| HL-6 | P1 | Build a local-first stack evaluation checklist | Future local-first decisions need a repeatable evaluation matrix instead of stack-by-vibe. | A checklist covers offline need, latency, sensitivity, sync model, conflict policy, auth boundary, encryption, observability, recovery, and operational fit. |
| HL-7 | P2 | Prototype a local-first AI inference router | The strongest AI architecture pattern from the research is deterministic/local first, cloud only on low confidence, human review for high-impact uncertainty. | A small prototype routes sample inputs through deterministic extraction, confidence scoring, optional cloud escalation, and human-review queue output. |
| HL-8 | P2 | Evaluate per-user local agent memory | The decision is per-user memory with project/workspace filters. A dry-run can test whether local memory improves agent continuity without leaking secrets. | A dry-run report covers storage location, project filters, redaction, "no secrets" policy, export/delete behavior, and one safe preflight example. |
| HL-9 | P2 | Make local-first development loops explicit | CAP-style local mocks and contract-first inner loops are part of the same trend: local-first applies to developer workflow, not just app UX. | A development note identifies top external dependencies to mock, contract-test boundaries, and "cloud unavailable" workflows. |
| HL-10 | P2 | Complete Firecrawl cloud setup | Research tooling should not require repeated ad hoc CLI installs or browser auth loops. | Future cloud agents start with `firecrawl --version --auth-status` authenticated via `FIRECRAWL_API_KEY`, with `.firecrawl/` ignored. |

## Recommended ordering

### Phase 1: Make the primary pilot real

1. **HL-1: Pi local-first pilot brief**
2. **HL-2: Pi sync contract tests**
3. **HL-3: Pi device-scoped auth and org authorization**

Rationale: these tasks turn the audit into an executable pilot. They also reduce the biggest risks before adding local SQLite, package builders, or offline UI work.

### Phase 2: Make sensitive local data safe

4. **HL-4: home-cyber privacy and data-retention policy**
5. **HL-5: local storage encryption policy**

Rationale: local-first systems move responsibility to the edge. These policies prevent "local" from becoming "plaintext, unrecoverable, or silently leaked through logs."

### Phase 3: Build reusable decision machinery

6. **HL-6: local-first stack evaluation checklist**
7. **HL-9: local-first development loops**
8. **HL-10: Firecrawl cloud setup**

Rationale: these make future research and implementation cheaper and less dependent on one agent's memory.

### Phase 4: Explore AI-native upside

9. **HL-7: local-first AI inference router**
10. **HL-8: per-user local agent memory evaluation**

Rationale: these are high-upside but should follow the more immediate pilot and safety work.

## Task details

### HL-1: Write the Pi local-first pilot brief

**Type:** DOCS / PLAN  
**Primary source:** [local_first_pilot_audit_2026_05_14.md](local_first_pilot_audit_2026_05_14.md)  
**Proposed destination:** `docs/research/` until a concrete `docs/local-first/` handbook exists.

Include:

- Read-only content sync scope.
- Local entities: `content_items`, `media_files`, `sync_packages`, `sync_events`, `device_state`, `completion_queue`.
- Explicit non-goals: collaborative editing, CRDTs, multi-org fleet management, learner progress writeback.
- Trust boundary: education service authoritative; Pi local store as interaction/cache surface.
- Acceptance gates copied from the pilot audit.

### HL-2: Add Pi sync contract tests

**Type:** TEST / CODE  
**Primary source:** [local_first_pilot_audit_2026_05_14.md](local_first_pilot_audit_2026_05_14.md)

Tests should lock:

- Package download shape.
- `sync/complete` request binding.
- `sync/check` ready vs pending package behavior.
- Checksum mismatch rejection.
- Poison tarball rejection.

### HL-3: Define Pi device-scoped auth and org authorization

**Type:** SECURITY / DOCS / TEST  
**Primary source:** [local_first_pilot_audit_2026_05_14.md](local_first_pilot_audit_2026_05_14.md)

Questions to resolve:

- Is the Pi authenticated by certificate, scoped device token, or both?
- How does a device rotate credentials?
- How does server-side code verify device belongs to the caller's organization?
- How do revoked/wiped devices fail closed?

### HL-4: Write home-cyber privacy and data-retention policy

**Type:** SECURITY / DOCS  
**Primary source:** [local_first_pilot_audit_2026_05_14.md](local_first_pilot_audit_2026_05_14.md)

Decide:

- What external providers receive identifiers.
- Whether `raw_data` is stored, redacted, encrypted, or dropped.
- Whether logs contain identifiers.
- Whether Loki/Grafana are in or out of pilot scope.
- How backups of `data/`, `.env`, and `config/identifiers.yml` are encrypted.

### HL-5: Draft local storage encryption policy

**Type:** SECURITY / DOCS  
**Primary source:** [local_storage_encryption_key_recovery_2026_05_14.md](local_storage_encryption_key_recovery_2026_05_14.md)

Policy stance:

- Random local DEK.
- Multiple explicit wraps: recovery key, trusted device, optional trusted contact/org public key.
- No support-held bypass key.
- Honest loss language if all recovery methods are lost.

### HL-6: Build a local-first stack evaluation checklist

**Type:** DOCS  
**Primary source:** [local_first_followup_report_2026_05_14.md](local_first_followup_report_2026_05_14.md)

Checklist dimensions:

- Offline need.
- Latency pain.
- Data sensitivity.
- Conflict model.
- Partial sync shape.
- Schema migration.
- Auth/trust boundary.
- Local encryption/recovery.
- Observability.
- Self-hosting/commercial lock-in.

### HL-7: Prototype local-first AI inference router

**Type:** RESEARCH / CODE  
**Primary source:** [local_first_news_2026_05_14_ai_trends.md](local_first_news_2026_05_14_ai_trends.md)

Prototype:

- Deterministic local extraction first.
- Confidence scoring.
- Optional cloud model escalation only below threshold.
- Human review queue for low-confidence or high-impact outputs.
- Clear logs of routing decisions and cost avoided.

### HL-8: Evaluate per-user local agent memory

**Type:** RESEARCH / SECURITY / DOCS  
**Primary source:** [local_first_followup_report_2026_05_14.md](local_first_followup_report_2026_05_14.md)

Evaluation should preserve the decision:

- Owner is one human user.
- Project/workspace IDs are metadata filters.
- No shared memory unless explicitly created.
- Export/delete operate at user and project scope.

### HL-9: Make local-first development loops explicit

**Type:** DEVEX / DOCS  
**Primary source:** [local_first_news_2026_05_14_ai_trends.md](local_first_news_2026_05_14_ai_trends.md)

Capture:

- Which external APIs should have local mocks.
- Which contracts need tests.
- What developers can do with network/cloud unavailable.
- How to prevent mock drift from production behavior.

### HL-10: Complete Firecrawl cloud setup

**Type:** CONFIG / ENV  
**Primary source:** [../agent-tooling-firecrawl.md](../agent-tooling-firecrawl.md)

Use the existing setup prompt from [agent-tooling-firecrawl.md](../agent-tooling-firecrawl.md). Do not commit secrets.

## Promotion rule

Promote at most three tasks at once:

1. HL-1
2. HL-2
3. HL-3

Leave the rest as queued candidates until the Pi pilot brief and contract tests exist.

## Notes for future AI

- Do not treat this document as proof that the tasks are already in the user's real task system.
- Search for `OBSIDIAN_PENDING_TASKS_MIGRATION_FLAG` before creating duplicate migration notes.
- If Obsidian access becomes available, migrate this document into the pending-tasks system and leave a backlink here.
- If no Obsidian access is available, keep this document as the repo-local source of truth.
