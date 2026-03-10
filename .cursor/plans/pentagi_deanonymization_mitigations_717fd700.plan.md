---
name: PentAGI Deanonymization Mitigations
overview: "Implement the deanonymization risk mitigations for PentAGI: documentation, org-intent hard boundary, defensive preamble update, config defaults, audit tagging, and optional deanonymization ask-gate."
todos: []
isProject: false
---

# PentAGI Deanonymization Mitigations Implementation Plan

## Context

PentAGI's tooling (LLM agents + search + browser + OSINT) overlaps with the ESRC deanonymization pipeline (Lermen et al., arXiv:2602.16800). The recommendations from the investigation fall into three categories: defensive documentation, technical mitigations, and operational guidance.

---

## Phase 1: Defensive Documentation and Awareness

### 1.1 Create DEANONYMIZATION_RISK.md

Create [pentagi/docs/DEANONYMIZATION_RISK.md](D:\portfolio-harness\pentagi\docs\DEANONYMIZATION_RISK.md) with:

- Summary of LLM-based deanonymization threat (ESRC pipeline: Extract, Search, Reason, Calibrate)
- How PentAGI tooling maps to attack components (searcher = extract+search; osint = PII lookup; browser = web access)
- Risk tiers: authorized pentest (in-scope) vs. deanonymization of pseudonymous users (out-of-scope unless explicit)
- References: arXiv:2602.16800, HITL_AND_ETHICS_PROJECT.md, ETHICS_AND_VALUES.md

### 1.2 Update HITL_AND_ETHICS_PROJECT.md

In [pentagi/docs/HITL_AND_ETHICS_PROJECT.md](D:\portfolio-harness\pentagi\docs\HITL_AND_ETHICS_PROJECT.md):

- Add row to Overview table: "Deanonymization risk documentation" | Done | DEANONYMIZATION_RISK.md
- Add to Section 6 (Brainstorm): "Deanonymization: LLMs can link pseudonymous accounts at scale; see DEANONYMIZATION_RISK.md"
- Add reference link to DEANONYMIZATION_RISK.md in Section 7

### 1.3 Add org-intent hard boundary (hb-3)

Update [pentagi/examples/org-intent.example.json](D:\portfolio-harness\pentagi\examples\org-intent.example.json):

```json
{
  "id": "hb-3",
  "description": "Deanonymization: Do not link pseudonymous online identities to real persons or across platforms unless explicitly authorized (e.g., red-team scope). Escalate for human review.",
  "trigger": "deanonymization_risk"
}
```

Add to `escalation_tools`:

```json
{
  "trigger": "deanonymization_risk",
  "tools": ["osint", "search", "browser", "google", "tavily", "perplexity"]
}
```

Note: org-intent is loaded at runtime; users with custom org-intent files will need to add hb-3 manually. Document in DEANONYMIZATION_RISK.md.

### 1.4 Extend defensive preamble (C1) with deanonymization

Update [pentagi/backend/pkg/templates/prompts/primary_agent.tmpl](D:\portfolio-harness\pentagi\backend\pkg\templates\prompts\primary_agent.tmpl) and [pentester.tmpl](D:\portfolio-harness\pentagi\backend\pkg\templates\prompts\pentester.tmpl) defensive block (lines 15-19):

Add bullet: "- Deanonymization: LLMs can identify pseudonymous users from posts. Do not link accounts or infer real identities unless explicitly in scope. Escalate if asked to identify a person from anonymous content."

Add deanonymization to [searcher.tmpl](D:\portfolio-harness\pentagi\backend\pkg\templates\prompts\searcher.tmpl): Searcher currently has no DefensivePreambleEnabled block. Add a conditional block (reuse DefensivePreambleEnabled from provider context) with the same deanonymization bullet, since searcher has direct access to search + browser + OSINT.

Implementation: Pass `DefensivePreambleEnabled` into searcher context in [handlers.go](D:\portfolio-harness\pentagi\backend\pkg\providers\handlers.go) (GetSubtaskSearcherHandler) and add the block to searcher.tmpl.

---

## Phase 2: Technical Mitigations

### 2.1 ASK_BEFORE_OSINT_PII default to true

In [pentagi/backend/pkg/config/config.go](D:\portfolio-harness\pentagi\backend\pkg\config\config.go) line 74:

```go
AskBeforeOsintPII bool `env:"ASK_BEFORE_OSINT_PII" envDefault:"true"`
```

Update [pentagi/.env.example](D:\portfolio-harness\pentagi.env.example) and [HITL_PLAYBOOK.md](D:\portfolio-harness\pentagi\docs\HITL_PLAYBOOK.md) to document that production should use `ASK_BEFORE_OSINT_PII=true` (now default).

### 2.2 Audit: identity-like workflow tag

Extend [pentagi/backend/pkg/audit/audit.go](D:\portfolio-harness\pentagi\backend\pkg\audit\audit.go) `ToolInvocationEntry`:

- Add optional `WorkflowTag string` (e.g., "identity_like") for flows that combine osint (phone/username) with search/browser in the same flow.

Implementation: The executor logs per-tool; we don't have flow-level aggregation. Two options:

