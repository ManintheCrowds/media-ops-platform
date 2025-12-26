# Breach Intake and Reporting System Guide

## Overview

The breach intake system allows you to securely submit data (emails, passwords, domains) for comprehensive breach analysis using **free** breach detection services. The system uses:
- **HIBP Pwned Passwords API** (free, no API key required) for password checking
- **Public breach sources** (free) for email and domain checking

The system generates actionable reports with risk assessments, compliance impact, and prioritized recommendations.

## Quick Start

### 1. Configure Environment Variables

Create a `.env` file in the project root (or copy from `.env.example`):

```bash
# Enable features (all free, no API key required)
SECURITY_HIBP_ENABLE_PASSWORD_CHECK=true  # Uses free HIBP Pwned Passwords API
SECURITY_HIBP_ENABLE_EMAIL_CHECK=true  # Uses free public breach sources

# Optional: Domain monitoring
SECURITY_BREACH_MONITORED_DOMAINS=example.com,yourcompany.com

# Optional: Public breach sources (GitHub repos, JSON/CSV URLs)
# SECURITY_PUBLIC_BREACH_SOURCES=https://raw.githubusercontent.com/user/repo/breaches.json
```

### 2. Configure Public Breach Sources

The system uses free public breach sources for email/domain checking. Configure sources in your `.env` file:

```bash
# Public Breach Sources (comma-separated URLs)
# Supported formats: GitHub raw URLs, JSON endpoints, CSV files
SECURITY_PUBLIC_BREACH_SOURCES=https://raw.githubusercontent.com/user/repo/breaches.json
```

**Supported Formats:**
- **JSON**: `{"breaches": [{"email": "...", "breach_name": "...", "breach_date": "..."}]}`
- **CSV**: `email,breach_name,breach_date`
- **Text**: One email address per line

**Initial Database Population:**

After configuring sources, populate the database:

```bash
# Via API
POST /api/security/breaches/update-database?force=true

# Or via script
python scripts/populate_breach_database.py
```

**Note:** Password checking uses the free HIBP Pwned Passwords API (no configuration needed).

### 3. Submit Data for Analysis

#### Using the API Endpoint

```bash
POST /api/security/breaches/intake
Content-Type: application/json

{
  "emails": ["user1@example.com", "user2@example.com"],
  "passwords": ["password1", "password2"],  # Optional
  "domains": ["example.com"],  # Optional
  "user_ids": {"user1@example.com": 1},  # Optional mapping
  "metadata": {"source": "manual_check", "reason": "security_audit"}
}
```

#### Using Python

```python
import httpx
import asyncio

async def check_breaches():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/security/breaches/intake",
            json={
                "emails": ["test@example.com"],
                "passwords": ["mypassword123"],  # Will be hashed immediately
                "domains": ["example.com"]
            }
        )
        return response.json()

# Run
results = asyncio.run(check_breaches())
print(results)
```

### 4. Generate Comprehensive Report

For detailed analysis with actionable insights:

```bash
POST /api/security/breaches/comprehensive-report
Content-Type: application/json

{
  "emails": ["user@example.com"],
  "passwords": ["password123"],
  "domains": ["example.com"]
}
```

## Report Structure

### Standard Intake Response

```json
{
  "processed_at": "2025-01-XX...",
  "source": "api",
  "summary": {
    "emails_checked": 2,
    "emails_breached": 1,
    "passwords_checked": 1,
    "passwords_breached": 1,
    "domains_checked": 1,
    "domains_breached": 0
  },
  "email_results": [...],
  "password_results": [...],
  "domain_results": [...],
  "recommendations": [...],
  "risk_score": 75
}
```

### Comprehensive Report Response

Includes all of the above plus:

- **Executive Summary**: High-level overview and risk assessment
- **Detailed Findings**: Deep analysis of each category
- **Risk Assessment**: Comprehensive risk scoring and factors
- **Action Plan**: Prioritized actions with timelines
- **Trend Analysis**: Historical context and comparisons
- **Compliance Impact**: GDPR, CCPA, HIPAA, PCI-DSS assessments
- **Detailed Recommendations**: Prioritized, actionable recommendations

## Security Features

### Password Handling

- Passwords are **never stored** in plain text
- Passwords are hashed (SHA-1) immediately for checking
- Only hash prefixes sent to HIBP Pwned Passwords API (k-anonymity model)
- Passwords removed from memory after processing

