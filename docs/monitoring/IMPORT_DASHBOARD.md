# Import Cursor Dashboard Guide

## Quick Import

### Option 1: Using the Import Script (Recommended)

Run the import script and enter your password when prompted:

```powershell
.\scripts\monitoring\import-cursor-dashboard.ps1
```

Or provide the password directly:

```powershell
.\scripts\monitoring\import-cursor-dashboard.ps1 -Password "your-password"
```

### Option 2: Manual Import via Web UI

1. Open Grafana in your browser: http://localhost:3001
2. Log in with your credentials
3. Navigate to **Dashboards** → **Import** (or click the **+** icon → **Import**)
4. Click **Upload JSON file**
5. Select: `monitoring/grafana/dashboards/cursor-connections.json`
6. Select your **Prometheus** data source
7. Click **Import**

### Option 3: Import via Grafana API

If you have a Grafana API key:

```powershell
# Get your API key from Grafana: Configuration → API Keys → New API Key
$apiKey = "YOUR_API_KEY"
$grafanaUrl = "http://localhost:3001"
$dashboardJson = Get-Content "monitoring\grafana\dashboards\cursor-connections.json" -Raw

$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

$body = @{
    dashboard = ($dashboardJson | ConvertFrom-Json).dashboard
    overwrite = $true
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "$grafanaUrl/api/dashboards/db" -Method Post -Headers $headers -Body $body
```

## Verify Import

After importing, verify the dashboard:

1. Go to **Dashboards** → **Browse**
2. Look for **"Cursor Connection Monitoring"**
3. Click to open and verify panels are displaying

## Troubleshooting

### Authentication Failed (401)

- Make sure you're using the correct password
- If you changed the password, use the `-Password` parameter
- Verify Grafana is accessible: `http://localhost:3001`

### Dashboard Not Appearing

- Check if import was successful (look for success message)
- Refresh the Grafana dashboard list
- Check Grafana logs: `docker logs platform-grafana`

### No Data in Panels

- Verify Prometheus data source is configured
- Check Prometheus is scraping the cursor-exporter
- Verify metrics exist: Query `cursor_connections_active` in Prometheus
- Ensure monitoring scripts are running and collecting data

## See Also

- [Cursor Monitoring Quick Start](CURSOR_MONITORING_QUICKSTART.md)
- [Grafana Password Reset](GRAFANA_PASSWORD_RESET.md)
