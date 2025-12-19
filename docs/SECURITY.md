# Security Guide

## Security Overview

This document outlines security best practices, configuration, and procedures for the Self-Hosted Platform Integration system.

## Critical Security Requirements

### 1. Change Default Secrets

**MUST be done before production deployment:**

- [ ] Generate new `SECRET_KEY`
- [ ] Generate new `JWT_SECRET_KEY`
- [ ] Change all service default passwords
- [ ] Update database passwords
- [ ] Configure service API tokens

### 2. Environment Variables Security

**Never commit `.env` file to version control!**

The `.env` file contains sensitive information:
- Database credentials
- API keys and tokens
- Secret keys
- Service passwords

**Best Practices:**
- Use `.env.example` as template
- Add `.env` to `.gitignore`
- Use secrets management in production
- Rotate secrets regularly

## Authentication Security

### JWT Token Security

**Configuration:**
```python
# app/config.py
JWT_SECRET_KEY = "change-me-in-production-jwt-secret"  # MUST CHANGE
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30
```

**Best Practices:**
1. Use strong, random secret keys (minimum 32 characters)
2. Set appropriate expiration times
3. Implement token refresh mechanism (future enhancement)
4. Validate tokens on every request
5. Invalidate tokens on logout (future enhancement)

**Generating Secure Keys:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Password Security

**Hashing:**
- Uses bcrypt with automatic salt
- Minimum 12 rounds (configurable)
- Passwords never stored in plain text

**Password Policy (Recommended):**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Not in common password lists
- Unique per user

**Implementation:**
```python
from app.auth.oauth2 import get_password_hash, verify_password

# Hashing
hashed = get_password_hash("user_password")

# Verification
is_valid = verify_password("user_password", hashed)
```

## Authorization Security

### Role-Based Access Control

**User Roles:**
- **Regular User**: Can access services via gateway
- **Admin**: Can manage services, view all data

**Admin-Only Endpoints:**
- `POST /api/services` - Create service
- `PUT /api/services/{id}` - Update service
- `DELETE /api/services/{id}` - Delete service
- `GET /api/gateway/security/stats` - Security statistics

**Implementation:**
```python
if not current_user.is_admin:
    raise HTTPException(status_code=403, detail="Admin access required")
```

### Token Validation

**Every protected endpoint:**
1. Validates token signature
2. Checks token expiration
3. Verifies user exists and is active
4. Loads user permissions

## Input Validation

### SQL Injection Prevention

**Protected by:**
- SQLAlchemy ORM (parameterized queries)
- No raw SQL queries
- Input validation

**Example:**
```python
# Safe - SQLAlchemy handles parameterization
user = db.query(User).filter(User.username == username).first()

# Never do this:
# db.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### XSS Prevention

**Frontend Responsibility:**
- Escape user input in templates
- Use Content Security Policy
- Validate and sanitize HTML

**Backend:**
- Store data as-is (no HTML rendering)
- Validate input format
- Return JSON (not HTML)

### Path Traversal Prevention

**Service URL Validation:**
- Validate URL format
- Reject non-HTTP(S) URLs
- Sanitize paths

**Example:**
```python
from urllib.parse import urlparse

def validate_service_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and parsed.netloc
```

## Network Security

### CORS Configuration

**Production Configuration:**
```python
# app/config.py
CORS_ORIGINS = ["https://yourdomain.com"]  # Specific domains
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]
```

**Development:**
```python
CORS_ORIGINS = ["*"]  # Allow all (development only)
```

### HTTPS/TLS

**Required for Production:**
1. Obtain SSL/TLS certificates (Let's Encrypt recommended)
2. Configure Nginx/Traefik for HTTPS
3. Redirect HTTP to HTTPS
4. Use HSTS headers

**Nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
}
```

### Firewall Configuration

**Recommended Rules:**
- Allow: 80 (HTTP), 443 (HTTPS)
- Block: All other ports
- Restrict service ports to internal network
- Use fail2ban for brute force protection

## Data Security

### Database Security

**PostgreSQL Configuration:**
```sql
-- Strong password required
ALTER USER platform WITH PASSWORD 'strong-password';

-- Limit connections
ALTER USER platform WITH CONNECTION LIMIT 50;

-- Revoke unnecessary privileges
REVOKE ALL ON DATABASE platform FROM PUBLIC;
```

**Connection Security:**
- Use SSL for database connections
- Restrict database access to application only
- Regular backups with encryption
- Access logging enabled

### Service Token Storage

**Current Implementation:**
- Tokens stored in database (plain text)
- Access restricted to admin users
- Not exposed in API responses

**Future Enhancements:**
- Encrypt tokens at rest
- Use secrets management service
- Token rotation mechanism

## Security Headers

### Recommended Headers

```python
# In FastAPI middleware or Nginx
headers = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

## Rate Limiting

**Current Status:** Not implemented

**Recommended Implementation:**
- Use slowapi or similar
- Limit by IP address
- Different limits for different endpoints
- Exempt admin users

**Example:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/auth/token")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Implementation
```

## Security Monitoring

### Logging

**Security Events to Log:**
- Failed login attempts
- Admin actions
- Service registration/deletion
- Unauthorized access attempts
- Token validation failures

**Example:**
```python
import logging

security_logger = logging.getLogger("security")

# Log failed login
security_logger.warning(f"Failed login attempt for username: {username}")
```

### Audit Trail

**Track:**
- User registrations
- Service changes
- Admin actions
- Configuration changes

**Implementation:**
- Add audit log table
- Log all admin operations
- Regular audit reviews

## Vulnerability Management

### Dependency Scanning

**Tools:**
- `safety` - Check for known vulnerabilities
- `bandit` - Python security linter
- `snyk` - Comprehensive scanning

**Regular Checks:**
```bash
# Check dependencies
safety check

# Security linting
bandit -r app services

# Update dependencies
pip list --outdated
pip install --upgrade <package>
```

### Security Updates

**Process:**
1. Monitor security advisories
2. Test updates in development
3. Apply patches promptly
4. Document changes
5. Verify after update

## Incident Response

### Security Incident Procedure

1. **Identify:** Detect security issue
2. **Contain:** Isolate affected systems
3. **Assess:** Evaluate impact
4. **Remediate:** Fix vulnerability
5. **Document:** Record incident
6. **Notify:** Inform stakeholders (if required)
7. **Review:** Post-incident analysis

### Reporting Vulnerabilities

**If you discover a security vulnerability:**
1. Do not disclose publicly
2. Report to maintainers privately
3. Provide detailed information
4. Allow time for fix before disclosure

## Security Checklist

### Pre-Deployment

- [ ] All default secrets changed
- [ ] Strong passwords configured
- [ ] HTTPS/TLS configured
- [ ] Firewall rules set
- [ ] CORS properly configured
- [ ] Database secured
- [ ] Security headers enabled
- [ ] Logging configured
- [ ] Backup strategy in place
- [ ] Monitoring enabled

### Ongoing Maintenance

- [ ] Regular security updates
- [ ] Dependency scanning
- [ ] Log review
- [ ] Access audit
- [ ] Backup verification
- [ ] Security testing
- [ ] Documentation updates

## Security Best Practices Summary

1. **Never commit secrets** to version control
2. **Use HTTPS** in production
3. **Validate all inputs** from users
4. **Use parameterized queries** (SQLAlchemy does this)
5. **Implement rate limiting** for API endpoints
6. **Regular security updates** for dependencies
7. **Monitor and log** security events
8. **Use strong passwords** and keys
9. **Restrict access** to admin functions
10. **Regular security audits**

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security](https://python.readthedocs.io/en/stable/library/security.html)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
