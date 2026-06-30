# Purge verified Adzuna secrets from git history
#
# APPROVAL_NEEDED: Rotate Adzuna API keys at https://developer.adzuna.com/ BEFORE running.
# APPROVAL_NEEDED: Force-push rewrites main — coordinate with collaborators.
#
# Prerequisites: pip install git-filter-repo
#
# Usage (from repo root, with a clean working tree):
#   .\scripts\purge-adzuna-history.ps1              # dry-run instructions
#   .\scripts\purge-adzuna-history.ps1 -Execute      # run filter-repo (local only)
#   git push --force-with-lease origin main          # operator step after -Execute
#
# Replacements: config/filter-repo-adzuna-replacements.txt (regex-only, safe to commit)
# Paths historically flagged: job-automation-service/.env.backup (gitignored on main; still in history)

param(
    [switch]$Execute
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Replacements = Join-Path $RepoRoot "config\filter-repo-adzuna-replacements.txt"

Set-Location $RepoRoot

if (-not (Test-Path $Replacements)) {
    Write-Error "Missing $Replacements"
}

Write-Host "Gate 1 - Adzuna history purge"
Write-Host "  1. Rotate ADZUNA_API_ID / ADZUNA_API_KEY at https://developer.adzuna.com/"
Write-Host "  2. Confirm job-automation-service/.env.backup is not tracked (git ls-files)"
Write-Host "  3. Replacements file: $Replacements"
Write-Host ""

$tracked = git ls-files "*env.backup*" 2>$null
if ($tracked) {
    Write-Warning "Tracked env backup files still in index: $tracked"
} else {
    Write-Host "OK: no *.env.backup tracked in index"
}

if (-not $Execute) {
    Write-Host ""
    Write-Host "Dry run. To rewrite local history:"
    Write-Host "  pip install git-filter-repo"
    Write-Host "  git filter-repo --force --replace-text config/filter-repo-adzuna-replacements.txt"
    Write-Host "  git push --force-with-lease origin main"
    Write-Host ""
    Write-Host "Then re-run scheduled TruffleHog and update docs/portfolio/GH-PF-03-security-scan.md"
    exit 0
}

$filterRepo = Get-Command git-filter-repo -ErrorAction SilentlyContinue
if (-not $filterRepo) {
    Write-Error "git-filter-repo not found. Install: pip install git-filter-repo"
}

$alreadyRan = Join-Path $RepoRoot ".git\filter-repo\already_ran"
if (Test-Path $alreadyRan) {
    Remove-Item $alreadyRan -Force
}

Write-Host "Running git filter-repo (non-interactive)..."
"Y" | git filter-repo --force --replace-text $Replacements
Write-Host "Done. Verify with trufflehog, then: git push --force-with-lease origin main"
