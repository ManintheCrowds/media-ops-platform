---
name: Unhuman Deals Integration
overview: Add unhuman.deals price-checking to the harness via (1) agent context instructions so the agent uses the API when prices/deals are mentioned, and (2) an MCP tool plus skill for reliable search and comparison.
todos: []
isProject: false
---

# Unhuman Deals Integration Plan

Integrate [unhuman.deals](https://unhuman.deals) (agent-oriented price API) into portfolio-harness so the human can ask "what does X cost?" or "compare prices for Y" and the agent reliably fetches real-time offers.

---

## 1. Context Instructions (Lightweight)

**Goal:** Agent knows to use unhuman.deals when the user mentions prices or deals.

**Artifacts:**


| Action      | Path                                                                                                       | Content                                                                                                                                                                                               |
| ----------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Add section | [.cursorrules](D:\portfolio-harness.cursorrules)                                                           | New subsection under "Context Retrieval" or after "Bitcoin-Chaos org-intent": brief instruction to use unhuman.deals API when user asks about prices, deals, or "what does X cost"; link to llms.txt. |
| Add row     | [.cursor/docs/AGENT_ENTRY_INDEX.md](D:\portfolio-harness.cursor\docs\AGENT_ENTRY_INDEX.md)                 | New row: "Checking prices or comparing deals" -> UNHUMAN_DEALS.md (or inline doc).                                                                                                                    |
| Create doc  | `.cursor/docs/UNHUMAN_DEALS.md`                                                                            | One-page reference: API base URL, endpoints (search, offers), params (q, limit, country), example curl, link to llms.txt. Keeps .cursorrules lean.                                                    |
| Add row     | [.cursor/docs/CONTEXT_INTEGRATION_AUDIT.md](D:\portfolio-harness.cursor\docs\CONTEXT_INTEGRATION_AUDIT.md) | Tool routing table: "Product prices / deals" -> unhuman-deals MCP (or mcp_web_fetch fallback).                                                                                                        |


**Fallback:** If MCP is not loaded, agent can use `mcp_web_fetch` on `https://unhuman.deals/api/search?q=...` and `https://unhuman.deals/api/offers/{id}?country=us` per llms.txt.

---

## 2. MCP Tool (Structured)

**Goal:** Expose `search_products` and `get_offers` as MCP tools so the agent can reliably search and compare without parsing HTML.

**Artifacts:**


| Action | Path                                                                                                      | Content                                                                                                                                                                                    |
| ------ | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Create | `local-proto/scripts/unhuman_deals_mcp.py`                                                                | FastMCP server with two tools. Use `urllib.request` (stdlib) for GET requests to avoid new deps. Pattern: [provenance_mcp.py](D:\portfolio-harness\local-proto\scripts\provenance_mcp.py). |
| Update | [.cursor/mcp.json](D:\portfolio-harness.cursor\mcp.json)                                                  | Add `unhuman-deals` server block: `audit_wrapper.py -- python local-proto/scripts/unhuman_deals_mcp.py`, env `ORG_INTENT_PATH`, `ORG_INTENT_ENFORCE`, `MCP_RISK_TIER: low`.                |
| Update | [local-proto/config/mcp_server_tiers.json](D:\portfolio-harness\local-proto\config\mcp_server_tiers.json) | Add `unhuman-deals` to tier 3 (or 1 if preferred for quick access); smoke_tool: `search_products`.                                                                                         |


**MCP tools:**

```python
@mcp.tool()
def search_products(query: str, limit: int = 10) -> str:
    """Search for products by name, brand, or UPC. Returns JSON array of {id, name, brand, category, image_url}."""

@mcp.tool()
def get_offers(product_id: str, country: str = "us") -> str:
    """Get current pricing offers for a product. Returns JSON array of {merchant, price, currency, url, in_stock}."""
```

**Base URL:** `https://unhuman.deals` (no auth). Supported countries: us, ca, uk, de, fr, it, es, nl, se, pl, au, jp, in, sg, ae, sa, br, mx.

**Risk:** Low (read-only, external API, no credentials).

---

## 3. Skill (Routing + Instructions)

**Goal:** Load price-deals skill when user asks about prices or deals; skill instructs agent to use MCP tools.

**Artifacts:**


| Action | Path                                                                                               | Content                                                                                                                                                                                                                                       |
| ------ | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Create | `.cursor/skills/price-deals/SKILL.md`                                                              | Skill file with frontmatter (triggers: "price", "deal", "compare prices", "what does X cost", "best price for"), steps (search -> get_offers -> summarize), tool choice (unhuman-deals MCP preferred, mcp_web_fetch fallback), exit criteria. |
| Update | [.cursor/rules/role-routing.mdc](D:\portfolio-harness.cursor\rules\role-routing.mdc)               | Add branch **4c** after 4b: "Is the task checking prices or comparing deals?" -> Load **price-deals** (`.cursor/skills/price-deals/SKILL.md`). Add to tie-break priority.                                                                     |
| Update | [.cursor/docs/SKILL_EXCLUSION_GRAPH.md](D:\portfolio-harness.cursor\docs\SKILL_EXCLUSION_GRAPH.md) | No mutual exclusion needed (price-deals composes with docs, qa-verifier). Optional: add composition note.                                                                                                                                     |


**Skill structure (reference):** [browser-web SKILL](D:\portfolio-harness.cursor\skills\browser-web\SKILL.md) — frontmatter, When to use, Inputs, Steps, Composes with, Guardrails.

---

## 4. Verification


| Step           | Command / Action                                                                         |
| -------------- | ---------------------------------------------------------------------------------------- |
| API smoke test | `curl "https://unhuman.deals/api/search?q=airpods+pro&limit=3"`                          |
| MCP smoke test | Restart Cursor; invoke `search_products` via unhuman-deals MCP                           |
| Skill load     | Ask "What's the best price for AirPods Pro?"; agent should load price-deals and call MCP |


---

## 5. Data Flow

```mermaid
flowchart LR
    User[User: "best price for X"]
    Agent[Agent]
    Skill[price-deals SKILL]
    MCP[unhuman-deals MCP]
    API[unhuman.deals API]
    User --> Agent
    Agent --> Skill
    Skill --> Agent
    Agent --> MCP
    MCP --> API
    API --> MCP
    MCP --> Agent
    Agent --> User
```



---

## 6. File Summary


| New                                        | Modified                                           |
| ------------------------------------------ | -------------------------------------------------- |
| `local-proto/scripts/unhuman_deals_mcp.py` | `.cursorrules`                                     |
| `.cursor/skills/price-deals/SKILL.md`      | `.cursor/mcp.json`                                 |
| `.cursor/docs/UNHUMAN_DEALS.md`            | `local-proto/config/mcp_server_tiers.json`         |
|                                            | `.cursor/docs/AGENT_ENTRY_INDEX.md`                |
|                                            | `.cursor/docs/CONTEXT_INTEGRATION_AUDIT.md`        |
|                                            | `.cursor/rules/role-routing.mdc`                   |
|                                            | `.cursor/docs/SKILL_EXCLUSION_GRAPH.md` (optional) |


---

## 7. Risk and Rollback

- **Risk:** Low. Read-only external API; no credentials; no local state.
- **Rollback:** Remove mcp.json block; remove role-routing branch; delete skill and MCP script. Context instructions can remain (agent falls back to mcp_web_fetch).

