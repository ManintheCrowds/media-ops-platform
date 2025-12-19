# Cursor Monitoring Quick Start Guide

## Status Check

### Verify Monitoring Components

```powershell
# Check if exporter is running
Invoke-WebRequest -Uri "http://localhost:9101/health" -UseBasicParsing

# Check if metrics are available
Invoke-WebRequest -Uri "http://localhost:9101/metrics" -UseBasicParsing

# Check if monitoring scripts are running
Get-Process powershell | Where-Object { $_.CommandLine -like '*cursor*' }
```

## Starting the Monitoring System

### Option 1: Use the Startup Script (Recommended)

```powershell
.\scripts\monitoring\start-cursor-monitoring.ps1
```

This script will:
- Create necessary directories
- Start all monitoring scripts
- Start the Prometheus exporter
- Display status information

### Option 2: Manual Start

#### 1. Start Process Monitor

```powershell
.\scripts\monitoring\cursor-process-monitor.ps1 -Interval 5 -OutputDir "cursor-metrics"
```

#### 2. Start Connection Quality Monitor

```powershell
.\scripts\monitoring\cursor-connection-quality.ps1 -Endpoints @("api.cursor.com") -Interval 30 -OutputDir "cursor-quality-metrics"
```

#### 3. Start Event Log Monitor (Optional)

```powershell
.\scripts\monitoring\cursor-event-log-monitor.ps1 -Interval 60 -OutputDir "cursor-event-logs"
```

#### 4. Start Prometheus Exporter

```powershell
python monitoring\cursor-exporter\cursor_exporter.py --port 9101 --interval 30
```

## Grafana Dashboard Import

### Option 1: Automatic Provisioning (If Grafana is Configured)

The dashboard is located at:
```
monitoring/grafana/dashboards/cursor-connections.json
```

If Grafana is configured with dashboard provisioning, it will automatically import this dashboard.

### Option 2: Manual Import via Web UI

1. Open Grafana: http://localhost:3001
   - **Note**: Port 3001 is for external access from your host machine
   - Internal Docker services use `http://grafana:3000` (container port)
2. Navigate to **Dashboards** → **Import**
3. Click **Upload JSON file**
4. Select: `monitoring/grafana/dashboards/cursor-connections.json`
5. Select your Prometheus data source
6. Click **Import**

### Option 3: Import via API

```powershell
# Get Grafana API key from Grafana UI (Configuration → API Keys)
$apiKey = "YOUR_API_KEY"
$grafanaUrl = "http://localhost:3001"
$dashboardJson = Get-Content "monitoring\grafana\dashboards\cursor-connections.json" -Raw

$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

$body = @{
    dashboard = ($dashboardJson | ConvertFrom-Json).dashboard
    overwrite = $true
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "$grafanaUrl/api/dashboards/db" -Method Post -Headers $headers -Body $body
```

## Verify Everything is Working

### 1. Check Exporter

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:9101/health" -UseBasicParsing

# Should return: {"status": "healthy"}
```

### 2. Check Metrics

```powershell
# View metrics
Invoke-WebRequest -Uri "http://localhost:9101/metrics" -UseBasicParsing | Select-Object -ExpandProperty Content
```

You should see metrics like:
- `cursor_connections_active`
- `cursor_latency_seconds`
- `cursor_packet_loss_ratio`
- etc.

### 3. Check Prometheus

1. Open Prometheus: http://localhost:9090
2. Go to **Status** → **Targets**
3. Verify `cursor-exporter` target is **UP**

### 4. Check Grafana Dashboard

1. Open Grafana: http://localhost:3001
2. Navigate to **Dashboards** → **Cursor Connection Monitoring**
3. Verify panels are showing data

## Troubleshooting

### Exporter Not Starting

```powershell
# Check if port is in use
Get-NetTCPConnection -LocalPort 9101 -ErrorAction SilentlyContinue

# Check Python installation
python --version

# Install dependencies
pip install -r monitoring\cursor-exporter\requirements.txt
```

### No Metrics Appearing

1. Verify Cursor IDE is running
2. Check monitoring script output directories exist
3. Verify scripts are collecting data (check JSON files in output directories)
4. Check exporter logs for errors

### Dashboard Not Loading

1. Verify Prometheus data source is configured in Grafana
2. Check Prometheus is scraping the exporter (Status → Targets)
3. Verify metrics exist in Prometheus (query: `cursor_connections_active`)
4. Check dashboard JSON is valid

### Prometheus Not Scraping

1. Check `prometheus/prometheus.yml` has cursor-exporter job
2. Verify exporter is accessible from Prometheus container
3. For Docker: Use `host.docker.internal:9101` as target
4. Check Prometheus logs for scrape errors

## Next Steps

1. **Establish Baseline**: Let monitoring run for 1-2 weeks to establish normal patterns
2. **Configure Alerts**: Review and adjust alert thresholds in `prometheus/alert_rules.yml`
3. **Optimize**: Follow the optimization guide: `docs/monitoring/CURSOR_OPTIMIZATION.md`
4. **Regular Review**: Generate weekly health reports using `cursor-health-report.ps1`

## Useful Commands

```powershell
# Generate health report
.\scripts\monitoring\cursor-health-report.ps1 -Days 7

# Run connection test
.\scripts\monitoring\cursor-connection-test.ps1 -Endpoints @("api.cursor.com")

# Analyze disconnects
.\scripts\monitoring\cursor-disconnect-analysis.ps1 -LogDirectory "cursor-metrics"

# Discover endpoints
.\scripts\monitoring\cursor-endpoint-discovery.ps1 -Duration 300
```

## Expanding Monitoring

Once Cursor monitoring is working, you can easily add monitoring for other applications:

**Quick Start:**
```powershell
# Monitor any application using the template
.\scripts\monitoring\app-monitor-template.ps1 -AppName "VSCode" -ProcessName "Code" -Interval 5
```

**Full Integration:**
See [Monitoring Expansion Guide](MONITORING_EXPANSION_GUIDE.md) for complete instructions on:
- Creating exporters
- Adding to Prometheus
- Creating dashboards
- Setting up alerts

## See Also

- [Full Monitoring Guide](CURSOR_MONITORING.md)
- [Optimization Guide](CURSOR_OPTIMIZATION.md)
- [Network Endpoints](../CURSOR_NETWORK_ENDPOINTS.md)
- [Monitoring Expansion Guide](MONITORING_EXPANSION_GUIDE.md) - Add monitoring for other applications
- [Alert Notification Setup](ALERT_NOTIFICATION_SETUP.md) - Configure email/Slack alerts