### Data Privacy

- Email addresses checked against local breach database (downloaded from public sources)
- Breach data cached securely in database
- All API calls respect rate limits
- Fail-safe design (doesn't break if service unavailable)
- No external API calls for email checking (uses local database)

## Use Cases

### 1. User Registration Security

Check emails and passwords during registration:

```python
intake_data = {
    "emails": [new_user_email],
    "passwords": [new_user_password]
}

results = await intake_service.process_intake(intake_data)

if results["summary"]["passwords_breached"] > 0:
    # Reject registration
    raise ValueError("Password found in breach database")
```

### 2. Security Audit

Batch check multiple accounts:

```python
intake_data = {
    "emails": ["user1@example.com", "user2@example.com", ...],
    "domains": ["example.com"]
}

report = await comprehensive_reporter.generate_report(intake_data)
# Review report["action_plan"] and report["recommendations"]
```

### 3. Incident Response

When a breach is suspected:

```python
intake_data = {
    "emails": affected_emails,
    "passwords": suspected_passwords,  # If available
    "metadata": {"incident_id": "INC-12345"}
}

results = await intake_service.process_intake(intake_data)
# Use risk_score and recommendations for response
```

### 4. Compliance Reporting

Generate compliance-ready reports:

```python
report = await comprehensive_reporter.generate_report(intake_data)

# Check compliance impact
gdpr_impact = report["compliance_impact"]["gdpr_impact"]
if gdpr_impact.get("breach_notification_required"):
    # Trigger GDPR notification process
    notify_gdpr_authorities(gdpr_impact)
```

## Risk Scoring

The system calculates a risk score (0-100) based on:

- **Email Breaches**: 5-30 points per breach (based on data exposed)
- **Password Breaches**: 25 points per breached password
- **Domain Breaches**: 2 points per affected email (capped at 50)

**Risk Levels:**
- 0-24: LOW
- 25-49: MEDIUM
- 50-74: HIGH
- 75-100: CRITICAL

## Action Plans

Reports include prioritized action plans:

### Immediate Actions (Critical Risk)
- Force password resets
- Enable enhanced monitoring
- User notifications

### Short-Term Actions (High Risk)
- Security posture review
- Organizational security audit
- Enhanced controls

### Long-Term Actions
- Continuous monitoring setup
- Security awareness training
- Policy updates

## Best Practices

1. **Regular Monitoring**: Schedule periodic checks for all users
2. **Batch Processing**: Group requests to respect rate limits
3. **Cache Results**: Use cached data when possible (1 hour TTL)
4. **Error Handling**: Always handle service unavailability gracefully
5. **Privacy**: Never log or store plain-text passwords
6. **Notifications**: Implement user notification workflows
7. **Documentation**: Keep records of all breach findings

## Troubleshooting

### Breach Database Issues

**Error:** "No breach data available"
- Ensure public breach sources are configured
- Run breach database update: The system will download breach data automatically
- Check `SECURITY_BREACH_DATA_CACHE_DIR` is writable

### Rate Limiting

**Error:** "Rate limit exceeded"
- Increase delay between requests
- Reduce batch sizes
- Use cached results when possible

### Service Unavailable

**Error:** "HIBP request failed"
- Check network connectivity
- Verify HIBP API status
- Service fails open (doesn't block operations)

## Example Workflow

```python
# 1. Intake data
intake_data = {
    "emails": ["user@example.com"],
    "passwords": ["password123"],
    "domains": ["example.com"]
}

# 2. Process intake
intake_service = BreachIntakeService(db)
results = await intake_service.process_intake(intake_data)

# 3. Check risk level
if results["risk_score"] >= 75:
    # 4. Generate comprehensive report
    reporter = ComprehensiveBreachReporter(db)
    report = reporter.generate_report(results)
    
    # 5. Execute action plan
    for action in report["action_plan"]["immediate_actions"]:
        execute_action(action)
    
    # 6. Notify stakeholders
    notify_security_team(report["executive_summary"])
```

## API Reference

See [HIBP Integration Guide](./HIBP_INTEGRATION.md) for detailed API documentation.

## Support

For issues or questions:
1. Check [HIBP Integration Guide](./HIBP_INTEGRATION.md)
2. Review [Security Framework](./SECURITY_FRAMEWORK.md)
3. Check application logs for detailed error messages

