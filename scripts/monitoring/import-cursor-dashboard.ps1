# Import Cursor Monitoring Dashboard to Grafana

param(
    [string]$GrafanaUrl = "http://localhost:3001",
    [string]$Username = "admin",
    [Parameter(Mandatory=$false)]
    [string]$Password,
    [string]$DashboardFile = "monitoring\grafana\dashboards\cursor-connections.json"
)

# If password not provided, prompt for it securely
if (-not $Password) {
    $securePassword = Read-Host "Enter Grafana password for user '$Username'" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
}

Write-Host "Importing Cursor Monitoring Dashboard..." -ForegroundColor Cyan

# Read dashboard JSON
$dashboardPath = Join-Path $PSScriptRoot "..\..\$DashboardFile"
if (-not (Test-Path $dashboardPath)) {
    Write-Host "Error: Dashboard file not found at $dashboardPath" -ForegroundColor Red
    exit 1
}

Write-Host "Reading dashboard from: $dashboardPath" -ForegroundColor Gray
$dashboardJson = Get-Content $dashboardPath -Raw
$dashboard = $dashboardJson | ConvertFrom-Json

# Prepare request body
$body = @{
    dashboard = $dashboard.dashboard
    overwrite = $true
} | ConvertTo-Json -Depth 20

# Create authentication header
$credentials = "${Username}:${Password}"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($credentials)
$base64Auth = [Convert]::ToBase64String($bytes)
$headers = @{
    "Authorization" = "Basic $base64Auth"
    "Content-Type" = "application/json"
}

# Import dashboard
try {
    Write-Host "Sending request to Grafana..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri "$GrafanaUrl/api/dashboards/db" -Method Post -Headers $headers -Body $body
    
    Write-Host ""
    Write-Host "Dashboard imported successfully!" -ForegroundColor Green
    Write-Host "  Dashboard ID: $($response.id)" -ForegroundColor Cyan
    Write-Host "  Dashboard UID: $($response.uid)" -ForegroundColor Cyan
    Write-Host "  Dashboard URL: $($response.url)" -ForegroundColor Cyan
    Write-Host ""
    $dashboardUrl = "$GrafanaUrl$($response.url)"
    Write-Host "Access dashboard at: $dashboardUrl" -ForegroundColor Yellow
} catch {
    Write-Host ""
    Write-Host "Import failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $responseBody = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
    
    exit 1
}
