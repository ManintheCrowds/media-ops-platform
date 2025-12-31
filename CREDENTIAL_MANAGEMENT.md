# Credential Management Guide

This document outlines best practices for managing credentials and secrets in the platform.

## Overview

All sensitive credentials (API keys, passwords, tokens) must be stored securely and never committed to version control. This guide covers:

- Local development setup (`.env` files)
- Production deployment (secrets managers)
- Security best practices

## Local Development

### Using .env Files

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your actual credentials:**
   ```bash
   # Edit .env with your actual values
   nano .env  # or use your preferred editor
   ```

3. **Verify .env is in .gitignore:**
   ```bash
   # Check that .env is excluded
   git check-ignore .env
   ```

### Service-Specific .env Files

Each service may have its own `.env.example` file:

- **Main Platform**: `D:\software\.env.example`
- **Job Automation Service**: `D:\software\job-automation-service\.env.example`
- **Education Service**: `D:\software\education-service\.env.example`

### Required Credentials

#### Main Platform
- `SECRET_KEY` - Flask secret key (min 32 chars)
- `JWT_SECRET_KEY` - JWT signing key (min 32 chars)
- `DATABASE_URL` - PostgreSQL connection string
- `ARLO_USERNAME` - Arlo camera account email (if using)
- `ARLO_PASSWORD` - Arlo camera account password (if using)
- `NOTIFICATION_EMAIL` - Email for notifications

#### Job Automation Service
- `ADZUNA_API_ID` - Adzuna API ID
- `ADZUNA_API_KEY` - Adzuna API key
- `JSEARCH_API_KEY` - JSearch API key
- `DATABASE_URL` - PostgreSQL connection string
- `OLLAMA_URL` - Ollama service URL (default: http://localhost:11434)

### Generating Secure Keys

**Python:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**PowerShell:**
```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

**Bash:**
```bash
openssl rand -base64 32
```

## Production Deployment

### Option 1: Docker Secrets (Recommended for Docker Swarm)

1. **Create secrets:**
   ```bash
   echo "your-secret-key" | docker secret create secret_key -
   echo "your-jwt-secret" | docker secret create jwt_secret -
   ```

2. **Use in docker-compose:**
   ```yaml
   services:
     app:
       secrets:
         - secret_key
         - jwt_secret
   secrets:
     secret_key:
       external: true
     jwt_secret:
       external: true
   ```

### Option 2: HashiCorp Vault

1. **Install and start Vault:**
   ```bash
   vault server -dev
   ```

2. **Store secrets:**
   ```bash
   vault kv put secret/platform secret_key="your-key" jwt_secret="your-jwt"
   ```

3. **Access in application:**
   ```python
   import hvac
   client = hvac.Client(url='http://localhost:8200')
   secret = client.secrets.kv.v2.read_secret_version(path='platform')
   ```

### Option 3: AWS Secrets Manager

1. **Store secrets:**
   ```bash
   aws secretsmanager create-secret \
     --name platform/credentials \
     --secret-string '{"SECRET_KEY":"your-key","JWT_SECRET":"your-jwt"}'
   ```

2. **Access in application:**
   ```python
   import boto3
   client = boto3.client('secretsmanager')
   secret = client.get_secret_value(SecretId='platform/credentials')
   ```

### Option 4: Kubernetes Secrets

1. **Create secret:**
   ```bash
   kubectl create secret generic platform-secrets \
     --from-literal=SECRET_KEY=your-key \
     --from-literal=JWT_SECRET=your-jwt
   ```

2. **Use in deployment:**
   ```yaml
   env:
     - name: SECRET_KEY
       valueFrom:
         secretKeyRef:
           name: platform-secrets
           key: SECRET_KEY
   ```

## Security Best Practices

### ✅ DO

- Use `.env` files for local development
- Store `.env` files in `.gitignore`
- Use strong, randomly generated keys (min 32 characters)
- Rotate credentials regularly
- Use different credentials for dev/staging/production
- Use secrets managers in production
- Encrypt secrets at rest
- Limit access to secrets (principle of least privilege)
- Audit secret access logs

### ❌ DON'T

- Commit `.env` files to version control
- Hardcode credentials in source code
- Share credentials via email/chat
- Use weak or predictable passwords
- Reuse credentials across environments
- Log secrets in application logs
- Store secrets in client-side code
- Commit example files with real credentials

## Rotating Compromised Credentials

If credentials are exposed:

1. **Immediately rotate the compromised credential:**
   ```bash
   # Generate new key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Update all environments:**
   - Update `.env` files locally
   - Update production secrets manager
   - Update CI/CD pipeline secrets

3. **Review access logs:**
   - Check for unauthorized access
   - Review recent API usage
   - Check database access logs

4. **Update dependent services:**
   - Update all services using the credential
   - Restart services to load new credentials
   - Verify services are functioning

## Environment-Specific Configuration

### Development
- Use `.env` files
- Can use weaker security (for testing)
- Local database OK

### Staging
- Use secrets manager
- Mirror production security
- Separate database

### Production
- **MUST** use secrets manager
- Strong encryption
- Regular rotation
- Access logging
- Backup/restore procedures

## Troubleshooting

### .env file not loading

1. **Check file location:**
   ```bash
   # Should be in service root directory
   ls -la .env
   ```

2. **Check file permissions:**
   ```bash
   chmod 600 .env  # Restrict access
   ```

3. **Verify .env syntax:**
   ```bash
   # No spaces around =
   KEY=value  # ✅ Correct
   KEY = value  # ❌ Wrong
   ```

### Secrets not found in production

1. **Check secrets manager connection**
2. **Verify secret names match**
3. **Check IAM/permissions**
4. **Review application logs for errors**

## Additional Resources

- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_cryptographic_key)
- [12-Factor App: Config](https://12factor.net/config)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)

## Support

For issues with credential management:
1. Check this guide first
2. Review service-specific README
3. Check application logs
4. Contact platform administrator

