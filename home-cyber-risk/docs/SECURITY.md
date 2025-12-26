# Security Guide

## Sensitive Files

The following files contain sensitive information and must never be committed to git:

- `.env` - Contains API keys, passwords, and configuration secrets
- `config/identifiers.yml` - Contains your personal email addresses, usernames, and domains
- `data/` - Contains breach database and logs

All of these are already in `.gitignore`.

## File Permissions (Linux/Mac)

For additional security, restrict file permissions:

```bash
chmod 600 .env
chmod 600 config/identifiers.yml
chmod 700 data/
```

This ensures only the file owner can read/write these files.

## Windows Security

On Windows, use file properties to restrict access:
1. Right-click the file → Properties → Security
2. Remove unnecessary users/groups
3. Keep only your user account with read/write access

## What Gets Stored

### Breach Database

The system stores:
- Email addresses and usernames (for breach matching)
- Breach names and dates
- Data classes exposed (e.g., "Email addresses", "Passwords")
- Breach metadata from HIBP API

The system does NOT store:
- Passwords (never stored)
- Raw credential data
- Personal information beyond identifiers

### Logs

Logs may contain:
- Identifiers being checked
- Breach names detected
- Error messages
- Check timestamps

Logs are sent to Loki (if configured) and stored locally in `data/` directory.

## Data Retention

- Breach records: Kept indefinitely (manual cleanup required)
- Check history: Kept indefinitely (manual cleanup required)
- Logs: Retained per Loki configuration (default: 30 days)

## Backup Considerations

When backing up:
- Exclude `.env` and `config/identifiers.yml` from backups unless encrypted
- Encrypt backups containing sensitive data
- Store backups securely (encrypted storage, access controls)

## API Keys

- HIBP API key: Optional, only needed for email/username checking
- Store in `.env` file, never hardcode
- Rotate keys periodically
- Use different keys for different environments if applicable

## Network Security

- All services run on internal Docker network by default
- Grafana UI (port 3000) should only be accessible on local network
- Pi-hole (port 80) should only be accessible on local network
- No external ports exposed by default

## Best Practices

1. Review `.gitignore` before committing
2. Use `git status` to verify sensitive files aren't staged
3. Never share `.env` or `config/identifiers.yml` files
4. Use strong passwords for database (if using Postgres)
5. Regularly review breach data and clean up old records
6. Monitor logs for suspicious activity
7. Keep dependencies updated for security patches

