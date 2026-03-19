---
name: Workshop Prep Videos and Brandon Notes
overview: Curated example videos and debate prep materials aligned to the panel's moment-by-moment flow (from Brandon PDF + 2026-03-18-panel-workshop-prep.md), plus suggested leading questions for Brandon to steer discussion.
todos: []
isProject: false
---

# Workshop Prep: Example Videos, Debate Materials, and Leading Questions for Brandon

Based on [2026-03-18-panel-workshop-prep.md](D:\portfolio-harness\docs\brainstorms\2026-03-18-panel-workshop-prep.md) (source: Brandon PDF + panel-section-additions).

---

## Example Videos (by Panel Block)

### Opening (0–8 min) — "Agentic moment" / why payments matter


| Video                                                                                                           | Duration | Why watch                                                                                                                                                   |
| --------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [TFTC: MACHINES Use BITCOIN — Jim Carucci](https://www.tftc.io/bitcoin-ai-agent-economy-jim-carucci-tftc/)      | ~1h      | "Bitcoin is the glue that holds together an open agent economy." Agent-to-agent commerce, modular AI, Bitcoin micropayments. Strong opening-story material. |
| [AI Agents Are Already Using Bitcoin — Bitcoin Policy Hour Ep. 27](https://www.youtube.com/watch?v=MTTxyywbV4s) | ~59 min  | Policy angle; bot-run economy; good for "moment that made you realize agents need their own money."                                                         |


### L402 Deep Dive (8–20 min)


| Video                                                                                                                                           | Duration | Why watch                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------- |
| [Unleashing AI with L402: Replit, LND, and More — Lightning Labs](https://www.youtube.com/watch?v=PzspY0rePC0)                                  | ~22 min  | L402 + AI hands-on; Replit, LND; invoice + macaroon flow. |
| [Lightning Labs: The Agents Are Here and They Want to Transact](https://lightning.engineering/posts/2026-02-11-ln-agent-tools/)                 | Article  | Lightning Agent Tools; seven composable skills.           |
| [Lightning Labs: Why L402 Is the Internet-Native Payments Protocol for Agents](https://lightning.engineering/posts/2026-03-11-L402-for-agents/) | Article  | L402 protocol, HTTP 402, machine-payable web.             |


### Payment Rail Showdown (20–32 min)


| Video                                                                                                                                                                                                           | Duration | Why watch                                                                                                                             |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [Someone Is About To Control Every Payment On Earth — Matt Corallo (TFTC)](https://www.youtube.com/watch?v=1CrdxZj9ces)                                                                                         | ~72 min  | **Critical.** Proprietary vs open rails; ACP, x402, Stripe; why Bitcoin matters. Directly supports Lightning vs x402 vs Legacy table. |
| [Bitfinex: Why Bitcoin and Stablecoins on Lightning Will Power AI Agent Payments](https://blog.bitfinex.com/education/why-bitcoin-and-stablecoins-on-lightning-will-power-the-next-phase-of-ai-agent-payments/) | Article  | Stablecoins on Lightning, Taproot Assets; complements rail comparison.                                                                |


### Developer Tooling (32–42 min)


| Video                                                                                                               | Duration | Why watch                                                                    |
| ------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------- |
| [eCash on Bitcoin & Nostr w/ Calle from Cashu (BTC201)](https://www.youtube.com/watch?v=Z55drsUfIos)                | ~72 min  | Cashu eCash, blinded tokens, Lightning mint; preps your Cashu/Routstr angle. |
| [The Smartest Man I Know Says Your Job Is Already Gone — Calle (TFTC)](https://www.youtube.com/watch?v=Iui9ixdzkbw) | ~76 min  | Calle (Cashu) on AI, jobs, future; broader context for Cashu/Routstr.        |
| [Start With Bitcoin](https://www.startwithbitcoin.com/)                                                             | Site     | Claude Code Skill, full setup; referenced in Brandon's list.                 |
| [LangChainBitcoin](https://github.com/langchain-ai/langchain-bitcoin)                                               | Repo     | AI tools for Lightning; LangChain integration.                               |


### Road Ahead (42–50 min)


| Video                                                                                                                    | Duration | Why watch                                                  |
| ------------------------------------------------------------------------------------------------------------------------ | -------- | ---------------------------------------------------------- |
| [Matt Corallo TFTC](https://www.youtube.com/watch?v=1CrdxZj9ces)                                                         | ~72 min  | Taproot Assets, scaling, "one thing in 12 months" framing. |
| [How AI Agents Could Reshape the Global Economy by 2030 — Bitcoin Magazine](https://www.youtube.com/watch?v=lmA0Y6or4JA) | Video    | Long-term vision; agent economy.                           |


### Q&A / Debate Prep


| Video                                                                                                       | Duration | Why watch                                                             |
| ----------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------- |
| [You Gave AI Full Access To Your Computer — Mark Suman (TFTC)](https://www.youtube.com/watch?v=BpnzrmkpPgQ) | ~61 min  | Agent security, access, trust; wallet security, bounded agents.       |
| [OpenClaw Agents, Bitcoin & Nostr](https://www.tftc.io/openclaw-agents-bitcoin-nostr/)                      | TFTC     | Marty Bent's OpenClaw agents; autonomous wallets, Lightning channels. |


---

## Debate Preparation Materials

### Core tension: Open vs proprietary rails

- **Matt Corallo (TFTC)**: Proprietary rails (ACP, x402, Stripe) will box out open agents; Bitcoin is the only open rail.
- **Spiral: Open-Source AI Needs to Get Serious** (referenced in [bitcoin_meetup_talk_points.md](D:\portfolio-harness\docs\bitcoin_meetup_talk_points.md)): Same thesis.
- **Jim Carucci**: "We either have Apples, Amazons, Googles, OpenAI controlling everything, or we have an open system."

### Payment rail table (know cold)

From workshop prep — Lightning vs x402 vs Legacy: settlement, fees, identity, counterparty risk, micropayments, censorship resistance, developer adoption, volatility. Rehearse each row.

### Your distinct angles (for debate)

1. **Cashu/Routstr**: Blinded tokens vs macaroon; same Lightning rail, different protocol.
2. **Data layer vs payment**: AI pools use payment; none use inscriptions/OP_RETURN as data layer.
3. **Pay + verify + act**: Agents need provenance, 402 handling in loops, action parity.

---

## Leading Questions for Brandon (to add to the doc)

Brandon asked: *"Any other notes you want to add to the doc? Ideally some leading questions so I can steer you in interesting directions."*

### Suggested leading questions (copy-paste block)

```
Leading Questions (for moderator to steer panel)

Opening / Agentic moment
• "What's the moment that made you realize agents would need their own money?"
• "When did it click that traditional payment rails—cards, Stripe, API keys—wouldn't work for autonomous agents?"

L402 / Protocol
• "Is L402 the moment HTTP 402 finally gets its protocol, or just the beginning?"
• "If two protocols (L402, Cashu) already sit on Lightning for machine payments, what comes next?"

Payment rails
• "If you're building an agent today, which rail do you reach for first and why?"
• "Lightning, x402, or cards—what's the one tradeoff that decides it for you?"

Developer tooling
• "How many lines of code to give an agent a Lightning wallet today vs. a year ago? What's still missing?"
• "Agents can pay—but can they verify what they paid for? Is provenance part of the stack?"

Road ahead
• "What's the one thing that needs to happen in the next 12 months for Lightning to win?"
• "AI pools use Bitcoin as payment; none use block space (inscriptions, OP_RETURN) as a data layer. Is that an unexplored frontier or is payment sufficient?"

Q&A seed
• "Agent wallet security: bounded wallets, approval gates, or something else?"
• "Walled garden risk: L402 and Cashu are permissionless; ACP and x402 introduce gatekeepers. How do you think about that?"
```

### Rationale for each

- **Opening**: Surfaces your "emergent behavior + mistakes + impacts" story.
- **L402**: Sets up your "just the beginning" + Cashu/Routstr angle.
- **Payment rails**: Directly invokes the comparison table.
- **Developer tooling**: Leads to "pay + verify + act" and Routstr.
- **Road ahead**: Surfaces data-layer angle and "one thing in 12 months."
- **Q&A**: Wallet security, walled gardens—your prep answers.

---

## Quick reference: written materials (from Brandon's list)

- [L402 Protocol Documentation](https://docs.lightning.engineering/the-lightning-network/l402)
- [Coinbase x402 Protocol Documentation](https://docs.cdp.coinbase.com/x402/docs/client-server-model)
- [Routstr docs](https://docs.routstr.com/)
- [Cashu](https://cashu.space)
- [Spiral: Open-Source AI Needs to Get Serious](https://spiralbtc.substack.com/p/open-source-ai-needs-to-get-serious)

---

## Pre-panel checklist (from workshop prep)

- Review payment rail table — know each row
- Memorize Cashu/Routstr one-liner
- Memorize data layer one-liner
- Rehearse opening story (emergent behavior, mistakes, impacts)
- Pick answer to "one thing in 12 months" (A, B, C, or D)
- Know answer to "which rail first"
- Watch Matt Corallo TFTC (payment rails) + Lightning Labs L402 video (protocol)

