# Local-First News 2026-05-14 - AI and local-first trend scan

**Source:** Uploaded Gmail PDF export of Local-First News, 2026-05-14, by Conrad Hofmeyr.  
**Newsletter issue scope:** News, tools, resources, and apps related to local-first software, local AI, sync engines, P2P networking, and private knowledge tools.  
**Research date:** 2026-05-14.

## Provenance

- Uploaded Gmail PDF export, not committed to the repo.
- File SHA256: `eb590eca7a92aa83898ab54a32e9fdbd5ee10426d396e2d28364311752e240b1`
- Copyright handling: the full newsletter text is not mirrored here. This note records only short attributed summaries, public links, and our interpretation.
- Web research note: Firecrawl CLI was installed for the preferred research workflow, but it required browser authentication. Public web fetch/search tools were used for targeted source lookups. The uploaded PDF contents were not sent to external web tools.

## SCP gate

- SCP tools were not available in this environment (`GetMcpTools` found no SCP/provenance tools).
- Treat this as a human-readable research note, not an approved RAG corpus.
- Before feeding the uploaded PDF or this synthesis into an automated agent/RAG handoff: extract -> chunk -> run SCP/provenance checks -> record results here.

## Primary public sources

- [Tether developer grants for local-first AI and payments infrastructure](https://tether.io/news/tether-launches-developer-grants-program-to-fund-local-first-ai-and-payments-infrastructure/)
- [PowerSync app performance/local SQLite case study](https://dev.to/doszhan/why-your-app-feels-slow-and-how-we-fixed-it-with-powersync-ehc)
- [Jazz v2: local-first relational database](https://jazz.tools/blog/what-is-jazz)
- [Ano local-first AI-native team chat](https://ano.chat/)
- [InfoWorld: local-first data and reactive SQL](https://www.infoworld.com/article/4168581/kill-the-loading-spinner-with-local-first-data-and-reactive-sql.html)
- [Local AI Needs to be the Norm](https://viralpique.com/local-ai-needs-to-be-the-norm/)
- [iroh 1.0.0-rc.0](https://www.iroh.computer/blog/iroh-1-0-0-rc-0)
- [Ditto SDK v5](https://www.ditto.com/blog/ditto-sdk-v5)
- [InfoQ: Local-First AI Inference architecture pattern](https://www.infoq.com/articles/local-first-ai-inference-cloud/)
- [QVAC](https://qvac.tether.io/)
- [SAP CAP inner-loop development](https://cap.cloud.sap/docs/guides/integration/inner-loops)
- [Logos Builders Hub](https://build.logos.co/)
- [Audrey README](https://raw.githubusercontent.com/Evilander/Audrey/ded9ea2294434ec0f42456352185be0bb1e589fb/README.md)
- [Beanies.family](https://beanies.family/)
- [Kuku](https://www.kuku.mom/)
- [Memora](https://appmemora.app/)
- [Bun Rust rewrite commit](https://github.com/oven-sh/bun/commit/23427dbc12fdcff30c23a96a3d6a66d62fdc091d)
- [Zero sync overview](https://zero.rocicorp.dev/docs/sync)

## Compressed take (F - facts)

- **Local AI is being funded and productized.** Tether launched grants for local-first AI and payments infrastructure, with deliverable-based payouts and a focus on QVAC and WDK components that run locally rather than through hosted AI or custodial intermediaries ([Tether](https://tether.io/news/tether-launches-developer-grants-program-to-fund-local-first-ai-and-payments-infrastructure/)). QVAC positions itself as a cross-platform SDK for local AI models, including LLM completions, local apps, and P2P/native deployment surfaces ([QVAC](https://qvac.tether.io/)).
- **The argument for local AI is trust, latency, cost, and failure isolation.** "Local AI Needs to be the Norm" argues that cloud AI dependencies turn app features into distributed systems with vendor uptime, rate-limit, billing, retention, and privacy obligations, and gives an on-device article-summary example using Apple's local model APIs ([Local AI Needs to be the Norm](https://viralpique.com/local-ai-needs-to-be-the-norm/)).
- **Local-first data is now a mainstream web architecture candidate.** PowerSync, InfoWorld, Zero, and Jazz all describe the same shift: move routine reads/writes to a local database, sync in the background, and stop blocking the UI on request/response loops ([PowerSync case study](https://dev.to/doszhan/why-your-app-feels-slow-and-how-we-fixed-it-with-powersync-ehc), [InfoWorld](https://www.infoworld.com/article/4168581/kill-the-loading-spinner-with-local-first-data-and-reactive-sql.html), [Zero](https://zero.rocicorp.dev/docs/sync), [Jazz](https://jazz.tools/blog/what-is-jazz)).
- **Different sync engines optimize different seams.** PowerSync emphasizes local SQLite in front of an existing backend/Postgres, Zero emphasizes sync against queried data and server reconciliation, Jazz v2 proposes an integrated local-first relational database with permissions, migrations, reactive subscriptions, and query-driven sync, while Ditto v5 emphasizes edge meshes, cross-platform DQL, observability, and mobile/edge reconnection behavior ([PowerSync case study](https://dev.to/doszhan/why-your-app-feels-slow-and-how-we-fixed-it-with-powersync-ehc), [Zero](https://zero.rocicorp.dev/docs/sync), [Jazz](https://jazz.tools/blog/what-is-jazz), [Ditto](https://www.ditto.com/blog/ditto-sdk-v5)).
- **The local-first AI inference pattern is pragmatic, not ideological.** The InfoQ architecture routes predictable documents through deterministic local extraction first, escalates only uncertain cases to Azure OpenAI Vision, and sends low-confidence or conflicting results to human review; the reported production workload cut Azure OpenAI costs by 75% and processing time by 55% on 4,700 documents ([InfoQ](https://www.infoq.com/articles/local-first-ai-inference-cloud/)).
- **P2P and decentralized infrastructure are maturing below the app layer.** iroh 1.0.0-rc.0 is a Rust networking stack release candidate for direct device connections with NAT traversal improvements and an API surface being stabilized for 1.0 ([iroh](https://www.iroh.computer/blog/iroh-1-0-0-rc-0)). Logos provides a builder hub for decentralized applications spanning blockchain, private P2P messaging, and decentralized storage, but its hub clearly marks the testnet as not production-ready ([Logos](https://build.logos.co/)).
- **Local-first apps are showing concrete UX/security patterns.** Beanies stores encrypted family data in user-controlled storage with only a lookup table in the cloud ([Beanies](https://beanies.family/)); Kuku keeps Markdown files local and applies AI edits as reviewable diffs ([Kuku](https://www.kuku.mom/)); Memora records/transcribes meetings on-device and exposes local meeting memory through MCP ([Memora](https://appmemora.app/)); Ano uses local-first chat data to make message rendering, scrolling, and offline behavior feel instant, while integrating Claude Code and CLI/MCP workflows into channels ([Ano](https://ano.chat/)).
- **Agent-era engineering is changing migration and memory practices.** Audrey provides a SQLite-backed memory/preflight layer for AI agents, with guard decisions, reflexes, decay, contradiction handling, and host integrations ([Audrey](https://raw.githubusercontent.com/Evilander/Audrey/ded9ea2294434ec0f42456352185be0bb1e589fb/README.md)). Bun's public Rust rewrite commit includes many workflow files for staged migration, verification, locking, CI issue classification, and agent swarm-style porting around a million-line rewrite ([Bun commit](https://github.com/oven-sh/bun/commit/23427dbc12fdcff30c23a96a3d6a66d62fdc091d)).

## Subject scan

| Subject | What the source says | Valuable for our local-first software development knowledge | Watch / avoid |
|---|---|---|---|
| Tether developer grants | Grants fund local-first AI, self-custodial payment infrastructure, QVAC, WDK, docs, apps, research, and standards ([Tether](https://tether.io/news/tether-launches-developer-grants-program-to-fund-local-first-ai-and-payments-infrastructure/)). | Local-first is attracting capital around "compute and keys stay local"; payment-enabled agents may become a real design surface. | Treat crypto/payment integrations as high-risk until threat models, custody boundaries, and compliance needs are explicit. |
| PowerSync performance case study | The author moved routine UI reads/writes to local SQLite, used PowerSync for sync, kept auth/permissions/business validation on the backend, and noted migration/conflict/debugging tradeoffs ([PowerSync case study](https://dev.to/doszhan/why-your-app-feels-slow-and-how-we-fixed-it-with-powersync-ehc)). | Strong reference pattern: local DB is the UI source of truth; backend remains the trust boundary. | Do not call local-first "just a cache"; also do not trust client writes. Conflict and local schema migration need first-class design. |
| Bun Rust rewrite / Jazz v2 | Bun's Rust rewrite commit shows large-scale staged migration and agent workflow artifacts ([Bun commit](https://github.com/oven-sh/bun/commit/23427dbc12fdcff30c23a96a3d6a66d62fdc091d)). Jazz v2 is a local-first relational database in public alpha ([Jazz](https://jazz.tools/blog/what-is-jazz)). | The valuable local-first part is Jazz: collapse ORM, sync, permissions, migrations, and reactive state into one database-shaped abstraction. The valuable AI-engineering part is Bun's explicit migration orchestration. | Do not infer production readiness from announcement energy; Jazz is alpha, and Bun's rewrite was not yet non-canary per the commit message. |
| Ano on Zero / Slack model | Ano says local-first sync puts messages on disk for sub-millisecond render, instant scroll, and offline behavior; Zero documents sync engines as local copies with background reconciliation ([Ano](https://ano.chat/), [Zero](https://zero.rocicorp.dev/docs/sync)). | Team software and agent chat should be judged by "is the work surface waiting on the network?" not just by message features. | Ano says E2E encryption is on the roadmap, not shipped; do not overstate current privacy guarantees. |
| Reactive SQL / in-browser SQLite | InfoWorld demonstrates React + SQLite Wasm + PowerSync + Supabase, with UI subscriptions over local SQL and background sync ([InfoWorld](https://www.infoworld.com/article/4168581/kill-the-loading-spinner-with-local-first-data-and-reactive-sql.html)). | Use reactive SQL as a candidate default for high-interaction apps where state continuity matters. | Keep REST/GraphQL for simple dashboards/forms where the sync complexity is not buying enough UX or resilience. |
| Local AI needs to be the norm | Local models are framed as data transformers for user-owned data, with typed outputs and privacy-by-architecture instead of cloud trust promises ([Local AI Needs to be the Norm](https://viralpique.com/local-ai-needs-to-be-the-norm/)). | Good product rule: use local AI for summarize/classify/extract/rewrite/normalize when the input is already on-device. | Cloud models still make sense for tasks requiring frontier reasoning or broad world knowledge; decide per feature. |
| iroh 1.0.0-rc.0 | iroh is stabilizing a Rust stack for direct device connections; the RC refines public APIs and improves NAT traversal ([iroh](https://www.iroh.computer/blog/iroh-1-0-0-rc-0)). | Candidate layer for direct peer/device connectivity when server relay should be optional or fallback. | RC status and breaking changes mean pinning, upgrade tests, and protocol-level observability matter. |
| Ditto SDK v5 | Ditto v5 is a rearchitecture with query/sync performance improvements, one DQL API across platforms, virtual system collections for observability, and mixed v4.11+/v5 migration support ([Ditto](https://www.ditto.com/blog/ditto-sdk-v5)). | Useful for edge/mobile fleets where devices must sync under weak network conditions and debugability on-device matters. | Commercial platform and migration complexity need evaluation against open-source/self-hosting needs. |
| Local-first AI inference | Deterministic local extraction first, cloud vision fallback second, human review third; reported lower cost/time and bounded silent hallucination ([InfoQ](https://www.infoq.com/articles/local-first-ai-inference-cloud/)). | This is the clearest immediately reusable AI architecture pattern: "ask whether the model call is needed" before calling it. | Works best for predictable document layouts and well-defined fields; breaks down for free-form, scanned-dominant, or multi-field dependency-heavy corpora. |
| QVAC | QVAC markets a single API for local/decentralized AI across Linux, macOS, Windows, Android, and iOS, with local models, P2P-native surfaces, and WDK-enabled autonomous transactions ([QVAC](https://qvac.tether.io/)). | Track as a possible local inference API surface, especially if cross-platform local AI and payments converge. | Separate working SDK evidence from positioning language; do not adopt transaction-capable agents without strict approvals and audit logs. |
| CAP Node.js local-first dev | CAP inner-loop docs show local mocks for remote services, `cds watch`, shared in-memory mocks, workspaces, and >100x faster turnaround in the cited example ([SAP CAP](https://cap.cloud.sap/docs/guides/integration/inner-loops)). | Local-first is not only end-user UX; it is also a development-loop principle: mock all external services with contract fidelity. | Mock fidelity must be tested against real integrations; mocks can hide contract drift. |
| Logos Builders Hub | Logos exposes a modular stack for decentralized apps: blockchain, private P2P messaging, and decentralized storage, with docs, scaffold, RFPs, and office hours; the testnet warns about breaking changes/data resets ([Logos](https://build.logos.co/)). | Useful landscape marker for censorship-resistant/local-sovereign architecture. | Not production-ready; evaluate only for prototypes or research. |
| Audrey | Audrey is a SQLite-backed memory and continuity layer for agents, with preflight guard, reflexes, recall, consolidation, decay, contradiction handling, MCP, CLI, REST, and local embeddings ([Audrey](https://raw.githubusercontent.com/Evilander/Audrey/ded9ea2294434ec0f42456352185be0bb1e589fb/README.md)). | Strong fit with "agent-native local-first": memory should be local, inspectable, pre-action, and validated after use. | Never encode secrets; isolate `AUDREY_DATA_DIR` by tenant/project; require auth for non-loopback REST. |
| Beanies.family | Open-source family management app with AES-256-GCM encryption, user-held keys, user-controlled storage, IndexedDB encrypted cache, Automerge CRDTs, and only a lookup table in the cloud ([Beanies](https://beanies.family/)). | Good reference for "server as locator, not owner" and user-controlled encrypted data files. | Account recovery and key loss become product design problems, not support footnotes. |
| Kuku | Native macOS Markdown workspace using local files, wikilinks/backlinks/graph, offline operation, and AI edits as reviewable diffs ([Kuku](https://www.kuku.mom/)). | Reviewable AI diffs are the right default for agent edits to human-owned knowledge. | AI features may still call external providers; distinguish local files from local inference. |
| Memora | macOS app records/transcribes meetings locally with Whisper, stores data locally, and exposes meeting memory through MCP to Claude/Cursor/other clients ([Memora](https://appmemora.app/)). | Pattern: sensitive personal/team knowledge can be local-first and agent-accessible through MCP without becoming a hosted SaaS corpus. | MCP access to meeting data needs local permissioning, audit, and retention controls. |

## Meditation (I + M - interpretation and implications)

**I:** The through-line is not just "offline support." The trend is toward moving the trust boundary, the latency boundary, and the cost boundary back onto the user's machine wherever the task allows it. Local-first is becoming the architectural answer to several AI-era problems at once: privacy, prompt/data retention, cloud inference cost, fragile vendor dependencies, slow UX, and agent memory continuity.

**I:** The sources split local-first into at least five layers:

1. **Data layer:** SQLite/Wasm, embedded local stores, reactive SQL, CRDTs, sync engines.
2. **Inference layer:** local models first, cloud models as escalation, human review for bounded error.
3. **Networking layer:** P2P direct connections, relay fallback, decentralized messaging/storage.
4. **Agent layer:** local memories, preflight guards, MCP-accessible personal/team data, reviewable diffs.
5. **Developer-loop layer:** local mocks, local data, contract-first service emulation, reproducible inner loops.

**M1:** We should evaluate local-first candidates with a repeatable matrix instead of picking a stack by vibe. Minimum dimensions: data sensitivity, latency budget, offline requirement, conflict model, partial-sync need, schema migration story, backend trust boundary, storage encryption, observability, self-hosting/commercial lock-in, and agent access surface.

**M2:** For AI features, default to a "local-first inference router" question: can deterministic code or a small local model handle this input with measurable confidence? Only escalate to cloud models when local confidence is low or the task needs frontier capability. Human review is part of the architecture for high-impact outputs, not a last-minute UX patch.

**M3:** Local-first should not mean "frontend trusted." The backend still validates permissions, business rules, and uploaded mutations. The local database is a responsiveness and continuity surface; it is not the authority for invariants.

**M4:** Agent-accessible local knowledge is valuable only if it is inspectable and bounded. Audrey, Kuku, and Memora point toward a stack where agents can recall and act from local state, but only with preflight checks, redaction, reviewable edits, and isolation by project/tenant.

**M5:** The Bun Rust rewrite commit is a reminder that agent-era migrations need explicit orchestration artifacts: locks, phase plans, classification passes, verification loops, CI triage, and small checkable tasks. That pattern is transferable even when the target technology is unrelated.

## Caution / scope

- This note is a research digest, not a decision record.
- Several sources are alpha, beta, RC, private beta, or testnet status; treat them as trend signals until validated.
- "Local-first" can increase responsibility for local data security, key recovery, migrations, conflict resolution, and observability.
- Payment-enabled agents, medical/meeting data, and family finance data are high-sensitivity domains. Require explicit threat modeling, approvals, and rollback/audit plans before implementation.

## Backlog candidates (from meditation)

| ID | Type | Tag | Candidate one-liner | Acceptance (one sentence) | Routed to |
|----|------|-----|----------------------|---------------------------|-----------|
| M1 | DOCS | M | Create a local-first stack evaluation checklist | A markdown checklist exists with the dimensions from M1 plus example pass/fail questions for data, inference, networking, agent, and developer-loop layers. | deferred |
| M2 | CODE/RESEARCH | M | Spike a local-first AI inference router for document extraction | A local script processes a small sample with deterministic extraction first, emits confidence/routing decisions, and requires explicit opt-in before any cloud call. | deferred |
| M3 | CONFIG/DOCS | M | Evaluate Audrey-style local agent memory preflight | A dry-run note documents install surface, data isolation, secret redaction policy, and one safe preflight demo result before any persistent use. | deferred |

## Open questions

- Which current project has enough offline/sensitive/high-latency pain to justify a local-first data pilot?
- Do we need a dedicated `docs/local-first/` handbook, or should local-first notes continue as `docs/research/` meditations until a concrete implementation exists?
- What local storage encryption and key recovery pattern fits our users without turning support into a decryption bypass?
- For agent memory, should local MCP data be per-project, per-user, or both?
- If future agents should use Firecrawl for research, configure Firecrawl authentication in the cloud environment rather than relying on ad hoc installs.

---

*Archived in-repo as a sourced synthesis; do not mirror the full newsletter PDF here.*
