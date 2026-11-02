---
title: "Local-first Pi sync contract + platform hardening"
date: 2026-09-26
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
origin: Project store local-proto-audit + nextcloud-gap-analysis; user Immediate LFG Track A+B
---

# Local-first Pi sync contract + platform hardening

## Goal Capsule

Unblock local-first by making education-service ↔ pi-client sync a coherent, versioned contract with device-scoped auth, and land cheap platform hardening (auth rate limit, audit emit, validate endpoint) without rewriting collaboration products.

Authority: user-directed Track A+B from local proto audit; in-repo `docs/research/local_first_pilot_audit_2026_05_14.md` acceptance gates; do not rebuild Nextcloud Hub apps.

Stop when: sync check/download/complete agree under tests; only ready+checksum packages advertise updates; tar path-traversal rejected; device JWT required on Pi sync routes; `GET /api/capabilities` exposes sync protocol + education base URL; nginx routes `/api/v1/pi` and applies `auth_limit` on `/api/auth/`; platform emits `auth.login|fail` and `gateway.proxy` into security-service audit; `/api/auth/validate` exists.

## Product Contract

### Problem

Pi sync is scaffolded but contract-broken (download shape, complete params, stub packages, unsafe extract, human JWT as device auth). Platform login lacks applied auth rate-limit and SIEM-facing audit events. Education falls back to a missing `/api/auth/validate`.

### Requirements

- R1. Sync download uses one advertised protocol: server streams package bytes (`StreamingResponse` / file stream) when package is `ready`.
- R2. `POST .../sync/complete` accepts an explicit JSON body `{ "package_id": int }` matching pi-client.
- R3. Sync packages have status `pending | ready | expired | failed`; `has_updates` is true only when at least one unexpired `ready` package has a non-empty checksum (and downloadable bytes or storage path).
- R4. Package request creates `pending` then a builder fills content, checksum, size, and flips to `ready` (or `failed`); no silent “row exists ⇒ ready”.
- R5. pi-client rejects tar members with path traversal / absolute paths before extract.
- R6. Pi sync/content/stream routes accept device-scoped credentials (device JWT with `token_use=device` + matching `device_id`), not human dashboard JWT alone; human admin JWT remains for device registration / cert admin.
- R7. Platform exposes `GET /api/capabilities` including `sync.protocol_version`, education base URL (via nginx when present), auth methods, and gateway service types.
- R8. Nginx proxies `/api/v1/pi/` to education-service and applies `limit_req zone=auth_limit` on `/api/auth/`.
- R9. Platform login success/failure and gateway proxy attempts emit audit events `auth.login`, `auth.fail`, `gateway.proxy` into security-service (best-effort; must not break login if security-service down).
- R10. Platform implements `GET /api/auth/validate` returning current-user claims for education’s shared-secret fallback path.

### Actors

- Platform API (`app/`) — capabilities, auth validate, audit emit, JWT minting for humans.
- Education-service — Pi device/sync authority.
- pi-client — edge sync consumer.
- Nginx — edge routing + auth rate limit.
- security-service — audit persistence.

### Key flows

1. Admin registers device (human JWT) → mints device token → configures pi-client.
2. Device `sync/check` → only ready packages → `download` streams bytes → checksum → safe extract → `sync/complete` JSON.
3. Client/agent `GET /api/capabilities` before assuming endpoints.
4. Attacker floods `/api/auth/token` → nginx `auth_limit` throttles; failures audited.

### Acceptance examples

- AE1. Given a pending package without checksum, `sync/check` returns `has_updates=false`.
- AE2. Given a ready package with checksum and bytes, download returns `application/gzip` (or tar.gz) body; client writes file and verifies checksum.
- AE3. Poison tar with `../` member is rejected by pi-client before write outside extract dir.
- AE4. Human JWT on `sync/check` returns 401/403; device JWT for that `device_id` succeeds.
- AE5. `GET /api/capabilities` includes `sync.protocol_version` and education URL containing `/api/v1/pi`.
- AE6. Nginx config applies `auth_limit` to `/api/auth/`; `/api/auth/validate` returns 200 for valid Bearer.

### Product scope

In: Track A sync contract + device auth + capabilities + nginx pi route; Track B auth_limit + audit emit + validate.

Out: Full offline UI content browser wiring; package incremental CRDT; OIDC/WebAuthn; Share DTO; TrustedServers; Nextcloud compose; E2E cache encryption wiring; Talk/Deck/Office.

### Open questions

- OQ1 (deferred): Whether package bytes live on local disk vs object storage — start with education `storage/` path + StreamingResponse.
- OQ2 (deferred): mTLS cert header enforcement beyond device JWT — JWT first; cert fingerprint check as follow-on if time.
- OQ3 (deferred): Hash-chain upgrade for audit integrity — keep per-entry hash; chain later.

