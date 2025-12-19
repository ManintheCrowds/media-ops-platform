# Security Monitoring and Protection Framework

## Overview

The Security Monitoring and Protection Framework provides comprehensive security capabilities for the self-hosted platform, including intrusion detection, log aggregation, anomaly detection, threat intelligence, automated protection mechanisms, and SIEM capabilities.

## Architecture

The framework consists of several key components:

### Monitoring Layer
- **Intrusion Detection System (IDS)**: Signature-based and behavioral detection
- **Log Aggregation**: Centralized log collection from all services
- **Anomaly Detection**: Statistical anomaly detection with baseline establishment
- **Alerting System**: Multi-channel alerting (email, Slack, webhook)

### Protection Layer
- **Firewall Automation**: Automated IP blocking and rule management
- **DDoS Protection**: Traffic analysis and automatic mitigation
- **Rate Limiting**: Per-IP, per-user, and per-endpoint rate limiting
- **Access Control**: IP whitelist/blacklist, time-based access, geographic restrictions

### Threat Intelligence
- **IP Reputation**: Integration with AbuseIPDB and VirusTotal
- **Malware Scanning**: File scanning with ClamAV and VirusTotal
- **Vulnerability Scanning**: Dependency and container scanning
- **Patch Management**: Security patch detection and tracking

### SIEM & Analytics
- **SIEM Engine**: Event correlation and incident generation
- **Correlation Rules**: Time-based, sequence-based, and pattern-based correlation
- **Incident Management**: Automatic creation, tracking, and resolution workflow

### Compliance
- **Audit Logging**: Comprehensive audit trail with integrity verification
- **Compliance Reporting**: Automated reports with multiple framework support
- **Backup Verification**: Integrity checks and restoration testing

## API Endpoints

### Security Events
- `GET /api/security/events` - List security events
- `GET /api/security/events/{id}` - Get event details

### Incidents
- `GET /api/security/incidents` - List incidents
- `GET /api/security/incidents/{id}` - Get incident details
- `POST /api/security/incidents` - Create incident
- `PUT /api/security/incidents/{id}` - Update incident

### Threat Intelligence
- `GET /api/security/threats` - List threat intelligence entries
- `GET /api/security/threats/ip/{ip}` - IP reputation lookup

### Firewall Rules
- `GET /api/security/firewall/rules` - List firewall rules
- `POST /api/security/firewall/rules` - Create firewall rule
- `DELETE /api/security/firewall/rules/{id}` - Delete firewall rule

### Vulnerabilities
- `GET /api/security/vulnerabilities` - List vulnerabilities
- `POST /api/security/vulnerabilities/scan` - Trigger vulnerability scan

### Audit & Compliance
- `GET /api/security/audit` - Get audit logs
- `GET /api/security/compliance/report` - Get compliance report

## Configuration

### Environment Variables

```bash
# Service Configuration
SECURITY_SERVICE_PORT=8001
SECURITY_DATABASE_URL=postgresql://platform:platform@postgres:5432/platform
SECURITY_REDIS_URL=redis://redis:6379

# Threat Intelligence
ABUSEIPDB_API_KEY=your-key
VIRUSTOTAL_API_KEY=your-key

# Alerting
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.example.com
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/...

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_IP=100
RATE_LIMIT_WINDOW=60
```

## Incident Response Procedures

### 1. Detection
- Security events are automatically detected by IDS
- Anomalies are identified by the anomaly detection engine
- Events are correlated by the SIEM engine

### 2. Alerting
- Alerts are sent via configured channels (email, Slack, webhook)
- Alert severity determines response priority

### 3. Incident Creation
- Incidents are automatically created for critical events
- Manual incident creation is available via API

### 4. Investigation
- Review incident timeline and related events
- Check threat intelligence for source IPs
- Analyze logs and security events

### 5. Response
- Apply firewall rules to block malicious IPs
- Update access control policies
- Document findings and actions

### 6. Resolution
- Mark incident as resolved
- Update resolution notes
- Close incident after verification

## Compliance Reporting

The framework supports automated compliance reporting:

- **Security Audit Report**: Summary of security events, incidents, and vulnerabilities
- **Access Control Report**: Login attempts, admin actions, and access patterns
- **Vulnerability Report**: Detected vulnerabilities and remediation status
- **Patch Status Report**: Available security patches and application status

Reports can be exported in CSV format and scheduled for automatic generation.

## Integration

### Prometheus
Security metrics are exported at `/metrics` endpoint and scraped by Prometheus.

### Grafana
Pre-configured dashboards are available for:
- Security Overview
- Intrusion Detection
- Protection Status
- Threat Intelligence
- Incident Management
- Compliance

### pfSense
pfSense integration is prepared for future implementation. When configured, firewall rules can be automatically applied to pfSense.

## Monitoring

Key metrics to monitor:

- `security_events_total` - Total security events
- `intrusion_attempts_total` - Intrusion attempts
- `blocked_ips_total` - Blocked IP addresses
- `ddos_attacks_detected` - DDoS attacks
- `vulnerabilities_detected` - Detected vulnerabilities
- `incidents_active` - Active incidents

## Best Practices

1. **Regular Review**: Review security events and incidents daily
2. **Threat Intelligence**: Keep threat intelligence feeds updated
3. **Vulnerability Management**: Scan regularly and patch promptly
4. **Access Control**: Regularly review and update access control policies
5. **Backup Verification**: Verify backups regularly
6. **Incident Response**: Follow incident response procedures consistently
7. **Compliance**: Generate and review compliance reports regularly

## Troubleshooting

### High False Positive Rate
- Adjust IDS signature thresholds
- Review and tune anomaly detection baselines
- Update correlation rules

### Performance Issues
- Enable Redis for rate limiting
- Optimize database queries
- Review log retention policies

### Missing Alerts
- Verify alert channel configuration
- Check alert deduplication settings
- Review alert severity thresholds

