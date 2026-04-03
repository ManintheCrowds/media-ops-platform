---
name: Local Port Registry
overview: Introduce a port registry (`.cursor/state/ports.json`) so scripts and agents always know which port each local service is running on, with agent-accessible read and documented conventions.
todos: []
isProject: false
---

# Local Port Registry — Solution Design

## Problem

- **Demo script:** Opens browser to `localhost:3000` but OpenGrimoire may run on 3001, 3002 when 3000 is in use (Next.js auto-increments).
- **Agent parity:** MCP_CAPABILITY_MAP says "Navigate to `http://localhost:3000/context-atlas`" — agent cannot reliably navigate if port is wrong.
- **No single source of truth:** Ports are hardcoded in scripts (start_openrag.ps1: 3000, demo_brain_map.ps1: 3000, Ollama: 11434). When services conflict or auto-increment, nothing is updated.

## Agent-Native Principles


| Principle            | Application                                                                                                                       |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Parity**           | Whatever the user can do (open Brain Map in browser), the agent must achieve via `browser_navigate`. Agent needs the correct URL. |
| **Shared workspace** | Port registry is a file both scripts and agents read/write. Same data space.                                                      |
| **Dynamic context**  | System prompt or capability map should reference "check ports.json for current URL" — runtime, not hardcoded.                     |


## Proposed Solution: Port Registry

### 1. Registry file

**Path:** `.cursor/state/ports.json`

**Schema:**

```json
{
  "services": {
    "opengrimoire": {
      "port": 3002,
      "baseUrl": "http://localhost:3002",
      "source": "demo_brain_map.ps1",
      "updated": "2026-03-19T12:34:56Z"
    },
    "openrag": { "port": 3000, "baseUrl": "http://localhost:3000", "source": "OPENRAG_URL", "updated": "..." },
    "ollama": { "port": 11434, "baseUrl": "http://localhost:11434", "source": "fixed", "updated": "..." }
  },
  "defaults": {
    "opengrimoire": 3000,
    "openrag": 3000,
    "ollama": 11434
  }
}
```

- **services:** Runtime-discovered or script-written. When a script starts a server, it writes the actual port.
- **defaults:** Fallback when service not yet running. Used when registry has no entry.

### 2. Who writes the registry


| Service       | Writer               | When                                                                              |
| ------------- | -------------------- | --------------------------------------------------------------------------------- |
| **OpenGrimoire** | `demo_brain_map.ps1` | After starting npm run dev, parse stdout for `localhost:(\d+)`, write to registry |
| **OpenRAG**   | `start_openrag.ps1`  | Already uses OPENRAG_URL; could write port to registry when starting              |
| **Ollama**    | Static / manual      | Fixed 11434; add to defaults; optional: probe and write if reachable              |


**OpenGrimoire capture:** Run `npm run dev` in a background job, wait 8s, `Receive-Job` to get output, regex `localhost:(\d+)`, write to ports.json. Then open browser with that URL.

### 3. Agent access


| Agent action          | How                                                                                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Navigate to Brain Map | `read_file` `.cursor/state/ports.json` → get `services.opengrimoire.baseUrl` or `defaults.opengrimoire` → `browser_navigate` to `{baseUrl}/context-atlas` |
| Navigate to OpenRAG   | Same pattern                                                                                                                                        |
| Know what's running   | Read `ports.json`; `services` = runtime; `defaults` = conventional fallback                                                                         |


**Capability map update:** "Before navigating to OpenGrimoire, read `.cursor/state/ports.json`; use `services.opengrimoire.baseUrl` if present, else `http://localhost:{defaults.opengrimoire}`."

### 4. Placement (tech-lead)


| Artifact     | Path                            | Rationale                                                                 |
| ------------ | ------------------------------- | ------------------------------------------------------------------------- |
| Registry     | `.cursor/state/ports.json`      | State dir is agent-accessible, already holds handoff, daily, decision-log |
| Doc          | `.cursor/docs/PORT_REGISTRY.md` | Documents schema, writers, agent usage                                    |
| Known-issues | `.cursor/state/known-issues.md` | Log the demo-script port mismatch; link to PORT_REGISTRY                  |


### 5. Implementation order

1. **Log issue** — Add known-issues entry: demo script opens 3000 but OpenGrimoire may be on 3001/3002; solution: port registry.
2. **Create PORT_REGISTRY.md** — Schema, defaults, agent usage, browser-web skill note.
3. **Create ports.json** — Initial file with `defaults` only (no runtime entries yet).
4. **Update demo_brain_map.ps1** — Use Start-Job to capture npm output; parse port; write to registry; open browser with discovered URL.
5. **Update MCP_CAPABILITY_MAP** — OpenGrimoire row: "Read ports.json for baseUrl; default 3000."
6. **Update browser-web SKILL** — Add note: "For local dev (OpenGrimoire, OpenRAG), check .cursor/state/ports.json for actual port before navigate."

### 6. Access control

- **Private:** ports.json lives in `.cursor/state/` — not committed if state is gitignored; or commit a template with defaults only.
- **Agent access level:** Any agent with `read_file` on workspace can read. No special MCP tool needed — parity via filesystem.
- **Writers:** Scripts that start services. Human can manually edit if needed.

### 7. Out of scope (for now)

- Port allocation daemon
- Automatic cleanup when server stops (stale entries)
- Production/staging URLs (different concern)

## Files to create/modify


| File                                 | Action                                       |
| ------------------------------------ | -------------------------------------------- |
| `.cursor/state/known-issues.md`      | Add port mismatch issue                      |
| `.cursor/docs/PORT_REGISTRY.md`      | New — schema, usage                          |
| `.cursor/state/ports.json`           | New — defaults template                      |
| `.cursor/scripts/demo_brain_map.ps1` | Capture port, write registry, use it for URL |
| `.cursor/docs/MCP_CAPABILITY_MAP.md` | OpenGrimoire row: check ports.json              |
| `skills/browser-web/SKILL.md`        | Note: local dev → check ports.json           |


