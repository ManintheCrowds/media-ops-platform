---
name: Med-Vis to OpenGrimoire rename
overview: Rename the portfolio-harness Next.js app folder from `Med-Vis` to `OpenGrimoire`, relocate the nested `OpenGrimoire/` backup doc to avoid path collision, update all docs/scripts/skills that reference `Med-Vis`/`med-vis`, and align cross-repo (OpenHarness) brain-map references—without breaking `gh` until GitHub’s repo slug changes.
todos:
  - id: relocate-backup-doc
    content: Move Med-Vis/OpenGrimoire/BACKUP_STRATEGY.md → docs/BACKUP_STRATEGY.md; strip nested OpenGrimoire/; rename Med-Vis → OpenGrimoire
    status: completed
  - id: opengrimoire-docs-docker
    content: Sweep OpenGrimoire README, CLAUDE, DEPLOYMENT, guides, prompt file; docker tag opengrimoire-med-vis → opengrimoire
    status: completed
  - id: harness-scripts-state
    content: Update build_brain_map.py, setup_env.py, security_scan.ps1, pending_tasks.md; gh script description + comment only
    status: completed
  - id: portfolio-brain-map-docs
    content: Update portfolio-harness docs/BRAIN_MAP_AUDIT.md and BRAIN_MAP_E2E.md paths and wording
    status: in_progress
  - id: openharness-sweep
    content: Update brain-map-visualization SKILL.md and BRAIN_MAP_PROCESS_GAP_ANALYSIS.md
    status: pending
  - id: verify-build-grep
    content: rg verification (exclude .next) + npm run build in OpenGrimoire
    status: pending
isProject: false
---

# Med-Vis → OpenGrimoire naming alignment

## Constraint: nested folder vs parent rename

`[Med-Vis/OpenGrimoire/BACKUP_STRATEGY.md](D:/portfolio-harness/Med-Vis/OpenGrimoire/BACKUP_STRATEGY.md)` exists today. Renaming the parent to `OpenGrimoire` would collide with a child `OpenGrimoire/`.

**Resolution (order matters):**

1. Move `Med-Vis/OpenGrimoire/BACKUP_STRATEGY.md` → `[Med-Vis/docs/BACKUP_STRATEGY.md](D:/portfolio-harness/Med-Vis/docs/BACKUP_STRATEGY.md)` (edit title/body: product is **OpenGrimoire**; local backup paths use `OpenGrimoire/` after rename; **GitHub URL** stays factual—today it is still `github.com/.../Med-Vis.git`—add one line that `origin` may keep that slug until you rename the repo on GitHub).
2. Remove `Med-Vis/OpenGrimoire/` (`.gitignore` if present).
3. Rename `[D:/portfolio-harness/Med-Vis](D:/portfolio-harness/Med-Vis)` → `D:/portfolio-harness/OpenGrimoire` (PowerShell `Rename-Item`).

## App repo: docs and copy

Update strings and paths in (non-exhaustive; final pass = `rg Med-Vis|med-vis` excluding `.next`):


| Area                  | Files                                                                                                                                                                                                                                                     |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Entry / agent context | `[OpenGrimoire/README.md](D:/portfolio-harness/Med-Vis/README.md)`, `[OpenGrimoire/CLAUDE.md](D:/portfolio-harness/Med-Vis/CLAUDE.md)`                                                                                                                          |
| Ops                   | `[OpenGrimoire/DEPLOYMENT.md](D:/portfolio-harness/Med-Vis/DEPLOYMENT.md)`, `[OpenGrimoire/docs/DEVELOPER_GUIDE.md](D:/portfolio-harness/Med-Vis/docs/DEVELOPER_GUIDE.md)`, `[OpenGrimoire/docs/USAGE_GUIDE.md](D:/portfolio-harness/Med-Vis/docs/USAGE_GUIDE.md)` |
| Prompt artifact       | Root file matching `## Master System Prompt - DataVisualization Implem` (grep hit)                                                                                                                                                                        |
| Docker examples       | Replace image tag `opengrimoire-med-vis` with `**opengrimoire`** (or `opengrimoire-web` if you prefer disambiguation—pick one and use consistently in USAGE_GUIDE).                                                                                                |


