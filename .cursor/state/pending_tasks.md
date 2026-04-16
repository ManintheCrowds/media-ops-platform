# Pending Tasks (software repo)

**Last updated:** 2026-04-16

---

## Site & publishing

| ID | Status | Task | Notes |
|----|--------|------|-------|
| GHOST1 | in_progress | Stand up a **Ghost-powered** personal or project site | **Runbook (SSOT):** MiscRepos `docs/GHOST1_RUNBOOK.md` (local sibling: `../MiscRepos/docs/GHOST1_RUNBOOK.md`). **Phased checklist:** `docs/operations/INTEGRATION_ROLLOUT_OPERATOR_CHECKLIST.md`. **After verification:** `docs/operations/GHOST1_CLOSEOUT.md`. Reference: [josephvoelbel.com](https://josephvoelbel.com). Theme: [highnoonoffice/ghost-theme](https://github.com/highnoonoffice/ghost-theme). Voelbel primer: `docs/collaborators/joseph-voelbel-openclaw-clawhub.md`. Cursor vs OpenClaw: `docs/collaborators/CURSOR_OPENCLAW_INTEGRATION.md`. Mark **done** only per GHOST1_CLOSEOUT after [GHOST1_RUNBOOK.md](../../../MiscRepos/docs/GHOST1_RUNBOOK.md) §Verification on a real instance. |

**OpenClaw / ClawHub (Voelbel “Magnus” stack — for later):** [Brain Map Visualizer](https://clawhub.ai/highnoonoffice/brain-map-visualizer) · [Ghost Publishing Pro](https://clawhub.ai/highnoonoffice/ghost-publishing-pro) · [Second Brain Visualizer](https://clawhub.ai/highnoonoffice/second-brain-visualizer) · [Library of Babel](https://clawhub.ai/highnoonoffice/library-of-babel) (hub-flagged: review docs vs code). Legacy slug: [clawhub.com/skills/oc-brain-map](https://clawhub.com/skills/oc-brain-map). Repo: [highnoonoffice/hno-skills](https://github.com/highnoonoffice/hno-skills). **Aggregated write-up (local clone):** `MiscRepos/docs/collaborators/joseph-voelbel-openclaw-clawhub.md`. Articles: [The Brain Map Visualizer](https://josephvoelbel.com/the-brain-map-visualizer/), [Installing OpenClaw: Meet Magnus](https://josephvoelbel.com/installing-openclaw-meet-magnus/).

---

## Critic follow-ups (git diff branch→main)

From critic review of Darktide removal + README changes:

| ID | Status | Task | Fix |
|----|--------|------|-----|
| CR1 | pending | Author link 404 in standalone clone | Replace `../portfolio-harness/docs/AUTHOR.md` with absolute URL or document workspace assumption |
| CR2 | pending | Confirm .gitignore covers all Darktide outputs | Add patterns for report dirs (e.g. `*darktide*report*`) if such outputs exist |

**Critic verdict:** Pass. Changes are safe and focused.
