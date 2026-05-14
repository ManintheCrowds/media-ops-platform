# Local-first follow-up report - open questions from 2026-05-14 trend scan

**Source:** Follow-up to [local_first_news_2026_05_14_ai_trends.md](local_first_news_2026_05_14_ai_trends.md).  
**Scope:** Resolve the local-first pilot, documentation location, agent memory scope, and Firecrawl setup questions raised in the initial trend scan.  
**Status:** Research and recommendation, not an implementation decision record.

## Compressed take

- **Best current pilot candidate:** `pi-client` + `education-service`. The Pi client already promises local caching, offline support, encrypted local cache, background sync, and package downloads, while the education service already exposes sync-check, package request/download, and completion endpoints.
- **Second candidate:** `home-cyber-risk`, because it stores sensitive identifiers and breach history in SQLite by default.
- **Do not create `docs/local-first/` yet.** In this repo, local-first research should remain under `docs/research/` until a concrete implementation exists. `local-proto` is not present in this repo and is referenced as an external tooling/MCP stack, not as the local-first product architecture handbook.
- **Agent memory scope:** per user, as directed. If this becomes a built feature, project/workspace boundaries should be metadata and access filters inside a user-owned memory store, not independent cross-user stores.
- **Firecrawl:** add a dedicated agent-tooling setup guide in `docs/agent-tooling-firecrawl.md` and link it from `docs/AI_DOCUMENTATION_INDEX.md`.

## Location verification

### Is `local-proto` in this repo?

No. A file search found only `.cursor/plans/*local-proto*.plan.md` files, not a checked-in `local-proto/` tree. The clearest in-repo plan says to treat `portfolio-harness/local-proto/` as canonical for Cursor runtime and MCP/tooling integrations, and treats `D:/local-proto` as an optional sibling clone that can drift (`.cursor/plans/local-proto_ssot_and_matrices_5dd15a4b.plan.md`).

### What is `local-proto` for?

The local-proto plans describe tool servers, MCP scripts, capability maps, SCP pipelines, and Cursor integration. For example, the SSOT plan frames `portfolio-harness/local-proto/` as canonical for Cursor runtime, MCP scripts, and tool-safeguard machinery, not as the product local-first architecture corpus.

### Where should this work live now?

Use `docs/research/` for the current work:

- It already contains the 2026-05-14 local-first trend scan.
- It has an explicit meditation/research template and README.
- The current artifacts are evaluations and research, not implementation handbook content.

Do **not** create `docs/local-first/` until at least one implementation artifact exists, such as a pilot brief, stack checklist, schema/sync design, or implementation plan. If that happens, promote only stable, decision-level content into `docs/local-first/` and keep source research in `docs/research/`.

If the external `local-proto` repo becomes available, put **agent/tooling setup** there, not product pilot research. If an external `local-first` repo exists, it may be a better long-term product-handbook SSOT than `local-proto`.

## Local-first data pilot evaluation

| Rank | Project | Fit | Evidence | Recommendation |
|---|---|---|---|---|
| 1 | `pi-client` + `education-service` | Highest | `pi-client/README.md` lists local caching, offline support, certificate auth, optional encrypted cache, remote wipe, and education-service sync endpoints. `pi-client/pi_client/cache/sync.py` has a background sync loop, package download, checksum verification, extraction, and sync-complete marking. `education-service/app/api/pi/sync.py` exposes sync check, request, download, and complete endpoints. | Run the first pilot here. Convert the Pi side from ad hoc package/file metadata toward a structured local store with explicit replay, sync state, and server validation. |
| 2 | `home-cyber-risk` | Strong privacy pilot | `home-cyber-risk/README.md` says SQLite is default and the app stores personal identifiers. `home-cyber-risk/services/breach_monitor/storage.py` stores identifiers, breach names, data classes, risk scores, source/confidence, and check history. | Good second pilot for encrypted local SQLite and local report UX. Keep network checks as background refreshes. |
| 3 | `job-automation-service` | Selective only | `job-automation-service/app/utils/pii_redaction.py` redacts SSNs, email, and phones before LLM calls, showing high PII sensitivity. The product still depends on external job sources and LLM workflows. | Pilot only local drafts, saved searches, profile mirrors, or application notes. Do not local-first the ingestion pipeline yet. |
| 4 | Main dashboard / `frontend` | Narrow UX cache | `frontend/static/js/dashboard.js` stores a JWT in `localStorage`, polls `/health/services`, and updates service status from network responses. | Consider a last-known-good service snapshot cache only. This is not a sync-engine pilot. |
| 5 | `security-service` | Poor first pilot | Security/SIEM correlation and threat data should remain server-authoritative. | Keep central Postgres/Redis-style service authority; edge buffering is a reliability topic, not local-first app data. |
| 6 | `monitoring` / Grafana / Prometheus | Poor fit | Monitoring data is inherently centralized/time-series oriented. | Do not use as pilot. |
| 7 | `business/` docs and `portfolio/` static pages | Not applicable | Markdown/static files are already file-local and have no sync engine problem. | No action. |

