# Refresh docs/portfolio/metrics.json generated_at and validate required keys.
# Live CaptionPipeline stats (Grafana / homelab DB): PF-REPO-8 — stub hooks below.
#
# Usage (from repo root):
#   .\docs\portfolio\refresh_metrics.ps1
#   .\docs\portfolio\refresh_metrics.ps1 -DryRun
#   .\docs\portfolio\refresh_metrics.ps1 -FromGrafanaJson path\to\export.json   # future

param(
    [switch]$DryRun,
    [string]$FromGrafanaJson = ""
)

$ErrorActionPreference = "Stop"
$metricsPath = Join-Path $PSScriptRoot "metrics.json"

$requiredTop = @("schema_version", "generated_at", "sources", "caption_pipeline", "scp", "openharness")
$requiredCaption = @(
    "as_of", "caption_files_min", "content_hours_min", "success_rate_pct_min",
    "error_rate_pct_max", "production_feeds", "uptime_pct"
)
$requiredScp = @("as_of", "promptfoo_tier_probes_pass", "promptfoo_tier_probes_total")
$requiredOh = @("as_of", "autoresearch_tier_b")

function Test-RequiredKeys {
    param([object]$Obj, [string[]]$Keys, [string]$Label)
    foreach ($k in $Keys) {
        if (-not $Obj.PSObject.Properties.Name.Contains($k)) {
            throw "metrics.json: missing $Label key '$k'"
        }
    }
}

if (-not (Test-Path -LiteralPath $metricsPath)) {
    throw "metrics.json not found: $metricsPath"
}

$raw = Get-Content -LiteralPath $metricsPath -Raw -Encoding UTF8
try {
    $data = $raw | ConvertFrom-Json
} catch {
    throw "metrics.json is not valid JSON: $_"
}

foreach ($k in $requiredTop) {
    if (-not $data.PSObject.Properties.Name.Contains($k)) {
        throw "metrics.json: missing top-level key '$k'"
    }
}
Test-RequiredKeys -Obj $data.caption_pipeline -Keys $requiredCaption -Label "caption_pipeline"
Test-RequiredKeys -Obj $data.scp -Keys $requiredScp -Label "scp"
Test-RequiredKeys -Obj $data.openharness -Keys $requiredOh -Label "openharness"

# Future: PF-REPO-8 — merge live Grafana / DB export into caption_pipeline.*
if ($FromGrafanaJson) {
    if (-not (Test-Path -LiteralPath $FromGrafanaJson)) {
        throw "FromGrafanaJson not found: $FromGrafanaJson"
    }
    Write-Warning "FromGrafanaJson hook not implemented yet (PF-REPO-8). Validated schema only."
}

$newGeneratedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

if ($DryRun) {
    Write-Host "ValidateOnly OK: schema_version=$($data.schema_version) generated_at would become $newGeneratedAt"
    exit 0
}

$data.generated_at = $newGeneratedAt
$json = $data | ConvertTo-Json -Depth 8
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($metricsPath, $json + "`n", $utf8NoBom)
Write-Host "Updated generated_at -> $newGeneratedAt ($metricsPath)"
exit 0
