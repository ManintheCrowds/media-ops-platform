# Run GH-PF-03 local secret scans (gitleaks + trufflehog).
# Install once: winget install Gitleaks.Gitleaks
# TruffleHog: download to %LOCALAPPDATA%\Programs\trufflehog\ or use CI workflows on push.
# Usage (from repo root): .\docs\portfolio\run-gh-pf03-local-scan.ps1

$ErrorActionPreference = "Continue"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$logPath = Join-Path $PSScriptRoot "GH-PF-03-security-scan.log"
$lines = @(
    "# GH-PF-03 local scan $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')"
    "repo: $repoRoot"
    ""
)

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [System.Environment]::GetEnvironmentVariable("Path", "User")

Push-Location $repoRoot
try {
    $gitleaks = Get-Command gitleaks -ErrorAction SilentlyContinue
    if (-not $gitleaks) {
        $lines += "gitleaks: NOT INSTALLED (winget install Gitleaks.Gitleaks; new shell)"
    } else {
        $ver = (& gitleaks version 2>&1 | Out-String).Trim().Split("`n")[0]
        & gitleaks detect --source . --config .gitleaks.toml --no-git 2>&1 | Out-Null
        $code = $LASTEXITCODE
        $note = if ($code -eq 0) { "no leaks" } else { "review output" }
        $lines += "gitleaks: $ver - exit $code ($note)"
    }

    $thExe = "$env:LOCALAPPDATA\Programs\trufflehog\trufflehog.exe"
    if (-not (Test-Path $thExe)) {
        $cmd = Get-Command trufflehog -ErrorAction SilentlyContinue
        if ($cmd) { $thExe = $cmd.Source }
    }

    if (-not $thExe -or -not (Test-Path $thExe)) {
        $lines += "trufflehog: NOT INSTALLED (see .github/workflows/security-trufflehog.yml on push)"
    } else {
        $thVer = (& $thExe --version 2>&1 | Out-String).Trim().Split("`n")[0]
        $thOut = (& $thExe filesystem . --results=verified,unknown 2>&1 | Out-String)
        $code = $LASTEXITCODE
        $v = "?"
        $u = "?"
        if ($thOut -match 'verified_secrets":\s*(\d+)') { $v = $Matches[1] }
        if ($thOut -match 'unverified_secrets":\s*(\d+)') { $u = $Matches[1] }
        $lines += "trufflehog: $thVer - exit $code (verified=$v unverified=$u)"
    }
} finally {
    Pop-Location
}

$lines | Set-Content -Path $logPath -Encoding utf8
$lines | ForEach-Object { Write-Host $_ }
if ($lines -match "NOT INSTALLED") { exit 2 }
exit 0
