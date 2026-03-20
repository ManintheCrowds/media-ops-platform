---
name: Pre-review documentation
overview: "Add three small artifacts before executing the multi-stack review: (1) a \"Lightweight agent-native refresh\" subsection in AGENT_NATIVE_CHECKLIST.md, (2) a reusable multi-stack review template with Session 0 reflection and trust assumptions, (3) a cross-link from the multi-stack review plan or MCP map to the template—so the prior audit plan can reference a concrete file path."
todos:
  - id: checklist-lightweight
    content: Add § Lightweight agent-native refresh + link to MULTI_STACK_REVIEW_TEMPLATE in AGENT_NATIVE_CHECKLIST.md
    status: completed
  - id: template-file
    content: Create .cursor/docs/MULTI_STACK_REVIEW_TEMPLATE.md (Session 0, trust, phase placeholders)
    status: completed
  - id: stack-overview-link
    content: Optional one-line See also in STACK_OVERVIEW.md to template
    status: completed
isProject: false
---

# Pre-review documentation (before multi-stack audit)

## Goal

Capture the agreed learnings as **durable docs** so the upcoming [multi-stack review](c:/Users/schum/.cursor/plans/multi-stack_review_audit_dfe8bf89.plan.md) runs with a clear methodology and a copy-paste report skeleton.

## 1. Lightweight agent-native refresh — [AGENT_NATIVE_CHECKLIST.md](D:/portfolio-harness/.cursor/docs/AGENT_NATIVE_CHECKLIST.md)

Insert a new subsection **after** "Baseline audit" (before "When adding UI or MCP tools") titled e.g. **Lightweight agent-native refresh**.

**Content (3–6 lines):**

- Full eight-principle / eight-parallel deep audit is **optional** and often too heavy for one session.
- Default refresh: read the latest **action parity** artifact under `.cursor/state/adhoc/` (e.g. `action_parity_audit_cm3_*.md`), compare **Missing/Partial** rows to current [MCP_CAPABILITY_MAP.md](D:/portfolio-harness/.cursor/docs/MCP_CAPABILITY_MAP.md) and Daggr MCP tools — **delta only** since audit date.
- Principle-level scores: narrative + evidence links; **full UI enumeration** only when scoped to one app.
- Link to `/agent-native-audit` or agent-native-reviewer for full passes when needed.

## 2. Multi-stack review template — new file

**Path:** [.cursor/docs/MULTI_STACK_REVIEW_TEMPLATE.md](D:/portfolio-harness/.cursor/docs/MULTI_STACK_REVIEW_TEMPLATE.md) (keeps templates discoverable next to other harness docs; copies to dated file under `.cursor/state/adhoc/` when running the audit).

**Sections:**

1. **Metadata** — date, repo scope, auditor (optional).
2. **Session 0 — Reflection (before deep scan)** — bullets: what changed since last parity doc; what we are **not** re-proving this run; assumptions.
3. **Trust assumptions** — one paragraph: shared workspace / no agent sandbox ([MCP_CAPABILITY_MAP Workspace](D:/portfolio-harness/.cursor/docs/MCP_CAPABILITY_MAP.md)); credential seam + TOOL_SAFEGUARDS; tool output as data.
4. **Placeholder headings** matching the multi-stack plan: Phase 1 rules/skills scan, Phase 2 intent, Phase 3 context, Phase 4 agent-native delta, Phase 5 risks, Phase 6 gaps + product-scope AC — each with a one-line *Evidence:* prompt.

## 3. Wire-up (minimal)

- Add one line under **Baseline audit** in [AGENT_NATIVE_CHECKLIST.md](D:/portfolio-harness/.cursor/docs/AGENT_NATIVE_CHECKLIST.md): link to `MULTI_STACK_REVIEW_TEMPLATE.md` for periodic stack reviews.
- Optionally add a **See also** row in [STACK_OVERVIEW.md](D:/portfolio-harness/.cursor/docs/STACK_OVERVIEW.md) pointing to the template (single line) — only if it stays short.

## Non-goals

- Do not edit the plan file `multi_stack_review_audit_dfe8bf89.plan.md` (user preference from prior turns: do not edit plan files).
- Do not run the full multi-stack audit in this task—documentation only.

## Verification

- Links resolve (relative paths from `.cursor/docs/`).
- No duplicate of full CHECKLIST content—template points at phases, not copies the whole plan.

