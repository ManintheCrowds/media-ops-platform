# Local-first pilot audit - Pi client, education service, and home cyber risk

**Date:** 2026-05-14  
**Task type:** DOCS / RESEARCH  
**Risk level:** Low. This audit changes documentation only; no runtime behavior, schema, or credentials are modified.  
**Source:** Follow-up to [local_first_followup_report_2026_05_14.md](local_first_followup_report_2026_05_14.md).  
**Scope:** Prepare implementation-readiness audits for the two selected local-first pilot candidates:

1. **Primary pilot:** `pi-client` + `education-service`
2. **Second candidate:** `home-cyber-risk`

## Executive recommendation

| Candidate | Audit outcome | Pilot posture |
|---|---|---|
| `pi-client` + `education-service` | Best strategic fit, but **not pilot-ready without contract/auth/offline fixes**. | Proceed to a narrow pilot brief after fixing the sync package protocol and device trust boundary. |
| `home-cyber-risk` | Credible local-data/privacy candidate, but **not an offline-first discovery system**. | Treat as a second pilot for encrypted local retention, local reports, and honest privacy/observability, not as a sync-engine pilot. |

## Audit criteria

| Dimension | What the audit checked |
|---|---|
| Local persistence | Is local data structured, queryable, durable, and recoverable? |
| Sync lifecycle | Is there a coherent flow for detecting, downloading, applying, and acknowledging changes? |
| Trust boundary | Does the server remain authoritative for permissions, validation, and device identity? |
| Offline UX | Can the user/device still perform meaningful work with the network unavailable? |
| Data security | Are local secrets, sensitive records, and recovery paths handled deliberately? |
| Contract readiness | Do docs, client code, and server APIs agree? |
| Observability | Can operators tell whether sync/checks succeeded, failed, or drifted? |
| Testability | Are there objective acceptance gates that can be automated? |

---

## Primary candidate audit: `pi-client` + `education-service`

### Summary

The Pi stack is the right first pilot because it already has the shape of a local-first edge client: a Pi device, local cache, background sync, content packages, server-side device records, and a user-visible offline/kiosk context. However, the current implementation is closer to a scaffold than a working local-first data path.

The key issue is not "missing SQLite"; it is that the **client and server do not yet share a coherent sync contract**.

### What is already promising

| Area | Evidence | Why it matters |
|---|---|---|
| Local cache layout exists | `pi-client/pi_client/cache/storage.py:18-28` creates metadata, media, and sync package directories. | There is already a durable on-device content boundary to evolve into a structured local store. |
| Client background sync exists | `pi-client/pi_client/cache/sync.py:47-80` loops through `check_and_sync`, checks updates, and processes packages. | The agent/device lifecycle already has a place to add durable sync state and retries. |
| Client verifies checksums when present | `pi-client/pi_client/cache/sync.py:101-105` checks package checksum if supplied. | The right integrity seam exists, though server-side checksum generation is missing. |
| Server has sync package model fields | `education-service/app/models/pi_device.py:65-78` includes package type, content IDs, URL, size, checksum, created time, and expiry. | The server schema anticipates packaged sync artifacts. |
| Server has sync endpoints | `education-service/app/api/pi/sync.py:15-93` exposes sync check, request, download, and complete endpoints. | There is a natural place to formalize a package protocol. |
| Device security fields exist | `education-service/app/models/pi_device.py:54-56` includes certificate fingerprint, security status, and encrypted device key. | The data model anticipates a device trust boundary, even though enforcement is incomplete. |

### Hard blockers before a pilot

