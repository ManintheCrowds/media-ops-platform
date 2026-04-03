---
name: Pass D + resolved Qs
overview: (Done) North-star brainstorm Pass D + resolved open questions. (Follow-on) Critic-engagement discipline, per-theme mitigations (metrics, precedence, ethics, L402 commercial, sync policy, privacy/logs, survey separation), and optional artifacts in brainstorm or adjacent docs.
todos:
  - id: resolve-open-qs
    content: Move three open questions to Resolved; clear Open questions section
    status: completed
  - id: pass-a-influence
    content: Split Influence into three sub-outcome rows or subsection in Pass A table
    status: completed
  - id: pass-d-section
    content: "Add Pass D: MCP scope table, L402 design questions, DoD matrix, mermaid, repo links"
    status: completed
  - id: critic-log-and-gates-doc
    content: Add critic log template + gate calibration (intent-alignment vs critic JSON) to brainstorm or short doc
    status: completed
  - id: metrics-questionnaire-pass-a
    content: Leading/lagging/anti-metrics per domain + Goodhart questionnaire block + task metric-class tagging note
    status: completed
  - id: precedence-spec
    content: One-page precedence spec (macro weekly / micro soft-rank / escalate); intent-alignment drift thresholds note
    status: completed
  - id: org-intent-ethics-l402-sync-privacy-survey
    content: "Batch: org-intent ethics IDs; L402 commercial + risk register; sync policy; privacy/logs; survey mapping table"
    status: completed
isProject: false
---

# Pass D brainstorm update and resolved open questions

## Scope

- **Single primary artifact:** [D:/openharness/docs/brainstorms/2026-03-22-org-intent-north-star-brainstorm.md](D:/openharness/docs/brainstorms/2026-03-22-org-intent-north-star-brainstorm.md)
- **Out of scope (unless you ask later):** editing `D:/software/.cursor/plans/`*; changing org-intent JSON examples beyond what the brainstorm text implies; implementing L402 (this pass is **design-time documentation** only).

## 1. Resolve open questions (move into “Resolved questions”)

Apply your decisions verbatim in spirit:


| Former open question    | Resolution to record                                                                                                                                                                                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Influence: one vs split | **Three sub-outcomes under Influence** (separate measurable outcomes, same parent domain): **artist practice / public creative output**, **open-source / alignment-adjacent shipping**, **Fedimint-style collective / communal experiments** (each with its own anti-goal line where useful).                 |
| Regulatory honesty      | **Operate legally** in relevant jurisdictions; be **pro-social** and **collaborative** (no laundering risk onto others; escalate ambiguous liability). Tie to existing Pass B “Legal, contractual…” bullets—add one short sentence that this is the v1 public bar (not a substitute for professional advice). |
| Quarter calendar        | **Calendar year** Q1–Q4 (Jan–Dec).                                                                                                                                                                                                                                                                            |


**Edit:** Remove or empty the three bullets under `## Open questions` (or replace with “None — see Resolved”); append three new bullets under `## Resolved questions` with the above.

## 2. Pass A — refine Influence (table + optional sub-table)

- Replace the single **Influence** row in the domain table (lines 26–30) with either:
  - **Option A (compact):** one **Influence** row summarizing the three lanes + pointer to a new subsection, or
  - **Option B (explicit):** three rows prefixed e.g. `Influence — art`, `Influence — open source`, `Influence — collective`.

**Recommendation:** **Option B** for quarterly measurability (each row gets its own “example shape” and anti-goal), with a one-line note that soft-rank still applies to the parent **Influence** domain.

## 3. New section: Pass D — Operational harness (OpenHarness + L402 + tools)

Add after Pass C (before “Why this matters for prompting”) a `## Pass D — Operational harness` with four subsections:

### D.1 Role in the stack

- **OpenHarness:** intent docs, handoffs, gates ([INTENT_ENGINEERING.md](D:/openharness/docs/INTENT_ENGINEERING.md)), authority model.
- **Tools/MCP:** agents use the same capabilities as operators where parity matters (per Pass C); scope is **documented**, not “everything installed.”

### D.2 Skills / MCP in scope (template)

A **short table** with columns such as: **Capability**, **In scope (Y/N/TBD)**, **Notes** — seeded from what you already reference:

- OpenGrimoire alignment context + brain map ([MCP_CAPABILITY_MAP.md](D:/portfolio-harness/.cursor/docs/MCP_CAPABILITY_MAP.md), OpenGrimoire rows).
- SCP / provenance when Bitcoin-sourced or untrusted content (per portfolio Bitcoin agent capabilities — pointer only).
- **Placeholder rows** for: browser automation, git, project-specific MCPs — mark **TBD** until you curate a minimal set per repo.

**Intent:** a checklist to freeze “default harness” vs “on-demand” tools without implementing billing yet.

### D.3 L402 / budget / metering (design-time only)

