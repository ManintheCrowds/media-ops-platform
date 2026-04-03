---
name: Public repo README voice alignment
overview: "Align READMEs (and optional GitHub short descriptions) for LangChainChatBot, OpenGrimoire, PrusaXL_Monitor, moltbook_watchtower, and Arc_Forge with OpenHarness voice: concept-led title, technical tagline, framework/taxonomy where relevant, Key Concepts table, and consistent structure. OpenHarness remains the reference; no change to portfolio-harness README unless you request it."
todos: []
isProject: false
---

# Public repository README voice alignment

## Voice (from OpenHarness + AUTHOR.md)

- **Lead:** Concept-led title ("X — Y") and one-line technical tagline (what it is, which taxonomy/framework if any).
- **Tone:** Technical, formal; no corporate speak. "Code speaks." ([portfolio-harness/docs/AUTHOR.md](D:\portfolio-harness\docs\AUTHOR.md))
- **Structure:** Short intro, optional **Key Concepts** table, **Contents** (paths), **Integration/Quick start**, **References** (doc links). Tables for concepts and layout.
- **Frameworks:** Name frameworks or principles where they apply (e.g. Guard–Guide–Build, local-first, ACE, human-in-the-loop).

Reference: [OpenHarness README](D:\openharness\README.md) — "Harness — Context and Intent Engineering" / "Portable AI harness: context engineering, intent engineering, handoff flow, and state schema. **Guide** in the Guard–Guide–Build taxonomy."

---

## Repositories and changes

### 1. LangChainChatBot

**Location:** [portfolio-harness/LangChainChatBot/README.md](D:\portfolio-harness\LangChainChatBot\README.md)

**Current:** "YouTube RAG Chatbot (Local-First)" — solid technical content but lead is product-y; no concept table; no framework tagline.

**Proposed:**

- **Title:** "LangChainChatBot — YouTube transcript RAG, local-first."
- **Tagline (below title):** One sentence: local-first RAG over YouTube transcripts; LangChain, SQLite, sqlite-vec; embeddings and optional LLM local (Ollama). Align with local-first and credential-vault patterns.
- **Add:** A short **Key Concepts** table (e.g. RAG, local-first, credential vault, HITL consent) before or after Architecture.
- **Keep:** All existing architecture diagrams, setup, run, test, AI security table, and files table; only adjust the opening and add the concepts table so the voice matches OpenHarness.
- **GitHub description (suggested):** "Local-first RAG over YouTube transcripts. LangChain, SQLite, sqlite-vec; compliant with local-first and credential-vault patterns."

---

### 2. OpenGrimoire

**Location:** [portfolio-harness/OpenGrimoire/README.md](D:\portfolio-harness\OpenGrimoire\README.md)

**Current:** Good technical content; first line is a bit long and doesn’t lead with a crisp "X — Y" and tagline.

**Proposed:**

- **Title:** "OpenGrimoire — Operator context graph and brain-map visualization."
- **Tagline:** One sentence: Next.js app for co-access across `.cursor/state` handoffs and daily notes; D3/Three.js; static JSON graph, no Supabase required. Part of portfolio-harness **Build** (see Guard–Guide–Build).
- **Add:** **Key Concepts** table (e.g. context graph, brain-map, handoff-derived nodes, static JSON contract).
- **Keep:** Context graph section, routes table, quick start, scripts, agent/API docs links; trim or tighten the first paragraph so the new title + tagline carry the identity.
- **GitHub description (suggested):** "Operator context graph and brain-map visualization. Co-access across handoffs and daily notes; D3/Three.js; static JSON, no Supabase required."

---

### 3. PrusaXL_Monitor (prusa_XL_soft)

**Location:** [prusa_XL_soft/README.md](D:\prusa_XL_soft\README.md)

**Current:** "Seeking to identify, monitor and suggest fixes" — informal; minimal structure; no concept table.

**Proposed:**

