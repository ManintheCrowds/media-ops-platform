# Monitoring and Alerting Guide

## Overview

This guide covers the monitoring stack including Prometheus, Grafana, Alertmanager, and exporters.

## Components

### Prometheus

Metrics collection and storage.

**Configuration:** `prometheus/prometheus.yml`

**Exporters:**
- Node Exporter - System metrics
- cAdvisor - Container metrics
- PostgreSQL Exporter - Database metrics
- Cursor Exporter - Cursor IDE connection metrics

### Grafana

Visualization and dashboards.

**Access:** 
- External (from host): http://localhost:3001
- Internal (Docker network): http://grafana:3000

**Default credentials:**
- Username: admin
- Password: admin (change on first login)

**Dashboards:**
- Platform Overview
- Service Health Dashboard
- Service-specific dashboards
- Infrastructure dashboards
- Cursor Connection Monitoring
- **DAGGR Workflow Metrics** – workflow runs and duration by project (WatchTower, campaign_kb)

### Alertmanager

Alert routing and notifications.

**Configuration:** `monitoring/alertmanager/alertmanager.yml`

**Notification Channels:**
- Email (primary)
- Webhooks
- Escalation policies

## Service Coverage

The monitoring stack monitors all platform services:

### Core Platform Services
- **Platform API** (Port 8000) - Health, request rates, response times
- **PostgreSQL** (Port 5432) - Connection pool, query performance, replication lag

### Security & Monitoring Services
- **Security Service** (Port 8001) - Threat detection, firewall events, IDS alerts
- **Home Cyber Risk** (Port 8002) - Breach check frequency, alert delivery, risk scores
- **Monitoring Stack** - Self-monitoring (Prometheus, Grafana, Alertmanager)

### Application Services
- **Job Automation Service** (Port 8004) - Job search frequency, match scores, application tracking
- **Education Service** (Port 8003) - Content requests, Pi sync status, progress tracking
- **Pi Client** - Device connectivity, sync status, offline mode

### Infrastructure Services
- **Seafile** (Port 8001) - File operations, storage usage, sync status
- **Jellyfin** (Port 8096) - Media streaming, library size, user activity
- **Gitea** (Port 3000) - Repository operations, webhook delivery, user activity

### DAGGR and App Pipeline (WatchTower, campaign_kb, harness, workflow_ui)

**Projects monitored:** WatchTower_main (Flask, port 5000), campaign_kb (FastAPI, port 8000), harness (portfolio-harness Gradio, metrics port 9091), workflow_ui (Flask, port 5050). All expose `/metrics` with DAGGR workflow metrics (or basic app metrics).

**Shared label convention:** All DAGGR metrics use:
- `project` = `watchtower_main` | `campaign_kb` | `harness` | `workflow_ui`
- `workflow` = workflow name (e.g. simple, rag, ingest, scp, blue_hat_privacy)
- `status` = `success` | `failure`

**Metric names:** `daggr_workflow_runs_total` (Counter), `daggr_workflow_duration_seconds` (Histogram), `daggr_workflow_errors_total` (Counter). Grafana can filter with `project=~"watchtower_main|campaign_kb|harness|workflow_ui"`.

**How DAGGR integrates:** Workflow runs in Gradio/Daggr POST to WatchTower `POST /api/daggr/run-complete`; WatchTower records to Prometheus. campaign_kb can also POST run-complete with `project=campaign_kb` and exposes its own `/metrics` for direct scrape. **Harness** (portfolio-harness) runs SCP and blue_hat workflows; metrics are served on port 9091 (separate from Gradio UI on 7860). **workflow_ui** exposes `/metrics` for scrape (basic app metrics).

**How to add a new project:** Add a scrape job in `prometheus/prometheus.yml` with a unique `job_name` and label `project: '<name>'`; ensure the app exposes `/metrics` with the same metric names and label scheme.

**How to verify:** Start WatchTower (and optionally campaign_kb, harness SCP Gradio, workflow_ui), run a DAGGR workflow, then in Grafana open the "DAGGR Workflow Metrics" dashboard and confirm `daggr_workflow_runs_total` or duration series appear. Scrape targets use `host.docker.internal` for host-run apps; adjust if running in Docker.

### Service-Specific Dashboards

Each service has dedicated dashboards:
- Platform API Dashboard - Request metrics, error rates, response times
- Security Service Dashboard - Threat events, firewall rules, IDS alerts
- Home Cyber Risk Dashboard - Breach statistics, risk scores, alert delivery
- Job Automation Dashboard - Search frequency, match scores, applications
- Education Service Dashboard - Content access, Pi sync, progress tracking
- Database Dashboard - Query performance, connection pool, replication
- Infrastructure Dashboard - System resources, container health, network

### Alert Rules Per Service

Located in `prometheus/alert_rules.yml`:

**Platform API:**
- Service availability alerts
- High error rate alerts
- Slow response time alerts

**Security Service:**
- Threat detection alerts
- Firewall rule changes
- IDS signature matches

**Home Cyber Risk:**
- Breach detection alerts
- High-risk breach alerts
- Alert delivery failures

**Job Automation:**
- Search failures
- High match score jobs
- Application tracking issues

**Education Service:**
- Pi sync failures
- Content access errors
- Progress tracking issues

**Infrastructure:**
- Resource usage alerts (CPU, memory, disk)
- Database performance alerts
- Pi device alerts
- Cursor connection alerts

