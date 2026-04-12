#requires -Version 5.1
<#
.SYNOPSIS
    Stage a full Cursor-related profile and produce an AES-256 encrypted .zip (via 7-Zip).

.DESCRIPTION
    "Full" means everything typically needed to restore Cursor behavior on a new PC, excluding
    obvious browser-style caches under %APPDATA%\Cursor that bloat the archive without helping migration.

    Staged layout (under -OutputDir\cursor_full_<timestamp>\):
      MANIFEST.txt              - inventory, restore hints, security notes
      Roaming_Cursor\           - copy of %APPDATA%\Cursor (filtered)
      UserProfile_dot_cursor\   - copy of %USERPROFILE%\.cursor (filtered)
      UserProfile_dot_codex\    - copy of %USERPROFILE%\.codex (filtered, optional)
      Roaming_Code_User\        - optional: %APPDATA%\Code\User if present (VS Code parity)
      LocalAppData_Cursor\      - optional: %LOCALAPPDATA%\Cursor (often cache-heavy; off by default)

    After staging, runs 7-Zip: AES-256 Zip (-tzip -mem=AES256). Plain "zip" encryption in older tools
    is weak; 7z zip AES is the common portable choice.

    SECURITY: Close Cursor before running to avoid locked files. The archive may contain tokens (mcp.json).
    Prefer sharing the password out-of-band; avoid -PlainTextPassword in logged shells.

.PARAMETER OutputDir
    Parent folder for staging + final zip (default: D:\)

.PARAMETER PlainTextPassword
    Optional. If omitted, you are prompted for a password (masked). Avoid passing on command line in shared environments.

.PARAMETER StageOnly
    If set, only creates the stage folder; does not invoke 7-Zip.

.PARAMETER IncludeCodex
    Include %USERPROFILE%\.codex (Codex skills, config).

.PARAMETER IncludeCodeUser
    Include %APPDATA%\Code\User (settings/keybindings) if that path exists.

.PARAMETER IncludeLocalAppDataCursor
    Include %LOCALAPPDATA%\Cursor (can be large; mostly caches - use only if you know you need it).

.PARAMETER IncludePluginCache
    Include .cursor\plugins\cache (large; marketplace can refetch - default skip).

.PARAMETER IncludeUserHistory
    Include %APPDATA%\Cursor\User\History (local file history; can be very large).

.PARAMETER IncludeWorkspaceStorage
    Include workspaceStorage under Roaming\Cursor (binary state; large).

.PARAMETER SevenZipExe
    Path to 7z.exe. If omitted, uses PATH or "C:\Program Files\7-Zip\7z.exe".

.EXAMPLE
    .\Build-CursorFullEncryptedArchive.ps1
    Prompts for password; writes D:\cursor_full_yyyyMMdd_HHmmss.zip

.EXAMPLE
    .\Build-CursorFullEncryptedArchive.ps1 -IncludeCodex -StageOnly
    Inspect stage only, then run again without -StageOnly to zip.
#>
[CmdletBinding()]
param(
    [string]$OutputDir = 'D:\',
    [string]$PlainTextPassword = '',
    [switch]$StageOnly,
    [switch]$IncludeCodex,
    [switch]$IncludeCodeUser,
    [switch]$IncludeLocalAppDataCursor,
    [switch]$IncludePluginCache,
    [switch]$IncludeUserHistory,
    [switch]$IncludeWorkspaceStorage,
    [string]$SevenZipExe = '',
    [switch]$DryRun
)

Set-StrictMode -Version 3
$ErrorActionPreference = 'Stop'

function Resolve-SevenZipPath {
    param([string]$Explicit)
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) { return $Explicit }
    $cmd = Get-Command '7z' -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    $def = 'C:\Program Files\7-Zip\7z.exe'
    if (Test-Path -LiteralPath $def) { return $def }
    $def86 = 'C:\Program Files (x86)\7-Zip\7z.exe'
    if (Test-Path -LiteralPath $def86) { return $def86 }
    return $null
}

function Test-RobocopySuccess {
    param([int]$ExitCode)
    # robocopy: 0 = nothing copied; 1-7 = success with copies; >=8 = failure
    return ($ExitCode -lt 8)
}

