---
name: Brain Map Visual Audit
overview: Plan for a full visual audit and E2E analysis of the Brain Map system across OpenHarness (standalone) and portfolio-harness (Med-Vis), including parser verification, viewer testing, accessibility scans, critic report, and documentation.
todos: []
isProject: false
---

# Brain Map Full Visual Audit and E2E Analysis Plan

## Current Architecture Summary

```mermaid
flowchart TB
    subgraph OpenHarness [OpenHarness - Standalone]
        OH_Parser[scripts/build_brain_map.py]
        OH_State[state/ or .cursor/state]
        OH_Viewer[scripts/brain_map_viewer.html]
        OH_JSON[brain-map-graph.json]
        OH_Parser --> OH_State
        OH_Parser --> OH_JSON
        OH_Viewer --> OH_JSON
    end

    subgraph PortfolioHarness [Portfolio-Harness - Med-Vis]
        PH_Parser[.cursor/scripts/build_brain_map.py]
        PH_State[.cursor/state]
        PH_MedVis[Med-Vis Next.js]
        PH_API[/api/brain-map/graph]
        PH_Page[/brain-map]
        PH_Parser --> PH_State
        PH_Parser --> PH_MedVis
        PH_MedVis --> PH_API
        PH_Page --> PH_API
    end
```



**Key differences:**

- **OpenHarness:** Standalone vis-network HTML viewer; parser outputs to `state/brain-map-graph.json`; no Med-Vis.
- **Portfolio-harness:** Med-Vis Next.js app with D3 force-directed graph; parser outputs to `Med-Vis/public/brain-map-graph.json`; no standalone HTML viewer.

---

## Phase 1: Parser Verification

### 1.1 OpenHarness


| Step | Action                                                                                                             | Verification                                                                     |
| ---- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| 1    | `cd D:\openharness; python scripts/build_brain_map.py`                                                             | Exit 0; "Wrote ..." printed                                                      |
| 2    | Check `state/brain-map-graph.json` exists                                                                          | File present                                                                     |
| 3    | Validate JSON schema                                                                                               | `nodes` (array), `edges` (array), `generated` (ISO8601), `sessionCount` (number) |
| 4    | Optional: `$env:BRAIN_MAP_OUTPUT="D:\openharness\scripts\brain-map-graph.json"; python scripts/build_brain_map.py` | JSON in scripts/ for standalone viewer                                           |


### 1.2 Portfolio-harness


| Step | Action                                                               | Verification                                            |
| ---- | -------------------------------------------------------------------- | ------------------------------------------------------- |
| 1    | `cd D:\portfolio-harness; python .cursor/scripts/build_brain_map.py` | Exit 0; output to `Med-Vis/public/brain-map-graph.json` |
| 2    | Validate schema                                                      | Same as above                                           |


**Schema (Brain Map):**

- `nodes`: `[{ id, group, accessCount, path }]`
- `edges`: `[{ source, target, weight, sessionType, sessions }]`
- `generated`: ISO8601 string
- `sessionCount`: number

---

## Phase 2: Standalone Viewer (OpenHarness)

### 2.1 Serve and Load


| Step | Action                                                                                                                           | Verification                           |
| ---- | -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| 1    | Ensure JSON in scripts: `$env:BRAIN_MAP_OUTPUT="D:\openharness\scripts\brain-map-graph.json"; python scripts/build_brain_map.py` | JSON at `scripts/brain-map-graph.json` |
| 2    | `cd D:\openharness\scripts; python -m http.server 8080` (background)                                                             | Server on 8080                         |
| 3    | Navigate to `http://localhost:8080/brain_map_viewer.html`                                                                        | Page loads                             |
| 4    | `browser_wait_for` (text: "nodes" or time: 3)                                                                                    | Content ready                          |
| 5    | `browser_snapshot`                                                                                                               | Nodes visible or "No nodes" / dropzone |
| 6    | `browser_take_screenshot`                                                                                                        | Visual evidence                        |


**Fallback:** If fetch fails (empty state), viewer shows dropzone; use file input to load `brain-map-graph.json` manually.

### 2.2 File Input Path

If graph is empty, use "Choose JSON file" to load `state/brain-map-graph.json` and verify render.

---

## Phase 3: Med-Vis (Portfolio-harness)

