# Cursor Connection Monitoring Guide

## Overview

This guide explains how to set up and use the Cursor connection monitoring system to observe, diagnose, and optimize Cursor IDE connections.

## Architecture

The monitoring system consists of:

1. **Windows Client Monitoring**: PowerShell scripts that monitor Cursor process and network activity
2. **Network Infrastructure Monitoring**: pfSense firewall log analysis and traffic statistics
3. **Prometheus**: Metrics collection and storage
4. **Grafana**: Visualization and dashboards
5. **Alerting**: Prometheus alert rules and Alertmanager

## Setup

### Prerequisites

- Windows machine running Cursor IDE
- pfSense router (optional, for network-level monitoring)
- Prometheus and Grafana deployed
- Python 3.8+ (for exporters)
- PowerShell 5.1+ (for monitoring scripts)

### Step 1: Install Dependencies

```powershell
# Install Python dependencies
pip install prometheus-client
```

### Step 2: Configure pfSense (Optional)

1. Import firewall rules from `config/pfsense/cursor-firewall-rules.xml`
2. Configure syslog forwarding to monitoring server
3. Enable firewall logging for Cursor endpoints

### Step 3: Start Monitoring Scripts

#### Process Monitor

```powershell
# Start process monitoring
.\scripts\monitoring\cursor-process-monitor.ps1 -Interval 5 -ExportPrometheus
```

#### Connection Quality Monitor

```powershell
# Start quality monitoring
.\scripts\monitoring\cursor-connection-quality.ps1 -Endpoints @("api.cursor.com") -Interval 30
```

#### Event Log Monitor

```powershell
# Start event log monitoring (requires admin)
.\scripts\monitoring\cursor-event-log-monitor.ps1 -Interval 60
```

### Step 4: Start Prometheus Exporter

```bash
# Start Cursor exporter
python monitoring/cursor-exporter/cursor_exporter.py --port 9101 --interval 30
```

### Step 5: Configure Prometheus

Prometheus configuration is already updated in `prometheus/prometheus.yml`:

```yaml
- job_name: 'cursor-exporter'
  static_configs:
    - targets: ['host.docker.internal:9101']
  scrape_interval: 30s
```

### Step 6: Import Grafana Dashboard

1. Open Grafana
2. Navigate to **Dashboards > Import**
3. Upload `monitoring/grafana/dashboards/cursor-connections.json`
4. Select Prometheus data source
5. Click **Import**

## Usage

### Discovery Scripts

#### Discover Endpoints

```powershell
# Discover Cursor endpoints
.\scripts\monitoring\cursor-endpoint-discovery.ps1 -Duration 300
```

This will:
- Monitor active Cursor connections
- Identify all domains and IPs
- Export results to JSON and Markdown

#### Analyze Network Path

```powershell
# Analyze network path to Cursor endpoints
.\scripts\monitoring\cursor-path-analysis.ps1 -Endpoints @("api.cursor.com")
```

### Monitoring Scripts

#### Process Monitor

Monitors Cursor process network connections:

```powershell
.\scripts\monitoring\cursor-process-monitor.ps1 `
    -Interval 5 `
    -OutputDir "cursor-metrics" `
    -ExportPrometheus
```

Outputs:
- Active connections count
- Total connections
- Bytes sent/received
- Connection states
- Process resource usage

#### Connection Quality Monitor

Monitors connection quality metrics:

```powershell
.\scripts\monitoring\cursor-connection-quality.ps1 `
    -Endpoints @("api.cursor.com") `
    -Interval 30 `
    -PingCount 5 `
    -ExportPrometheus
```

Outputs:
- Latency measurements
- Packet loss percentage
- DNS resolution time
- HTTP latency

#### Event Log Monitor

Monitors Windows Event Log for network events:

```powershell
.\scripts\monitoring\cursor-event-log-monitor.ps1 `
    -Interval 60 `
    -OutputDir "cursor-event-logs"
```

### Diagnostic Tools

#### Connection Test

Run comprehensive connection tests:

```powershell
.\scripts\monitoring\cursor-connection-test.ps1 `
    -Endpoints @("api.cursor.com") `
    -TestWebSocket `
    -OutputFile "connection-test-report.html"
```

#### Disconnect Analysis

Analyze disconnect patterns:

```powershell
.\scripts\monitoring\cursor-disconnect-analysis.ps1 `
    -LogDirectory "cursor-metrics" `
    -StartDate (Get-Date).AddDays(-7) `
    -EndDate (Get-Date) `
    -OutputFile "disconnect-analysis.html"
```