## Planning Contract

### Key technical decisions

- KTD1. Download protocol = **StreamingResponse of package bytes** (not signed URL). Provenance: user allowed either; pipeline chooses stream to avoid signing infra. Rejected: signed URL MVP.
- KTD2. Nginx **will** route `/api/v1/pi/` to education-service. Provenance: user allowed route or document-only; pipeline chooses route for local-first DX. Rejected: capabilities-only `:8003` documentation as sole fix.
- KTD3. **Add** `GET /api/auth/validate` (do not remove education fallback). Provenance: user allowed add or remove; education already calls it. Rejected: deleting fallback without replacement.
- KTD4. Device auth = **device-scoped JWT** (`token_use=device`, `device_id`, short TTL) minted by admin-authenticated education endpoint; sync routes depend on device principal. Rejected: continuing human dashboard JWT for devices.
- KTD5. Audit emit = **HTTP POST** to new security-service ingest endpoint (best-effort async/sync with timeout); platform must not fail request if audit down. Rejected: only local logs.
- KTD6. Package status column on `pi_sync_packages` + Alembic migration in education-service; builder writes tarball under `storage/sync_packages/` and sets checksum SHA-256.
- KTD7. `sync.protocol_version` = `"1"` string in capabilities; bump only on breaking sync changes.

### Technical design (directional)

```text
pi-client --device JWT--> nginx /api/v1/pi --> education-service
                                |
platform /api/capabilities  ----+--> education_base_url, sync.protocol_version
platform /api/auth/token    --> auth_limit; audit auth.login|fail
platform /api/gateway/*     --> audit gateway.proxy (best-effort)
education sync/download     --> StreamingResponse(file) if status=ready
```

### Assumptions

- A1. JWT_SECRET_KEY shared between platform and education (already in compose).
- A2. Device JWT may be signed with same JWT secret and verified in education (claim-gated).
- A3. security-service reachable from platform at compose DNS `http://security-service:8001` (config via env).
- A4. Pilot package builder can pack minimal metadata JSON + placeholder media from content IDs already in DB; empty content_ids ⇒ empty but valid ready archive still allowed for contract tests.

### Sequencing

U1 capabilities + validate → U2 nginx → U3 package FSM + stream download + complete body → U4 device JWT → U5 safe extract + client align → U6 audit emit + auth hardening tests.

### Risks

- Risk: education Postgres migration needed — mitigate with Alembic revision + SQLite-free test strategy using existing education fixtures or unit-test service layer with mocks if PG unavailable in CI.
- Risk: breaking existing human-token pi-client configs — mitigate: document device token mint; keepalive short deprecation note in capabilities `auth.device_token_required: true`.
- Risk: audit POST adds latency — mitigate: short timeout, swallow errors.

### Patterns to follow

- Platform routers in `app/main.py` / `app/auth/oauth2.py`.
- Education Pi routers under `education-service/app/api/pi/`.
- SSRF/validation style in `app/validation.py` (for any new URLs).
- Existing pilot audit gates in `docs/research/local_first_pilot_audit_2026_05_14.md`.

## Implementation Units

### U1. Platform capabilities + auth validate

Files: `app/main.py`, `app/api/capabilities.py` (new), `app/auth/oauth2.py`, `tests/integration/test_api_capabilities.py` (new), `tests/integration/test_api_auth.py`

- Add `GET /api/capabilities` (unauthenticated or auth-optional) returning JSON: app name/version, `auth.methods`, `auth.validate_path`, `gateway.service_types`, `sync.protocol_version`, `sync.education_base_path` (`/api/v1/pi`), `features` flags.
- Add `GET /api/auth/validate` using `get_current_user` → `{sub, email, is_admin, is_active}`.
- Tests: capabilities keys present; validate 401 without token / 200 with token.

### U2. Nginx auth_limit + Pi reverse proxy

Files: `nginx/nginx.conf`, short note in `docs/SECURITY.md` or `ENV_SETUP_GUIDE.md` only if needed for operators

- `location /api/auth/` with `limit_req zone=auth_limit burst=5 nodelay;` before broader `/api`.
- `location /api/v1/pi/` → `proxy_pass http://education-service:8000` (define upstream `education-service`).
- Preserve existing security headers.
- Verification: config syntax review; document expected paths in capabilities (U1) to match.

### U3. Sync package FSM + stream download + complete body

Files: `education-service/app/models/pi_device.py`, Alembic migration under `education-service/alembic/`, `education-service/app/schemas/pi.py`, `education-service/app/services/pi_service.py`, `education-service/app/api/pi/sync.py`, `education-service/tests/unit/test_pi_sync_service.py` (new), `education-service/tests/integration/test_api_pi_sync.py` (new)

