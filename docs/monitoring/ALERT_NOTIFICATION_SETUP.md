# Alert Notification Setup Guide

## Overview

This guide walks you through configuring Alertmanager to send notifications via email and optional Slack webhooks when alerts fire.

## Prerequisites

- Alertmanager deployed and running
- Access to Alertmanager configuration file: `monitoring/alertmanager/alertmanager.yml`
- Email account for sending alerts (Gmail, Office365, or custom SMTP)
- Optional: Slack workspace for webhook integration

## Email Configuration

### Option 1: Gmail Setup

Gmail requires an App Password for SMTP authentication.

#### Step 1: Create Gmail App Password

1. Go to your Google Account: https://myaccount.google.com
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Go to **App passwords**
4. Select **Mail** and **Other (Custom name)**
5. Enter "Alertmanager" as the name
6. Click **Generate**
7. Copy the 16-character password (you'll need this)

#### Step 2: Configure Alertmanager

Edit `monitoring/alertmanager/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'your-email@gmail.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-16-char-app-password'
  smtp_require_tls: true
```

#### Step 3: Update Receivers

Update the email addresses in receivers:

```yaml
receivers:
  - name: 'default'
    email_configs:
      - to: 'your-alert-email@gmail.com'
        headers:
          Subject: 'Platform Alert: {{ .GroupLabels.alertname }}'
        html: '{{ template "email.default.html" . }}'
        send_resolved: true
```

#### Step 4: Restart Alertmanager

```bash
docker-compose restart alertmanager
```

### Option 2: Office365 Setup

#### Step 1: Get Office365 SMTP Settings

- SMTP Server: `smtp.office365.com`
- Port: `587`
- Authentication: Required
- TLS/SSL: Required

#### Step 2: Configure Alertmanager

```yaml
global:
  smtp_smarthost: 'smtp.office365.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'alerts@yourdomain.com'
  smtp_auth_password: 'your-office365-password'
  smtp_require_tls: true
```

**Note**: If using MFA, you may need an App Password similar to Gmail.

### Option 3: Custom SMTP Server

#### Step 1: Gather SMTP Information

You'll need:
- SMTP server hostname
- Port (usually 587 for TLS, 465 for SSL, 25 for unencrypted)
- Username
- Password
- From email address

#### Step 2: Configure Alertmanager

```yaml
global:
  smtp_smarthost: 'smtp.yourdomain.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'alerts@yourdomain.com'
  smtp_auth_password: 'your-smtp-password'
  smtp_require_tls: true  # Set to false if using port 25
```

### Using Environment Variables (Recommended)

For security, use environment variables instead of hardcoding passwords:

#### Step 1: Update docker-compose.yml

```yaml
alertmanager:
  environment:
    - SMTP_HOST=smtp.gmail.com
    - SMTP_PORT=587
    - SMTP_FROM=your-email@gmail.com
    - SMTP_USER=your-email@gmail.com
    - SMTP_PASSWORD=${SMTP_PASSWORD}
```

#### Step 2: Update Alertmanager Config

```yaml
global:
  smtp_smarthost: '${SMTP_HOST}:${SMTP_PORT}'
  smtp_from: '${SMTP_FROM}'
  smtp_auth_username: '${SMTP_USER}'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true
```

#### Step 3: Set Environment Variable

In your `.env` file:
```bash
SMTP_PASSWORD=your-app-password-here
```

## Slack Integration (Optional)

### Step 1: Create Slack Webhook

1. Go to your Slack workspace
2. Navigate to **Apps** → **Incoming Webhooks**
3. Click **Add to Slack**
4. Choose a channel (e.g., #alerts)
5. Click **Add Incoming Webhooks Integration**
6. Copy the Webhook URL

### Step 2: Configure Alertmanager

Add Slack webhook to receivers:

```yaml
receivers:
  - name: 'critical'
    email_configs:
      - to: 'oncall@example.com'
        headers:
          Subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        html: '{{ template "email.critical.html" . }}'
        send_resolved: true
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: 'CRITICAL Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        send_resolved: true
```

### Step 3: Test Slack Integration

Use the test script (see Testing section below).

## Testing Alert Notifications

### Method 1: Using Test Script

Create and run `scripts/monitoring/test-alert-notification.ps1`:

```powershell
# Test email notification
.\scripts\monitoring\test-alert-notification.ps1 -Type email -Email "your-email@example.com"

# Test Slack notification
.\scripts\monitoring\test-alert-notification.ps1 -Type slack
```

### Method 2: Trigger Test Alert

1. Temporarily lower an alert threshold in `prometheus/alert_rules.yml`
2. Wait for alert to fire
3. Verify notification received
4. Restore original threshold

### Method 3: Use Alertmanager API

```powershell
# Send test alert via API
$body = @{
    labels = @{
        alertname = "TestAlert"
        severity = "warning"
    }
    annotations = @{
        summary = "This is a test alert"
        description = "Testing alert notification delivery"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:9093/api/v1/alerts" -Method Post -Body $body -ContentType "application/json"
```

## Verification

### Check Alertmanager Status

1. Open Alertmanager UI: http://localhost:9093
2. Go to **Status** → **Configuration**
3. Verify your configuration is loaded correctly
4. Check for any configuration errors

### Check Alert Logs

```bash
# View Alertmanager logs
docker logs platform-alertmanager

# Look for SMTP connection messages
docker logs platform-alertmanager | grep -i smtp
```

### Verify Email Delivery

1. Trigger a test alert
2. Check your email inbox (and spam folder)
3. Verify email contains alert details
4. Check for any bounce messages

## Troubleshooting

### Email Not Sending

**Problem**: Alerts not received via email

**Solutions**:
1. **Check SMTP credentials**
   - Verify username and password are correct
   - For Gmail, ensure you're using App Password, not regular password
   - Test SMTP connection manually

2. **Check firewall/network**
   - Ensure port 587 (or your SMTP port) is not blocked
   - Test SMTP connection: `telnet smtp.gmail.com 587`

3. **Check Alertmanager logs**
   ```bash
   docker logs platform-alertmanager | grep -i error
   ```

4. **Verify configuration syntax**
   ```bash
   docker exec platform-alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
   ```

5. **Test SMTP connection manually**
   ```powershell
   # Test Gmail SMTP
   $smtp = New-Object System.Net.Mail.SmtpClient("smtp.gmail.com", 587)
   $smtp.EnableSsl = $true
   $smtp.Credentials = New-Object System.Net.NetworkCredential("your-email@gmail.com", "your-app-password")
   $smtp.Send("from@example.com", "to@example.com", "Test", "Test message")
   ```

### Slack Not Working

**Problem**: Slack notifications not received

**Solutions**:
1. **Verify webhook URL**
   - Ensure URL is complete and correct
   - Check webhook is still active in Slack

2. **Check Alertmanager logs**
   ```bash
   docker logs platform-alertmanager | grep -i slack
   ```

3. **Test webhook directly**
   ```powershell
   $body = @{ text = "Test message" } | ConvertTo-Json
   Invoke-RestMethod -Uri "YOUR_WEBHOOK_URL" -Method Post -Body $body -ContentType "application/json"
   ```

### Alerts Firing But No Notifications

**Problem**: Alerts appear in Prometheus but no notifications sent

**Solutions**:
1. **Check Alertmanager is receiving alerts**
   - Open Alertmanager UI: http://localhost:9093
   - Go to **Alerts** tab
   - Verify alerts are listed

2. **Check routing rules**
   - Verify alert labels match route matchers
   - Check receiver names are correct

3. **Check inhibition rules**
   - Verify alerts aren't being inhibited
   - Review inhibition rule logic

4. **Check group_wait and repeat_interval**
   - Alerts may be grouped and waiting
   - Check group_wait time has passed

## Best Practices

### 1. Use Environment Variables

Never hardcode passwords in configuration files. Use environment variables:

```yaml
# In alertmanager.yml
smtp_auth_password: '${SMTP_PASSWORD}'

# In docker-compose.yml
environment:
  - SMTP_PASSWORD=${SMTP_PASSWORD}

# In .env file
SMTP_PASSWORD=your-secure-password
```

### 2. Separate Receivers by Severity

```yaml
receivers:
  - name: 'critical'
    # Immediate notification, multiple channels
  - name: 'warning'
    # Less urgent, email only
  - name: 'info'
    # Low priority, daily digest
```

### 3. Configure Alert Grouping

```yaml
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s      # Wait before sending first alert in group
  group_interval: 10s  # Wait before sending updated alerts
  repeat_interval: 12h # Wait before repeating same alert
```

### 4. Set Appropriate Repeat Intervals

- **Critical**: 1 hour (don't spam, but ensure visibility)
- **Warning**: 6 hours
- **Info**: 24 hours

### 5. Use Inhibition Rules

Prevent alert spam:

```yaml
inhibit_rules:
  # If node is down, don't alert on all services
  - source_match:
      alertname: 'NodeDown'
    target_match_re:
      alertname: '.*'
    equal: ['instance']
```

### 6. Test Regularly

- Test alert delivery monthly
- Verify email addresses are current
- Check Slack webhooks are active
- Review and update alert thresholds

## Configuration Examples

### Complete Gmail Configuration

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'alerts@yourdomain.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true

route:
  receiver: 'default'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      repeat_interval: 1h
    - match:
        severity: warning
      receiver: 'warning'
      repeat_interval: 6h

receivers:
  - name: 'default'
    email_configs:
      - to: 'admin@yourdomain.com'
        send_resolved: true
  
  - name: 'critical'
    email_configs:
      - to: 'oncall@yourdomain.com'
        headers:
          Subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        send_resolved: true
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts'
        send_resolved: true
  
  - name: 'warning'
    email_configs:
      - to: 'admin@yourdomain.com'
        headers:
          Subject: 'WARNING: {{ .GroupLabels.alertname }}'
        send_resolved: true
```

### Office365 Configuration

```yaml
global:
  smtp_smarthost: 'smtp.office365.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'alerts@yourdomain.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true
```

### Custom SMTP with Authentication

```yaml
global:
  smtp_smarthost: 'mail.yourdomain.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'alerts@yourdomain.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true
  smtp_hello: 'alertmanager.yourdomain.com'
```

## Security Considerations

1. **Never commit passwords** to version control
2. **Use App Passwords** for Gmail/Office365
3. **Rotate passwords** regularly
4. **Use environment variables** for sensitive data
5. **Restrict Alertmanager access** (firewall rules)
6. **Use TLS** for SMTP connections
7. **Monitor alert logs** for suspicious activity

## Maintenance

### Regular Tasks

- **Monthly**: Test alert delivery
- **Quarterly**: Review and update email addresses
- **Quarterly**: Review alert thresholds and routing
- **Annually**: Rotate SMTP passwords

### Monitoring Alertmanager

Monitor Alertmanager itself:

- Alertmanager uptime
- Configuration reload success
- Notification delivery success rate
- Failed notification attempts

## See Also

- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Monitoring README](../../monitoring/README.md)
- [Monitoring Expansion Guide](MONITORING_EXPANSION_GUIDE.md)