Point to [CASHU_L402_REFERENCE.md](D:/portfolio-harness/docs/CASHU_L402_REFERENCE.md) for **macaroon + preimage**, `WWW-Authenticate`, and Cashu vs L402 comparison.

List **explicit open design questions** (no answers required in this edit):

- **Who pays:** human operator vs org budget vs per-project wallet; prepaid vs pay-per-request.
- **Which endpoints:** which HTTP surfaces (OpenGrimoire API, future agent proxy, third-party tools) are payment-gated vs free tier.
- **Preimage / retry flow:** how the client obtains invoice, pays, and retries with `Authorization: L402 <macaroon>:<preimage>`; macaroon caveats and rotation.
- **Metering unit:** per request, per token, per session — align with observability later.

Keep this as a **bullet list** so it stays honest “backlog,” not fake precision.

### D.4 Definition of done by project type

Align with [VERIFICATION_CI_ALIGNMENT.md](D:/portfolio-harness/docs/VERIFICATION_CI_ALIGNMENT.md) and OpenHarness rules:


| Project type                             | Minimum bar                                                                                                                                                                                                                            |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Docs-only** (single file, low stakes)  | Human read + link check if adding paths.                                                                                                                                                                                               |
| **Docs multi-file / normative**          | Same + **critic JSON** per [critic-loop-gate](D:/portfolio-harness/.cursor/rules/critic-loop-gate.mdc) (or workspace copy).                                                                                                            |
| **Code / config**                        | Project CI alignment: **tests + lint + typecheck/build** as applicable; UI changes add smoke/browser review when the repo expects it.                                                                                                  |
| **Substantive multi-file / high-stakes** | **Critic JSON + intent-alignment JSON** ([intent-alignment-gate.mdc](D:/openharness/.cursor/rules/intent-alignment-gate.mdc)); handoff block per [HANDOFF_FLOW.md](D:/openharness/docs/HANDOFF_FLOW.md) when the session changed code. |


Add one line: **L402-related code** is not “done” until payment flow is testable in staging (even if manual) — defer until implementation ticket exists.

## 4. Extend “Repo alignment”

Append bullets for Pass D:

- L402 / Cashu reference: [CASHU_L402_REFERENCE.md](D:/portfolio-harness/docs/CASHU_L402_REFERENCE.md)
- Verification / CI: [VERIFICATION_CI_ALIGNMENT.md](D:/portfolio-harness/docs/VERIFICATION_CI_ALIGNMENT.md)
- Dual gates: [intent-alignment-gate.mdc](D:/openharness/.cursor/rules/intent-alignment-gate.mdc) + critic-loop rule in portfolio/workspace

## 5. Optional diagram (small)

One **mermaid** block under Pass D: `Client` → `402 challenge` → `Lightning pay` → `retry with L402 header` → `Resource`; parallel swimlane for `OpenHarness handoff + gates` (documentation-only boundary).

---

## Verification after edit

- Manually confirm relative links from `openharness/docs/brainstorms/` resolve to `portfolio-harness` paths (same pattern as Pass C).
- No JSON schema change required for this brainstorm-only update.

---

## 6. Follow-on: Engaging the critic (normative mitigations)

**Status:** Not yet applied in-repo; use this section when implementing the next slice of docs / org-intent / questionnaire work.

### 6.1 Discipline (how to use gates and logs)


| Practice                  | Detail                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Critic log**            | For each theme below, maintain rows: **risk**, **current mitigation**, **residual risk**, **next experiment**. Place as a subsection in [2026-03-22-org-intent-north-star-brainstorm.md](D:/openharness/docs/brainstorms/2026-03-22-org-intent-north-star-brainstorm.md) or a short adjacent doc (e.g. `docs/critic-log-org-intent.md` under openharness) if the brainstorm grows too large. |
| **Artifact vs process**   | Each critique should yield **one** concrete outcome: either an **artifact** (boundary text, questionnaire item, sync policy paragraph, org-intent `values` / `hard_boundaries` ids) or a **process** (e.g. quarterly anti-metric review).                                                                                                                                                    |
| **Intent-alignment gate** | Use for **drift** and **constraint violations**, not every trade-off. Calibrate **when** it fires (drift thresholds) so unresolved **conflict** surfaces, not routine tension.                                                                                                                                                                                                               |
| **Critic JSON**           | Reserve for **multi-file / normative** updates per Pass D definition-of-done table ([VERIFICATION_CI_ALIGNMENT](D:/portfolio-harness/docs/VERIFICATION_CI_ALIGNMENT.md), [intent-alignment-gate.mdc](D:/openharness/.cursor/rules/intent-alignment-gate.mdc)).                                                                                                                               |


### 6.2 Goodhart / shallow metrics