### 3.1 Start and Navigate


| Step | Action                                                           | Verification                              |
| ---- | ---------------------------------------------------------------- | ----------------------------------------- |
| 1    | `cd D:\portfolio-harness\Med-Vis; npm run dev` (background)      | Dev server on 3000                        |
| 2    | Navigate to `http://localhost:3000/brain-map`                    | Page loads                                |
| 3    | `browser_wait_for` (textGone: "Loading brain map..." or time: 3) | Graph or EMPTY_GRAPH visible              |
| 4    | `browser_snapshot`                                               | D3 graph nodes, header, "Brain Map" title |
| 5    | `browser_take_screenshot`                                        | Visual evidence                           |


### 3.2 Describe and Summarize

- Header: "Brain Map" + refresh instruction
- Graph: D3 force-directed; nodes colored by group; edges by sessionType
- Fallback: EMPTY_GRAPH (3 nodes) when API returns 404 or empty

---

## Phase 4: A2UI / Accessibility

### 4.1 BrowserStack Accessibility Scan

**Constraint:** `startAccessibilityScan` requires a **public URL**. For localhost:

- Use [BrowserStack Local](https://www.browserstack.com/docs/local-testing) to expose localhost, or
- Deploy to a staging URL and scan that.

**If public URL available:**


| Step | Action                                                                                     | Verification           |
| ---- | ------------------------------------------------------------------------------------------ | ---------------------- |
| 1    | `mcp_browserstack_startAccessibilityScan(name="Brain Map Viewer", pageURL="<public-url>")` | Scan ID returned       |
| 2    | Fetch issues via `fetchAccessibilityIssues` if needed                                      | WCAG violations listed |


**If localhost only:** Document that accessibility scan requires public URL or tunnel; use `mcp_browserstack_accessibilityExpert` for WCAG guidance instead.

### 4.2 Accessibility Expert (WCAG)


| Step | Action                                                                                                                                                                                                                                           |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1    | `mcp_browserstack_accessibilityExpert(query="What WCAG 2.1 AA requirements apply to interactive force-directed graph visualizations with nodes and edges? Include contrast, focus management, keyboard navigation, and screen reader support.")` |
| 2    | Apply findings to audit report                                                                                                                                                                                                                   |


---

## Phase 5: Critic Report (critic-loop-gate)

Produce model-as-judge critic JSON **before** marking complete:

```json
{
  "pass": true | false,
  "score": 0.0 - 1.0,
  "issues": [{"type": "...", "detail": "..."}],
  "fixes": [{"action": "...", "detail": "..."}]
}
```

**Domain:** `workflow_ui`

**Criteria:** Parser runs, viewer loads, nodes/edges visible (or empty state handled), accessibility considerations documented, docs created.

---

## Phase 6: Documentation

### 6.1 [docs/BRAIN_MAP_AUDIT.md](D:\openharness\docs\BRAIN_MAP_AUDIT.md) (OpenHarness) and [docs/BRAIN_MAP_AUDIT.md](D:\portfolio-harness\docs\BRAIN_MAP_AUDIT.md) (portfolio-harness)


| Section           | Content                                                                      |
| ----------------- | ---------------------------------------------------------------------------- |
| **Purpose**       | How to run a visual audit of the Brain Map system                            |
| **Prerequisites** | Python 3.9+, state dir with daily/handoff data, http.server or Med-Vis       |
| **Steps**         | 1) Run parser; 2) Serve viewer; 3) Open URL; 4) Optional: accessibility scan |
| **Tools**         | Playwright MCP, cursor-ide-browser, BrowserStack (accessibility, Percy)      |
| **MCP servers**   | playwright, cursor-ide-browser, browserstack (if configured)                 |
| **Skills**        | browser-web, brain-map-visualization, qa-verifier                            |


### 6.2 [docs/BRAIN_MAP_E2E.md](D:\openharness\docs\BRAIN_MAP_E2E.md) (OpenHarness) and [docs/BRAIN_MAP_E2E.md](D:\portfolio-harness\docs\BRAIN_MAP_E2E.md) (portfolio-harness)


