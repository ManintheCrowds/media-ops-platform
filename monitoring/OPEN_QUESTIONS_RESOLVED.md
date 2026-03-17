# Grafana DAGGR Monitoring — Open Questions Resolved

Resolutions from the Grafana + DAGGR monitoring pipeline project (see `.cursor/docs/GRAFANA_DAGGR_MONITORING_PROMPT.md` in portfolio-harness).

---

## 1. First-class workflow list

| Project | First-class workflows | Notes |
|---------|----------------------|-------|
| **WatchTower** | simple, rag, ingest, error-analysis, metrics | DAGGR workflows; emit `daggr_workflow_runs_total`, `daggr_workflow_duration_seconds` |
| **Campaign_kb** | search, ingest, merge | DAGGR workflows; same metric names |
| **Harness** | scp, blue_hat_privacy, blue_hat_* | SCP and blue-hat workflows; metrics on port 9091 |
| **workflow_ui** | (none) | UI only; exposes basic app metrics at `/metrics` |
| **Moltbook watchtower** | (none) | Passive monitoring agent; no DAGGR workflows; no `/metrics` yet |

**Convention:** Add new workflows to this list when they are explicitly added to the pipeline. Document in each app repo.

---

## 2. Signal vs email

- **Primary:** Email via Alertmanager `smtp_*` config. Configure `monitoring/alertmanager/alertmanager.yml` with real SMTP credentials.
- **Signal:** Not configured by default. To add Signal:
  1. Use a Signal relay (e.g. [signal-cli-rest](https://github.com/bbernhard/signal-cli-rest), [ntfy](https://ntfy.sh), or similar) that accepts webhooks.
  2. Add a `webhook_configs` entry in Alertmanager receivers pointing to the relay URL.
  3. Document the relay setup in this README or a separate runbook.

**Current state:** Email is the primary channel; webhook for critical alerts goes to `security-service:8001/api/alerts`. Signal can be added later via webhook relay.

---

## 3. Moltbook watchtower metrics

- **Resolution:** Moltbook watchtower does **not** expose a `/metrics` endpoint. It is a passive monitoring agent (reads from Moltbook API, runs local analyzers, produces reports).
- **Monitoring today:** No direct Prometheus scrape. If Moltbook adds a Flask/FastAPI app with `/metrics` in the future, add a scrape config in `prometheus/prometheus.yml` with `project: moltbook_watchtower`.
- **Placeholder:** A commented scrape config exists in `prometheus/prometheus.yml` for when Moltbook adds metrics.

---

## 4. Shared label convention

All DAGGR and app metrics use:

- `project` = `watchtower_main` | `campaign_kb` | `harness` | `workflow_ui` | `moltbook_watchtower` (when added)
- `workflow` = workflow name (e.g. simple, rag, ingest, scp)
- `status` = `success` | `failure`
- `env` = `dev` | `prod` (optional; add via relabel if needed)

**Grafana filter example:** `project=~"watchtower_main|campaign_kb|harness|workflow_ui"`