### Recommended pilot shape: Pi client structured local store

**Goal:** Make the Pi device usable through network interruptions with a queryable, inspectable local state model while preserving the education service as authority.

**Candidate local entities:**

- `content_items`
- `media_files`
- `sync_packages`
- `sync_events`
- `device_state`
- `upload_queue` or `completion_queue`

**Trust boundary:**

- The Pi local store is the interaction/cache surface.
- The education service remains authoritative for permissions, package eligibility, device validity, and final sync status.
- Local writes are queued observations/completions, not trusted server truth.

**Conflict policy:**

- Content packages are mostly server-authored and versioned; use package ID/checksum/version as immutable identity.
- Device progress/completion events should be idempotent and append-only where possible.
- If the server rejects a queued event, keep a local error row and surface it in the Pi admin UI/logs.

**Pilot acceptance:**

- A short pilot brief names the local tables, authority model, sync lifecycle, and failure modes.
- A prototype can list cached content and sync state without network access.
- A sync-complete replay path is idempotent and survives process restart.
- No user or device secret is stored unencrypted in the local DB.

## Agent memory scope decision

Use **per-user local MCP data**.

Recommended model:

- **Owner:** one user-owned memory store per human user.
- **Project scoping:** project/workspace IDs are metadata filters within that user store.
- **Default retrieval:** restrict to the current project unless the user asks for cross-project recall.
- **Isolation:** no shared team memory unless explicitly created as a separate shared corpus with its own access policy.
- **Deletion:** delete/export should operate at both user-store and project-scope granularity.

Why this fits the local-first direction:

- It keeps personal working memory inspectable and portable.
- It avoids accidental cross-user leakage.
- It still supports project-specific context without fragmenting memory into too many physical stores.

## Follow-up artifacts

- Key-recovery research project: [local_storage_encryption_key_recovery_2026_05_14.md](local_storage_encryption_key_recovery_2026_05_14.md)
- Firecrawl cloud agent setup guide: [../agent-tooling-firecrawl.md](../agent-tooling-firecrawl.md)

## Backlog candidates

| ID | Type | Candidate | Acceptance | Routed to |
|---|---|---|---|---|
| LF-P1 | DOCS | Write Pi client local-first pilot brief | Brief covers local tables, sync lifecycle, trust boundary, conflict policy, encrypted local storage, and rollback. | deferred |
| LF-P2 | CODE/RESEARCH | Prototype Pi local state SQLite schema | Prototype can list cached content and pending sync events offline using sample package metadata. | deferred |
| LF-P3 | DOCS | Promote a `docs/local-first/` handbook only after pilot brief exists | New handbook contains stable decisions/checklists, while source research remains linked in `docs/research/`. | deferred |

## Sources

- Internal: [Local-first trend scan](local_first_news_2026_05_14_ai_trends.md)
- Internal: `.cursor/plans/local-proto_ssot_and_matrices_5dd15a4b.plan.md`
- Internal: `pi-client/README.md`
- Internal: `pi-client/pi_client/cache/sync.py`
- Internal: `education-service/app/api/pi/sync.py`
- Internal: `home-cyber-risk/README.md`
- Internal: `home-cyber-risk/services/breach_monitor/storage.py`
- Internal: `job-automation-service/app/utils/pii_redaction.py`
- Internal: `frontend/static/js/dashboard.js`
