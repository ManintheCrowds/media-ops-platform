# CaptionPipeline portfolio export kit

Use this kit to showcase CaptionPipeline in a developer portfolio with ready-made architecture sources, metrics, and screenshot guidance.

## What to Say (Problem → Solution → Impact)

- **Problem:** Large video libraries were hard to search and lacked consistent captions; manual captioning did not scale across multiple production feeds.
- **Solution:** CaptionPipeline automates ingest → WhisperX transcription → broadcast SCC-format captions → publication to VOD/search with monitoring and alerting.
- **Impact (Dec 2025 snapshot):** 256+ caption files, 330+ content hours, ~85 min average processing time, 93.5%+ success rate, &lt;1% errors, 100% uptime across 9 production feeds; peaks of 121 files/day (18.29 avg).

## Assets to Include

### 1. Architecture Diagrams (Mermaid Sources)

- **High-level flow:** `architecture-high-level.mmd` (input → processing → outputs)
- **Detailed system architecture:** `architecture-detailed.mmd` (sources, core services, pipeline, outputs)

#### Export to PNG/SVG

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i architecture-high-level.mmd -o ../../portfolio/assets/diagrams/architecture-high-level.png --backgroundColor white
mmdc -i architecture-detailed.mmd -o ../../portfolio/assets/diagrams/architecture-detailed.png --backgroundColor white
```

### 2. Monitoring/Reliability Screenshot

- Capture Grafana when the stack is running (uptime and error-rate panels)
- Save as `portfolio/assets/diagrams/grafana-reliability.png`

### 3. Talking Points

- **Stack:** Flask + FastAPI APIs; Celery + Redis; PostgreSQL; WhisperX; SCC-format captions; Prometheus + Grafana; VOD/broadcast integrations
- **Workflow:** Detect videos across storage mounts → transcribe (WhisperX) → generate captions → quality check → publish → archive → monitor health
- **Operational scope:** Nine production feeds, 100% uptime since deployment (portfolio snapshot), error rate &lt;1%
- **Throughput:** 18.29 files/day avg; 121 files/day peak; 330+ hours processed

## Machine-readable metrics

**SSOT for agents and profile copy:** [`metrics.json`](metrics.json) — CaptionPipeline (Dec 2025 snapshot), SCP promptfoo probes, OpenHarness autoresearch Tier B. Prefer this file over re-parsing markdown.

**Refresh (validate schema + bump `generated_at`):**

```powershell
# From media-ops-platform repo root
.\docs\portfolio\refresh_metrics.ps1
.\docs\portfolio\refresh_metrics.ps1 -DryRun
```

Live homelab/Grafana export hooks are stubbed for **PF-REPO-8** (`-FromGrafanaJson`). Quarterly ritual: MiscRepos `pending_tasks` **PF-PR-16**.

## Related docs

- [metrics.json](metrics.json) · [refresh_metrics.ps1](refresh_metrics.ps1)
- [PORTFOLIO_README_TEMPLATE.md](PORTFOLIO_README_TEMPLATE.md)
- [PUBLIC_REPO_AUDIT_CHECKLIST.md](PUBLIC_REPO_AUDIT_CHECKLIST.md)
- [NAMING_BRAINSTORM.md](NAMING_BRAINSTORM.md)
