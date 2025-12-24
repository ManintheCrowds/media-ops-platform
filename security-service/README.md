# Security Service

Comprehensive security monitoring and protection framework for the self-hosted platform.

## Features

- **Intrusion Detection System (IDS)**: Signature-based and behavioral detection
- **Log Aggregation**: Centralized log collection and analysis
- **Anomaly Detection**: Statistical anomaly detection with baseline establishment
- **Alerting**: Multi-channel alerting (email, Slack, webhook)
- **Firewall Automation**: Automated IP blocking and rule management
- **DDoS Protection**: Traffic analysis and automatic mitigation
- **Rate Limiting**: Per-IP, per-user, and per-endpoint rate limiting
- **Access Control**: IP whitelist/blacklist, time-based access, geographic restrictions
- **Threat Intelligence**: IP reputation checking (AbuseIPDB, VirusTotal)
- **Malware Scanning**: File scanning with ClamAV and VirusTotal
- **Vulnerability Scanning**: Dependency and container scanning
- **Patch Management**: Security patch detection and tracking
- **SIEM**: Event correlation and incident generation
- **Compliance**: Audit logging, reporting, and backup verification

## Configuration

Set environment variables:

```bash
SECURITY_SERVICE_PORT=8001
SECURITY_DATABASE_URL=postgresql://platform:platform@postgres:5432/platform
SECURITY_REDIS_URL=redis://redis:6379
ABUSEIPDB_API_KEY=your-key
VIRUSTOTAL_API_KEY=your-key
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

## Running

```bash
docker-compose up security-service
```

Or directly:

```bash
uvicorn security_service.main:app --host 0.0.0.0 --port 8001
```







