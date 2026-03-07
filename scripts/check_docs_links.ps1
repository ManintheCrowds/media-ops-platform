# Check external links in docs (especially coding_standards_matrix.md)
# Run from repo root: .\scripts\check_docs_links.ps1
# Exit 0 if all links OK, 1 if any fail

param(
    [string]$DocsPath = "docs",
    [string[]]$FocusFiles = @("docs/coding_standards_matrix.md")
)

$ErrorActionPreference = "Stop"
$failed = @()
$checked = 0

function Get-UrlsFromMarkdown {
    param([string]$Content)
    $pattern = 'https?://[^\s\)\]\`"\''<>]+'
    [regex]::Matches($Content, $pattern) | ForEach-Object { $_.Value.TrimEnd('.,;:') }
}

function Test-Url {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 400
    } catch {
        return $false
    }
}

$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path $root)) { $root = Get-Location }
Set-Location $root

$filesToCheck = @()
foreach ($f in $FocusFiles) {
    if (Test-Path $f) { $filesToCheck += $f }
}
if ($filesToCheck.Count -eq 0) {
    $filesToCheck = Get-ChildItem -Path $DocsPath -Filter "*.md" -Recurse | Select-Object -ExpandProperty FullName
}

foreach ($file in $filesToCheck) {
    $content = Get-Content -Path $file -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    $urls = Get-UrlsFromMarkdown $content | Sort-Object -Unique
    foreach ($url in $urls) {
        if ($url -match '^https://') {
            $checked++
            if (-not (Test-Url $url)) {
                $failed += [PSCustomObject]@{ File = $file; Url = $url }
            }
        }
    }
}

if ($failed.Count -gt 0) {
    Write-Host "FAILED: $($failed.Count) link(s) returned non-2xx:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  $($_.File): $($_.Url)" }
    exit 1
}

Write-Host "OK: $checked link(s) checked, all returned 2xx" -ForegroundColor Green
exit 0