function Invoke-RobocopyMirror {
    param(
        [string]$SourceRoot,
        [string]$DestRoot,
        [string[]]$ExcludeDirNames
    )
    if (-not (Test-Path -LiteralPath $SourceRoot)) {
        Write-Host "Skip missing path: $SourceRoot" -ForegroundColor DarkYellow
        return
    }
    if (-not (Test-Path -LiteralPath $DestRoot)) {
        New-Item -ItemType Directory -Path $DestRoot -Force | Out-Null
    }
    $xd = @()
    if ($ExcludeDirNames -and $ExcludeDirNames.Count -gt 0) {
        $xd = ($ExcludeDirNames | ForEach-Object { "/XD"; $_ })
    }
    $args = @($SourceRoot, $DestRoot, '/E', '/COPY:DAT', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS') + $xd
    Write-Host "robocopy $($args -join ' ')" -ForegroundColor Gray
    if (-not $DryRun) {
        & robocopy @args | Out-Host
        $code = $LASTEXITCODE
        if (-not (Test-RobocopySuccess -ExitCode $code)) {
            throw "robocopy failed with exit code $code for $SourceRoot -> $DestRoot"
        }
    }
}

function Get-PlainPassword {
    param([string]$PlainParam)
    if ($PlainParam) { return $PlainParam }
    $secure = Read-Host 'Encryption password' -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringUni($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

Write-Host ''
Write-Host 'Close Cursor (and any VS Code windows using the same profile) before continuing to reduce locked files.' -ForegroundColor Yellow
Write-Host ''

$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$bundleName = "cursor_full_$ts"
$stageRoot = Join-Path $OutputDir $bundleName
$zipPath = Join-Path $OutputDir "$bundleName.zip"

if (-not $DryRun -and -not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$roamingCursor = Join-Path $env:APPDATA 'Cursor'
$userDotCursor = Join-Path $env:USERPROFILE '.cursor'
$userDotCodex = Join-Path $env:USERPROFILE '.codex'
$roamingCodeUser = Join-Path $env:APPDATA 'Code\User'
$localCursor = Join-Path $env:LOCALAPPDATA 'Cursor'

# Default excludes under Roaming Cursor (Electron-ish noise)
$roamingExclude = [System.Collections.Generic.List[string]]::new()
@(
    'Cache', 'CachedData', 'GPUCache', 'Code Cache', 'logs', 'blob_storage',
    'Crashpad', 'Service Worker', 'DawnGraphiteCache', 'DawnWebGPUCache'
) | ForEach-Object { [void]$roamingExclude.Add($_) }

if (-not $IncludeUserHistory) { [void]$roamingExclude.Add('History') }

if (-not $IncludeWorkspaceStorage) { [void]$roamingExclude.Add('workspaceStorage') }

$dotCursorExclude = [System.Collections.Generic.List[string]]::new()
@('Cache', 'CachedData', 'GPUCache', 'Code Cache', 'logs', 'Crashpad') | ForEach-Object { [void]$dotCursorExclude.Add($_) }
if (-not $IncludePluginCache) { [void]$dotCursorExclude.Add('cache') } # .cursor\plugins\cache

$codexExclude = [System.Collections.Generic.List[string]]::new()
@('Cache', 'logs') | ForEach-Object { [void]$codexExclude.Add($_) }

$localExclude = @('Cache', 'CachedData', 'GPUCache', 'Code Cache', 'logs', 'blob_storage', 'Crashpad')

if ($DryRun) {
    Write-Host "[dry-run] Would stage to: $stageRoot" -ForegroundColor Cyan
    Write-Host "[dry-run] Would write zip to: $zipPath" -ForegroundColor Cyan
}

$lines = New-Object System.Collections.Generic.List[string]
[void]$lines.Add("CURSOR FULL ARCHIVE MANIFEST")
[void]$lines.Add("Generated (UTC): $([DateTimeOffset]::UtcNow.ToString('o'))")
[void]$lines.Add("Host: $env:COMPUTERNAME  User: $env:USERNAME")
[void]$lines.Add('')
[void]$lines.Add('FLAGS')
[void]$lines.Add("  IncludeCodex:              $IncludeCodex")
[void]$lines.Add("  IncludeCodeUser:           $IncludeCodeUser")
[void]$lines.Add("  IncludeLocalAppDataCursor: $IncludeLocalAppDataCursor")
[void]$lines.Add("  IncludePluginCache:        $IncludePluginCache")
[void]$lines.Add("  IncludeUserHistory:        $IncludeUserHistory")
[void]$lines.Add("  IncludeWorkspaceStorage:   $IncludeWorkspaceStorage")
[void]$lines.Add('')
[void]$lines.Add('SOURCES')
[void]$lines.Add("  Roaming Cursor: $roamingCursor")
[void]$lines.Add("  User .cursor:   $userDotCursor")
[void]$lines.Add("  User .codex:    $userDotCodex")
[void]$lines.Add('')
[void]$lines.Add('ROAMING CURSOR EXCLUDED DIRECTORY NAMES')
$roamingExclude | ForEach-Object { [void]$lines.Add("  - $_") }
[void]$lines.Add('')
[void]$lines.Add('USER .cursor EXCLUDED DIRECTORY NAMES')
$dotCursorExclude | ForEach-Object { [void]$lines.Add("  - $_") }
[void]$lines.Add('')
[void]$lines.Add('RESTORE (summary)')
[void]$lines.Add('  1) Install Cursor on the new machine; sign in if you use account sync.')
[void]$lines.Add('  2) Exit Cursor completely.')
[void]$lines.Add('  3) Unzip with 7-Zip using the same password.')
[void]$lines.Add('  4) Merge Roaming_Cursor\* into %APPDATA%\Cursor\ (prefer diff on User\settings.json and User\mcp.json first).')
[void]$lines.Add('  5) Merge UserProfile_dot_cursor\* into %USERPROFILE%\.cursor\')
[void]$lines.Add('  6) If included, merge UserProfile_dot_codex\* into %USERPROFILE%\.codex\')
[void]$lines.Add('  7) Reinstall CLIs / set env vars referenced by mcp.json; re-auth OAuth MCPs as needed.')
[void]$lines.Add('')
[void]$lines.Add('SECURITY')
[void]$lines.Add('  This bundle may contain secrets (mcp.json, tokens in storage). Keep encrypted at rest; rotate if exposure risk.')

if (-not $DryRun) {
    New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null
    $lines | Set-Content -Path (Join-Path $stageRoot 'MANIFEST.txt') -Encoding UTF8

    Invoke-RobocopyMirror -SourceRoot $roamingCursor -DestRoot (Join-Path $stageRoot 'Roaming_Cursor') -ExcludeDirNames @($roamingExclude)
    Invoke-RobocopyMirror -SourceRoot $userDotCursor -DestRoot (Join-Path $stageRoot 'UserProfile_dot_cursor') -ExcludeDirNames @($dotCursorExclude)

    if ($IncludeCodex) {
        Invoke-RobocopyMirror -SourceRoot $userDotCodex -DestRoot (Join-Path $stageRoot 'UserProfile_dot_codex') -ExcludeDirNames @($codexExclude)
    }

    if ($IncludeCodeUser -and (Test-Path -LiteralPath $roamingCodeUser)) {
        Invoke-RobocopyMirror -SourceRoot $roamingCodeUser -DestRoot (Join-Path $stageRoot 'Roaming_Code_User') -ExcludeDirNames @('History')
    }

    if ($IncludeLocalAppDataCursor -and (Test-Path -LiteralPath $localCursor)) {
        Invoke-RobocopyMirror -SourceRoot $localCursor -DestRoot (Join-Path $stageRoot 'LocalAppData_Cursor') -ExcludeDirNames $localExclude
    }
}
else {
    Write-Host ($lines -join "`n")
}

if ($StageOnly -or $DryRun) {
    Write-Host ''
    Write-Host "StageOnly or DryRun: skipping 7-Zip. Stage: $stageRoot" -ForegroundColor Yellow
    exit 0
}

$seven = Resolve-SevenZipPath -Explicit $SevenZipExe
if (-not $seven) {
    throw '7-Zip (7z.exe) not found. Install 7-Zip or pass -SevenZipExe "C:\Program Files\7-Zip\7z.exe".'
}

$pass = Get-PlainPassword -PlainParam $PlainTextPassword
if ([string]::IsNullOrWhiteSpace($pass)) {
    throw 'Password is empty.'
}

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

# 7-Zip: add folder contents at root of zip matching stage folder name for clarity
$parent = Split-Path -LiteralPath $stageRoot -Parent
$leaf = Split-Path -LiteralPath $stageRoot -Leaf
Push-Location -LiteralPath $parent
try {
    Write-Host "Creating encrypted zip with 7-Zip: $zipPath" -ForegroundColor Cyan
    $sevenArgs = @(
        'a',
        '-tzip',
        '-mx=9',
        '-mem=AES256',
        "-p$pass",
        $zipPath,
        $leaf
    )
    & $seven @sevenArgs | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "7-Zip failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host "Done. Encrypted archive: $zipPath" -ForegroundColor Green
Write-Host "Stage folder (unencrypted copy): $stageRoot - delete after verifying the zip if you want a single artifact." -ForegroundColor DarkYellow
