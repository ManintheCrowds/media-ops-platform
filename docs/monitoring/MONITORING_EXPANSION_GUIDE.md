# Monitoring Expansion Guide

## Overview

This guide provides step-by-step instructions for adding monitoring to any application or service, following the proven pattern established with Cursor monitoring.

## Quick Start

If you want to monitor a Windows application quickly:

```powershell
# Use the template script
.\scripts\monitoring\app-monitor-template.ps1 -AppName "VSCode" -ProcessName "Code" -Interval 5
```

For full integration with Prometheus and Grafana, follow the complete guide below.

## Step-by-Step Process

### Step 1: Identify Your Monitoring Target

**Questions to answer:**
- What application/service do you want to monitor?
- What metrics matter? (connections, performance, errors, resources)
- Why are you monitoring it? (troubleshooting, optimization, alerting)
- What process name(s) does it use?

**Example:**
- **Target**: VS Code
- **Process Name**: "Code"
- **Metrics**: Network connections, CPU, Memory
- **Purpose**: Track VS Code's network usage and performance

### Step 2: Create Monitoring Script

#### Option A: Use the Template (Recommended)

```powershell
# Copy template and customize
Copy-Item scripts\monitoring\app-monitor-template.ps1 scripts\monitoring\vscode-process-monitor.ps1

# Edit the script if needed, or use as-is with parameters
.\scripts\monitoring\app-monitor-template.ps1 -AppName "VSCode" -ProcessName "Code" -Interval 5
```

#### Option B: Create Custom Script

1. Copy `scripts/monitoring/cursor-process-monitor.ps1` as a starting point
2. Rename to match your application (e.g., `vscode-process-monitor.ps1`)
3. Update process name filters
4. Customize metrics collection as needed
5. Test the script

**Example customization:**
```powershell
# Change process names
$ProcessNames = @("Code", "code")  # VS Code process names

# Add custom metrics if needed
# ... your custom logic here
```

### Step 3: Test the Monitoring Script

```powershell
# Run the script and verify it collects data
.\scripts\monitoring\app-monitor-template.ps1 -AppName "VSCode" -ProcessName "Code" -Interval 5

# Check output directory for JSON files
Get-ChildItem vscode-metrics\*.json | Select-Object -First 1 | Get-Content | ConvertFrom-Json
```

**Verify:**
- Script runs without errors
- JSON files are created
- Metrics contain expected data
- Process is detected when application is running

### Step 4: Create Prometheus Exporter (Optional)

If you want real-time metrics in Prometheus:

#### Step 4a: Copy Exporter Template

```powershell
# Copy Cursor exporter as template
Copy-Item monitoring\cursor-exporter\cursor_exporter.py monitoring\exporters\vscode_exporter.py
```

#### Step 4b: Customize Exporter

Edit the exporter file:

1. **Update metric names:**
   ```python
   # Change from cursor_* to your_app_*
   vscode_connections_active = Gauge(
       'vscode_connections_active',
       'Current number of active VS Code connections',
       ['endpoint']
   )
   ```

2. **Update directory paths:**
   ```python
   def __init__(
       self,
       metrics_dir='vscode-metrics',  # Your app's metrics directory
       quality_dir='vscode-quality-metrics',
       event_log_dir='vscode-event-logs'
   ):
   ```

3. **Update metric collection logic** if needed

#### Step 4c: Test Exporter Locally

```bash
# Install dependencies
pip install prometheus-client

# Run exporter
python monitoring/exporters/vscode_exporter.py --port 9102 --interval 30

# Test metrics endpoint
curl http://localhost:9102/metrics
```

### Step 5: Add to Prometheus

#### Step 5a: Update prometheus.yml

Edit `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  # ... existing jobs ...
  
  # Your new exporter
  - job_name: 'vscode-exporter'
    static_configs:
      - targets: ['host.docker.internal:9102']  # Windows host
    scrape_interval: 30s
    metrics_path: '/metrics'
    scrape_timeout: 10s
```

#### Step 5b: Reload Prometheus

```bash
# Reload Prometheus configuration
docker exec platform-prometheus kill -HUP 1

# Or restart Prometheus
docker-compose restart prometheus
```

#### Step 5c: Verify Scraping

1. Open Prometheus: http://localhost:9090
2. Go to **Status** → **Targets**
3. Verify your exporter shows as **UP**
4. Query a metric: `vscode_connections_active`

### Step 6: Create Grafana Dashboard

#### Step 6a: Export Cursor Dashboard

1. Open Grafana: http://localhost:3001
2. Go to **Dashboards** → **Cursor Connection Monitoring**
3. Click **Dashboard settings** (gear icon)
4. Click **JSON Model**
5. Copy the JSON

