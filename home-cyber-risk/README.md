# Home Cyber Risk Awareness Server

A simple, achievable home cyber risk awareness server that monitors breach exposure for personal identifiers, provides DNS-level protection, and offers lightweight observability.

## Quick Start

1. Copy configuration files:
   ```bash
   cp .env.example .env
   cp config/identifiers.yml.example config/identifiers.yml
   ```

2. Edit `config/identifiers.yml` with your identifiers

3. Edit `.env` with your configuration (HIBP API key, alert settings)

4. Start services:
   ```bash
   cd infra
   docker-compose up -d
   ```

5. Run manual check:
   ```bash
   python scripts/check_breaches.py
   ```

See `docs/README.md` for detailed documentation.

## Features

- **Multi-source breach detection:**
  - Have I Been Pwned (HIBP) API (optional API key for email/username)
  - Public breach databases (free, local cache)
  - Paste site monitoring (Pastebin, GitHub Gists)
- **Free password checking** (HIBP Pwned Passwords, no API key required)
- **Risk scoring and prioritization** (Critical/High/Medium/Low)
- **Multi-source aggregation** with deduplication
- **Breach differencing** (new vs updated breaches)
- Multiple alert channels (Email, Telegram, Webhook, Log)
- Lightweight observability (Grafana + Loki)
- Optional Pi-hole DNS protection
- SQLite by default (PostgreSQL optional)
- **Platform integration** - Can integrate with main platform API

## Project Structure

- `services/breach_monitor/` - Core breach monitoring service
- `scripts/` - CLI scripts and utilities
- `infra/` - Docker configuration
- `config/` - Configuration files
- `docs/` - Documentation
- `tests/` - Test suite
- `data/` - Data directory (SQLite DB, logs)

## Documentation

- `docs/README.md` - Full documentation
- `docs/runbook.txt` - Operational procedures
- `docs/dns-setup.md` - Pi-hole setup guide

## License

MIT License