| Step | Action                                                                | Verification                                                  |
| ---- | --------------------------------------------------------------------- | ------------------------------------------------------------- |
| 1    | Run parser from project root                                          | brain-map-graph.json exists; JSON has nodes, edges, generated |
| 2    | Start HTTP server (OpenHarness: scripts/; portfolio-harness: Med-Vis) | Server running                                                |
| 3    | Navigate to viewer URL                                                | Page loads                                                    |
| 4    | Wait for content                                                      | browser_wait_for (text or time 2–3s)                          |
| 5    | Snapshot                                                              | browser_snapshot — nodes visible or empty state               |
| 6    | Screenshot                                                            | browser_take_screenshot                                       |
| 7    | Optional: file input                                                  | If fetch fails, load JSON via file input                      |
| 8    | Optional: accessibility scan                                          | startAccessibilityScan on public URL                          |


---

## Phase 7: OpenHarness Standalone System

**Requirement:** OpenHarness must have a self-contained Brain Map process.

**Current state:** OpenHarness already has:

- [scripts/build_brain_map.py](D:\openharness\scripts\build_brain_map.py)
- [scripts/brain_map_viewer.html](D:\openharness\scripts\brain_map_viewer.html)
- [state/brain-map-graph.json](D:\openharness\state\brain-map-graph.json)
- [docs/BRAIN_MAP.md](D:\openharness\docs\BRAIN_MAP.md)
- [.cursor/skills/brain-map-visualization/SKILL.md](D:\openharness.cursor\skills\brain-map-visualization\SKILL.md)

**Gaps to address:**

1. Add [docs/BRAIN_MAP_AUDIT.md](D:\openharness\docs\BRAIN_MAP_AUDIT.md) — user-facing audit guide
2. Add [docs/BRAIN_MAP_E2E.md](D:\openharness\docs\BRAIN_MAP_E2E.md) — E2E playbook
3. Document one-command flow: `BRAIN_MAP_OUTPUT=scripts/brain-map-graph.json python scripts/build_brain_map.py` then serve scripts/

---

## Phase 8: Skill and Rule Updates

### 8.1 brain-map-visualization (OpenHarness)

Add to Steps section:

> **For visual audit:** Load browser-web skill; use Playwright MCP or cursor-ide-browser; run accessibility scan (if public URL); produce critic report per critic-loop-gate.

### 8.2 capability-summary (OpenHarness)

Add row:

> browser_navigate → Brain Map viewer; startAccessibilityScan → accessibility

### 8.3 qa-verifier (portfolio-harness)

Add to Matrix or Verification types:

> **Brain Map E2E:** parser → serve → navigate → snapshot → screenshot. See docs/BRAIN_MAP_E2E.md.

---

## MCP / Tools Reference


| Tool                    | Server                          | Use                             |
| ----------------------- | ------------------------------- | ------------------------------- |
| browser_navigate        | Playwright / cursor-ide-browser | Open viewer URL                 |
| browser_snapshot        | Same                            | Accessibility tree              |
| browser_take_screenshot | Same                            | Visual evidence                 |
| browser_wait_for        | Same                            | Wait for content                |
| startAccessibilityScan  | BrowserStack                    | WCAG scan (requires public URL) |
| accessibilityExpert     | BrowserStack                    | A11y questions                  |


---

## PowerShell Commands (Windows)

```powershell
# OpenHarness
cd D:\openharness; python scripts/build_brain_map.py
$env:BRAIN_MAP_OUTPUT="D:\openharness\scripts\brain-map-graph.json"; python scripts/build_brain_map.py
cd scripts; python -m http.server 8080

# Portfolio-harness
cd D:\portfolio-harness; python .cursor/scripts/build_brain_map.py
cd Med-Vis; npm run dev
```

---

## Execution Order (Agent Mode)

1. Parser verification (both repos)
2. Standalone viewer (OpenHarness)
3. Med-Vis (portfolio-harness)
4. Accessibility (expert query; scan if URL public)
5. Critic JSON
6. Create BRAIN_MAP_AUDIT.md and BRAIN_MAP_E2E.md (both repos)
7. Update skills/rules

---

## Risk and Notes

- **Empty graph:** OpenHarness state may have no daily/handoff data → empty nodes. Use file input or seed data for visual verification.
- **BrowserStack scan:** Localhost not directly scannable; document tunnel/staging requirement.
- **Med-Vis EMPTY_GRAPH:** Fallback renders 3 sample nodes when API fails; verify both success and fallback paths.

