# Archivist Portfolio Export Kit

Use this kit to showcase Archivist in a developer portfolio with ready-made architecture sources, metrics, and screenshot guidance.

## What to Say (Problem → Solution → Impact)

- **Problem:** Government meeting videos were hard to search and inaccessible for citizens with hearing needs; manual captioning didn't scale across nine cities.
- **Solution:** Archivist automates ingest → WhisperX transcription → SCC caption generation → publication to VOD/search with monitoring and alerting.
- **Impact (Dec 2025 snapshot):** 256+ caption files, 330+ content hours, ~85 min average processing time, 93.5%+ success rate, <1% errors, 100% uptime, serving 9 cities; peaks of 121 files/day (18.29 avg).

## Assets to Include

### 1. Architecture Diagrams (Mermaid Sources)

- **High-level flow:** `architecture-high-level.mmd` (input → processing → outputs)
- **Detailed system architecture:** `architecture-detailed.mmd` (sources, core services, pipeline, outputs)

#### Export to PNG/SVG

Export diagrams locally with Mermaid CLI:

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i architecture-high-level.mmd -o ../../portfolio/assets/diagrams/architecture-high-level.png --backgroundColor white
mmdc -i architecture-detailed.mmd -o ../../portfolio/assets/diagrams/architecture-detailed.png --backgroundColor white
```

> Note: Automatic export may be blocked in some environments by upstream registry/HTTP 403 restrictions. Run the commands above in a network-allowed environment.

### 2. Monitoring/Reliability Screenshot

- Capture Grafana at `http://localhost:9092` once the stack is running (e.g., Cities dashboard or home dashboard showing uptime and error rate)
- Save as `portfolio/assets/diagrams/grafana-reliability.png` (capture from a live instance)

### 3. Talking Points for Portfolio Page

- **Stack:** Flask + FastAPI APIs; Celery + Redis; PostgreSQL; WhisperX; SCC captioning; Prometheus + Grafana; Cablecast/VIOLITE/HELO integrations
- **Workflow:** Detect videos across 9 storage mounts → transcribe (WhisperX) → generate SCC → quality check → publish → archive → monitor health
- **Operational scope:** Nine municipalities served, 100% uptime since deployment, error rate <1%
- **Throughput highlights:** 18.29 files/day avg; 121 files/day peak; 330+ hours processed

## How to Use

- Embed the exported PNG/SVG diagrams on your portfolio site alongside the metrics above
- Mention the Grafana reliability screenshot to demonstrate observability and uptime focus
- Link back to the repository README sections for deeper context on architecture and performance

## For Other Projects- **[PORTFOLIO_README_TEMPLATE.md](PORTFOLIO_README_TEMPLATE.md)** — Reusable README structure (hero, problem/solution/impact, features, tech stack, quick start, docs, testing, license) and a portfolio-readiness checklist for any repo.
- **[PUBLIC_REPO_AUDIT_CHECKLIST.md](PUBLIC_REPO_AUDIT_CHECKLIST.md)** — Single audit checklist (security, hygiene, runnability, consistency, trust, narrative) with concrete commands and file names to run across CodeRepositories, software, Arc_Forge, and moltbook-watchtower.