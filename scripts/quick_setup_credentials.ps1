# Quick setup script - prompts for common credentials
# This version works in non-interactive mode by using parameters

param(
    # Main Platform
    [string]$ArloUsername,
    [string]$ArloPassword,
    [string]$NotificationEmail,
    
    # Job Automation Service
    [string]$AdzunaApiId,
    [string]$AdzunaApiKey,
    [string]$JSearchApiKey,
    
    # Database
    [string]$DatabaseUrl
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick Credential Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Main Platform
if ($ArloUsername -or $ArloPassword -or $NotificationEmail) {
    Write-Host "=== Main Platform ===" -ForegroundColor Yellow
    $mainEnvPath = "D:\software\.env"
    
    if (Test-Path $mainEnvPath) {
        $content = Get-Content $mainEnvPath -Raw
        
        if ($ArloUsername) {
            if ($content -match "ARLO_USERNAME=") {
                $content = $content -replace "ARLO_USERNAME=.*", "ARLO_USERNAME=$ArloUsername"
            } else {
                $content += "`nARLO_USERNAME=$ArloUsername"
            }
            Write-Host "[OK] Set ARLO_USERNAME" -ForegroundColor Green
        }
        
        if ($ArloPassword) {
            if ($content -match "ARLO_PASSWORD=") {
                $content = $content -replace "ARLO_PASSWORD=.*", "ARLO_PASSWORD=$ArloPassword"
            } else {
                $content += "`nARLO_PASSWORD=$ArloPassword"
            }
            Write-Host "[OK] Set ARLO_PASSWORD" -ForegroundColor Green
        }
        
        if ($NotificationEmail) {
            if ($content -match "NOTIFICATION_EMAIL=") {
                $content = $content -replace "NOTIFICATION_EMAIL=.*", "NOTIFICATION_EMAIL=$NotificationEmail"
            } else {
                $content += "`nNOTIFICATION_EMAIL=$NotificationEmail"
            }
            Write-Host "[OK] Set NOTIFICATION_EMAIL" -ForegroundColor Green
        }
        
        Set-Content $mainEnvPath -Value $content -NoNewline
    }
}

# Job Automation Service
if ($AdzunaApiId -or $AdzunaApiKey -or $JSearchApiKey) {
    Write-Host ""
    Write-Host "=== Job Automation Service ===" -ForegroundColor Yellow
    $jobEnvPath = "D:\software\job-automation-service\.env"
    
    if (Test-Path $jobEnvPath) {
        $content = Get-Content $jobEnvPath -Raw
        
        if ($AdzunaApiId) {
            $content = $content -replace "ADZUNA_API_ID=.*", "ADZUNA_API_ID=$AdzunaApiId"
            Write-Host "[OK] Set ADZUNA_API_ID" -ForegroundColor Green
        }
        
        if ($AdzunaApiKey) {
            $content = $content -replace "ADZUNA_API_KEY=.*", "ADZUNA_API_KEY=$AdzunaApiKey"
            Write-Host "[OK] Set ADZUNA_API_KEY" -ForegroundColor Green
        }
        
        if ($JSearchApiKey) {
            $content = $content -replace "JSEARCH_API_KEY=.*", "JSEARCH_API_KEY=$JSearchApiKey"
            Write-Host "[OK] Set JSEARCH_API_KEY" -ForegroundColor Green
        }
        
        Set-Content $jobEnvPath -Value $content -NoNewline
    }
}

# Database URL (can apply to both)
if ($DatabaseUrl) {
    Write-Host ""
    Write-Host "=== Database URL ===" -ForegroundColor Yellow
    
    # Main platform
    if (Test-Path "D:\software\.env") {
        $content = Get-Content "D:\software\.env" -Raw
        $content = $content -replace "DATABASE_URL=.*", "DATABASE_URL=$DatabaseUrl"
        Set-Content "D:\software\.env" -Value $content -NoNewline
        Write-Host "[OK] Updated DATABASE_URL in main platform" -ForegroundColor Green
    }
    
    # Job automation
    if (Test-Path "D:\software\job-automation-service\.env") {
        $content = Get-Content "D:\software\job-automation-service\.env" -Raw
        $content = $content -replace "DATABASE_URL=.*", "DATABASE_URL=$DatabaseUrl"
        Set-Content "D:\software\job-automation-service\.env" -Value $content -NoNewline
        Write-Host "[OK] Updated DATABASE_URL in job automation service" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Example usage:" -ForegroundColor Yellow
Write-Host '  .\quick_setup_credentials.ps1 -ArloUsername "email@example.com" -ArloPassword "password"' -ForegroundColor White
Write-Host '  .\quick_setup_credentials.ps1 -AdzunaApiKey "your-key" -JSearchApiKey "your-key"' -ForegroundColor White