#### Health Report

Generate health reports:

```powershell
.\scripts\monitoring\cursor-health-report.ps1 `
    -MetricsDirectory "cursor-metrics" `
    -QualityDirectory "cursor-quality-metrics" `
    -Days 1 `
    -OutputFile "health-report.html"
```

## Metrics

### Available Metrics

- `cursor_connections_active` - Current active connections
- `cursor_connections_total` - Total connection attempts
- `cursor_connection_duration_seconds` - Connection duration histogram
- `cursor_bytes_sent_total` - Total bytes sent
- `cursor_bytes_received_total` - Total bytes received
- `cursor_latency_seconds` - Latency to endpoints
- `cursor_packet_loss_ratio` - Packet loss percentage
- `cursor_dns_resolution_seconds` - DNS resolution time
- `cursor_connection_errors_total` - Connection error count
- `cursor_disconnects_total` - Disconnect events

### Prometheus Queries

#### Active Connections

```promql
cursor_connections_active
```

#### Connection Rate

```promql
rate(cursor_connections_total[5m])
```

#### Average Latency

```promql
avg(cursor_latency_seconds)
```

#### Packet Loss

```promql
avg(cursor_packet_loss_ratio) * 100
```

#### Disconnect Rate

```promql
rate(cursor_disconnects_total[5m])
```

## Alerts

### Alert Rules

Alerts are configured in `prometheus/alert_rules.yml`:

- **CursorHighLatency**: Latency > 500ms for 5 minutes
- **CursorHighPacketLoss**: Packet loss > 5% for 5 minutes
- **CursorFrequentDisconnects**: > 3 disconnects per minute
- **CursorDNSResolutionFailure**: DNS resolution failures
- **CursorConnectionTimeout**: Connection timeout errors
- **CursorNoActiveConnections**: No connections for 10 minutes

### Alert Configuration

Configure Alertmanager to send notifications:
- Email
- Slack
- Webhook
- PagerDuty

## Grafana Dashboards

### Connection Overview

- Active connections gauge
- Connection duration over time
- Bytes sent/received rate
- Connection state breakdown
- Top endpoints by traffic

### Connection Quality

- Latency by endpoint
- Packet loss percentage
- DNS resolution time
- Connection success/failure rate
- Error rate by type

### Diagnostics

- Disconnect events timeline
- Correlation with network events
- System resource usage
- Error logs

## Troubleshooting

### Metrics Not Appearing

1. Check exporter is running: `http://localhost:9101/health`
2. Verify Prometheus can scrape: Check Prometheus targets
3. Check script output directories exist
4. Verify PowerShell execution policy

### High Latency

1. Check DNS resolution time
2. Test network path with traceroute
3. Verify firewall rules
4. Check for network congestion

### Frequent Disconnects

1. Review disconnect analysis report
2. Check connection error logs
3. Verify firewall state table limits
4. Check Windows Event Logs

### Prometheus Not Scraping

1. Verify exporter is accessible
2. Check Prometheus configuration
3. Review Prometheus logs
4. Test connectivity: `curl http://localhost:9101/metrics`

## Maintenance

### Regular Tasks

1. **Daily**: Review Grafana dashboards
2. **Weekly**: Generate health reports
3. **Monthly**: Analyze disconnect patterns
4. **Quarterly**: Review and optimize configurations

### Data Retention

- Metrics: 30 days (configurable in Prometheus)
- Logs: 90 days (configurable)
- Reports: Archive monthly

### Backup

Backup configurations:
- Prometheus configuration
- Grafana dashboards
- Alert rules
- Script configurations

## Performance Considerations

### Resource Usage

- Process monitor: ~10-20 MB RAM
- Quality monitor: ~5-10 MB RAM
- Exporter: ~20-30 MB RAM
- Disk usage: ~100 MB/day (metrics)

### Optimization

- Adjust scrape intervals based on needs
- Reduce metric retention if needed
- Use metric relabeling to filter metrics
- Optimize Grafana queries

## Security

### Access Control

- Restrict access to monitoring endpoints
- Use authentication for Grafana
- Secure Prometheus API
- Encrypt sensitive data

### Data Privacy

- Monitor only connection metadata
- Do not log sensitive content
- Follow data retention policies
- Comply with privacy regulations

## See Also

- [Cursor Optimization Guide](CURSOR_OPTIMIZATION.md)
- [Cursor Network Endpoints](../CURSOR_NETWORK_ENDPOINTS.md)
- [Monitoring README](../../monitoring/README.md)
- [Prometheus Documentation](https://prometheus.io/docs/)
