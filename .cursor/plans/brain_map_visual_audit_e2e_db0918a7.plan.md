---
name: Brain Map Visual Audit E2E
overview: Execute a full visual audit and end-to-end analysis of the Brain Map system using Playwright MCP, cursor-ide-browser, BrowserStack (when available), produce critic JSON, and update BRAIN_MAP_AUDIT.md and BRAIN_MAP_E2E.md with findings and playbook steps.
todos: []
isProject: false
---

# Brain Map Full Visual Audit and E2E Analysis

## Current State

- **OpenHarness** ([D:\openharness](D:\openharness)): Parser at [scripts/build_brain_map.py](D:\openharness\scripts\build_brain_map.py), standalone viewer at [scripts/brain_map_viewer.html](D:\openharness\scripts\brain_map_viewer.html)
- **Docs exist:** [BRAIN_MAP_AUDIT.md](D:\openharness\docs\BRAIN_MAP_AUDIT.md), [BRAIN_MAP_E2E.md](D:\openharness\docs\BRAIN_MAP_E2E.md) — contain steps, WCAG guidance, verification checklist
- **Med-Vis** (portfolio-harness): D3 viewer at `/context-atlas` and `/brain-map`; Playwright e2e in [Med-Vis/e2e/](D:\portfolio-harness\Med-Vis\e2e\) — smoke.spec.ts does not cover context-atlas

---

## Execution Plan

### Phase 1: Parser Verification

1. Run parser from OpenHarness root:

```powershell
   cd D:\openharness; $env:BRAIN_MAP_OUTPUT="D:\openharness\scripts\brain-map-graph.json"; python scripts/build_brain_map.py
   

```

1. Verify `scripts/brain-map-graph.json` exists; validate schema: `nodes`, `edges`, `generated`, `sessionCount` (per [BRAIN_MAP_SCHEMA.md](D:\portfolio-harness\Med-Vis\docs\BRAIN_MAP_SCHEMA.md))

### Phase 2: Standalone Viewer Audit

1. Start HTTP server in background: `cd D:\openharness\scripts; python -m http.server 8080`
2. Use **Playwright MCP** or **cursor-ide-browser**:
  - `browser_navigate` to `http://localhost:8080/brain_map_viewer.html`
  - `browser_wait_for` (time 2–3s or text "nodes" / "No nodes")
  - `browser_snapshot` — inspect accessibility tree, nodes or dropzone
  - `browser_take_screenshot` — visual evidence
3. If empty state: verify dropzone and file input; optionally load JSON via file input
4. Stop HTTP server after audit

### Phase 3: Med-Vis / OpenGrimoire Audit (if portfolio-harness present)

1. Run parser from portfolio-harness: `python .cursor/scripts/build_brain_map.py` (output to Med-Vis/public)
2. Start Med-Vis dev server: `cd Med-Vis; npm run dev`
3. Navigate to `http://localhost:3000/context-atlas` (or `/brain-map`)
4. `browser_wait_for` → `browser_snapshot` → `browser_take_screenshot`
5. Stop dev server after audit

### Phase 4: Accessibility (when feasible)

- **BrowserStack Local:** If user has tunnel running, call `startAccessibilityScan` with tunneled URL
- **accessibilityExpert:** Query WCAG guidance for graph viz; document if 401 (credentials)
- **Manual:** Apply [WCAG 2.1 AA checklist](D:\openharness\docs\BRAIN_MAP_AUDIT.md) (contrast, keyboard, focus, ARIA) — already in BRAIN_MAP_AUDIT.md

### Phase 5: Critic JSON

Produce model-as-judge critic per critic-loop-gate (domain: `workflow_ui`):

```json
{
  "pass": true|false,
  "score": 0.0-1.0,
  "issues": [{"type": "...", "detail": "..."}],
  "fixes": [{"action": "...", "detail": "..."}]
}
```

### Phase 6: Documentation Updates

1. **BRAIN_MAP_AUDIT.md** — Append new **Audit Findings** row with date, component status, notes; update critic JSON if revised
2. **BRAIN_MAP_E2E.md** — Confirm steps match execution; add any new steps (e.g. Med-Vis Playwright spec reference)
3. **Optional:** Add `context-atlas.spec.ts` in Med-Vis/e2e/ for automated E2E (see below)

---

## Optional: Med-Vis Playwright Spec for Context Atlas

Add [Med-Vis/e2e/context-atlas.spec.ts](D:\portfolio-harness\Med-Vis\e2e\context-atlas.spec.ts):

```typescript
import { test, expect } from '@playwright/test';

test.describe('Context Atlas (Brain Map)', () => {
  test('context-atlas loads and shows graph or empty state', async ({ page }) => {
    await page.goto('/context-atlas');
    await expect(page.getByText(/Loading context graph|No nodes|nodes/)).toBeVisible({ timeout: 10000 });
    // Graph canvas or empty-state fallback
    await expect(page.locator('#mynetwork, [data-testid="brain-map-graph"], .empty-state')).toBeVisible({ timeout: 15000 });
  });
});
```

Requires: `baseURL` in playwright.config; BrainMapGraph has `data-testid` or identifiable selector. Check [BrainMapGraph.tsx](D:\portfolio-harness\Med-Vis\src\components\BrainMap\BrainMapGraph.tsx) for existing test IDs.

---

## Tool and Skill Reference


| Tool                    | MCP Server                      | Use                              |
| ----------------------- | ------------------------------- | -------------------------------- |
| run_terminal_cmd        | harness                         | build_brain_map.py, http.server  |
| browser_navigate        | Playwright / cursor-ide-browser | Open viewer URL                  |
| browser_snapshot        | Same                            | Accessibility tree               |
| browser_take_screenshot | Same                            | Visual evidence                  |
| browser_wait_for        | Same                            | Wait for content                 |
| startAccessibilityScan  | BrowserStack                    | WCAG scan (tunneled/staging URL) |
| accessibilityExpert     | BrowserStack                    | A11y questions                   |


**Skills:** browser-web, brain-map-visualization, qa-verifier, frontend-a2ui (for A2UI checklist when auditing components)

---

## File Summary


| Action            | Path                                                                                                                                                |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Update            | [D:\openharness\docs\BRAIN_MAP_AUDIT.md](D:\openharness\docs\BRAIN_MAP_AUDIT.md) — append findings, critic JSON                                     |
| Update            | [D:\openharness\docs\BRAIN_MAP_E2E.md](D:\openharness\docs\BRAIN_MAP_E2E.md) — confirm/refine steps                                                 |
| Create (optional) | [D:\portfolio-harness\Med-Vis\e2e\context-atlas.spec.ts](D:\portfolio-harness\Med-Vis\e2e\context-atlas.spec.ts) — Playwright E2E for context-atlas |


---

## Verification

- Parser exits 0; JSON schema valid
- Standalone viewer: snapshot shows nodes or dropzone; screenshot captured
- Med-Vis (if run): context-atlas loads; graph or empty state visible
- Critic JSON produced and included in audit doc
- Docs updated with findings

