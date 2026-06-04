# Grafana Password Reset Guide

## Why the Default Password Doesn't Work

Grafana only uses the `GF_SECURITY_ADMIN_PASSWORD` environment variable **on the first startup** when the database is empty. Once Grafana has been initialized, it stores the password in its database and ignores the environment variable.

If Grafana was already set up, the password may have been changed from the default.

## Solution 1: Reset via Docker Exec (Recommended)

Reset the password directly in the running container:

```bash
# Reset password to "admin"
docker exec -it platform-grafana grafana-cli admin reset-admin-password admin

# Or set a new password
docker exec -it platform-grafana grafana-cli admin reset-admin-password your-new-password
```

## Solution 2: Reset via SQL (If CLI doesn't work)

Access the Grafana database and reset the password:

```bash
# Access Grafana container
docker exec -it platform-grafana bash

# Access SQLite database (Grafana uses SQLite by default)
sqlite3 /var/lib/grafana/grafana.db

# Reset password (default is "admin") — example bcrypt hash only, not a live credential
UPDATE user SET password = '<grafana-bcrypt-hash-for-admin>' WHERE login = 'admin';
# Generate with: grafana-cli admin reset-admin-password admin (preferred) or official Grafana hash docs

# Exit SQLite
.exit

# Exit container
exit
```

**Note**: The hash above is for password "admin". For a different password, you'll need to generate the hash.

## Solution 3: Fresh Start (Nuclear Option)

If you want to completely reset Grafana (this will delete all dashboards and settings):

```bash
# Stop Grafana
docker-compose stop grafana

# Remove Grafana volume
docker volume rm software_grafana_data

# Or if using named volume:
docker volume rm platform-grafana_data

# Restart Grafana (will use default password from env)
docker-compose up -d grafana
```

## Solution 4: Check Current Password

If you're not sure what the password is, you can check Grafana logs:

```bash
# View Grafana logs
docker logs platform-grafana

# Look for any password-related messages or check if it was changed
```

## Verify Password Reset

After resetting, test the login:

```bash
# Test login via API
curl -X POST http://localhost:3001/api/login \
  -H "Content-Type: application/json" \
  -d '{"user":"admin","password":"admin"}'
```

## Update Documentation

After resetting, update your `.env` file if you're using a different password, and update the docker-compose.yml if needed:

```yaml
environment:
  - GF_SECURITY_ADMIN_USER=admin
  - GF_SECURITY_ADMIN_PASSWORD=your-actual-password
```

**Note**: Remember, this env var only works on first startup. For existing installations, use Solution 1 or 2.

## Prevention

To avoid this issue in the future:

1. **Document the actual password** you set when first configuring Grafana
2. **Use a password manager** to store Grafana credentials
3. **Set up API keys** for programmatic access instead of using passwords
4. **Use environment-specific passwords** in your `.env` file and document them

## See Also

- [Grafana Admin CLI Documentation](https://grafana.com/docs/grafana/latest/administration/cli/)
- [Grafana Password Reset](https://grafana.com/docs/grafana/latest/administration/user-management/manage-users/#reset-admin-password)
