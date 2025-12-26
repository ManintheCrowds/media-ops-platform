# Security Service

Comprehensive security monitoring and protection framework for the self-hosted platform.

## Features

### Detection & Monitoring
- **Intrusion Detection System (IDS)**: Signature-based and behavioral detection
  - Pattern matching for known attack signatures
  - Behavioral analysis for anomaly detection
  - Real-time traffic analysis
- **Log Aggregation**: Centralized log collection and analysis
  - Collects logs from all platform services
  - Centralized search and analysis
  - Long-term retention
- **Anomaly Detection**: Statistical anomaly detection with baseline establishment
  - Machine learning-based detection
  - Adaptive baselines
  - Threshold-based alerts

### Protection & Response
- **Firewall Automation**: Automated IP blocking and rule management
  - Automatic IP blocking for threats
  - Rule generation and deployment
  - Integration with pfSense and other firewalls
- **DDoS Protection**: Traffic analysis and automatic mitigation
  - Traffic pattern analysis
  - Automatic rate limiting
  - Source IP blocking
- **Rate Limiting**: Per-IP, per-user, and per-endpoint rate limiting
  - Configurable limits per endpoint
  - User-based throttling
  - IP-based restrictions

### Access Control
- **IP Whitelist/Blacklist**: Manage allowed and blocked IPs
- **Time-based Access**: Restrict access by time of day
- **Geographic Restrictions**: Block or allow by geographic location

### Threat Intelligence
- **IP Reputation Checking**: Integration with AbuseIPDB and VirusTotal
  - Real-time IP reputation lookup
  - Historical threat data
  - Automated threat scoring
- **Malware Scanning**: File scanning with ClamAV and VirusTotal
  - On-demand file scanning
  - Scheduled scans
  - Quarantine management

### Vulnerability Management
- **Vulnerability Scanning**: Dependency and container scanning
  - Automated dependency scanning
  - Container image analysis
  - CVE database integration
- **Patch Management**: Security patch detection and tracking
  - Patch availability monitoring
  - Deployment tracking
  - Compliance reporting

### Security Operations
- **SIEM**: Event correlation and incident generation
  - Real-time event correlation
  - Incident creation and tracking
  - Automated response workflows
- **Compliance**: Audit logging, reporting, and backup verification
  - Comprehensive audit trails
  - Compliance report generation
  - Backup integrity verification

### Alerting
- **Multi-channel Alerting**: Email, Slack, webhook notifications
  - Configurable alert channels
  - Severity-based routing
  - Escalation policies

## Architecture

### Components

- **IDS Engine**: Signature and behavioral detection
- **Log Collector**: Centralized log aggregation
- **Anomaly Detector**: Statistical analysis engine
- **Firewall Manager**: Automated rule management
- **Threat Intelligence**: IP reputation and malware scanning
- **SIEM Engine**: Event correlation and incident management
- **Rate Limiter**: Traffic throttling and DDoS protection
- **Vulnerability Scanner**: Dependency and container analysis
- **Compliance Manager**: Audit logging and reporting

### Integration with Monitoring Stack

- **Prometheus Metrics**: Exposes metrics at `/metrics` endpoint
- **Grafana Dashboards**: Pre-configured security dashboards
- **Alertmanager Integration**: Routes security alerts to notification channels
- **Loki Integration**: Sends security logs to centralized logging

### Alert Routing

1. Security events detected by IDS, anomaly detector, or SIEM
2. Events evaluated against alert rules
3. Alerts routed based on severity (Critical → email + Slack, Warning → email)
4. Incidents created for high-severity events
5. Automated responses triggered (IP blocking, rate limiting)

### Firewall Automation Workflow

1. Threat detected (malicious IP, attack pattern)
2. Threat intelligence lookup (AbuseIPDB, VirusTotal)
3. Risk score calculated
4. If risk exceeds threshold: IP added to blacklist
5. Firewall rule generated and deployed
6. Alert sent to administrators
7. Incident created for tracking

## Configuration

### Environment Variables

Set environment variables:

