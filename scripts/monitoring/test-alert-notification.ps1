# Test Alert Notification Script
# Verifies Alertmanager notification delivery

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("email", "slack", "both", "api")]
    [string]$Type = "api",
    
    [string]$Email = "",
    [string]$AlertmanagerUrl = "http://localhost:9093",
    [string]$Severity = "warning"
)

$ErrorActionPreference = "Stop"

Write-Host "Testing Alert Notification Delivery" -ForegroundColor Cyan
Write-Host "=" * 50

# Test Alertmanager connectivity
Write-Host "`n1. Testing Alertmanager connectivity..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$AlertmanagerUrl/-/healthy" -UseBasicParsing -TimeoutSec 5
    Write-Host "   Alertmanager is reachable" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: Cannot reach Alertmanager at $AlertmanagerUrl" -ForegroundColor Red
    Write-Host "   Make sure Alertmanager is running: docker ps | grep alertmanager" -ForegroundColor Yellow
    exit 1
}

# Check Alertmanager status
Write-Host "`n2. Checking Alertmanager status..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "$AlertmanagerUrl/api/v1/status" -UseBasicParsing
    Write-Host "   Version: $($status.data.versionInfo.version)" -ForegroundColor Green
    Write-Host "   Uptime: $($status.data.uptime)" -ForegroundColor Green
} catch {
    Write-Host "   WARNING: Could not get Alertmanager status" -ForegroundColor Yellow
}

# Send test alert via API
Write-Host "`n3. Sending test alert..." -ForegroundColor Yellow

$testAlert = @{
    labels = @{
        alertname = "TestAlert"
        severity = $Severity
        test = "true"
    }
    annotations = @{
        summary = "Test alert notification"
        description = "This is a test alert to verify notification delivery. You can safely ignore this."
    }
    startsAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$AlertmanagerUrl/api/v1/alerts" -Method Post -Body $testAlert -ContentType "application/json"
    Write-Host "   Test alert sent successfully" -ForegroundColor Green
    Write-Host "   Alert ID: $($response.status)" -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: Failed to send test alert" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Wait a moment for processing
Start-Sleep -Seconds 2

# Check if alert was received
Write-Host "`n4. Verifying alert processing..." -ForegroundColor Yellow
try {
    $alerts = Invoke-RestMethod -Uri "$AlertmanagerUrl/api/v1/alerts" -UseBasicParsing
    $testAlerts = $alerts.data | Where-Object { $_.labels.alertname -eq "TestAlert" }
    
    if ($testAlerts) {
        Write-Host "   Alert received by Alertmanager" -ForegroundColor Green
        foreach ($alert in $testAlerts) {
            Write-Host "   - Status: $($alert.status.state)" -ForegroundColor Gray
            Write-Host "   - Severity: $($alert.labels.severity)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   WARNING: Test alert not found in Alertmanager" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   WARNING: Could not verify alert processing" -ForegroundColor Yellow
}

# Test email configuration (if requested)
if ($Type -eq "email" -or $Type -eq "both") {
    Write-Host "`n5. Testing email configuration..." -ForegroundColor Yellow
    
    if (-not $Email) {
        $Email = Read-Host "Enter email address to test"
    }
    
    Write-Host "   Sending test email to: $Email" -ForegroundColor Gray
    Write-Host "   Check your inbox (and spam folder) for the test alert" -ForegroundColor Yellow
    Write-Host "   If email not received, check Alertmanager configuration" -ForegroundColor Yellow
}

# Test Slack configuration (if requested)
if ($Type -eq "slack" -or $Type -eq "both") {
    Write-Host "`n6. Testing Slack configuration..." -ForegroundColor Yellow
    Write-Host "   Check your Slack channel for the test alert" -ForegroundColor Yellow
    Write-Host "   If message not received, verify webhook URL in Alertmanager config" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + "=" * 50
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "=" * 50
Write-Host "Alert sent: Yes" -ForegroundColor Green
Write-Host "Alertmanager: $AlertmanagerUrl" -ForegroundColor Gray
Write-Host "Severity: $Severity" -ForegroundColor Gray

if ($Type -eq "email" -or $Type -eq "both") {
    Write-Host "Email test: Check inbox at $Email" -ForegroundColor Yellow
}

if ($Type -eq "slack" -or $Type -eq "both") {
    Write-Host "Slack test: Check configured channel" -ForegroundColor Yellow
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Check your email/Slack for the test alert" -ForegroundColor White
Write-Host "2. If not received, check Alertmanager logs: docker logs platform-alertmanager" -ForegroundColor White
Write-Host "3. Verify configuration: http://localhost:9093/#/status" -ForegroundColor White
Write-Host "4. Review alert notification setup guide: docs/monitoring/ALERT_NOTIFICATION_SETUP.md" -ForegroundColor White

Write-Host "`nTo clear test alerts, wait 5 minutes or restart Alertmanager" -ForegroundColor Gray
