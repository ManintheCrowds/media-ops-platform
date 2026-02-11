# Non-interactive script to set individual environment variables
# Usage: .\set_env_credential.ps1 -Service "main" -Key "ARLO_USERNAME" -Value "email@example.com"
#        .\set_env_credential.ps1 -Service "job" -Key "ADZUNA_API_KEY" -Value "your-key"

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("main", "job")]
    [string]$Service,
    
    [Parameter(Mandatory=$true)]
    [string]$Key,
    
    [Parameter(Mandatory=$true)]
    [string]$Value
)

$mainEnvPath = "D:\software\.env"
$jobEnvPath = "D:\software\job-automation-service\.env"

if ($Service -eq "main") {
    $envPath = $mainEnvPath
} else {
    $envPath = $jobEnvPath
}

if (-not (Test-Path $envPath)) {
    Write-Host "[ERROR] .env file not found at: $envPath" -ForegroundColor Red
    exit 1
}

# Read current content
$content = Get-Content $envPath -Raw

# Check if key already exists
if ($content -match "$Key=") {
    # Replace existing value
    $content = $content -replace "$Key=.*", "$Key=$Value"
    Write-Host "[OK] Updated $Key in $envPath" -ForegroundColor Green
} else {
    # Add new key-value pair
    $content += "`n$Key=$Value"
    Write-Host "[OK] Added $Key to $envPath" -ForegroundColor Green
}

# Write back to file
Set-Content $envPath -Value $content -NoNewline
Write-Host "Value set successfully!" -ForegroundColor Green




