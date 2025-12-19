# pfSense Monitoring Configuration

## Overview

This document describes how to configure monitoring and logging for pfSense to integrate with Prometheus and Grafana.

## Prometheus Integration

### Exporter Installation

1. **Install pfSense Exporter Package**:
   - Navigate to System → Package Manager
   - Search for "prometheus" or "exporter"
   - Install: `prometheus-pfsense-exporter` (if available)
   - Or use community package: `pfsense-prometheus-exporter`

2. **Alternative: Use SNMP Exporter**:
   - Enable SNMP in pfSense: Services → SNMP
   - Configure SNMP community (use secure community string)
   - Use Prometheus SNMP exporter to collect metrics

### SNMP Configuration

1. **Enable SNMP**:
   - Navigate to Services → SNMP
   - Enable SNMP: Yes
   - Listen Interfaces: LAN, VLAN interfaces
   - SNMP Community: Set secure community string
   - Save

2. **SNMP Traps** (optional):
   - Configure trap destinations
   - Set up trap authentication

### Prometheus Configuration

Add to `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  # pfSense SNMP Exporter
  - job_name: 'pfsense'
    static_configs:
      - targets:
        - '10.0.10.1:9116'  # pfSense exporter port
    scrape_interval: 30s
    metrics_path: /metrics

  # pfSense via SNMP (if using SNMP exporter)
  - job_name: 'pfsense-snmp'
    static_configs:
      - targets:
        - '10.0.10.1:161'  # SNMP port
    scrape_interval: 60s
    metrics_path: /snmp
    params:
      module: [pfsense]
```

### Metrics Available

- **Interface Statistics**:
  - `ifInOctets`, `ifOutOctets` - Bytes in/out
  - `ifInErrors`, `ifOutErrors` - Error counts
  - `ifSpeed` - Interface speed

- **Firewall Statistics**:
  - `pfStateCount` - Active firewall states
  - `pfStateLimit` - State table limit
  - `pfStateSearch` - State searches

- **System Statistics**:
  - `systemUptime` - System uptime
  - `systemLoad` - System load
  - `systemMemory` - Memory usage

- **VPN Statistics**:
  - `openvpnClients` - Active VPN clients
  - `openvpnBytesIn`, `openvpnBytesOut` - VPN traffic

## Grafana Dashboards

### Import Dashboard

1. **Create Dashboard**:
   - Navigate to Grafana → Dashboards → Import
   - Use dashboard ID: `pfsense` (community dashboard)
   - Or create custom dashboard

2. **Dashboard Panels**:
   - Interface traffic graphs
   - Firewall rule hit counts
   - VPN connection status
   - System resource usage
   - Bandwidth usage per VLAN

### Custom Dashboard JSON

Example dashboard configuration available in `config/grafana/pfsense-dashboard.json`

## Logging Configuration

### Syslog Setup

1. **Enable Remote Logging**:
   - Navigate to System → Advanced → Logging
   - Enable Remote Logging: Yes
   - Remote Syslog Server: IP of log aggregation server
   - Remote Syslog Contents: Select what to log

2. **Log Retention**:
   - Configure log rotation
   - Set retention period
   - Enable log compression

### Firewall Logging

1. **Enable Firewall Logs**:
   - Navigate to System → Advanced → Logging
   - Enable Firewall Logging: Yes
   - Log Packets: Blocked packets (or all)

2. **Log Analysis**:
   - Export logs to SIEM
   - Use log analysis tools
   - Set up alerts for suspicious activity

## Traffic Monitoring

### Interface Statistics

1. **View Real-time Stats**:
   - Navigate to Status → Traffic Graph
   - Select interface
   - View bandwidth usage

2. **Historical Data**:
   - Use RRD graphs (built-in)
   - Or export to Prometheus/Grafana

### Bandwidth Monitoring

1. **Per-VLAN Monitoring**:
   - Monitor each VLAN interface
   - Track bandwidth usage
   - Set up alerts for high usage

2. **Top Talkers**:
   - Use pfSense package: `bandwidthd` or `ntopng`
   - Identify high-bandwidth users
   - Monitor for anomalies

## Alerting

### Prometheus Alerts

Add to `prometheus/alert_rules.yml`:

```yaml
groups:
  - name: pfsense
    rules:
      - alert: PfSenseHighCPU
        expr: pfsense_cpu_usage > 80
        for: 5m
        annotations:
          summary: "pfSense CPU usage high"
      
      - alert: PfSenseHighMemory
        expr: pfsense_memory_usage > 90
        for: 5m
        annotations:
          summary: "pfSense memory usage high"
      
      - alert: PfSenseInterfaceDown
        expr: pfsense_interface_status == 0
        for: 1m
        annotations:
          summary: "pfSense interface down"
      
      - alert: PfSenseHighBandwidth
        expr: rate(pfsense_interface_bytes[5m]) > 1000000000
        for: 10m
        annotations:
          summary: "High bandwidth usage on interface"
```

### Grafana Alerts

1. **Create Alert Rules**:
   - In Grafana dashboard
   - Add alert to panel
   - Configure thresholds
   - Set notification channels

2. **Notification Channels**:
   - Email
   - Slack
   - Webhook
   - PagerDuty

## Security Service Integration

The security service can collect pfSense metrics via API:

1. **Enable API Access**:
   - System → Advanced → API
   - Enable API: Yes
   - Generate API key

2. **Configure Security Service**:
   - Set `PFSENSE_URL` and `PFSENSE_API_KEY`
   - Security service will collect:
     - Firewall logs
     - Traffic statistics
     - VPN connections
     - System status

3. **Metrics Endpoint**:
   - Security service exposes metrics at `/metrics`
   - Prometheus can scrape these metrics

## Best Practices

1. **Monitoring Coverage**:
   - Monitor all critical interfaces
   - Track firewall rule effectiveness
   - Monitor VPN connections
   - Watch system resources

2. **Alert Thresholds**:
   - Set realistic thresholds
   - Avoid alert fatigue
   - Use different severity levels

3. **Log Retention**:
   - Retain logs for compliance
   - Compress old logs
   - Archive to external storage

4. **Performance**:
   - Don't overload pfSense with monitoring
   - Use appropriate scrape intervals
   - Monitor monitoring system itself

## Troubleshooting

### Metrics Not Appearing

1. Check exporter is running
2. Verify network connectivity
3. Check firewall rules allow access
4. Verify Prometheus configuration

### High Resource Usage

1. Increase scrape intervals
2. Reduce metrics collected
3. Use sampling
4. Optimize queries

### Missing Data

1. Check time ranges
2. Verify data retention
3. Check for gaps in collection
4. Review exporter logs
