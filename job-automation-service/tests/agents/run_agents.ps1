# PowerShell script to run multi-agent testing and gap analysis

param(
    [string[]]$Agents,
    [int]$MaxParallel,
    [ValidateSet("quick", "full", "gap", "performance", "custom")]
    [string]$Suite = "full",
    [string]$Output,
    [switch]$Verbose
)

Write-Host "Starting Multi-Agent Testing and Gap Analysis Framework..." -ForegroundColor Green

# Set database URL if not set
if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
    Write-Host "Using default DATABASE_URL" -ForegroundColor Yellow
}

# Build command arguments
$args = @()

if ($Agents) {
    foreach ($agent in $Agents) {
        $args += "--agents"
        $args += $agent
    }
}

if ($MaxParallel) {
    $args += "--max-parallel"
    $args += $MaxParallel
}

if ($Suite) {
    $args += "--suite"
    $args += $Suite
}

if ($Output) {
    $args += "--output"
    $args += $Output
}

if ($Verbose) {
    $args += "--verbose"
}

# Change to job-automation-service directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$serviceDir = Split-Path -Parent $scriptDir
Set-Location $serviceDir

# Run the Python script
Write-Host "`nRunning agents..." -ForegroundColor Cyan
python -m tests.agents.run_agents @args

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nAgent execution failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`nAgent execution completed successfully!" -ForegroundColor Green
Write-Host "Check reports in: tests/agents/reports/" -ForegroundColor Cyan


