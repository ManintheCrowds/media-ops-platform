---
title: "Pi sync pilot / acceptance pass (WSL)"
date: 2026-09-27
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
origin: User LFG Option A; docs/research/local_first_pilot_audit_2026_05_14.md; docs/plans/2026-09-26-local-first-pi-sync-platform-hardening.md (merged PR #144); Project store local-proto-audit + nextcloud-gap-analysis
---

# Pi sync pilot / acceptance pass (WSL)

## Goal Capsule

Prove on this Ubuntu WSL checkout that Track A Pi sync (device JWT, package FSM + checksum-gated `has_updates`, stream download, safe tar extract, capabilities, nginx `/api/v1/pi/`) works as shipped in PR #144; close blocking test/behavior gaps; leave a durable acceptance record.

Authority: user-directed LFG Option A (pilot/acceptance, not P1 assimilation wedges); stay on assimilation/contracts path; prefer code+test fixes over docs-only when behavior is broken.

Stop when: automated acceptance gates for contract / integrity / safe-extract / ready-state / device-auth pass locally without Docker; nginx + capabilities statically verified; residual gates (offline UI, cache encryption, compose live stack, org-membership authz beyond device JWT) filed in the acceptance record; PR opened with evidence.

---

## Product Contract

### Problem

PR #144 landed the sync contract and hardening, but this machine has not run an acceptance pass. Gaps remain: no education HTTP integration suite for sync routes (planned `test_api_pi_sync.py` never shipped), no checksum-mismatch client test, education integration conftest assumes Postgres (unavailable without Docker), and no durable pilot acceptance artifact. Docker Engine is not installed in this WSL distro, so compose-based live proof is not available here.

### Requirements

- R1. Contract gate: HTTP-level proof that `sync/check`, `sync/request`, stream `download`, and `sync/complete` agree on shapes/status codes under device JWT, without requiring Docker/Postgres.
- R2. Ready-state gate: pending/no-checksum packages never set `has_updates=true`; ready packages with checksum appear and download as `application/gzip` bytes.
- R3. Authz gate (device trust): human JWT rejected on sync routes; device JWT for device A rejected on device B paths; matching device JWT succeeds.
- R4. Integrity gate: pi-client rejects a package whose on-disk checksum does not match the advertised checksum before extract.
- R5. Safe extraction gate: path-traversal / absolute tar members remain rejected (keep or extend existing coverage).
- R6. Platform discovery gate: `GET /api/capabilities` still advertises `sync.protocol_version`, `education_base_path=/api/v1/pi`, `download_mode=stream`.
- R7. Nginx static gate: `nginx/nginx.conf` applies `auth_limit` on `/api/auth/` and proxies `/api/v1/pi/` to education-service.
- R8. Durable acceptance record under `docs/research/` stating pass/fail per gate, commands run, host constraints (no Docker), and residual tickets for out-of-scope gates.
- R9. Fix blocking behavioral gaps discovered while running the suite (prefer code+test over docs-only).

### Actors

- education-service — Pi sync authority under `/api/v1/pi`
- pi-client — edge sync consumer (checksum + safe extract)
- platform API — capabilities discovery
- nginx — edge route + auth rate limit (static review on this host)
- Operator on Ubuntu WSL — runs pytest acceptance; cannot rely on Docker Desktop integration here

### Key flows

- F1. Device JWT sync happy path
  - **Trigger:** Acceptance suite mints/uses device token for `pi-1`
  - **Steps:** request package → check has_updates → download stream → complete JSON body
  - **Outcome:** 200s; body is gzip bytes; complete acknowledges package_id
- F2. Negative device auth
  - **Trigger:** Human JWT or wrong-device JWT on sync/check
  - **Outcome:** 401/403; no package metadata leak beyond auth failure
- F3. Integrity fail-closed
  - **Trigger:** SyncManager processes package file with wrong checksum metadata
  - **Outcome:** Package not extracted; failure recorded/returned without writing outside cache

### Acceptance examples

- AE1. Covers R2. Given pending package without checksum, check returns `has_updates=false`.
- AE2. Covers R1/R2. Given ready package with path+checksum, download returns gzip stream and `X-Package-Checksum` header.
- AE3. Covers R1. `POST .../sync/complete` with JSON `{ "package_id": N }` returns completed status.
- AE4. Covers R3. Human JWT on sync/check → forbidden/unauthorized; matching device JWT → 200.
- AE5. Covers R3. Device token for `pi-1` on `pi-2` path → 403.
- AE6. Covers R4. Checksum mismatch → extract skipped / ValueError or false from process path.
- AE7. Covers R5. Poison tar `../` member rejected.
- AE8. Covers R6/R7. Capabilities + nginx.conf assertions green.

### Product scope

In: Automated acceptance for Track A sync contract on WSL; sqlite/TestClient-based education HTTP tests; pi-client integrity test; capabilities/nginx static checks; gap fixes found during the pass; acceptance markdown record.

Out: Docker compose live stack on this host; physical Pi hardware; offline UI cache wiring; local cache encryption; OIDC/share/OCM/Nextcloud Hub rewrite; P1 assimilation wedges; home-cyber-risk pilot.

### Open questions

- OQ1 (deferred): When Docker Desktop WSL integration is enabled later, add an optional compose smoke job — not required to close this LFG.
- OQ2 (deferred): Org-membership authz beyond matching `device_id` on the token — residual ticket if still thin after device JWT gate.
- OQ3 (deferred): Offline gate + secret gate from the May 2026 pilot audit remain non-goals for this acceptance slice (explicit in prior plan DoD).

---

## Planning Contract

### Key technical decisions

- KTD1. session-settled: Run Option A pilot/acceptance (+ gap fixes), not P1 assimilation wedges. Provenance: user-directed. Rejected: Option B (OIDC/share/OCM) and Option C (plan-only). Reason: user invoked `/lfg A`.
- KTD2. session-settled: Stay on assimilation/contracts path; do not rewrite as Nextcloud Hub. Provenance: user-approved (gap analysis). Rejected: full Hub rewrite.
- KTD3. session-settled: Execute on Ubuntu WSL checkout `media-ops-platform` (not Windows-native agent). Provenance: user-approved. Rejected: Windows-native `agent worker` (better-sqlite3 ABI).
- KTD4. session-settled: Treat PR #144/#145 as landed baseline; this work is acceptance + gap fixes, not greenfield reimplementation. Provenance: user-approved.
- KTD5. Acceptance proof on this host = **pytest + ASGI/TestClient** (sqlite for education sync HTTP), not Docker compose. Provenance: planning (Docker CLI absent in this WSL). Rejected: blocking the pilot on compose.
- KTD6. Do **not** rewrite education `tests/conftest.py` Postgres integration for the whole suite; add a focused sync acceptance fixture/module that is docker-free. Provenance: planning (minimal blast radius). Rejected: converting all education integration tests to sqlite in this pass.
- KTD7. Out-of-scope audit gates (offline UI, cache encryption, compose live, deeper org authz) go into the acceptance record as **residuals**, not silent passes. Provenance: planning aligned with prior plan out-of-scope.

### Technical design (directional)

```text
WSL host (no Docker)
  ├── pytest platform: capabilities (existing)
  ├── pytest education: sqlite TestClient → /api/v1/pi/... sync routes + device JWT
  ├── pytest pi-client: safe extract (existing) + checksum mismatch (new)
  ├── static: nginx.conf auth_limit + /api/v1/pi/
  └── docs/research/*-acceptance-*.md  ← durable pass/fail matrix
```

### Assumptions

- A1. Main already contains PR #144 sync contract code and PR #145 CI setuptools fix.
- A2. `uv` is available to create ephemeral venvs for platform / education-service / pi-client test runs.
- A3. Physical Pi and full compose are unavailable; automated contract proof is sufficient for this pilot slice.
- A4. Settled decisions remain valid; if Docker-or-hardware requirement were mandatory for “pilot,” that would invalidate KTD5 — report `settled-decision-invalidated` only if user later requires live compose as the sole acceptance definition (not current brief).

### Sequencing

U1 education sync HTTP acceptance → U2 pi-client integrity → U3 platform/nginx static gates → U4 fix blocking gaps → U5 acceptance record.

### Risks

- Risk: FastAPI dependency overrides + device auth interact poorly with OAuth2PasswordBearer — mitigate by following existing education TestClient patterns and explicit override of `get_current_device` only when unavoidable.
- Risk: Scope creep into offline UI — mitigate via KTD7 residuals.
- Risk: Flaky checksum test if process path short-circuits — mitigate by testing `_verify_checksum` and/or `_process_package` with temp files.

### Patterns to follow

- `education-service/tests/unit/test_pi_sync_service.py` sqlite StaticPool fixture
- `tests/integration/test_api_capabilities.py` for platform shape assertions
- `pi-client/tests/test_sync_safe_extract.py` for SyncManager construction via `__new__`
- Prior plan `docs/plans/2026-09-26-local-first-pi-sync-platform-hardening.md` for contract semantics

---

## Implementation Units

### U1. Education sync HTTP acceptance suite (docker-free)

**Goal:** Prove check/request/download/complete + device JWT at the HTTP layer using sqlite + TestClient.

**Requirements:** R1, R2, R3 — Covers AE1–AE5

**Dependencies:** None (baseline #144 code)

**Files:** `education-service/tests/unit/test_pi_sync_http_acceptance.py` (new) or `education-service/tests/integration/test_api_pi_sync_acceptance.py` (new); reuse models/services from `education-service/app/`; optionally thin helpers under `education-service/tests/`

**Approach:**

1. Build an in-memory sqlite engine + `create_all`, seed org + device(s), override `get_db`.
2. Use real `create_device_token` for Authorization headers; assert human JWT fails on sync/check.
3. Exercise request → check → download → complete; assert download `media_type`/body is gzip and checksum header present.
4. Assert wrong-device token → 403.
5. Keep Postgres-based `tests/conftest.py` unchanged (KTD6).

**Execution note:** Start with failing HTTP tests for AE4/AE2 if coverage is missing, then green against existing handlers; only change production code if a real contract bug surfaces.

**Patterns to follow:** Unit sqlite fixture in `test_pi_sync_service.py`; router wiring in `education-service/app/api/pi/sync.py`.

**Test scenarios:**

- Covers AE1. Pending package without checksum → check `has_updates` false via HTTP.
- Covers AE2. After request, download returns 200 with gzip bytes and checksum header.
- Covers AE3. Complete with JSON body returns completed for that package_id.
- Covers AE4. Human JWT on check → 403 (or 401); device JWT → 200.
- Covers AE5. Token for other device_id → 403.
- Download of pending package → 202 or 409 per existing handler semantics.
- Unauthenticated check → 401.

**Verification:** New education acceptance module passes under `uv`/pytest without Postgres or Docker.

### U2. Pi-client integrity gate test

**Goal:** Automate checksum mismatch rejection before extract.

**Requirements:** R4, R5 — Covers AE6, AE7

**Dependencies:** None

**Files:** `pi-client/tests/test_sync_safe_extract.py` and/or `pi-client/tests/test_sync_integrity.py` (new); `pi-client/pi_client/cache/sync.py` only if mismatch path is broken

**Approach:**

1. Add test that writes a tar.gz whose content hash ≠ advertised checksum and asserts SyncManager fails closed (no extract of payload).
2. Keep poison-path tests green (AE7).
3. Fix `_verify_checksum` / process path only if tests expose a behavior bug.

**Execution note:** Prefer testing the public process path used by sync; fall back to `_verify_checksum` + `_extract_package` composition if async orchestration is heavy to mock.

**Test scenarios:**

- Covers AE6. Mismatched checksum → process does not extract members into cache.
- Matching checksum + safe members → extract succeeds (happy path).
- Covers AE7. Existing traversal rejection still passes.

**Verification:** pi-client integrity tests green.

### U3. Platform capabilities + nginx static acceptance

**Goal:** Lock discovery and edge config gates into the acceptance run.

**Requirements:** R6, R7 — Covers AE8

**Dependencies:** None

**Files:** `tests/integration/test_api_capabilities.py` (extend if thin); `tests/unit/test_nginx_pi_routes.py` (new) or assert helpers reading `nginx/nginx.conf`; optionally `docs/SECURITY.md` only if operator note is wrong

**Approach:**

1. Confirm capabilities assertions for protocol_version, education_base_path, download_mode.
2. Add a small unit test that reads `nginx/nginx.conf` text and asserts `limit_req zone=auth_limit` under `/api/auth/` and `location /api/v1/pi/`.
3. Do not require `nginx -t` on this host.

**Test scenarios:**

- Covers AE8. Capabilities JSON shape matches sync contract advertisement.
- nginx.conf contains auth_limit on auth location and pi proxy location.

**Verification:** Platform pytest subset green; nginx assertions green.

### U4. Fix blocking gaps found during the pass

**Goal:** Prefer code+test fixes when acceptance scenarios fail for real product reasons.

**Requirements:** R9

**Dependencies:** U1, U2, U3

**Files:** Touched production paths under `education-service/app/`, `pi-client/pi_client/`, `app/`, `nginx/` as failures dictate — keep diffs minimal

**Approach:**

1. Classify each failure: test harness bug vs product bug.
2. Product bugs: fix and keep the new regression test.
3. Harness bugs: fix fixture/overrides only.
4. Non-blocking residuals (offline UI, encryption, compose): do not implement here — record in U5.

**Test expectation:** none beyond regressions already owned by U1–U3 — this unit lands only the production fixes those suites demand.

**Verification:** Full acceptance command set from Verification Contract is green after fixes.

### U5. Durable pilot acceptance record

**Goal:** Leave an auditable pass/fail matrix for this WSL run.

**Requirements:** R8

**Dependencies:** U1–U4

**Files:** `docs/research/local_first_pi_sync_pilot_acceptance_2026_09_27.md` (new)

**Approach:**

1. Table each gate (contract, ready-state, authz-device, integrity, safe-extract, capabilities, nginx, offline, secret, restart, compose-live) with status pass / residual / n/a.
2. Record host facts (WSL, no Docker), commit SHA, commands run, PR link placeholder filled at ship time.
3. Explicitly list residuals with recommended follow-up (not silent green).

**Test expectation:** none -- documentation artifact; content validated by matching U1–U3 evidence.

**Verification:** File exists, cites evidence, and matches actual suite outcomes.

---

## Verification Contract

- Education: run the new docker-free sync HTTP acceptance module with `uv` + pytest from `education-service/`.
- Pi-client: run safe-extract + integrity tests from `pi-client/`.
- Platform: run capabilities (+ nginx static test) from repo root.
- Behavior change: true when U4 fixes product code; may be false if only tests+docs — still ship the acceptance record.
- Execution direction: test-first for missing gates; fix-forward only on red product failures.

---

## Definition of Done

- U1–U3 suites green on this WSL host without Docker/Postgres.
- U4 applied for any blocking product gaps discovered.
- U5 acceptance record committed with honest residual section.
- Feature branch pushed; PR opened against main; CI babysat to decided.
- No Hub rewrite; no Option B assimilation wedges.

### Per-unit DoD

- U1: HTTP AE1–AE5 covered and passing docker-free.
- U2: Checksum mismatch fail-closed tested; poison tar still passes.
- U3: Capabilities + nginx static assertions pass.
- U4: No known red acceptance scenario left unfixed or unexplained.
- U5: Acceptance markdown present under `docs/research/`.

## Appendix

- Origin: `docs/research/local_first_pilot_audit_2026_05_14.md` acceptance gates; merged plan `docs/plans/2026-09-26-local-first-pi-sync-platform-hardening.md`; Project store audits `local-proto-audit.md`, `nextcloud-gap-analysis.md`.
- Host constraint discovered at planning: Docker CLI not present in this WSL distro → KTD5.
- Confidence: high on scope/KTDs; medium on exact TestClient override shape until U1 implements (implementation-time detail, not a blocking product question).