```bash
# Service Configuration
SECURITY_SERVICE_PORT=8001
SECURITY_DATABASE_URL=postgresql://platform:platform@postgres:5432/platform
SECURITY_REDIS_URL=redis://redis:6379

# Threat Intelligence APIs
ABUSEIPDB_API_KEY=your-abuseipdb-key
VIRUSTOTAL_API_KEY=your-virustotal-key

# ClamAV Configuration
CLAMAV_HOST=clamav
CLAMAV_PORT=3310

# Alert Configuration
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.example.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=security@example.com
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Firewall Integration
FIREWALL_TYPE=pfsense  # or 'iptables', 'ufw'
FIREWALL_API_URL=http://pfsense:8080/api
FIREWALL_API_KEY=your-firewall-api-key

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_URL=redis://redis:6379

# SIEM Configuration
SIEM_CORRELATION_ENABLED=true
SIEM_INCIDENT_AUTO_CREATE=true
```

### Integration with AbuseIPDB

1. Sign up at https://www.abuseipdb.com/
2. Get API key from account settings
3. Set `ABUSEIPDB_API_KEY` in environment
4. Service automatically checks IPs against AbuseIPDB

### Integration with VirusTotal

1. Sign up at https://www.virustotal.com/
2. Get API key from account settings
3. Set `VIRUSTOTAL_API_KEY` in environment
4. Service uses VirusTotal for:
   - IP reputation checks
   - File hash lookups
   - URL scanning

### ClamAV Setup

1. Start ClamAV container (if not already running)
2. Configure `CLAMAV_HOST` and `CLAMAV_PORT`
3. Service automatically connects for file scanning

### Alert Channel Configuration

**Email Alerts:**
```bash
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
ALERT_EMAIL_FROM=security@example.com
ALERT_EMAIL_TO=admin@example.com
```

**Slack Alerts:**
```bash
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ALERT_SLACK_CHANNEL=#security-alerts
```

**Webhook Alerts:**
```bash
ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URL=https://your-webhook-endpoint.com/security
ALERT_WEBHOOK_SECRET=your-webhook-secret
```

## API Endpoints

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /api/security/events` - List security events
- `GET /api/security/incidents` - List incidents
- `GET /api/security/threats/ip/{ip}` - IP reputation lookup
- `GET /api/security/firewall/rules` - List firewall rules
- `GET /api/security/vulnerabilities` - List vulnerabilities
- `GET /api/security/audit` - Get audit logs
- `GET /api/security/compliance/report` - Get compliance report

## Platform Integration

The security service integrates with the main platform:

- **Service Registry**: Registers with platform API
- **Authentication**: Uses platform JWT tokens
- **Health Monitoring**: Exposes health endpoint for platform monitoring
- **Metrics**: Prometheus metrics available to monitoring stack
- **Logs**: Sends logs to centralized Loki instance

### Service Registration

Register the security service with the platform:

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "security-service",
    "service_type": "security",
    "base_url": "http://security-service:8001",
    "health_check_url": "http://security-service:8001/health",
    "requires_auth": true
  }'
```

## Running

### Docker Compose

```bash
docker-compose up -d security-service
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECURITY_DATABASE_URL=postgresql://...
export SECURITY_REDIS_URL=redis://...

# Run service
uvicorn security_service.main:app --host 0.0.0.0 --port 8001 --reload
```

## Related Services

- [Platform API](../README.md) - Main integration layer
- [Monitoring Stack](../monitoring/README.md) - Prometheus, Grafana, Alertmanager
- [Home Cyber Risk](../home-cyber-risk/README.md) - Breach monitoring service

## Troubleshooting

### Service won't start

- Check database connection: `SECURITY_DATABASE_URL`
- Verify Redis is running: `SECURITY_REDIS_URL`
- Check required API keys are set
- Review logs: `docker logs security-service`

### Alerts not working

- Verify alert configuration in environment variables
- Test SMTP settings manually
- Check Slack webhook URL is correct
- Review alert logs for errors

### Firewall automation not working

- Verify firewall API credentials
- Check firewall API is accessible
- Review firewall integration logs
- Test firewall API connection manually

### Threat intelligence not updating

- Verify API keys are valid
- Check API rate limits haven't been exceeded
- Review threat intelligence logs
- Test API connections manually