## portfolio-harness harness: scripts and state


| File                                                                                                                                         | Change                                                                                                                                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[.cursor/scripts/build_brain_map.py](D:/portfolio-harness/.cursor/scripts/build_brain_map.py)`                                              | Default output dir: `OpenGrimoire/public/brain-map-graph.json` when `OpenGrimoire/` exists; rename variable from `med_vis_*` to `opengrimoire_*`.                                                                                      |
| `[.cursor/scripts/setup_env.py](D:/portfolio-harness/.cursor/scripts/setup_env.py)`                                                          | Project id / path tuples: `OpenGrimoire` folder, dict keys aligned with folder name (`opengrimoire` vs display—match existing pattern for other projects).                                                                          |
| `[.cursor/scripts/security_scan.ps1](D:/portfolio-harness/.cursor/scripts/security_scan.ps1)`                                                | `$subdirs`: `Med-Vis` → `OpenGrimoire`.                                                                                                                                                                                          |
| `[.cursor/scripts/update_github_descriptions.ps1](D:/portfolio-harness/.cursor/scripts/update_github_descriptions.ps1)`                      | **Keep hashtable key `Med-Vis`** (matches GitHub repo slug `ManintheCrowds/Med-Vis` until renamed). Update the **description string** to OpenGrimoire-focused copy; add a one-line comment that the key is the remote repo name. |
| `[.cursor/state/pending_tasks.md](D:/portfolio-harness/.cursor/state/pending_tasks.md)`                                                      | Paths and labels: `Med-Vis` → `OpenGrimoire`.                                                                                                                                                                                    |
| [docs/BRAIN_MAP_AUDIT.md](D:/portfolio-harness/docs/BRAIN_MAP_AUDIT.md), [docs/BRAIN_MAP_E2E.md](D:/portfolio-harness/docs/BRAIN_MAP_E2E.md) | Titles, `cd` paths, relative links (`../OpenGrimoire/...`), verification paths.                                                                                                                                                  |


## OpenHarness (separate git repo)


| File                                                                                                                | Change                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `[.cursor/skills/brain-map-visualization/SKILL.md](D:/openharness/.cursor/skills/brain-map-visualization/SKILL.md)` | `Med-Vis` paths → `OpenGrimoire/...`.                                                                                                       |
| `[docs/BRAIN_MAP_PROCESS_GAP_ANALYSIS.md](D:/openharness/docs/BRAIN_MAP_PROCESS_GAP_ANALYSIS.md)`                   | Replace “Med-Vis” with “OpenGrimoire” where it denotes the app; preserve historical port note if needed (“OpenGrimoire dev server used 3002”). |


## Optional: software plans

`[D:/software/.cursor/plans/](D:/software/.cursor/plans/)` (e.g. `agent_context_atlas_med-vis_*.plan.md`, `brain_map_gap_closure_*.plan.md`) still cite `Med-Vis` paths—update links/headings for accuracy if you want plans to match disk after execution.

## Verification

- `rg -i "Med-Vis|med-vis" D:\portfolio-harness\OpenGrimoire` (exclude `.next`, `node_modules`).
- `rg -i "Med-Vis|med-vis" D:\portfolio-harness\.cursor D:\portfolio-harness\docs`.
- `rg -i "Med-Vis|med-vis" D:\openharness\.cursor D:\openharness\docs`.
- `cd D:\portfolio-harness\OpenGrimoire; npm run build`.

## Risk

**Low** for text/path updates; **Medium** for anyone with hardcoded `Med-Vis` in local scripts, IDE workspace roots, or CI outside this repo—call out in README one-liner: “Folder was renamed from `Med-Vis` to `OpenGrimoire`.”