# Research meditation template

Use this structure for notes that combine source facts, your synthesis, and actionable implications. Aligns with the **meditation → backlog** workflow: implications must pass **verb + object + acceptance** before promotion to [decision-log](../../../portfolio-harness/.cursor/state/decision-log.md), [goals.json](../../../portfolio-harness/.cursor/state/goals.json), or a `.cursor/plans/*.plan.md` file.

## Required sections

### Title and source

- Primary link(s), authors, date, optional repo.

### Provenance (if fetched or PDF)

- URL + content hash per `TOOL_SAFEGUARDS` / `document_provenance_record` when treating content as trusted for automation.

### SCP gate (if text feeds LLM / RAG / handoff)

- Note `scp_run_pipeline` / `scp_inspect` result or "pending extract → chunk → SCP".

### Compressed take (**F** — facts)

- Bullet summary of claims **from the source** (cited or clearly attributed).

### Meditation (**I** + **M** — interpretation and implications)

- **I:** Your framing, comparisons, limits of the source.
- **M:** Numbered threads that imply **we should / avoid / measure** something concrete.

Optional: prefix lines with **F:** / **I:** / **M:** while drafting.

### Caution / scope

- Disclaimers (e.g. not medical/legal advice), alignment with org-intent or wellbeing corpus policy.

---

## Backlog candidates (from meditation)

Copy this table into every meditation note when you are ready to triage. **Promote** at most three rows per week to real artifacts; leave the rest as **deferred** or move to `## Open questions`.

| ID | Type | Tag | Candidate one-liner | Acceptance (one sentence) | Routed to |
|----|------|-----|----------------------|---------------------------|-----------|
| M1 | DOCS/CONFIG/… | M | | | decision-log / plan / goals / deferred |
| M2 | | | | | |
| M3 | | | | | |

**Routing guide**

| Routed to | When |
|-----------|------|
| `decision-log.md` | Irreversible choice, principle, or stack/policy decision |
| `.cursor/plans/*.plan.md` | Multi-step work with ordered YAML `todos` |
| `goals.json` / `session_brief.md` | Current sprint or `active_focus` |
| `deferred` | No acceptance criteria yet — keep in `## Open questions` |

---

## Open questions

- Research debt: bullets that are not yet actionable.

---

*See also: [GOVERNANCE_RITUAL.md](../../../portfolio-harness/.cursor/docs/GOVERNANCE_RITUAL.md) § Weekly checklist (meditation→backlog scan).*