| Item                              | Implementation                                                                                                                                                                                                                                         |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Org-intent / quarterly review** | For **each domain** (Health, Wealth, and **three Influence lanes**): add bullets or fields for **leading indicators** (process you control), **lagging indicators** (outcomes that lag), **anti-metrics** (“we will not optimize X even if it moves”). |
| **Questionnaire**                 | One block: *“What would look like success but would actually violate your values?”* — Goodhart shield.                                                                                                                                                 |
| **Agent behavior**                | Task-decomposition prompts: tag each leaf with **which metric class** it serves; if only **lagging vanity** metrics would move, flag **metric gaming risk** for human review.                                                                          |
| **Process**                       | Optional: **quarterly anti-metric review** (read anti-metrics vs actual dashboards).                                                                                                                                                                   |


### 6.3 Goal conflict and precedence ambiguity


| Item                                     | Implementation                                                                                                                                                                                                                                                        |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Precedence spec (one page, short OK)** | (a) **Macro:** weekly steering **overrides** when present. (b) **Micro:** soft rank **only** when steering is silent on that decision. (c) **Escalate** when domains conflict and weekly steering is **missing** — no silent default beyond the documented tie-break. |
| **Intent-alignment gate**                | Tune thresholds so **unresolved conflict** trips the gate, not every discussion of trade-offs.                                                                                                                                                                        |


### 6.4 Influence ethics (machine-readable)


| Item                | Implementation                                                                                                                                                                      |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **org-intent JSON** | Add stable `**hard_boundaries`** / `**values**` ids aligned with Pass B pattern: **no deception**, **consent / attribution**, **no dark patterns**, **reputation risk escalation**. |
| **Pass A**          | Extend Influence anti-goals where influence includes product or comms: **manipulation / coercive UX** alongside existing engagement-farming language.                               |


### 6.5 L402 / commercial and liability (beyond Pass D design-time bullets)


| Item                           | Implementation                                                                                                                                                                     |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Questionnaire / intent doc** | Capture **commercial intent**: hobby vs **productized API**; **merchant of record** for paid calls (if any); **refund / dispute** posture (including “none / best effort”).        |
| **Risk register**              | Map **preimage expiry**, **retry / attention** economics, **bad tool output after payment** to **escalation**, **disclaimers**, or **sync gates** — not Lightning mechanics alone. |


### 6.6 Dual source of truth (git vs OpenGrimoire vs `.cursor/state`)


| Layer                         | Canonical role                                                                                                                                              |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Git (org-intent JSON)**     | **Audit** truth: versioned, taggable; material changes optionally **signed tags**.                                                                          |
| **OpenGrimoire alignment items** | **Runtime** labor context: what the agent should load **this week** (Pass C).                                                                               |
| `**.cursor/state`**           | **Session / ephemeral**: preferences, handoffs — **not** long-term mission truth; document explicitly so agents do not treat it as org-intent.              |
| **Bridge**                    | **Export** (alignment → markdown/JSON in repo) on a **schedule or milestone** for audit trail; **import** that overwrites mission only with **human_gate**. |
| **OpenGrimoire A/B/C**           | If design doc chose **B** (DB live): state **what B implies for drift** (e.g. DB is operational source; git is **audit snapshot**).                         |


### 6.7 Privacy and logs


| Item              | Implementation                                                                                                                                                              |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data handling** | Short section: **what** is logged (tool calls, prompts, PII scope), **retention**, **who can access**, **jurisdiction / employer** caveats (pairs with Pass B private doc). |
| **Gates**         | Tie **rich logs** to `**sync`** / **human_gate** for sensitive content.                                                                                                     |


### 6.8 Survey mismatch (`survey.ts` vs strategic intent)


| Option          | Detail                                                                                                                           |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **A**           | **Separate wizard** for strategic intent / org-intent seeds — **different fields** than pedagogical / performance survey.        |
| **B**           | Same app, **two flows**; share only where **field names** and **storage** match alignment schema.                                |
| **Engineering** | Small **mapping table**: each question → `alignment_context_items` vs **org-intent file** vs **both** — avoids mixing semantics. |


### 6.9 Knowledge bundles / taxonomy (from prior critic thread)


| Item        | Implementation                                                                                                                                                |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bundles** | **Owner**, **version**, **last reviewed**, **deprecation** path — stale graph nodes must not pass as authoritative without freshness signal (tags or `body`). |


### 6.10 Approval bottleneck


| Item        | Implementation                                                                                                                                                                    |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Default** | `**async_ok`** for handoff chains; `**sync**` only for binding / irreversible / `hard_boundary` classes (per [INTENT_ENGINEERING.md](D:/openharness/docs/INTENT_ENGINEERING.md)). |
| **Process** | **Batch** weekly review where possible; treat **approval debt** as harness mis-tuning.                                                                                            |


---

## Follow-on verification

- After edits: link check for any new paths; org-intent JSON still validates against `org-intent.v1.json` if `values` / `hard_boundaries` change.
- Optional: run OpenGrimoire survey / wizard E2E only if UI code changes.