| Blocker | Evidence | Impact | Required fix |
|---|---|---|---|
| Package download contract mismatch | Client streams tarball bytes in `pi-client/pi_client/client.py:150-170`; server returns JSON download metadata or 202 in `education-service/app/api/pi/sync.py:44-81`. | The Pi cannot reliably download/apply a package from the current server endpoint. | Pick one protocol: server streams `FileResponse`/`StreamingResponse`, redirects to signed URL, or client follows `download_url`. Add contract tests. |
| `sync/complete` body/query mismatch | Client posts JSON body in `pi-client/pi_client/cache/sync.py:110-115`; server declares `package_id: int` without a body schema in `education-service/app/api/pi/sync.py:84-92`. | FastAPI will treat `package_id` as a query parameter by default, so the documented/client request can fail. | Define an explicit `SyncCompleteRequest` body or move client/docs to query param. |
| Server package generation is stubbed | `education-service/app/services/pi_service.py:159-174` creates a row and explicitly notes package generation/URL assignment would happen later. | `has_updates` can point at packages that are not downloadable. | Add package builder or mark packages pending until URL/checksum/size are ready. |
| `has_updates` means "row exists," not "ready package exists" | `education-service/app/services/pi_service.py:124-138` returns all unexpired package rows. | Client may spin on incomplete packages. | Add package status or require `package_url` and checksum before returning as available. |
| Tar extraction is unsafe | `pi-client/pi_client/cache/sync.py:137-143` uses `tar.extractall` directly. | A compromised package could write outside the intended extraction directory. | Validate members or use safe extraction filters before pilot. |
| Device auth is human-token based | `pi-client/pi_client/client.py:27-39` sends a bearer `auth_token`; `authenticate()` is a stub in `pi-client/pi_client/client.py:81-85`. | Device identity and human identity are conflated. | Use scoped device tokens or certificate-backed device auth; enforce device/org authorization server-side. |
| Authorization is too thin | `education-service/app/services/pi_service.py:57-59` fetches devices by ID; sync service methods do not accept or check current user/org. | Any authenticated principal may be able to interact with devices by ID if route guards do not enforce membership elsewhere. | Require org/device ownership checks on all Pi routes. |
| Offline UI is not wired to cache | `pi-client/pi_client/display/server.py:80-84` returns an empty content list. | A synced cache does not yet produce visible offline behavior. | Connect display/content browser to cached metadata/media. |
| Local encryption is only a promise | `pi-client/README.md:177-182` lists encrypted local cache; `pi-client/pi_client/cache/storage.py:42-77` writes JSON/media files directly. | Pilot may overstate sensitive local storage protection. | Either implement encryption for pilot data or explicitly scope pilot to non-sensitive content. |

### Pilot-ready MVP scope

Keep the first pilot intentionally narrow:

- One organization.
- One or a small number of pre-provisioned Pi devices.
- Read-only content sync first.
- Full content packages first; incremental packages later.
- No learner progress writeback until the package/download/complete protocol is stable.
- Server remains authoritative for device eligibility, content eligibility, and package creation.

### Primary pilot architecture target

```text
education-service
  content + device authority
  package builder
  package manifest with content IDs, versions, size, checksum
  sync package status: pending -> ready -> completed/failed/expired

pi-client
  local store for manifest, content metadata, media file references, sync events
  atomic package download
  checksum verification
  safe extraction
  local UI reads cached content first
  completion queue retries idempotently
```

### Proposed local entities

| Entity | Purpose |
|---|---|
| `content_items` | Queryable local metadata for display/browser UI. |
| `media_files` | Local file references, size/checksum, and content linkage. |
| `sync_packages` | Package ID, type, status, checksum, applied time, error state. |
| `sync_events` | Append-only local log of package applied, rejected, retried, or completed. |
| `device_state` | Last successful sync, server revision/package cursor, device health. |
| `completion_queue` | Idempotent outbound acknowledgements or future progress events. |

### Acceptance gates for primary pilot

| Gate | Required proof |
|---|---|
| Contract gate | FastAPI/client contract test proves package download and `sync/complete` agree on request/response shape. |
| Integrity gate | Server emits SHA-256; client rejects mismatched package before extraction. |
| Safe extraction gate | Poison tarball with path traversal is rejected. |
| Ready-state gate | `sync/check` returns only packages that are ready to download, or clearly labels pending packages that the client skips. |
| Authz gate | Negative test proves a principal/device cannot access another org's device or package. |
| Offline gate | With API unreachable, Pi UI lists cached content and opens at least one cached media item. |
| Restart gate | Interrupted download or process restart does not corrupt existing cache and can resume/retry safely. |
| Secret gate | No device token, private key, or encryption key is stored in plaintext in the pilot local DB. |

### Non-goals for primary pilot

- Collaborative editing.
- CRDT conflict resolution.
- Multi-org fleet management.
- Production certificate lifecycle.
- Full DRM for cached media.
- Learner progress writeback before read-only content works offline.

### Primary pilot verdict

**Go for a pilot brief, not implementation yet.** This remains the best candidate, but the first implementation milestone should be a contract-and-trust-boundary hardening slice rather than a broad "local-first rewrite."

---

## Second candidate audit: `home-cyber-risk`

### Summary

`home-cyber-risk` is a good second candidate because it already defaults to local SQLite and handles sensitive personal identifiers. Its local-first value is **local retention, local review, and privacy-conscious operation**, not offline discovery. Breach discovery depends on external sources such as HIBP and GitHub-backed fetchers.

