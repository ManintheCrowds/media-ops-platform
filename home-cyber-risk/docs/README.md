# Home Cyber Risk Awareness Server

A simple, achievable home cyber risk awareness server that monitors breach exposure for personal identifiers, provides DNS-level protection, and offers lightweight observability.

## Features

- **Multi-source breach detection:**
  - Have I Been Pwned (HIBP) API (optional API key for email/username)
  - Public breach databases (free, local cache)
  - Paste site monitoring (Pastebin, GitHub Gists)
- **Free password checking** (HIBP Pwned Passwords, no API key required)
- **Risk scoring and prioritization** (Critical/High/Medium/Low)
- **Multi-source aggregation** with deduplication
- **Breach differencing** (new vs updated breaches)
- **Data normalization** across sources
- **Check history tracking**
- Multiple alert channels: Email, Telegram, Webhook, Log
- Lightweight observability with Grafana and Loki
- Optional Pi-hole integration for DNS protection
- SQLite by default (PostgreSQL optional)
- Docker Compose deployment
- **Platform integration** - Can integrate with main platform API

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- HIBP API key (optional, for email/username checking)

### Installation

1. Clone or download this repository

2. Copy configuration files:
   ```bash
   cp .env.example .env
   cp config/identifiers.yml.example config/identifiers.yml
   ```

3. Edit `config/identifiers.yml` with your identifiers:
   ```yaml
   emails:
     - "your-email@example.com"
   usernames:
     - "your-username"
   ```

4. Edit `.env` with your configuration:
   ```bash
   HIBP_API_KEY=your-api-key-here  # Optional
   ALERT_EMAIL_ENABLED=true
   ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
   # ... other settings
   ```

5. Start services:
   ```bash
   cd infra
   docker-compose up -d
   ```

### Manual Check

Run a manual breach check:

```bash
python scripts/check_breaches.py
```

Or with dry-run (no storage, no alerts):

```bash
python scripts/check_breaches.py --dry-run
```

## Architecture

### Components

- **Fetchers** - Multi-source breach data retrieval:
  - `HIBPFetcher` - Have I Been Pwned API integration
  - `PublicBreachFetcher` - Free public breach databases
  - `PasteSiteFetcher` - Pastebin and GitHub Gists monitoring
- **Normalizer** - Standardizes breach data across sources
- **Aggregator** - Combines and deduplicates results from multiple sources
- **Risk Scorer** - Calculates risk scores and priorities
- **Differ** - Identifies new and updated breaches
- **Storage** - SQLite or PostgreSQL database persistence
- **Notifier** - Multi-channel alert system (Email, Telegram, Webhook, Log)

### Data Flow

1. Identifiers loaded from `config/identifiers.yml`
2. Each identifier checked against all enabled fetchers
3. Raw breach data normalized to standard format
4. Results aggregated and deduplicated across sources
5. Risk scores calculated for each breach
6. New/updated breaches identified via differencing
7. Alerts sent for new/updated breaches
8. Results stored in database with check history

### Platform Integration

The service can integrate with the main platform API:
- Register as a service in the platform service registry
- Expose health check endpoints
- Provide breach data via API endpoints
- Use platform authentication for API access

## Configuration

### Identifiers

Edit `config/identifiers.yml` to specify what to monitor:

- `emails`: List of email addresses
- `usernames`: List of usernames
- `domains`: List of domains (for reference, not directly checked)
- `metadata`: Optional notes per identifier

### Environment Variables

See `.env.example` for all available options:

- `HIBP_API_KEY`: Optional API key for email/username checking
- `DATABASE_URL`: Database connection (SQLite default)
- `CHECK_CADENCE`: Hours between checks (default: 168 = weekly)
- `ENABLE_PUBLIC_BREACH_DB`: Enable public breach database fetcher (default: true)
- `ENABLE_PASTE_MONITORING`: Enable paste site monitoring (default: true)
- `GITHUB_TOKEN`: Optional GitHub token for paste monitoring (increases rate limits)
- `PUBLIC_BREACH_CACHE_DIR`: Directory for public breach cache (default: data/breach_cache)
- `ALERT_EMAIL_*`: Email alert configuration
- `ALERT_TELEGRAM_*`: Telegram alert configuration
- `ALERT_WEBHOOK_*`: Webhook alert configuration
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Database Configuration

**SQLite (Default):**
- No additional configuration needed
- Database stored in `data/breaches.db`

**PostgreSQL (Optional):**
1. Uncomment PostgreSQL service in `docker-compose.yml`
2. Set `POSTGRES_PASSWORD` in `.env`
3. Update `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql://breachmon:your-password@postgres:5432/breaches
   ```
4. Start with profile: `docker-compose --profile postgres up -d`

## Scheduling

### Option 1: Cron (Linux/Mac)

```bash
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh
```

### Option 2: Systemd Timer (Linux)

Create `/etc/systemd/system/breach-monitor.service`:
```ini
[Unit]
Description=Breach Monitor Check

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/scripts/check_breaches.py
EnvironmentFile=/path/to/.env
```

Create `/etc/systemd/system/breach-monitor.timer`:
```ini
[Unit]
Description=Weekly Breach Check

[Timer]
OnCalendar=weekly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable: `systemctl enable --now breach-monitor.timer`

### Option 3: Docker Compose Schedule

Uncomment the schedule command in `docker-compose.yml`:
```yaml
command: ["/bin/sh", "-c", "while true; do python scripts/check_breaches.py; sleep ${CHECK_CADENCE:-168}h; done"]
```

### Option 4: Windows Task Scheduler

Use PowerShell scripts for Windows:

```powershell
# Setup Task Scheduler (GUI)
.\scripts\setup_task_scheduler_gui.ps1

