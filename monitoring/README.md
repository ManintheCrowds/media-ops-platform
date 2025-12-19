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

### Alertmanager

Alert routing and notifications.

**Configuration:** `monitoring/alertmanager/alertmanager.yml`

**Notification Channels:**
- Email (primary)
- Webhooks
- Escalation policies

## Alert Rules

Located in `prometheus/alert_rules.yml`:

- Service availability alerts
- Resource usage alerts (CPU, memory, disk)
- Security alerts
- Pi device alerts
- Database performance alerts
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

## Configuration

### Prometheus

Edit `prometheus/prometheus.yml` to:
- Add scrape targets
- Configure retention
- Set alert rules

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

## Best Practices

1. **Set appropriate thresholds** for alerts
2. **Configure escalation** for critical alerts
3. **Review dashboards** regularly
4. **Test alerting** periodically
5. **Document custom metrics**

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