### What is already promising

| Area | Evidence | Why it matters |
|---|---|---|
| SQLite by default | `home-cyber-risk/README.md:43-44` lists SQLite by default and optional platform integration; `home-cyber-risk/services/breach_monitor/main.py:45-47` defaults `DATABASE_URL` to `sqlite:///data/breaches.db`. | The project already has a local persistent store suitable for encrypted-retention experiments. |
| Sensitive data is explicit | `home-cyber-risk/docs/SECURITY.md:3-11` lists `.env`, `config/identifiers.yml`, and `data/` as sensitive. | The project already acknowledges local data risk. |
| Storage schema is useful | `home-cyber-risk/services/breach_monitor/storage.py:16-48` stores breach records, identifiers, data classes, raw data, risk score, priority, source, and confidence. | There is enough structured data to build local reports and retention policies. |
| Check history exists | `home-cyber-risk/services/breach_monitor/storage.py:51-64` defines `check_history`. | Local reporting can show trend/history without calling APIs. |
| Dry-run path exists | `home-cyber-risk/services/breach_monitor/main.py:317-343` supports `--dry-run` and prints a summary. | Pilot operations can rehearse without writes/alerts. |

### Hard blockers before a second pilot

| Blocker | Evidence | Impact | Required fix |
|---|---|---|---|
| Not an offline discovery system | `home-cyber-risk/services/breach_monitor/main.py:48-67` initializes external fetchers; `check_identifier` calls fetchers in `home-cyber-risk/services/breach_monitor/main.py:127-145`. | Without network/API access, new breach discovery is not meaningful. | Frame pilot as local retention/reporting plus scheduled cloud-assisted checks. |
| Identifier disclosure needs consent | Emails/usernames are loaded from `config/identifiers.yml` in `home-cyber-risk/services/breach_monitor/main.py:83-111` and sent to fetchers in `home-cyber-risk/services/breach_monitor/main.py:130-137`. | Users must understand what leaves the machine. | Add pilot consent/privacy note listing HIBP/GitHub/Paste/Gist disclosures. |
| Raw upstream payload is stored | Normalizer stores `raw_data` in `home-cyber-risk/services/breach_monitor/normalizer.py:106-119`; storage persists `raw_data` in `home-cyber-risk/services/breach_monitor/storage.py:33`. | Local DB may contain more than the security docs imply. | Decide and document: redact/drop `raw_data`, encrypt it, or explicitly retain it. |
| Security docs understate raw data | `home-cyber-risk/docs/SECURITY.md:42-45` says no raw credential data/personal info beyond identifiers is stored. | Documentation can mislead pilot users. | Update security text or change persistence behavior before pilot. |
| Domains are loaded but skipped | `home-cyber-risk/services/breach_monitor/main.py:103-106` loads domains; `home-cyber-risk/services/breach_monitor/main.py:296-298` skips domain checking. | Config can create false confidence. | Mark domain checks unsupported or implement domain flow. |
| Grafana dashboard expects metrics not emitted | Dashboard uses Prometheus expressions in `home-cyber-risk/config/grafana-dashboard.json:11-63`; the app setup shown in `main.py:26-30` configures logging/Loki, not Prometheus metrics. | Observability UI may be empty or misleading. | Either add metrics, rewrite dashboard for Loki/logs, or remove dashboard from pilot scope. |
| Observability can leak identifiers | `home-cyber-risk/services/breach_monitor/main.py:124` logs the identifier being checked; `home-cyber-risk/docs/SECURITY.md:47-55` says logs may contain identifiers and may be sent to Loki; `home-cyber-risk/infra/docker-compose.yml:75-93` exposes Loki/Grafana ports and defaults Grafana admin credentials to `admin`/`admin`. | A privacy/local-retention pilot could leak identifiers through logs or an exposed dashboard. | Redact identifiers in logs, bind Loki/Grafana locally or exclude them, and require non-default Grafana credentials before pilot use. |
| Schema migration is ad hoc | Storage creates/migrates SQLite tables in `home-cyber-risk/services/breach_monitor/storage.py:85-139`; Alembic is not wired in the audited paths. | Pilot data upgrades may drift. | Keep pilot SQLite-only and add migration tests, or introduce versioned migrations before broader use. |

### Second pilot scope

Recommended scope:

