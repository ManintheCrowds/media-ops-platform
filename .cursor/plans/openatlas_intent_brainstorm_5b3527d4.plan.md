---
name: OpenAtlas intent brainstorm
overview: Run a structured `/brainstorm` session (WHAT, not HOW) that triages your canonical backlog in `portfolio-harness/.cursor/state` against two intent layers—OpenAtlas alignment items and higher-level local hardware/stack goals—and defines an audit scope for OpenAtlas context monitoring plus observability for the incoming local-proto hardware stack.
todos:
  - id: run-brainstorm-dialogue
    content: "Facilitate Phase 1–2: clarify triage cadence, pick 2–3 approaches, document recommendation"
    status: completed
  - id: write-brainstorm-md
    content: Create docs/brainstorms/2026-03-22-openatlas-intent-triage-hardware-obs.md with template sections
    status: completed
  - id: resolve-open-questions
    content: Move resolved Qs to Resolved; leave true gaps as Open questions
    status: completed
  - id: handoff-next
    content: Offer review / workflows:plan / more questions / done per Phase 4
    status: completed
isProject: false
---

# Brainstorm: Todo triage, OpenAtlas context/intent audit, hardware-stack observation

## Context anchored in the repo

- **Canonical backlog (your choice):** `[portfolio-harness/.cursor/state](D:/portfolio-harness/.cursor/state)` — `decision-log.md`, `handoff_latest.md` / `handoff_archive/`, `daily/`, `AGENTS.md`, `continue_prompt.txt`, etc.
- **Tactical “intent” surface:** OpenAtlas `**alignment_context_items`** via `[GET/POST/PATCH /api/alignment-context](D:/portfolio-harness/OpenAtlas/docs/agent/ALIGNMENT_CONTEXT_API.md)` (title, body, tags, priority, status, `linked_node_id`).
- **Context visualization:** Brain map / context graph from `[build_brain_map.py](D:/portfolio-harness/.cursor/scripts/build_brain_map.py)` → `public/brain-map-graph.json` and routes `/context-atlas`, `/brain-map`; inventory in `[OPENATLAS_SYSTEMS_INVENTORY.md](D:/portfolio-harness/OpenAtlas/docs/OPENATLAS_SYSTEMS_INVENTORY.md)` (SCP-skipped files, multi-`CURSOR_STATE_DIRS`, vault roots).
- **Strategic intent layer:** `[local-proto/docs/HARDWARE.md](D:/portfolio-harness/local-proto/docs/HARDWARE.md)` and related scope docs (Alienware + eGPU, Jetson, NAS, Ollama, OpenClaw, MCP).

```mermaid
flowchart LR
  subgraph backlog [Backlog source]
    state[".cursor/state markdown"]
  end
  subgraph tactical [Tactical intents]
    align["alignment_context API"]
  end
  subgraph strategic [Strategic intents]
    hw["local-proto goals"]
  end
  subgraph oa [OpenAtlas monitoring surfaces]
    graph["brain-map / context-atlas"]
    api["alignment API + CLI"]
  end
  state --> graph
  state --> align
  align --> graph
  hw --> align
```



## Brainstorm session structure (follow `/brainstorm` command)

1. **Phase 0 — Requirements:** Requirements are exploratory (not a ready-made spec); full brainstorming is appropriate (no need to skip to implementation planning).
2. **Phase 1 — Clarify:** Already resolved: backlog = `.cursor/state`; intents = **both** alignment + stack goals. During the live brainstorm, optionally refine: **frequency** of triage (weekly vs per-handoff) and **who** updates alignment items when state changes.
3. **Phase 2 — Approaches (2–3):** Compare lightweight options, for example:
  - **A — Manual matrix:** One table mapping state-derived themes → alignment item IDs / tags → hardware doc sections (low automation, high clarity).
  - **B — Tag convention:** Standardize `tags` + `linked_node_id` in alignment items so they mirror decision-log areas or handoff IDs (minimal schema, agent-scriptable later).
  - **C — Split observability:** Separate “human alignment” (OpenAtlas UI/API) from “machine health” (Ollama/Jetson/NAS metrics — out of OpenAtlas unless you explicitly bridge them).
   Lead with a **YAGNI** recommendation (likely A or B first, C scoped as a second track).
4. **Phase 3 — Capture:** Write `[docs/brainstorms/2026-03-22-openatlas-intent-triage-hardware-obs.md](D:/portfolio-harness/docs/brainstorms/2026-03-22-openatlas-intent-triage-hardware-obs.md)` (or similar slug) using your brainstorming template: **What we’re building**, **Why this approach**, **Key decisions**, **Open questions**, **Resolved questions** (move items as you go).
5. **Phase 4 — Handoff:** Offer next step: refine doc, `/workflows:plan`, more questions, or pause.

## Content to cover in the brainstorm doc (not implementation)


| Theme                    | Questions to answer in prose                                                                                                                                                               |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Todo ↔ intent triage** | How to classify items in state (active vs stale, duplicate handoffs, superseded decisions). How each class maps to alignment `status` / `priority` and to HARDWARE/NAS scope.              |
| **OpenAtlas “audit”**    | What “working” means: graph freshness (regen cadence), SCP skips, API auth (`x-alignment-context-key`), E2E coverage (`npm run verify:e2e`), gaps between graph nodes and alignment links. |
| **Stack observation**    | What to observe when hardware lands: GPU visibility to Ollama, network paths to NAS, Jetson role; whether metrics belong in Grafana/Prometheus vs logs vs a simple checklist doc for v1.   |


## Tech-lead placement (per attached skill)

- **Brainstorm artifact:** `[portfolio-harness/docs/brainstorms/](D:/portfolio-harness/docs/brainstorms/)` — matches existing dated brainstorms (e.g. `[2026-03-21-juraj-bednar-openclaw-cypherpunk-way.md](D:/portfolio-harness/docs/brainstorms/2026-03-21-juraj-bednar-openclaw-cypherpunk-way.md)`).
- **Any future implementation** stays separate: OpenAtlas app code under `[OpenAtlas/](D:/portfolio-harness/OpenAtlas)`, harness scripts under `[.cursor/scripts/](D:/portfolio-harness/.cursor/scripts)`, local-proto under `[local-proto/docs/](D:/portfolio-harness/local-proto/docs)` — do not conflate in a single “monitoring” blob without a design note.

## Guardrails

- **No code in brainstorm phase** (per `/brainstorm`).
- **Plan mode:** This plan only; **execute** file creation and dialogue after you approve.

## Suggested open questions to resolve in the brainstorm (or in chat)

1. Should alignment items **mirror** decision-log rows 1:1, or only **themes** (many-to-one)?
2. Is the first hardware audit **offline** (checklist + manual tests) or do you want **one** metric source of truth from day one?
3. Should `openharness` state be merged into the graph via `CURSOR_STATE_DIRS` for this triage, or portfolio-harness only?

