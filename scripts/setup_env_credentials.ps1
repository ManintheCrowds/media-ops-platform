# Interactive script to set up environment variables in .env files
# This script helps you securely input credentials without exposing them in command history

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment Variables Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to securely read password/secret
function Read-SecureInput {
    param([string]$Prompt)
    $secure = Read-Host -Prompt $Prompt -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    return $plain
}

# Main Platform .env
Write-Host "=== Main Platform (.env) ===" -ForegroundColor Yellow
$mainEnvPath = "D:\software\.env"

if (Test-Path $mainEnvPath) {
    Write-Host "Found .env file at: $mainEnvPath" -ForegroundColor Green
    
    # Arlo Credentials (if using camera service)
    $setupArlo = Read-Host "Set up Arlo camera credentials? (y/n)"
    if ($setupArlo -eq 'y' -or $setupArlo -eq 'Y') {
        $arloUsername = Read-Host "Arlo Username (email)"
        $arloPassword = Read-SecureInput "Arlo Password"
        
        # Update .env file
        $content = Get-Content $mainEnvPath -Raw
        if ($content -match 'ARLO_USERNAME=') {
            $content = $content -replace 'ARLO_USERNAME=.*', "ARLO_USERNAME=$arloUsername"
        } else {
            $content += "`nARLO_USERNAME=$arloUsername"
        }
        if ($content -match 'ARLO_PASSWORD=') {
            $content = $content -replace 'ARLO_PASSWORD=.*', "ARLO_PASSWORD=$arloPassword"
        } else {
            $content += "`nARLO_PASSWORD=$arloPassword"
        }
        Set-Content $mainEnvPath -Value $content -NoNewline
        Write-Host "[OK] Arlo credentials updated" -ForegroundColor Green
    }
    
    # Notification Email
    $setupEmail = Read-Host "Set notification email? (y/n)"
    if ($setupEmail -eq 'y' -or $setupEmail -eq 'Y') {
        $notifEmail = Read-Host "Notification Email"
        $content = Get-Content $mainEnvPath -Raw
        if ($content -match 'NOTIFICATION_EMAIL=') {
            $content = $content -replace 'NOTIFICATION_EMAIL=.*', "NOTIFICATION_EMAIL=$notifEmail"
        } else {
            $content += "`nNOTIFICATION_EMAIL=$notifEmail"
        }
        Set-Content $mainEnvPath -Value $content -NoNewline
        Write-Host "[OK] Notification email updated" -ForegroundColor Green
    }
} else {
    Write-Host ".env file not found at $mainEnvPath" -ForegroundColor Red
}

Write-Host ""

# Job Automation Service .env
Write-Host "=== Job Automation Service (.env) ===" -ForegroundColor Yellow
$jobEnvPath = "D:\software\job-automation-service\.env"

if (Test-Path $jobEnvPath) {
    Write-Host "Found .env file at: $jobEnvPath" -ForegroundColor Green
    
    # Adzuna API
    $setupAdzuna = Read-Host "Set up Adzuna API credentials? (y/n)"
    if ($setupAdzuna -eq 'y' -or $setupAdzuna -eq 'Y') {
        $adzunaId = Read-Host "Adzuna API ID"
        $adzunaKey = Read-SecureInput "Adzuna API Key"
        
        $content = Get-Content $jobEnvPath -Raw
        $content = $content -replace 'ADZUNA_API_ID=.*', "ADZUNA_API_ID=$adzunaId"
        $content = $content -replace 'ADZUNA_API_KEY=.*', "ADZUNA_API_KEY=$adzunaKey"
        Set-Content $jobEnvPath -Value $content -NoNewline
        Write-Host "[OK] Adzuna credentials updated" -ForegroundColor Green
    }
    
    # JSearch API
    $setupJSearch = Read-Host "Set up JSearch API key? (y/n)"
    if ($setupJSearch -eq 'y' -or $setupJSearch -eq 'Y') {
        $jsearchKey = Read-SecureInput "JSearch API Key"
        
        $content = Get-Content $jobEnvPath -Raw
        $content = $content -replace 'JSEARCH_API_KEY=.*', "JSEARCH_API_KEY=$jsearchKey"
        Set-Content $jobEnvPath -Value $content -NoNewline
        Write-Host "[OK] JSearch API key updated" -ForegroundColor Green
    }
    
    # Database URL
    $setupDb = Read-Host "Update database URL? (y/n)"
    if ($setupDb -eq 'y' -or $setupDb -eq 'Y') {
        $dbUrl = Read-Host "Database URL (e.g., postgresql://user:pass@host:port/dbname)"
        
        $content = Get-Content $jobEnvPath -Raw
        $content = $content -replace 'DATABASE_URL=.*', "DATABASE_URL=$dbUrl"
        Set-Content $jobEnvPath -Value $content -NoNewline
        Write-Host "[OK] Database URL updated" -ForegroundColor Green
    }
} else {
    Write-Host ".env file not found at $jobEnvPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your .env files have been updated with your credentials." -ForegroundColor White
Write-Host "Remember: .env files are in .gitignore and will NOT be committed." -ForegroundColor Yellow
Write-Host ""

