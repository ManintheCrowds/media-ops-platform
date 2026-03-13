---
name: OpenClaw Hardware Section Implementation
overview: Implement ST1.1–ST1.6 by extending local-proto/docs/OPENCLAW.md with a Hardware section, using the task decomposition and research synthesis from the existing plan.
todos: []
isProject: false
---

# OpenClaw Hardware Section Implementation

## Target

Extend [local-proto/docs/OPENCLAW.md](D:\portfolio-harness\local-proto\docs\OPENCLAW.md) with a **Hardware** section. Place it after "Local backends" (line 33) and before "Google Workspace (gws)" (line 35). This keeps hardware guidance adjacent to local inference context.

**Reference:** [2026-03-13-openclaw-hardware-task-decomposition.md](D:\portfolio-harness\docs\plans\2026-03-13-openclaw-hardware-task-decomposition.md)

---

## Implementation Steps

### ST1.1 — Add Hardware section outline

Insert a new `## Hardware` section with placeholder subsections:

```markdown
## Hardware

Recommendations for running OpenClaw, especially for non-technical users. For developer topology (Jetson, GTX 1060), see [REQUIREMENTS.md](../REQUIREMENTS.md) §4 and [HARDWARE.md](HARDWARE.md).

### Minimum specs (cloud API)

### Mac Mini (recommended for Mac users)

### Alternatives (Mac Minis selling out)

### Non-technical / plug-and-run

### Cloud vs local trade-offs

### External resources
```

**AC:** All six subsections present; cross-ref to REQUIREMENTS §4 and HARDWARE.md.

---

### ST1.2 — Fill Mac Mini tier table

Replace the "Mac Mini" placeholder with a table and short prose:


| Config  | RAM      | Price         | Local model size | Use case                 |
| ------- | -------- | ------------- | ---------------- | ------------------------ |
| M4 base | 16 GB    | ~$599         | 7–8B             | Cloud API or light local |
| M4 Pro  | 24 GB    | ~$1,399       | 14B              | Mid-tier local           |
| M4 Pro  | 48–64 GB | ~$1,599–2,000 | 30B+             | Heavy local inference    |


- Add 1–2 sentences on unified memory, Neural Engine, power (~15W idle).
- Note: 16 GB sufficient for cloud-only; 48 GB+ for 30B local models.

---

### ST1.3 — Fill alternatives section

Replace the "Alternatives" placeholder with:

- **Refurb M1/M2 Mac Minis:** 30–40% cheaper; 7–8B local viable.
- **Cloud VPS:** Hetzner (€3.29/mo), DigitalOcean ($12/mo), AWS t3.small (~$15/mo). Use for cloud API; Windows requires WSL2.
- **RunPod GPU:** RTX 4090, A100, H100 by the hour; vLLM templates.
- **Windows:** WSL2 required; no native Windows support.
- **Linux:** Ubuntu 20.04+, Debian 11+; works well for VPS and Docker.

---

### ST1.4 — Fill non-technical path

Replace the "Non-technical" placeholder with:

- **[getopenclaw.ai](https://getopenclaw.ai):** Cloud trial, no server; connect channels in under 60 seconds. Data goes through their servers.
- **[getclawkit.com](https://getclawkit.com):** Diagnostics and config wizard; `npx clawkit-doctor@latest`; troubleshooting for common errors.
- **GUI installer:** [openclaw.ai/download](https://openclaw.ai/download) — double-click install, create account, connect WhatsApp/Telegram/Discord. 4 GB RAM, Mac/Windows 10+/Linux.

---

### ST1.5 — Fill cloud vs local trade-offs

Replace the "Cloud vs local" placeholder with a short table or bullets:


| Factor   | Cloud API                      | Local (Ollama)                                  |
| -------- | ------------------------------ | ----------------------------------------------- |
| Privacy  | Data on third-party servers    | Data stays on your machine                      |
| Offline  | No                             | Yes                                             |
| Setup    | Minimal                        | Requires 16 GB+ RAM for 7B models               |
| Best for | Low/medium volume, best models | High volume, privacy-critical, stable workloads |


---

### ST1.6 — Add external links and verify

- Add to the existing **Links** section at bottom:
  - [getopenclaw.ai](https://getopenclaw.ai) — cloud trial, beginner setup
  - [getclawkit.com](https://getclawkit.com) — diagnostics, config wizard
  - [docs.openclaw.ai](https://docs.openclaw.ai) — official docs
- Verify: All internal links (REQUIREMENTS.md, HARDWARE.md) resolve. All external URLs use https.

---

## Post-Implementation

1. **Mark ST1 done** in [.cursor/state/pending_tasks.md](D:\portfolio-harness.cursor\state\pending_tasks.md): change `ST1 | pending` to `ST1 | done`.
2. **Optional:** Remove or update the "parallel-cli" note in [2026-03-13-openclaw-hardware-task-decomposition.md](D:\portfolio-harness\docs\plans\2026-03-13-openclaw-hardware-task-decomposition.md) §1.1 (user dropped parallel-cli).

---

## File Changes Summary


| File                                                                                 | Change                                                   |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| [local-proto/docs/OPENCLAW.md](D:\portfolio-harness\local-proto\docs\OPENCLAW.md)    | Add Hardware section (~60–80 lines) after Local backends |
| [.cursor/state/pending_tasks.md](D:\portfolio-harness.cursor\state\pending_tasks.md) | ST1 status: pending → done                               |