- Single household or single operator.
- SQLite-only.
- Local encrypted backup/export decision before real use.
- HIBP plus optional GitHub/Pwdb/Paste fetchers only with explicit disclosure.
- Local report over existing `breaches` and `check_history`.
- One verified alert channel.

Do not promise:

- Offline breach discovery.
- Private non-disclosure to external providers.
- Working Grafana unless the dashboard/data source is fixed.
- Domain checks unless implemented.

### Acceptance gates for second pilot

| Gate | Required proof |
|---|---|
| Privacy gate | Pilot readme/consent states exactly which identifiers are sent to which external providers. |
| Data-retention gate | Decision recorded for `raw_data`: drop, redact, encrypt, or retain with warning. |
| Storage gate | SQLite DB path, backup path, and restore drill are documented. |
| Encryption gate | Either DB is stored on an encrypted volume with documented setup, or field/DB encryption is implemented for pilot data. |
| Config honesty gate | Domains are either disabled in example config or implemented/tested. |
| Observability gate | Grafana dashboard is fixed for actual emitted telemetry or excluded from pilot success criteria. |
| Observability privacy gate | Logs redact identifiers by default, Loki/Grafana are bound to local-only access or excluded, and Grafana credentials are not default values. |
| Alert gate | At least one alert channel is tested without leaking unnecessary identifiers. |
| Migration gate | Existing SQLite DB can survive the next schema change in a test or documented manual migration. |

### Second pilot verdict

**Proceed only as a privacy/local-retention pilot.** This is valuable, but it should not be compared to the Pi pilot as an offline sync pilot. Its first audit outcome should be a consent/data-minimization pass, not a sync-engine design.

---

## Cross-pilot findings

| Theme | Pi / education-service | home-cyber-risk | Shared lesson |
|---|---|---|---|
| Local storage | File cache exists, but not structured enough. | SQLite exists and is central. | Local-first readiness starts with queryable local state plus clear backup/restore. |
| Trust boundary | Needs device/org authorization and device credentials. | Needs disclosure of external provider queries. | "Local-first" must be precise about what stays local and what remains server/external. |
| Encryption | Claimed/anticipated, not implemented in cache path. | Relies on file permissions; no DB encryption. | Do not pilot sensitive local-first data without an at-rest encryption decision. |
| Observability | Needs sync state and failure surfacing. | Dashboard appears mismatched to emitted telemetry. | Operators need local evidence of success/failure before scale. |
| Docs vs code | README/API promises exceed implementation. | Security/audit docs are stale or incomplete. | Pilot docs must be written against code, not intention. |

## Recommended next work order

For the promoted task proposal and Obsidian migration flag, see [ai_trends_high_leverage_tasks_2026_05_14.md](ai_trends_high_leverage_tasks_2026_05_14.md).

1. **Pi pilot brief:** Write a narrow implementation brief for read-only package sync and offline content listing.
2. **Pi contract tests:** Add tests that lock package download and `sync/complete` behavior before implementation changes.
3. **Pi trust boundary:** Define device-scoped auth and org authorization requirements.
4. **Home-cyber pilot consent/data policy:** Decide `raw_data`, identifier disclosure, and backup/encryption stance.
5. **Home-cyber observability cleanup:** Fix or exclude Grafana from pilot success.

## Definition of done for this audit

- Primary and secondary candidates audited separately.
- Blockers and acceptance gates documented.
- Pilot scope and non-goals recorded.
- Cross-pilot lessons captured.
- No implementation changes required by this document.

## Sources

- Internal: [local_first_followup_report_2026_05_14.md](local_first_followup_report_2026_05_14.md)
- Internal: `pi-client/README.md`
- Internal: `pi-client/pi_client/client.py`
- Internal: `pi-client/pi_client/cache/storage.py`
- Internal: `pi-client/pi_client/cache/sync.py`
- Internal: `pi-client/pi_client/display/server.py`
- Internal: `education-service/app/api/pi/sync.py`
- Internal: `education-service/app/services/pi_service.py`
- Internal: `education-service/app/models/pi_device.py`
- Internal: `education-service/app/schemas/pi.py`
- Internal: `home-cyber-risk/README.md`
- Internal: `home-cyber-risk/services/breach_monitor/main.py`
- Internal: `home-cyber-risk/services/breach_monitor/storage.py`
- Internal: `home-cyber-risk/services/breach_monitor/normalizer.py`
- Internal: `home-cyber-risk/docs/SECURITY.md`
- Internal: `home-cyber-risk/config/grafana-dashboard.json`