# Or use command-line setup
.\scripts\setup_windows_scheduler.ps1
```

See `docs/WINDOWS_SETUP.md` for detailed Windows instructions.

## Observability

### Grafana

Access Grafana at http://localhost:3000
- Default credentials: admin/admin (change in `.env`)
- Dashboard: Pre-configured breach monitor dashboard
- Data source: Loki (automatically configured)

### Loki

Logs are automatically sent to Loki. View in Grafana:
- Explore → Select Loki data source
- Query: `{service="breach-monitor"}`

### Metrics and Statistics

The observability stack tracks:
- Check history and frequency
- Breach statistics (total, by source, by risk level)
- Risk score distribution
- Source-specific metrics (HIBP, public DB, paste sites)
- Alert delivery status

## DNS Protection (Pi-hole)

### Enable Pi-hole

1. Uncomment Pi-hole service in `docker-compose.yml`
2. Set `PIHOLE_PASSWORD` in `.env`
3. Start: `docker-compose up -d pihole`

### Configure DNS

Point your router or devices to Pi-hole IP (172.20.0.10 by default).

See `docs/dns-setup.md` for detailed instructions.

## Risk Scoring

Breaches are automatically scored and prioritized:

- **Critical (80+):** Passwords, credit cards, SSNs in recent breaches
- **High (60-79):** Sensitive data in verified breaches
- **Medium (40-59):** Email addresses, usernames in older breaches
- **Low (<40):** Limited exposure, older breaches

Factors considered:
- Data class sensitivity (passwords=10, emails=5, usernames=3)
- Breach recency (recent = higher score)
- Verification status (verified = +2)
- Exposure scope (widespread = +1)

## Development

### Setup

```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/
```

### Run Locally

```bash
python scripts/check_breaches.py
```

## Project Structure

```
home-cyber-risk/
├── services/
│   └── breach_monitor/          # Core breach monitoring service
│       ├── main.py              # Main service orchestrator
│       ├── fetcher.py           # HIBP API fetcher
│       ├── fetcher_public.py    # Public breach database fetcher
│       ├── fetcher_paste.py     # Paste site fetcher
│       ├── fetcher_base.py      # Base fetcher class
│       ├── normalizer.py        # Data normalization
│       ├── aggregator.py        # Multi-source aggregation
│       ├── differ.py            # Breach differencing
│       ├── risk_scorer.py       # Risk scoring system
│       ├── storage.py           # Database persistence
│       ├── notifier.py          # Alert system
│       └── logging_config.py    # Loki integration
├── scripts/                     # CLI scripts
│   ├── check_breaches.py        # Main check script
│   ├── setup_cron.sh            # Linux cron setup
│   ├── setup_windows_scheduler.ps1  # Windows Task Scheduler
│   └── run_breach_check.ps1     # Windows execution script
├── infra/                       # Docker configuration
│   ├── docker-compose.yml       # Service definitions
│   ├── Dockerfile.breach-monitor # Breach monitor image
│   └── migrations/              # Database migrations
├── config/                      # Configuration files
│   ├── identifiers.yml          # Identifiers to monitor
│   └── grafana-dashboard.json   # Grafana dashboard
├── docs/                        # Documentation
│   ├── README.md                # This file
│   ├── CONFIGURATION.md          # Detailed configuration
│   ├── WINDOWS_SETUP.md          # Windows-specific setup
│   ├── dns-setup.md             # Pi-hole setup
│   └── runbook.txt              # Operational procedures
├── tests/                       # Test suite
└── data/                        # Data directory
    ├── breaches.db              # SQLite database
    └── breach_cache/            # Public breach cache
```

## Security Notes

- Never commit `.env` or `config/identifiers.yml` to git
- Store secrets in environment variables
- All containers run as non-root users
- Only necessary ports are exposed
- Breach metadata only (no raw credentials stored)

## Troubleshooting

### No breaches found

- Check HIBP API key is set (for email/username checking)
- Verify identifiers are correct in `config/identifiers.yml`
- Check logs: `docker-compose logs breach-monitor`

### Alerts not working

- Verify alert configuration in `.env`
- Check logs for alert errors
- Test email SMTP settings manually
- Verify Telegram bot token and chat ID

### Database errors

- Ensure `data/` directory is writable
- Check database URL in `.env`
- For SQLite: ensure path is correct
- For Postgres: verify connection settings

### Public breach database not updating

- Check `ENABLE_PUBLIC_BREACH_DB` is set to true
- Verify `PUBLIC_BREACH_CACHE_DIR` is writable
- Check network connectivity for downloading breach data
- Review logs for download errors

### Paste monitoring not working

- Verify `ENABLE_PASTE_MONITORING` is set to true
- Check `GITHUB_TOKEN` if using GitHub Gists (optional but recommended)
- Verify rate limits haven't been exceeded
- Check logs for API errors

### Risk scores seem incorrect

- Review risk scoring factors in logs
- Verify breach data includes all required fields
- Check that normalization is working correctly
- Review risk scorer configuration

### Aggregation issues

- Verify all fetchers are returning data in expected format
- Check normalizer is handling all source types
- Review aggregator logs for deduplication issues
- Ensure source identifiers are unique

## Related Services

- [Platform API](../../README.md) - Main integration layer
- [Security Service](../../security-service/README.md) - Security monitoring and threat detection
- [Monitoring Stack](../../monitoring/README.md) - Prometheus, Grafana, Alertmanager

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- Check `docs/runbook.txt` for operational procedures
- Review logs in Grafana/Loki
- Check application logs: `docker-compose logs breach-monitor`