- Add `PackageStatus` enum + column default `pending`.
- `request_sync_package`: create pending; run/build package (sync or background) writing `.tar.gz`, set size/checksum/path, status `ready` or `failed`.
- `check_for_updates`: only `ready` + non-null checksum + not expired.
- `download`: if not ready → 409 or 202 with status; if ready → `StreamingResponse` file bytes (`application/gzip`).
- `complete`: body model `SyncCompleteRequest(package_id: int)`.
- Tests: AE1–AE2 style unit/integration with temp storage.

### U4. Device-scoped JWT on Pi routes

Files: `education-service/app/auth/` (device helpers), `education-service/app/dependencies.py`, `education-service/app/api/pi/sync.py`, `education-service/app/api/pi/content.py`, `education-service/app/api/pi/streaming.py`, `education-service/app/api/pi/devices.py` (mint endpoint), `pi-client/pi_client/client.py`, `pi-client/pi_client/security/auth.py`, tests under `education-service/tests/`

- Mint: `POST /api/v1/pi/devices/{device_id}/tokens` admin human JWT → device access token.
- Dependency `get_current_device` for sync/content/stream; reject human-only tokens lacking `token_use=device` matching path `device_id`.
- Registration/cert admin stays on `get_current_user` (human).
- pi-client: prefer device token from config; document field name.
- Tests: AE4.

### U5. Safe tar extract + client download/complete alignment

Files: `pi-client/pi_client/cache/sync.py`, `pi-client/pi_client/client.py`, `pi-client/tests/test_sync_safe_extract.py` (new), `pi-client/tests/test_client.py`

- Replace `tar.extractall` with member validation (no `..`, no absolute paths); use `tar.data_filter` when available (Py3.12+) else manual filter.
- `download_package`: consume raw bytes (already); ensure callers tolerate stream (not JSON).
- `complete`: keep JSON body `{package_id}` matching server.
- Tests: poison tarball rejected; benign extract succeeds.

### U6. Security-service audit ingest + platform emit

Files: `security-service/security_service/main.py`, `app/auth/oauth2.py`, `app/api/gateway.py`, `app/config.py` (security-service URL), `.env.example`, `tests/unit/test_audit_emit.py` (new) or integration with mocked httpx

- Add `POST /api/security/audit` accepting event_type, action, success, optional user/ip/details; writes via `AuditLogger`.
- Platform helper `emit_audit_event(...)` best-effort httpx with short timeout; env `SECURITY_SERVICE_URL` default `http://security-service:8001`.
- Call on login success/fail and gateway proxy entry (include service name, method, success when known).
- Tests: mock transport; login still 200 if audit fails.

## Verification Contract

- Platform: `pytest tests/integration/test_api_auth.py tests/integration/test_api_capabilities.py -q` (plus new audit unit tests).
- Education: `cd education-service && pytest tests/unit/test_pi_sync_service.py tests/integration/test_api_pi_sync.py -q` (adapt if PG unavailable: prefer service-unit tests with sqlite/mock where CI allows; document exception).
- Pi-client: `cd pi-client && pytest tests/test_sync_safe_extract.py tests/test_client.py -q`.
- Nginx: `nginx -t` when image available, else static review that `auth_limit` and `/api/v1/pi/` locations exist.
- Behavior change: true — sync protocol, authz, edge routing, audit side effects.

Execution direction: test-first for contract surfaces (download/complete/check/device auth/safe extract); characterization for existing oauth2 login before inserting audit hooks.

## Definition of Done

- All U1–U6 merged on feature branch with tests green for new coverage.
- Capabilities advertise `sync.protocol_version: "1"` and education path matching nginx.
- Pilot audit hard blockers for download/complete/ready-state/safe-extract/device-auth addressed (offline UI + cache encryption remain out of scope).
- No new silent human-JWT device path for sync routes.
- PR opened; CI watched per LFG.

### Per-unit DoD

- U1: capabilities + validate tests pass.
- U2: nginx.conf contains auth_limit on `/api/auth/` and pi upstream location.
- U3: check/download/complete contract tests pass.
- U4: device JWT positive/negative tests pass.
- U5: poison tar test fails closed; client complete uses JSON body.
- U6: audit POST exists; platform emit mocked test; login resilient to audit outage.

## Appendix

- Origin audits: Project `docs/local-proto-audit.md`, `docs/nextcloud-gap-analysis.md`; repo `docs/research/local_first_pilot_audit_2026_05_14.md`.
- Settled-decisions brief (LFG): both tracks ship together (user-directed); stream download (pipeline); nginx pi route (pipeline); add validate (pipeline).
