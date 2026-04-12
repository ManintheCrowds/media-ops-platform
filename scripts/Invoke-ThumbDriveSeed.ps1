#requires -Version 5.1
<#
.SYNOPSIS
    Run dev migration export and Cursor encrypted archive into one seed folder for USB transfer.

.DESCRIPTION
    1) Calls export_dev_migration_bundle.ps1 into -OutputDir (creates bundle\, dev-migration_*.zip).
    2) Calls Build-CursorFullEncryptedArchive.ps1 with the same -OutputDir (creates cursor_full_*\ and .zip).
    3) Writes SEED_INDEX.txt with restore order and security reminder.

    Close Cursor before running to minimize skipped profile files.

.PARAMETER OutputDir
    Target folder (created if missing). Example: D:\workstation_seed_20260412

.PARAMETER UseDefaultTen
    Pass through to export_dev_migration_bundle.ps1 (adds D:\Research, D:\ACE-first).

.PARAMETER IncludeCodex
    Pass through to Build-CursorFullEncryptedArchive.ps1.

.PARAMETER SkipDevZip
    Pass -SkipZip to export (stage only for bundle; smaller iteration).

.PARAMETER CursorStageOnly
    If set, Cursor step uses -StageOnly (no encrypted zip yet).

.PARAMETER DryRun
    If set, only writes SEED_INDEX preview to console; does not run children.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDir,
    [switch]$UseDefaultTen,
    [switch]$IncludeCodex,
    [switch]$SkipDevZip,
    [switch]$CursorStageOnly,
    [switch]$DryRun
)

Set-StrictMode -Version 3
$ErrorActionPreference = 'Stop'

$here = $PSScriptRoot
$export = Join-Path $here 'export_dev_migration_bundle.ps1'
$cursor = Join-Path $here 'Build-CursorFullEncryptedArchive.ps1'
$checklist = Join-Path $here 'THUMB_DRIVE_SEED_CHECKLIST.md'

if (-not (Test-Path -LiteralPath $export)) { throw "Missing: $export" }
if (-not (Test-Path -LiteralPath $cursor)) { throw "Missing: $cursor" }

$indexLines = [System.Collections.Generic.List[string]]::new()
[void]$indexLines.Add('WORKSTATION SEED INDEX')
[void]$indexLines.Add("Generated: $(Get-Date -Format 'o')")
[void]$indexLines.Add("Host: $env:COMPUTERNAME  User: $env:USERNAME")
[void]$indexLines.Add('')
[void]$indexLines.Add('CONTENTS (after successful run)')
[void]$indexLines.Add('  bundle\                    - export_dev_migration_bundle output (repos + machine_profile + reports)')
[void]$indexLines.Add('  dev-migration_*.zip         - optional zip of bundle (omit if -SkipDevZip)')
[void]$indexLines.Add('  cursor_full_*\             - staged Cursor profile')
[void]$indexLines.Add('  cursor_full_*.zip          - AES-256 zip of Cursor profile (omit if -CursorStageOnly)')
[void]$indexLines.Add('  THUMB_DRIVE_SEED_CHECKLIST.md - copy is next to scripts in repo; see repo path on old PC')
[void]$indexLines.Add('')
[void]$indexLines.Add('RESTORE ORDER')
[void]$indexLines.Add('  1) Decrypt archives on new PC.')
[void]$indexLines.Add('  2) Clone GitHub repos; merge bundle\repos\<name>\ ignored files into working trees.')
[void]$indexLines.Add('  3) Merge bundle\machine_profile per MIGRATION_BUNDLE_README.md.')
[void]$indexLines.Add('  4) Extract Cursor zip; merge Roaming_Cursor and UserProfile_dot_cursor per MANIFEST.txt inside zip.')
[void]$indexLines.Add('  5) Recreate env vars for MCP; reinstall toolchains; run one smoke test per repo.')
[void]$indexLines.Add('')
[void]$indexLines.Add('SECURITY')
[void]$indexLines.Add('  Encrypt USB or use encrypted zips only; rotate secrets if media was shared.')

if ($DryRun) {
    Write-Host ($indexLines -join "`n") -ForegroundColor Cyan
    Write-Host '[dry-run] No export or Cursor scripts executed.' -ForegroundColor Yellow
    exit 0
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$exportArgs = @{ OutputDir = $OutputDir }
if ($SkipDevZip) {
    $exportArgs['SkipZip'] = $true
}
if ($UseDefaultTen) {
    $exportArgs['UseDefaultTen'] = $true
}

Write-Host 'Running export_dev_migration_bundle.ps1 ...' -ForegroundColor Cyan
& $export @exportArgs

$cursorArgs = @{
    OutputDir = $OutputDir
}
if ($IncludeCodex) { $cursorArgs['IncludeCodex'] = $true }
if ($CursorStageOnly) { $cursorArgs['StageOnly'] = $true }

Write-Host 'Running Build-CursorFullEncryptedArchive.ps1 ...' -ForegroundColor Cyan
& $cursor @cursorArgs

[void]$indexLines.Add('')
[void]$indexLines.Add('PASS-THROUGH FLAGS')
[void]$indexLines.Add("  UseDefaultTen:    $UseDefaultTen")
[void]$indexLines.Add("  IncludeCodex:     $IncludeCodex")
[void]$indexLines.Add("  SkipDevZip:       $SkipDevZip")
[void]$indexLines.Add("  CursorStageOnly: $CursorStageOnly")

$indexPath = Join-Path $OutputDir 'SEED_INDEX.txt'
$indexLines | Set-Content -LiteralPath $indexPath -Encoding UTF8

Write-Host ''
Write-Host "Wrote $indexPath" -ForegroundColor Green
if (Test-Path -LiteralPath $checklist) {
    Write-Host "Reference: $checklist" -ForegroundColor Gray
}