- **Title:** "PrusaXL_Monitor — Observability and remediation for Prusa XL 3D printing."
- **Tagline:** One sentence: Identify, monitor, and suggest fixes for Prusa XL print issues; Flask API, PrusaLink/OctoPrint collectors, PostgreSQL, optional Redis/Grafana.
- **Add:** **Key Concepts** table (e.g. observability, collector, knowledge-base seed, troubleshoot pipeline).
- **Keep:** Quick start, project structure, testing, docs list, KB seed; rephrase the opening to match the new title and tagline.
- **GitHub description (suggested):** "Observability and remediation for Prusa XL 3D printing. Flask API, PrusaLink/OctoPrint collectors, PostgreSQL, optional Grafana."

---

### 4. moltbook_watchtower

**Location:** [moltbook-watchtower/README.md](D:\moltbook-watchtower\README.md)

**Current:** Strong Problem→Solution→Impact and architecture; only the lead and GitHub description need tightening to match OpenHarness voice.

**Proposed:**

- **Title:** "Moltbook Watchtower — Passive monitoring for the Moltbook agent network."
- **Tagline:** One sentence: Read-only observability; leak, injection, and behavior analysis over collected data; no writes to the network. Local-first analysis and static dashboard.
- **Optional:** Add a small **Key Concepts** table (read-only collector, leak/injection/behavior analyzers, static dashboard, local-first) if the rest of the README stays as-is.
- **Keep:** Problem→Solution→Impact, architecture diagram, features, tech stack, local-first alignment, quick start, docs, testing.
- **GitHub description (suggested):** "Passive monitoring for the Moltbook agent network. Read-only observability; leak, injection, and behavior analysis; local-first, no writes to the network."

---

### 5. Arc_Forge

**Location:** [Arc_Forge/README.md](D:\Arc_Forge\README.md)

**Current:** Already close to voice (RAG-backed campaign workbench, human authority); could use a sharper one-line identity and optional Key Concepts.

**Proposed:**

- **Title:** Keep or tighten to "Arc Forge — RAG-backed campaign workbench for Wrath & Glory."
- **Tagline:** One sentence: Human-in-the-loop narrative authority; adventure arcs, pipeline UI, session memory; local-first vault and optional RAG/campaign_kb.
- **Optional:** **Key Concepts** table (RAG, narrative workbench, human authority, pipeline S1–S5, session Archivist/Foreshadow) near the top.
- **Keep:** Purpose, What this is, Components table, Quickstart, Architecture links, testing, credentials, local-first. Only refine the opening and add the concepts table if it doesn’t bloat the README.
- **GitHub description (suggested):** "RAG-backed campaign workbench for Wrath & Glory. Human-in-the-loop narrative authority; pipeline UI, session memory; local-first."

---

## Out of scope / optional

- **OpenHarness:** No change; it is the reference.
- **portfolio-harness:** README already matches voice (Guard–Guide–Build, tables, agent entry). Optional: add or refine the GitHub repo description only if you want it to mirror the "Multi-project AI harness…" line.
- **GitHub descriptions:** Suggested one-liners above; you can paste them into each repo’s GitHub "About" / description field manually (no code change).

---

## Implementation order

1. **LangChainChatBot** — Add concept-led title, tagline, Key Concepts table; keep body.
2. **OpenGrimoire** — Add title, tagline, Key Concepts; tighten first paragraph.
3. **PrusaXL_Monitor** — Rewrite lead, add Key Concepts; keep quick start and structure.
4. **moltbook_watchtower** — Add tagline and optional Key Concepts; keep existing sections.
5. **Arc_Forge** — Add tagline and optional Key Concepts; keep existing sections.

---

## Deliverables

- Updated README.md in each of the five repos (edits only; no new files).
- Optional: a short checklist or copy-paste block of the five suggested GitHub descriptions for you to apply on GitHub.

No structural or code changes; only README content and voice alignment. After implementation, run critic loop per workspace rules and attach the critic JSON to the response summary.
