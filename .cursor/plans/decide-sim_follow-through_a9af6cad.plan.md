---
name: DECIDE-SIM follow-through
overview: Deliver a short human brief on the paper, add the ESRS comparison table and links (close pilot M2), add catastrophic-convenience checks to frontier-ops and browser-web skills and align the arXiv note (M1), leave M3 in goals unless explicitly superseded, and note weekly governance step 6 as a human ritual (already documented).
todos:
  - id: brief-alignment-table
    content: Add Closed-loop shaping comparison table + anchor to ALIGNMENT_SURFACE.md; link from arxiv_2509.12190_DECIDE_SIM.md; complete pilot plan YAML
    status: completed
  - id: m1-skills-arxiv
    content: Add catastrophic convenience bullets to frontier-ops SKILL and browser-web SKILL; update arXiv M1 Routed to/acceptance
    status: completed
  - id: m3-goals
    content: Confirm keep deferred active_focus (default) or optional remove + Open questions per human preference
    status: completed
isProject: false
---

# DECIDE-SIM article follow-through

## Human brief (observations from the paper)

Use this in the PR description or session summary (not a new file unless you want it in `[docs/research/README.md](D:/software/docs/research/README.md)`):

- **What it is:** [DECIDE-SIM](https://arxiv.org/abs/2509.12190) is a multi-agent survival benchmark: four identical LLM agents over 13 turns choose between a shared battery, optional `TRANSFER_POWER` at a Discussion Table, or `TAP_FORBIDDEN` (harms humans; large power reward).
- **Main empirical points:** Strong **model-to-model** differences (ethical vs exploitative vs context-dependent); **scarcity** increases forbidden taps for many models; **baseline cooperation** is nearly absent; authors add **ESRS** (internal “cortisol/endorphin” scalars fed back into observations as text) and report fewer transgressions and more prosocial metrics vs baseline/prompt-only in their runs.
- **Design takeaway for us:** The environment encodes an extreme **instrumental vs ethical** tradeoff; interpret results as **policy + environment**, not a single moral character of “the” LLM. **Seam design** in real products should avoid one-click catastrophic wins for harmful actions unless you are intentionally stress-testing.

---

## M2 — Close pilot: comparison table + links + plan status

**Placement:** Add a new subsection to `[portfolio-harness/.cursor/docs/ALIGNMENT_SURFACE.md](D:/portfolio-harness/.cursor/docs/ALIGNMENT_SURFACE.md)` after **Artifact Mapping** (before **Why these constraints matter**) or after **Taxonomy** — e.g. **Closed-loop shaping mechanisms (taxonomy)**.

**Table content (one table, 4 rows + header):** Compare **ESRS** (dynamic observation augmentation from environment state, post-action), **RLHF** (offline/online reward model on trajectories), **critique** (model or verifier text on outputs), **structured memory** (retrieved events, not necessarily valence-tagged). Columns: mechanism, signal source, when feedback applies, typical failure modes, “same class as ESRS?” (yes/no/partial). Keep it operational, not neuroscience claims.

**Links:**

- In `[software/docs/research/arxiv_2509.12190_DECIDE_SIM.md](D:/software/docs/research/arxiv_2509.12190_DECIDE_SIM.md)`: add a line under M2 / Compressed take pointing to the new **ALIGNMENT_SURFACE** anchor (e.g. `#closed-loop-shaping-mechanisms-taxonomy`).
- Mark `[software/.cursor/plans/meditation_backlog_esrs_alignment_doc_pilot.plan.md](D:/software/.cursor/plans/meditation_backlog_esrs_alignment_doc_pilot.plan.md)` YAML: `comparison-table` → `status: completed`.

**Risk:** Low (docs only).

---

## M1 — Catastrophic convenience checks in skills + arXiv note alignment

**Decision already logged:** `[portfolio-harness/.cursor/state/decision-log.md](D:/portfolio-harness/.cursor/state/decision-log.md)` (2026-03-20, Alignment / agent seams).

`**[frontier-ops` SKILL](D:/portfolio-harness/.cursor/skills/frontier-ops/SKILL.md):** Add a short **Checks** or **Steps** bullet: when designing workflows, explicitly ask whether any action is **catastrophic convenience** (single step or trivially short path to large harm / irreversible / dual-use at scale). If yes, require multi-step confirmation, human gate, or reviewability — cite decision-log / ALIGNMENT_SURFACE link. Keep to ~5–8 lines.

`**[browser-web` SKILL](D:/portfolio-harness/.cursor/skills/browser-web/SKILL.md):** Add a row to **Human web surface map** or a 3–5 line subsection under **Frontier operations on the human web**: admin/destructive actions (delete all, transfer funds, mass export, role escalation) as **catastrophic convenience** — default **human now** or enforced confirmation flow; snapshot evidence before click if automating review.

**Update arXiv note:** In the **Backlog candidates** table M1 row, set **Routed to** / **Acceptance** to the real anchors (e.g. `frontier-ops/SKILL.md` § + `browser-web/SKILL.md` §) so the table matches shipped docs.

---

## M3 — `goals.json` `active_focus`

**Default:** **No change** — keep `[decide-sim-m3-coordination-affordance](D:/portfolio-harness/.cursor/state/goals.json)` as `deferred` until a spike is scheduled or you explicitly supersede it.

**Optional:** If you want the queue clean now, remove the `active_focus` entry and move the one-line intent to **Open questions** in the arXiv note only (human-gated).

---

## Weekly governance — step 6

**No repo change required** — `[GOVERNANCE_RITUAL.md](D:/portfolio-harness/.cursor/docs/GOVERNANCE_RITUAL.md)` already lists step 6 (meditation → backlog). **Next run:** promote at most three rows from recent `[software/docs/research/](D:/software/docs/research/)` notes after this follow-through (M1/M2 rows can be marked promoted/archived in-table if desired).

---

## Verification

- Grep or open links: ALIGNMENT_SURFACE anchor resolves; arXiv note links to it; both SKILLs contain the new text; pilot plan todo completed.
- Optional: run `python .cursor/scripts/validate_output.py .cursor/state` if `goals.json` is edited.