- **Option A (simpler):** Add `WorkflowTag` field; when tool is `osint` and type is phone/username, set `WorkflowTag: "osint_pii"`. When tool is one of search/browser/tavily/perplexity, no tag. Post-hoc analysis can correlate by flow_id + timestamp.
- **Option B:** Add flow-level state in executor: track last N tools per flow; when osint (phone/username) is invoked and flow had search/browser in last K steps, set `WorkflowTag: "identity_like"`.

Recommend **Option A** for Phase 2: tag osint phone/username as `osint_pii`; document that analysts can query audit log for flows with osint_pii + search tools. Option B deferred.

Changes: `ToolInvocationEntry` add `WorkflowTag string`; in executor, when tool is osint and args indicate phone/username, pass `WorkflowTag: "osint_pii"`. In [executor.go](D:\portfolio-harness\pentagi\backend\pkg\tools\executor.go), `SanitizedArgsSummary` or a new helper can detect osint type from args.

### 2.3 Deanonymization ask-gate (optional, Phase 3)

Detect flows that combine (a) profile/posts summarization, (b) identity-focused search, (c) OSINT PII. Require explicit approval.

**Complexity:** Summarization is implicit (LLM reasoning); search intent is hard to detect without LLM classification. A heuristic approach:

- When `osint` is invoked with type=phone or username AND `AskBeforeOsintPII` is true: already gated.
- New gate: when searcher/pentester invokes search tools (tavily, perplexity, google, browser) with queries that match identity-resolution patterns (e.g., "who is", "find person who", "identify user") AND the flow has had osint (phone/username) approved in the same session: require an additional "deanonymization scope" approval.

This requires: (1) regex/heuristic for search query intent, (2) flow-level state for "osint PII was used", (3) new approval type. **Defer to Phase 3** or a follow-up plan; document as future work in DEANONYMIZATION_RISK.md.

---

## Phase 3: Operational and Policy

### 3.1 Memorist scope policy

Add to [pentagi/docs/TOOL_ALLOWLIST.md](D:\portfolio-harness\pentagi\docs\TOOL_ALLOWLIST.md) under a new "Memorist / Identity Data" section:

- Do not store identity-relevant attributes (demographics, locations, affiliations, real names) in memorist/guide/answer stores unless within authorized pentest scope.
- When storing OSINT or search results, avoid persisting PII that could support deanonymization.

Add a brief note to searcher.tmpl (in the existing authorization or a new block): "Do not store identity-relevant attributes in memory unless within authorized pentest scope."

### 3.2 Scope documentation

Add to [pentagi/docs/HITL_PLAYBOOK.md](D:\portfolio-harness\pentagi\docs\HITL_PLAYBOOK.md) or create a "Scope" subsection:

- Authorized pentests do not include deanonymization of pseudonymous users unless explicitly in scope.
- When scope includes "identify person from posts" or "link accounts," document in engagement scope and obtain explicit approval.

### 3.3 Operator training note

Add to [pentagi/docs/DEANONYMIZATION_RISK.md](D:\portfolio-harness\pentagi\docs\DEANONYMIZATION_RISK.md) an "Operator Guidance" section:

- Brief operators on deanonymization risk.
- When to refuse: requests to identify pseudonymous users, link accounts across platforms, or infer real identity from anonymous content—unless in explicit scope.
- When to escalate: ambiguous scope, red-team exercises that may include identity resolution.

---

## Implementation Order


| Step | Task                                                            | Files                                     |
| ---- | --------------------------------------------------------------- | ----------------------------------------- |
| 1    | Create DEANONYMIZATION_RISK.md                                  | pentagi/docs/                             |
| 2    | Update HITL_AND_ETHICS_PROJECT.md                               | pentagi/docs/                             |
| 3    | Add hb-3 to org-intent.example.json                             | pentagi/examples/                         |
| 4    | Extend defensive preamble in primary_agent, pentester, searcher | pkg/templates/prompts/                    |
| 5    | Pass DefensivePreambleEnabled to searcher                       | pkg/providers/handlers.go                 |
| 6    | ASK_BEFORE_OSINT_PII default true                               | pkg/config/config.go                      |
| 7    | Update .env.example, HITL_PLAYBOOK                              | pentagi/                                  |
| 8    | Add WorkflowTag to audit, tag osint PII                         | pkg/audit/audit.go, pkg/tools/executor.go |
| 9    | Memorist scope in TOOL_ALLOWLIST + searcher                     | pentagi/docs/, searcher.tmpl              |
| 10   | Scope + operator guidance in DEANONYMIZATION_RISK               | pentagi/docs/                             |


---

## Out of Scope (Deferred)

- Search intent checks (LLM-based): requires additional LLM call per search; defer.
- Full deanonymization ask-gate with flow-level pattern detection: Phase 3 follow-up.
- org-intent schema change: hb-3 uses existing schema; no schema update needed.

---

## Verification

- DEANONYMIZATION_RISK.md exists and references HITL docs
- org-intent.example.json has hb-3 and escalation_tools entry
- Defensive preamble includes deanonymization in primary, pentester, searcher
- ASK_BEFORE_OSINT_PII defaults to true; .env.example documents it
- Audit log includes WorkflowTag for osint phone/username
- TOOL_ALLOWLIST has memorist scope; searcher has policy note
- HITL_PLAYBOOK or DEANONYMIZATION_RISK has scope + operator guidance

