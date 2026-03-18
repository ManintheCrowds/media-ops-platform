---
name: Panel Section Additions
overview: Conservative bullet suggestions for your new section in Brandon's Bitcoin+AI panel doc. Focuses on topics you can speak to that aren't already covered, with no new demo content—demos stay as-is if used.
todos: []
isProject: false
---

# Panel Section Additions — Conservative Bullets for Your Topics

## Context

Brandon's doc already covers L402, x402, Lightning Labs Agent Tools, StartWithBitcoin, LangChainBitcoin, and the payment rail comparison. You've been asked to add a **new section** with bullets for topics you want to cover. Demos: keep them tight; what you have works.

---

## Proposed New Section: "Additional Topics / Panelist Contributions"

Add this as a new section (e.g., after Reference Materials or before Audience Q&A). Use 2–4 bullets max—conservative.

### Suggested Bullets (pick what fits)

**1. Cashu / Routstr — Lightning eCash for AI inference (Developer Tooling angle)**

- **Bullet:** "Cashu (Lightning eCash) + Routstr: pay-per-token AI inference with no accounts, no KYC. OpenAI-compatible; agents point at api.routstr.com with a Cashu token. Complements L402 for the 'agent pays for compute' use case—different flow (blinded tokens vs invoice+macaroon) but same Lightning rail."
- **When to use:** If you want to surface a Lightning-native option Brandon doesn't mention. Fits the 32:00 Developer Tooling block.

**2. Beyond payment: Bitcoin block space as data layer? (Road Ahead angle)**

- **Bullet:** "Open question from recent survey: AI compute pools (Gonka, x402, Lumerin, Routstr, etc.) all use Bitcoin/crypto as payment—none use inscriptions or OP_RETURN as an intent data layer for Bitcoiner AI coordination. Is block space as AI data an unexplored frontier, or is payment rail sufficient?"
- **When to use:** If you want a brief 'road ahead' / research angle. Fits the 42:00 block.

**3. Agent-native tooling beyond payment (optional)**

- **Bullet:** "Agents need more than a wallet: action parity (every UI action reachable by tools), provenance for Bitcoin-sourced data, and 402 handling in execution loops. Developer tooling is improving, but the full stack—pay + verify + act—is still emerging."
- **When to use:** If you want to tie in harness/agent-native work without going deep. Risk: may feel meta or off-topic.

---

## What NOT to Add

- **No new demo content.** You said demos should be super tight; current state works. Do not add demo bullets or expand demo scope.
- **No duplication.** Brandon already covers L402, x402, Lightning Labs tools, StartWithBitcoin, LangChainBitcoin. Skip those.
- **No over-expansion.** 2–4 bullets total; you can use 2 if that feels right.

---

## Recommendation

**Minimal set (2 bullets):** #1 (Cashu/Routstr) + #2 (data vs payment). Both are distinct from Brandon's doc and grounded in your recent work (Routstr skill, bitcoin-ai-pools survey).

**If you want only one:** #1 is the strongest—Routstr is a concrete, Lightning-native option the doc omits, and it fits naturally in the Developer Tooling discussion.

---

## Copy-Paste Block for Brandon's Doc

```
Additional Topics / Panelist Contributions

• Cashu / Routstr: Pay-per-token AI inference via Lightning eCash. No accounts, no KYC; OpenAI-compatible. Agents point at Routstr with a Cashu token—complements L402 for agent-paid compute.

• Data layer vs payment: Survey of AI pools (Gonka, x402, Lumerin, Routstr, etc.) shows all use Bitcoin/crypto as payment; none use inscriptions or OP_RETURN as a data layer for AI coordination. Open question: is block space as AI data an unexplored frontier?
```

---

## Demo Note

If demos run: keep them as-is. No additions to the plan. Current setup is sufficient.