#### Step 6b: Customize Dashboard

1. **Find and replace:**
   - `cursor` → `vscode` (or your app name)
   - `Cursor` → `VS Code` (or your app name)
   - Update metric names in queries

2. **Update queries:**
   ```promql
   # Change from:
   cursor_connections_active
   # To:
   vscode_connections_active
   ```

3. **Update panel titles and descriptions**

#### Step 6c: Import Dashboard

**Option 1: Via Grafana UI**
1. Go to **Dashboards** → **Import**
2. Paste your modified JSON
3. Click **Load**
4. Select Prometheus data source
5. Click **Import**

**Option 2: Save as File**
1. Save JSON to `monitoring/grafana/dashboards/vscode-monitoring.json`
2. Grafana will auto-import if provisioning is configured
3. Or use import script: `.\scripts\monitoring\import-cursor-dashboard.ps1`

### Step 7: Set Up Alerts

#### Step 7a: Define Alert Conditions

Decide what conditions should trigger alerts:
- High latency (>500ms)
- High error rate (>10 errors/min)
- Service down
- High resource usage

#### Step 7b: Add Alert Rules

Edit `prometheus/alert_rules.yml`:

```yaml
groups:
  # ... existing groups ...
  
  - name: vscode_alerts
    interval: 30s
    rules:
      - alert: VSCodeHighLatency
        expr: vscode_latency_seconds > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency to VS Code endpoint {{ $labels.endpoint }}"
          description: "Latency is {{ $value }}s (threshold: 0.5s)"
      
      - alert: VSCodeNoConnections
        expr: vscode_connections_active == 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "No active VS Code connections"
          description: "VS Code has no active connections for 10 minutes"
```

#### Step 7c: Reload Prometheus

```bash
docker exec platform-prometheus kill -HUP 1
```

#### Step 7d: Test Alerts

1. Temporarily lower a threshold to trigger an alert
2. Verify alert appears in Prometheus: http://localhost:9090/alerts
3. Verify notification is sent (if configured)
4. Restore original threshold

### Step 8: Documentation

#### Step 8a: Document What You're Monitoring

Create or update documentation:

```markdown
# VS Code Monitoring

## Overview
Monitors VS Code IDE network connections and performance.

## Metrics
- `vscode_connections_active` - Active connections
- `vscode_connections_total` - Total connections
- `vscode_cpu_usage_seconds` - CPU usage
- `vscode_memory_usage_bytes` - Memory usage

## Dashboard
- Location: Grafana → VS Code Monitoring
- URL: http://localhost:3001/d/vscode-monitoring

## Alerts
- High latency (>500ms)
- No connections (>10 minutes)
```

#### Step 8b: Update Monitoring Index

Add to `monitoring/README.md`:

```markdown
## Application Monitoring

- Cursor IDE - `docs/monitoring/CURSOR_MONITORING.md`
- VS Code - `docs/monitoring/VSCODE_MONITORING.md` (if created)
```

## Complete Example: Monitoring VS Code

### 1. Start Monitoring

```powershell
.\scripts\monitoring\app-monitor-template.ps1 -AppName "VSCode" -ProcessName "Code" -Interval 5 -OutputDir "vscode-metrics"
```

### 2. Create Exporter

```bash
# Copy and customize
cp monitoring/cursor-exporter/cursor_exporter.py monitoring/exporters/vscode_exporter.py
# Edit vscode_exporter.py (change metric names, directories)

# Run exporter
python monitoring/exporters/vscode_exporter.py --port 9102
```

### 3. Add to Prometheus

```yaml
# prometheus/prometheus.yml
- job_name: 'vscode-exporter'
  static_configs:
    - targets: ['host.docker.internal:9102']
  scrape_interval: 30s
```

### 4. Create Dashboard

- Clone Cursor dashboard
- Replace `cursor` with `vscode`
- Update metric queries
- Import to Grafana

### 5. Add Alerts

```yaml
# prometheus/alert_rules.yml
- alert: VSCodeHighLatency
  expr: vscode_latency_seconds > 0.5
  for: 5m
  labels:
    severity: warning
```

## Checklist

Use this checklist for each new monitoring target:

- [ ] Identified monitoring target and metrics
- [ ] Created monitoring script (or used template)
- [ ] Tested script and verified data collection
- [ ] Created exporter (if needed)
- [ ] Tested exporter locally
- [ ] Added scrape job to Prometheus
- [ ] Verified Prometheus is scraping
- [ ] Created Grafana dashboard
- [ ] Imported dashboard to Grafana
- [ ] Verified dashboard shows data
- [ ] Defined alert conditions
- [ ] Added alert rules to Prometheus
- [ ] Tested alert firing
- [ ] Documented monitoring setup
- [ ] Updated monitoring index