## Setup

### Using Ansible

```bash
ansible-playbook ansible/playbooks/monitoring-setup.yml
```

### Manual Setup

1. **Start Prometheus:**
   ```bash
   docker compose up -d prometheus
   ```

2. **Start Grafana:**
   ```bash
   docker compose up -d grafana
   ```

3. **Start Alertmanager:**
   ```bash
   docker compose up -d alertmanager
   ```

## Integration

### How Services Expose Metrics

All services expose Prometheus metrics at `/metrics` endpoint:

**FastAPI Services:**
- Use `prometheus-fastapi-instrumentator` middleware
- Automatically exposes request metrics
- Custom metrics via Prometheus client

**Example Service Metrics:**
```python
from prometheus_client import Counter, Histogram

requests_total = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
```

### Prometheus Scrape Configuration

Services are configured in `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'platform-api'
    static_configs:
      - targets: ['platform-api:8000']
  
  - job_name: 'security-service'
    static_configs:
      - targets: ['security-service:8001']
  
  - job_name: 'education-service'
    static_configs:
      - targets: ['education-service:8003']
  
  - job_name: 'job-automation-service'
    static_configs:
      - targets: ['job-automation-service:8004']
```

### Grafana Data Source Setup

Data sources are automatically configured from:
- `monitoring/grafana/provisioning/datasources/prometheus.yml`

All services use the same Prometheus data source:
- Name: Prometheus
- URL: http://prometheus:9090
- Access: Server (default)

## Configuration

### Prometheus

Edit `prometheus/prometheus.yml` to:
- Add scrape targets for new services
- Configure retention policies
- Set alert rules
- Configure service discovery (if using)

### Grafana

Dashboards are automatically provisioned from:
- `monitoring/grafana/dashboards/`

Data sources configured in:
- `monitoring/grafana/provisioning/datasources/`

### Alertmanager

Edit `monitoring/alertmanager/alertmanager.yml` to:
- Configure SMTP settings
- Set notification routes
- Define receivers

## Alert Configuration

### Email Notifications

Configure in `monitoring/alertmanager/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'
```

### Alert Routing

Alerts are routed based on severity:
- Critical → Critical receiver
- Warning → Warning receiver
- Default → Default receiver

## Dashboards

### Platform Overview

Shows:
- Service status
- CPU usage
- Memory usage
- Request rates

### Service Dashboards

Individual dashboards for:
- Platform API
- Database
- Monitoring stack
- Cursor IDE connections

## Cursor Monitoring

Comprehensive monitoring for Cursor IDE connections including:
- Connection status and metrics
- Latency and packet loss monitoring
- DNS resolution tracking
- Disconnect analysis
- Network path analysis

**Documentation:**
- [Cursor Monitoring Guide](../docs/monitoring/CURSOR_MONITORING.md)
- [Cursor Optimization Guide](../docs/monitoring/CURSOR_OPTIMIZATION.md)
- [Cursor Network Endpoints](../docs/CURSOR_NETWORK_ENDPOINTS.md)

**Scripts:**
- `scripts/monitoring/cursor-process-monitor.ps1` - Process monitoring
- `scripts/monitoring/cursor-connection-quality.ps1` - Quality monitoring
- `scripts/monitoring/cursor-endpoint-discovery.ps1` - Endpoint discovery
- `scripts/monitoring/cursor-connection-test.ps1` - Connection testing
- `scripts/monitoring/cursor-disconnect-analysis.ps1` - Disconnect analysis
- `scripts/monitoring/cursor-health-report.ps1` - Health reporting

**Exporter:**
- `monitoring/cursor-exporter/cursor_exporter.py` - Prometheus exporter

## Quick Wins & Expansion

**Templates and Guides:**
- [Monitoring Expansion Guide](../docs/monitoring/MONITORING_EXPANSION_GUIDE.md) - Step-by-step guide for adding new monitoring
- [Alert Notification Setup](../docs/monitoring/ALERT_NOTIFICATION_SETUP.md) - Configure email and Slack alerts
- `scripts/monitoring/app-monitor-template.ps1` - Reusable template for monitoring any application
- `scripts/monitoring/test-alert-notification.ps1` - Test alert delivery

**Dashboards:**
- Service Health Dashboard - Monitor core services (Platform API, PostgreSQL, Prometheus, Grafana)
- Import: `monitoring/grafana/dashboards/service-health.json`

## Related Services

- [Platform API](../README.md) - Main integration layer
- [Security Service](../security-service/README.md) - Security monitoring
- [Home Cyber Risk](../home-cyber-risk/README.md) - Breach monitoring
- [Education Service](../education-service/README.md) - Educational platform
- [Job Automation Service](../job-automation-service/README.md) - Job search automation

## Best Practices

1. **Set appropriate thresholds** for alerts
2. **Configure escalation** for critical alerts
3. **Review dashboards** regularly
4. **Test alerting** periodically
5. **Document custom metrics**
6. **Monitor service dependencies** (database, Redis, etc.)
7. **Track service-specific SLAs** (response times, availability)

## Troubleshooting

### Prometheus not scraping

- Check target configuration
- Verify network connectivity
- Check exporter status

### Alerts not firing

- Verify alert rules syntax
- Check Prometheus evaluation
- Verify Alertmanager configuration

### Grafana dashboards not loading

- Check data source configuration
- Verify Prometheus connectivity
- Check dashboard JSON syntax
