---
name: Task Info Gathering
overview: Consolidated answers to the "What AI needs from you" questions for tasks I1, I2, H5, R1-R3, and G8, based on codebase and docs research.
todos: []
isProject: false
---

# Task Info Gathering — What AI Needs From You

Answers to the "What AI needs from you" questions for each task, derived from codebase and docs.

---

## I1: Evaluate Continue.dev

**What AI needs from you:**


| Need                   | Answer (from codebase)                                                                                                                                                                                                                                                                                                                                                        |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Install path**       | VS Code extension from [continue.dev](https://continue.dev) or VS Code marketplace. No explicit install path in repo; standard extension install.                                                                                                                                                                                                                             |
| **Ollama config**      | Add Ollama model (e.g. `llama3.2`) in Continue settings. Plan: [continue_aider_eval.plan.md](D:\portfolio-harness\plans\continue_aider_eval.plan.md). Prereq: `ollama run llama3.2`.                                                                                                                                                                                          |
| **Handoff paste flow** | 1) Write handoff (`.cursorrules` context handoff); 2) Run `generate_next_prompt.ps1`; 3) Run `copy_continue_prompt.ps1` (or `.cmd` on Windows); 4) Paste into new Continue chat. Scripts: [copy_continue_prompt.ps1](D:\portfolio-harness.cursor\scripts\copy_continue_prompt.ps1), [generate_next_prompt.ps1](D:\portfolio-harness.cursor\scripts\generate_next_prompt.ps1). |


**Human action:** Confirm Continue is installed and Ollama is running; run the flow and report whether handoff context flows into Continue.

---

## I2: Evaluate Aider

**What AI needs from you:**


| Need                   | Answer (from codebase)                                                                                                                                                                               |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Install path**       | `pip install aider-chat`; run via `aider --model ollama_chat/qwen2.5-coder`.                                                                                                                         |
| **Ollama config**      | `ollama pull qwen2.5-coder` (or equivalent). Plan specifies `ollama_chat/qwen2.5-coder`.                                                                                                             |
| **Handoff paste flow** | 1) Run `generate_next_prompt.ps1`; 2) Use content of `continue_prompt.txt` or `next_prompt.txt`; 3) Run `aider --model ollama_chat/qwen2.5-coder`; 4) Paste handoff-derived prompt as first message. |


**Human action:** Same as I1 — confirm install, run flow, report whether Aider uses handoff context.

---

## H5: Agent Korean-language switch

**What AI needs from you:** **Confirmation that it's fixed or still happening.**

**Current state (from codebase):**

- [known-issues.md](D:\portfolio-harness.cursor\state\known-issues.md) §Agent behavior: **Status: open.** Symptom: Agent switches to Korean on short prompts (e.g. "do it") in English context.
- [.cursorrules](D:\portfolio-harness.cursorrules) line 217: "Respond in English unless the user explicitly requests another language (e.g. Korean)." — No "Always respond in Korean" rule found.
- Mitigation noted: Language preference added to AGENTS.md, preferences.json, .cursorrules per "Korean Output Audit plan."

**Human action:** Try a short prompt like "do it" in a new chat and report: (a) Still getting Korean? or (b) Fixed (English response)?

---

## R1–R3: obsidian-vault MCP, critic follow-up

**What AI needs from you:**

### R1: Whether MCP is running

- **Check:** Cursor Settings → MCP; confirm obsidian-vault shows running or has errors.
- **Note:** obsidian-vault tools (`session_save`, `apply_patch`, `vault_search`, etc.) are not in the current agent tool list, so the MCP may not be loaded in this session. Human must verify in Cursor Settings.

### R2: Re-test foam-pkm prompt 1

- **Prompt:** "Create a note in the Obsidian vault about Bitcoin-Chaos mapping, linking to CHAOS_BITCOIN_MAPPING"
- **Expected:** Agent uses obsidian-vault `apply_patch` (not `Write`).
- **Procedure:** [TEST_PROMPTS.md](D:\portfolio-harness.cursor\skills\foam-pkm\TEST_PROMPTS.md) #1 — new chat, paste prompt, verify behavior.

### R3: Which critic fixes to apply

R3 references "Critic report 2026-03-11" with these items:

1. **known-issues obsidian-vault entry** — Add/update entry for obsidian-vault status or issues.
2. **SKILL.md guardrail** — Add guardrail to [foam-pkm SKILL.md](D:\portfolio-harness.cursor\skills\foam-pkm\SKILL.md) (e.g. prefer `apply_patch` over `Write` for Obsidian).
3. **AI_TASK_EVALS** — Add or update AI task evals for foam-pkm / obsidian-vault flows.
4. **TEST_PROMPTS procedure** — Already exists in [TEST_PROMPTS.md](D:\portfolio-harness.cursor\skills\foam-pkm\TEST_PROMPTS.md); ensure it's followed.
5. **test_mcp_and_audit skip** — Add skip for obsidian-vault when MCP unavailable (e.g. in `test_mcp_and_audit.py`).

**Human action:** (1) Report obsidian-vault MCP status from Cursor Settings. (2) Choose which R3 fixes to apply (all, or subset).

---

## G8: MCP OAuth 2.1 + Streamable HTTP

**What AI needs from you:** **Priority and scope (tracking vs implementation).**

**Current state (from [pending_tasks.md](D:\portfolio-harness.cursor\state\pending_tasks.md)):**

- **Scope:** Track for future auth and deployment. Streamable HTTP uses OAuth 2.1 (Auth Code + PKCE) for remote MCP; enables secure SaaS MCP.
- **References:** [MCP Authorization](https://modelcontextprotocol.io/docs/tutorials/security/authorization), [LavX News](https://news.lavx.hu/article/authentication-and-authorization-in-model-context-protocol-oauth-2-1-and-the-streamable-http-transport)

**Options:**

- **Tracking only:** Keep as pending; add to a "future MCP auth" doc or roadmap. No code changes.
- **Implementation:** Design and implement OAuth 2.1 + Streamable HTTP for a specific MCP (e.g. SCP SaaS, credential-vault remote). Higher effort.

**Human action:** Decide: (a) Tracking only, or (b) Implementation — and if (b), which MCP/server and timeline.

---

## Summary


| Task | Human action                                                             |
| ---- | ------------------------------------------------------------------------ |
| I1   | Confirm Continue install + Ollama; run handoff paste flow; report result |
| I2   | Same for Aider                                                           |
| H5   | Test "do it" in new chat; report fixed vs still Korean                   |
| R1   | Check Cursor Settings → MCP for obsidian-vault status                    |
| R2   | Re-test foam-pkm prompt 1; verify `apply_patch`                          |
| R3   | Choose which critic fixes to apply (1–5)                                 |
| G8   | Choose tracking vs implementation; if implementation, scope and MCP      |