## Common Patterns

### Pattern 1: Simple Application Monitoring

**Use case**: Monitor any Windows application

**Steps**:
1. Use `app-monitor-template.ps1`
2. Run script (no exporter needed if just collecting data)
3. Analyze JSON files manually or with scripts

**Time**: 5 minutes

### Pattern 2: Full Integration

**Use case**: Monitor with Prometheus and Grafana

**Steps**:
1. Use template script
2. Create exporter
3. Add to Prometheus
4. Create dashboard
5. Set up alerts

**Time**: 1-2 hours

### Pattern 3: Service Monitoring

**Use case**: Monitor Docker services

**Steps**:
1. Use existing cAdvisor metrics
2. Create service-specific dashboard
3. Add service-specific alerts
4. No custom script needed

**Time**: 30 minutes

## Troubleshooting

### Script Not Finding Process

**Problem**: Script reports "process not found"

**Solutions**:
1. Verify process name is correct: `Get-Process | Where-Object {$_.ProcessName -like "*Code*"}`
2. Check if application is actually running
3. Try different process name variations
4. Use `-AdditionalProcessNames` parameter for multiple names

### Exporter Not Scraping

**Problem**: Prometheus shows target as DOWN

**Solutions**:
1. Verify exporter is running: `curl http://localhost:9102/metrics`
2. Check firewall allows connection
3. Verify target address (use `host.docker.internal` for Windows host)
4. Check Prometheus logs: `docker logs platform-prometheus`

### Dashboard Shows No Data

**Problem**: Dashboard panels show "No data"

**Solutions**:
1. Verify metrics exist in Prometheus: Query `vscode_connections_active`
2. Check time range (may need to adjust)
3. Verify metric names match between exporter and dashboard
4. Check data source is correct Prometheus instance

### Alerts Not Firing

**Problem**: Conditions met but alerts not firing

**Solutions**:
1. Check alert rule syntax: `docker exec platform-prometheus promtool check rules /etc/prometheus/alert_rules.yml`
2. Verify alert expression evaluates: Test in Prometheus query UI
3. Check `for` duration has passed
4. Verify Alertmanager is configured and running

## Best Practices

### 1. Start Simple

Begin with basic monitoring, then expand:
- First: Just collect data (script + JSON)
- Then: Add exporter for real-time metrics
- Finally: Add dashboards and alerts

### 2. Reuse Patterns

- Use Cursor monitoring as template
- Copy and modify rather than starting from scratch
- Maintain consistency across monitoring setups

### 3. Document Everything

- Document what you monitor
- Note any special configuration
- Keep track of metric names
- Update monitoring index

### 4. Test Incrementally

- Test script first
- Test exporter separately
- Test Prometheus scraping
- Test dashboard
- Test alerts last

### 5. Set Appropriate Intervals

- Script collection: 5-30 seconds
- Prometheus scraping: 15-30 seconds
- Alert evaluation: 30 seconds
- Dashboard refresh: 30 seconds

### 6. Use Meaningful Names

- Metric names: `app_metric_name`
- Dashboard titles: Clear and descriptive
- Alert names: Indicate what's wrong
- File names: Match application name

## Advanced: Custom Metrics

If you need metrics beyond the template:

### Adding Custom Metrics to Script

```powershell
function Get-CustomMetrics {
    param([int[]]$ProcessIds)
    
    $metrics = @{
        # Standard metrics
        ActiveConnections = ...
        
        # Your custom metrics
        CustomMetric1 = ...
        CustomMetric2 = ...
    }
    
    return $metrics
}
```

### Adding Custom Metrics to Exporter

```python
# In exporter
custom_metric = Gauge(
    'app_custom_metric',
    'Description of custom metric',
    ['label1', 'label2']
)

# Update metric
custom_metric.labels(label1='value1', label2='value2').set(value)
```

## Resources

- **Template Script**: `scripts/monitoring/app-monitor-template.ps1`
- **Exporter Template**: `monitoring/cursor-exporter/cursor_exporter.py`
- **Dashboard Template**: `monitoring/grafana/dashboards/cursor-connections.json`
- **Cursor Monitoring**: `docs/monitoring/CURSOR_MONITORING.md` (reference implementation)

## See Also

- [Cursor Monitoring Guide](CURSOR_MONITORING.md) - Complete reference implementation
- [Alert Notification Setup](ALERT_NOTIFICATION_SETUP.md) - Configure alerts
- [Monitoring README](../../monitoring/README.md) - Infrastructure overview
- [Expanding Monitoring](EXPANDING_MONITORING.md) - More expansion ideas
