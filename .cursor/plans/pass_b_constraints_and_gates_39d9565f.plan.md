---
name: Pass B constraints and gates
overview: Extend the org-intent North Star brainstorm with Pass B (constraints, gates, sync/async, legal lines), record soft rank Health→Wealth→Influence, and add a sanitized public org-intent example JSON that encodes boundaries and delegation rules without PII.
todos:
  - id: brainstorm-pass-b
    content: Add Pass B section to 2026-03-22-org-intent-north-star-brainstorm.md (soft rank resolved, crosswalk, sync/async table, legal lines, must/must-not/escalation drafts, mermaid, repo links)
    status: completed
  - id: example-json
    content: Create org-intent-spec/examples/org-intent.consulting-feedback.example.json (sanitized, schema-valid)
    status: completed
  - id: validate-json
    content: Validate new example against org-intent.v1.json
    status: completed
isProject: false
---

# Pass B — Constraints and gates (documentation + example JSON)

## Canonical references (already in repo)


| Concept                                                                                            | Source                                                                                                                                                                                                                             |
| -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Intent fields: `constraints`, `human_gate`, `latency_tolerance` (`sync` | `async_ok`)              | [openharness/docs/INTENT_ENGINEERING.md](D:/openharness/docs/INTENT_ENGINEERING.md) — Intent Schema table, Constraint Architecture, Latency Negotiation, Human Gate Protocol                                                       |
| org-intent: `hard_boundaries`, `delegation_rules`, `value_hierarchy`, `values`, `escalation_tools` | [portfolio-harness/org-intent-spec/schema/org-intent.v1.json](D:/portfolio-harness/org-intent-spec/schema/org-intent.v1.json) and [org-intent.example.json](D:/portfolio-harness/org-intent-spec/examples/org-intent.example.json) |
| Cryptographic vs social authority                                                                  | [openharness/docs/AUTHORITY_MODEL.md](D:/openharness/docs/AUTHORITY_MODEL.md)                                                                                                                                                      |


**Important mapping:** `human_gate` and `latency_tolerance` are **not** org-intent schema properties; they belong in **session briefs and handoffs** per INTENT_ENGINEERING. Pass B should document **both**: (1) what goes into org-intent JSON, and (2) what repeats in every high-stakes handoff as `human_gate` + `latency_tolerance`.

## 1. Extend [2026-03-22-org-intent-north-star-brainstorm.md](D:/openharness/docs/brainstorms/2026-03-22-org-intent-north-star-brainstorm.md)

Add a **Pass B** section with these subsections (concise tables, ~200–300 words each):

### 1.1 Soft rank (resolved)

- Move **open question 1** to **Resolved**: **soft rank** for within-week tie-breaks (after weekly steering): **Health → Wealth → Influence**. Clarify this does **not** override weekly human choice; it only breaks ties when steering is silent on a micro-decision.

### 1.2 Crosswalk: INTENT_ENGINEERING ↔ org-intent


| INTENT_ENGINEERING      | org-intent / practice                                                                                                               |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Musts**               | `values` entries (or prefixed strings like `MUST: ...`) + optional `delegation_rules` with `action: proceed` only where safe        |
| **Must-nots**           | `values` + explicit **must-not** bullets in brainstorm; violations → treat as constraint breach                                     |
| **Escalation triggers** | `hard_boundaries[]` (`id`, `description`, `trigger`)                                                                                |
| **Preferences**         | Document in brainstorm or `values`; lower priority than must-nots                                                                   |
| **human_gate** (string) | Not stored in JSON: use **named gates** in handoffs; mirror critical gates via `delegation_rules` → `escalate`                      |
| **latency_tolerance**   | Not stored in JSON: default `async_ok` for handoff chains per INTENT_ENGINEERING; `sync` when human must be present before continue |


Include a **small mermaid** diagram: `SessionIntent` → `handoff (human_gate, latency_tolerance)` vs `org-intent` → `hard_boundaries / delegation_rules`.

### 1.3 Sync vs async (action classes)

Build a **classification table** (examples, not exhaustive — user fills private edge cases):

- **Always `sync` (human present before proceed):** commits that bind legally or financially; irreversible infra; publishing security-relevant or reputation-critical claims; any action crossing **hard_boundaries**; first-time Fedimint/collective commitments; cryptographic key operations.
- **Default `async_ok`:** research, drafts, local branches, plans, non-binding reviews — per INTENT_ENGINEERING default for handoff chains.

### 1.4 Legal / contractual / reputational lines

- **Feeds `hard_boundaries`:** e.g. no public legal advice; no warranty of regulatory fit; no commits on behalf of another entity without proof; no deceptive claims about AI/agent capabilities.
- **Feeds `delegation_rules`:** e.g. “ambiguous liability → escalate”; “external communication that attributes org → escalate”.

Keep wording **generic** in the public doc; **private** doc holds employer/NDA specifics.

### 1.5 Must / must-not / escalation (draft lists)

Provide **placeholder bullets** the user can edit (sanitized): 3–5 musts, 3–5 must-nots, 3–5 escalation triggers aligned to their mission (consulting system, alignment tech, Fedimint interest) without numbers or PII.

### 1.6 Repo alignment (update existing section)

- Link INTENT_ENGINEERING Pass B mapping explicitly.
- Note new example JSON path (below).

## 2. New public example JSON

**Path:** [portfolio-harness/org-intent-spec/examples/org-intent.consulting-feedback.example.json](D:/portfolio-harness/org-intent-spec/examples/org-intent.consulting-feedback.example.json) (name can be shortened if you prefer `org-intent.pass-b.example.json`).

**Content guidelines:**

- **Validate** against `org-intent.v1.json` (required: `version`, `values`, `mission`).
- Populate:
  - `mission`: one line aligned with Pass A draft (generic).
  - `values`: mix of MUST-style norms and cooperation/integrity strings (no PII).
  - `hard_boundaries`: 3–5 entries with stable `id`s (e.g. `hb-legal`, `hb-reputation`, `hb-crypto-commit`) and `trigger` strings agents can match.
  - `delegation_rules`: rows for weekly steering, ambiguous liability, public attribution — `action: escalate` where appropriate.
  - `value_hierarchy.conflicts`: include weekly human choice rule + soft rank tie-break row (`health` vs `wealth` vs `influence` with rule text).
  - `pro_social`: optional; keep short if present.
  - `escalation_tools`: optional empty array or omit if schema allows; mirror [org-intent.example.json](D:/portfolio-harness/org-intent-spec/examples/org-intent.example.json) pattern — use generic tool names or empty to avoid implying real tooling.

**Do not** put `human_gate` / `latency_tolerance` inside JSON unless we extend the schema (out of scope). Instead, add a **comment block in the brainstorm** (or one-line file header comment is invalid JSON) — so the brainstorm file holds: *“Copy into handoffs: default `latency_tolerance: async_ok`; set `sync` when …”*

## 3. Verification (when executing)

- Run JSON validation against [org-intent.v1.json](D:/portfolio-harness/org-intent-spec/schema/org-intent.v1.json) (project script or `python -m jsonschema` if available).
- Quick read: [intent-alignment-gate.mdc](D:/openharness/.cursor/rules/intent-alignment-gate.mdc) optional cross-check that Pass B doesn’t contradict dual-gate practice.

## Out of scope (explicit)

- Changing the JSON Schema to add `human_gate` / `latency_tolerance` (would be a separate spec change).
- Private documentation file content (user-owned vault).

