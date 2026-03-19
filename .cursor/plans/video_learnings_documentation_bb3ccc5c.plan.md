---
name: Video Learnings Documentation
overview: Summarize two YouTube videos (NVIDIA NemoClaw/OpenClaw, ChatGPT Health respiratory failure), document learnings in portfolio-harness, and map audit/improvement opportunities for harness, SCP, and related stacks.
todos: []
isProject: false
---

# Video Learnings: NemoClaw/OpenClaw and ChatGPT Health

## Video Summaries

### Video 1: NVIDIA Jensen Huang — NemoClaw / OpenClaw (kRmZ5zmMS2o)

**Source:** [YouTube](https://www.youtube.com/watch?v=kRmZ5zmMS2o)

**Summary:** At GTC 2026 (March 15), Jensen Huang announced OpenClaw as mandatory infrastructure for every company, calling it "the operating system for personal AI." NVIDIA unveiled **NemoClaw**, an enterprise-grade secure stack built on OpenClaw that addresses security concerns around autonomous agents.

**Key points:**

- **OpenClaw:** Open-source personal AI assistant; 250K+ GitHub stars; created by Peter Steinberger (now at OpenAI)
- **NemoClaw:** Combines OpenClaw + Nemotron models + OpenShell runtime
- **Security features:** Sandboxing (Landlock, seccomp, network namespaces), privacy controls, policy-based guardrails
- **Addresses:** Agents accessing sensitive data, privilege escalation, incidents (mass-deleting emails, going rogue)
- **Deployment:** Cloud, on-premise, RTX PCs, DGX Spark; single-command install
- **Policy:** Declarative YAML for file access, network, and inference; no code changes for policy updates

---

### Video 2: ChatGPT Health — Respiratory Failure (4HeS_C02yAE)

**Source:** [YouTube](https://youtu.be/4HeS_C02yAE)

**Summary:** ChatGPT Health (launched Jan 2026) shows dangerous undertriage in medical emergencies. A Nature Medicine study (60 clinician vignettes, 960 responses) found a **52% undertriage rate** for emergency cases. In respiratory failure scenarios, the system identified the danger in its explanation but still advised patients to "wait" instead of seeking emergency care.

**Key points:**

- **Inverted U-shaped performance:** Worst failures at clinical extremes; adequate on textbook emergencies (stroke, anaphylaxis)
- **Respiratory failure:** Identified danger but advised 24–48 hour appointment vs. ED
- **Extreme case:** Suffocating woman sent to future appointment eight out of ten times—"she would not live to see"
- **Unpredictable crisis response:** Suicide intervention resources appeared inconsistently across self-harm scenarios
- **Research conclusion:** Consumer-scale deployment before prospective validation is risky

---

## Value-Add to Stacks

### Harness


| Insight                           | Application                                                                                                                                                                                                          |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Human-gated autonomy**          | ChatGPT Health shows AI can "identify" but still "advise wrong" — reinforces need for APPROVAL_NEEDED, REQUEST_HUMAN, and escalation gates before high-stakes actions                                                |
| **Inverted U-shaped performance** | Worst at extremes. Add to harness docs: validate agent behavior at edge cases (clinical extremes, rare domains, adversarial inputs).                                                                                 |
| **Policy-as-code**                | NemoClaw uses declarative YAML for policy. Harness already uses org-intent, TOOL_SAFEGUARDS, risk tiers. Consider: explicit policy registry for agent tool access (similar to TOOL_SAFEGUARDS but machine-readable). |


### SCP


| Insight                         | Application                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Sandboxing and isolation**    | NemoClaw/OpenShell adds Landlock, seccomp, network namespaces. SCP focuses on content; no runtime isolation. Consider: document SCP as content-layer guard; add reference to "runtime isolation" as complementary (e.g., OpenShell, Docker) in [scp/docs/REFERENCE.md](D:\scp\docs\REFERENCE.md) or [docs/INTEGRATION.md](D:\scp\docs\INTEGRATION.md). |
| **Policy-based guardrails**     | NemoClaw uses declarative policy for file/network/access. SCP threat registry is pattern-based. Consider: add domain-specific sink policies (e.g., `medical_triage` sink with stricter block rules) if SCP ever expands beyond LLM input.                                                                                                              |
| **"Identify but advise wrong"** | ChatGPT Health pattern: model correctly identified respiratory failure but still advised wait. SCP inspects content; it does not verify downstream agent behavior. Suggestion: add to SCP docs: "SCP does not guarantee downstream agent actions; human gates required for high-stakes decisions."                                                     |


### OpenClaw / local-proto


| Insight                | Application                                                                                                                                                                                                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **NemoClaw readiness** | NemoClaw is an OpenClaw plugin for OpenShell. Add to [OPENCLAW.md](D:\portfolio-harness\local-proto\docs\OPENCLAW.md) or [OPENCLAW_READINESS.md](D:\portfolio-harness\local-proto\docs\OPENCLAW_READINESS.md): "Optional: NemoClaw for enterprise sandboxing; see NVIDIA docs." |
| **Incident history**   | OpenClaw had agents mass-deleting emails and going rogue. Document in SAFETY_CONSTITUTION or SOUL alignment: ensure no destructive actions without explicit approval.                                                                                                           |


---

## Audit / Improvement Opportunities

### Harness audit

1. **Edge-case validation:** Add explicit guidance to [HARNESS_ARCHITECTURE.md](D:\harness\docs\HARNESS_ARCHITECTURE.md) or [HANDOFF_FLOW.md](D:\harness\docs\HANDOFF_FLOW.md): "Validate agent behavior at extremes (rare domains, adversarial inputs)."
2. **Policy registry:** Evaluate whether TOOL_SAFEGUARDS could be expressed as machine-readable JSON/YAML for tool-routing or audit_wrapper.
3. **Human gate before high-stakes:** Ensure TOOL_SAFEGUARDS and .cursorrules explicitly require human approval for any agent action that could cause harm (e.g., medical triage, financial advice).

### SCP audit

1. **Scope boundary:** Add to [REFERENCE.md](D:\scp\docs\REFERENCE.md): "SCP does not guarantee downstream agent behavior; human gates required for high-stakes decisions."
2. **Runtime isolation reference:** Add a "Complementary controls" section in [INTEGRATION.md](D:\scp\docs\INTEGRATION.md) linking to OpenShell/NemoClaw for runtime sandboxing.
3. **Domain-specific sinks:** If SCP expands to domain-specific sinks (e.g., medical), define stricter policies for those sinks.

### Elsewhere

- **frontier-ops-kb:** Add ChatGPT Health as a case study: "AI can identify but advise wrong." Use for seam design and calibration accuracy.
- **AI Principles / AI_DOCUMENTATION_INDEX:** Add "inverted U-shaped performance" as a known failure mode.

---

## Documentation Location

Create a new learnings document in portfolio-harness following the established pattern:

**Path:** `D:\portfolio-harness\docs\learnings\2026-03-18-video-nemoclaw-chatgpt-health.md`

**Structure (similar to [2026-03-14-video-analysis-engrams.md](D:\portfolio-harness\docs\bmi-neuroscience\2026-03-14-video-analysis-engrams.md)):**

- Frontmatter: date, topic, sources (video URLs), purpose
- Video 1 summary
- Video 2 summary
- Stack alignment table (harness, SCP, OpenClaw)
- Audit recommendations
- Other uses (next section)

---

## Other Uses of This Information

1. **Training / eval prompts:** Use ChatGPT Health vignettes as inspiration for agent eval scenarios. Add to [AI_TASK_EVALS.md](D:\portfolio-harness.cursor\docs\AI_TASK_EVALS.md) or similar: "Identify edge cases where agent correctly identifies risk but still advises wrong."
2. **Red-team prompts:** SCP [RED_TEAM_PROMPTS.md](D:\scp\docs\RED_TEAM_PROMPTS.md) — add "reversal" scenarios where content appears benign but agent downstream behavior is harmful (e.g., "This is not medical advice" followed by triage instructions).
3. **Panel / workshop prep:** If you present on AI safety or agent guardrails, cite both: NemoClaw as enterprise response to OpenClaw incidents; ChatGPT Health as consumer-scale deployment risk.
4. **NemoClaw evaluation:** If you run OpenClaw in production, evaluate NemoClaw for sandboxing; document in OPENCLAW_READINESS or a new NEMOCLAW_EVAL.md.
5. **AI Trends ingestion:** Add these video IDs to ai-trends MCP ingestion config if you want them summarized/analyzed in future runs; reference in [AI_TRENDS_MCP.md](D:\portfolio-harness\local-proto\docs\AI_TRENDS_MCP.md).

---

## Implementation Steps (Plan Mode — No Edits Yet)

1. Create `docs/learnings/` in portfolio-harness if it does not exist.
2. Create `docs/learnings/2026-03-18-video-nemoclaw-chatgpt-health.md` with full content.
3. Add optional cross-references:
  - [OPENCLAW.md](D:\portfolio-harness\local-proto\docs\OPENCLAW.md) — link to NemoClaw section in learnings
  - [SCP REFERENCE](D:\scp\docs\REFERENCE.md) — add scope boundary note
  - [SCP INTEGRATION](D:\scp\docs\INTEGRATION.md) — add complementary controls section
4. Decide: promote any learnings to harness if they pass delineation prompt (e.g., "inverted U-shaped performance" as a known failure mode).

