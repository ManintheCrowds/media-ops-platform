# PURPOSE: Stage non-GitHub dev artifacts (ignored files, Cursor profile subset, reports) for USB migration.
# REQUIRES: Git in PATH; optional Docker for compose introspection; optional rg (ripgrep) for CONFIG_HINTS.
# MODIFICATION NOTES: See scripts/MIGRATION_BUNDLE_README.md for dry-run and restore workflow.

[CmdletBinding()]
param(
    [string[]]$RepoRoots = @(
        'D:\software',
        'D:\portfolio-harness',
        'D:\openharness',
        'D:\scp',
        'D:\moltbook-watchtower',
        'D:\Arc_Forge',
        'D:\prusa_XL_soft',
        'D:\VibeLedger'
    ),
    [switch]$UseDefaultEight,
    [switch]$ConfirmSingleRepo,
    [string]$OutputDir = '',
    [string[]]$ExcludeDirPatterns = @(
        'node_modules', '.pnpm-store', 'venv', '.venv', 'ENV', '__pycache__', '.pytest_cache',
        '.pytest-tmp', '.tox', 'dist', 'build', '.next', 'target', '.gradle', '.git'
    ),
    [bool]$IncludeAppDataCursor = $true,
    [switch]$IncludeCursorState,
    [switch]$DryRun,
    [switch]$SkipZip,
    [switch]$DebugMigrationLog
)

Set-StrictMode -Version 3
$ErrorActionPreference = 'Stop'
$script:DebugMigrationLogEnabled = [bool]$DebugMigrationLog

#region agent log
$script:DebugAgentLogPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'debug-91f5e8.log'
$script:DebugRunId = if ($env:DEBUG_RUN_ID) { $env:DEBUG_RUN_ID } else { 'pre-fix' }
function Write-AgentDebugLog {
    param(
        [string]$HypothesisId,
        [string]$Location,
        [string]$Message,
        [hashtable]$Data = @{}
    )
    if (-not $script:DebugMigrationLogEnabled) { return }
    $o = [ordered]@{
        sessionId    = '91f5e8'
        runId        = $script:DebugRunId
        hypothesisId = $HypothesisId
        location     = $Location
        message      = $Message
        data         = $Data
        timestamp    = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    }
    $line = ($o | ConvertTo-Json -Compress -Depth 8)
    Add-Content -LiteralPath $script:DebugAgentLogPath -Value $line -Encoding UTF8
}
#endregion

function Test-IsLikelyFileLockOrSharingError {
    param([System.Exception]$Exception)
    if ($null -eq $Exception) { return $false }
    $msg = $Exception.Message
    if ($msg -match 'being used by another process') { return $true }
    if ($msg -match '(?i)cannot access the file') { return $true }
    if ($msg -match '(?i)being used') { return $true }
    try {
        $hr = [System.Runtime.InteropServices.Marshal]::GetHRForException($Exception)
        # ERROR_SHARING_VIOLATION 32 -> 0x80070020
        if (($hr -band 0xFFFF) -eq 32) { return $true }
    }
    catch { }
    return $false
}

function Copy-Item-MigrationSafe {
    param(
        [string]$LiteralSrc,
        [string]$LiteralDst,
        [string]$LogLocation,
        [switch]$RecordProfileSkips
    )
    try {
        Copy-Item -LiteralPath $LiteralSrc -Destination $LiteralDst -Force
        return $true
    }
    catch {
        if (Test-IsLikelyFileLockOrSharingError -Exception $_.Exception) {
            Write-Warning "Skipping locked file: $LiteralSrc"
            if ($RecordProfileSkips) {
                [void]$script:ProfileCopySkipped.Add($LiteralSrc)
            }
            Write-AgentDebugLog -HypothesisId 'H1' -Location $LogLocation -Message 'copy_skipped_locked' -Data @{
                src   = $LiteralSrc
                dst   = $LiteralDst
                error = $_.Exception.Message
            }
            return $false
        }
        Write-AgentDebugLog -HypothesisId 'H1' -Location $LogLocation -Message 'copy_failed' -Data @{
            src   = $LiteralSrc
            dst   = $LiteralDst
            error = $_.Exception.Message
            name  = $_.Exception.GetType().FullName
        }
        throw
    }
}

$DefaultMigrationRepoRoots = @(
    'D:\software',
    'D:\portfolio-harness',
    'D:\openharness',
    'D:\scp',
    'D:\moltbook-watchtower',
    'D:\Arc_Forge',
    'D:\prusa_XL_soft',
    'D:\VibeLedger'
)
if ($UseDefaultEight) {
    $RepoRoots = $DefaultMigrationRepoRoots
}

$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
if (-not $OutputDir) {
    $OutputDir = Join-Path 'D:\' "migration_export_$ts"
}

$stageRoot = Join-Path $OutputDir 'bundle'
$reportsDir = Join-Path $stageRoot 'reports'
$reposStage = Join-Path $stageRoot 'repos'
$profileStage = Join-Path $stageRoot 'machine_profile'

Write-Host ''
Write-Host "Migration bundle: $($RepoRoots.Count) repository root(s) will be processed." -ForegroundColor Cyan
foreach ($r in $RepoRoots) {
    Write-Host "  - $r" -ForegroundColor Gray
}
Write-Host ''
if ($RepoRoots.Count -eq 1) {
    if ($DryRun) {
        Write-Host 'Note: Single-repo dry-run is fine for testing. For a full USB bundle of all 8 repos, run without -RepoRoots or use -UseDefaultEight.' -ForegroundColor DarkYellow
        Write-Host ''
    }
    elseif (-not $ConfirmSingleRepo) {
        Write-Warning @'
Only ONE repository root is configured. If you used -RepoRoots @('D:\moltbook-watchtower') from the README dry-run example, that exports moltbook-watchtower only.

For all eight default repos, run either:
  .\export_dev_migration_bundle.ps1
  .\export_dev_migration_bundle.ps1 -UseDefaultEight

To export a single repo intentionally, add -ConfirmSingleRepo to silence this warning.
'@
    }
}

function Test-AnyPathSegment {
    param([string]$RelativePath, [string[]]$Segments)
    $parts = $RelativePath -split '[\\/]' | Where-Object { $_ }
    foreach ($p in $parts) {
        foreach ($s in $Segments) {
            if ($p -eq $s) { return $true }
        }
    }
    return $false
}

function Get-GitIgnoredUntrackedPaths {
    param([string]$RepoRoot)
    Push-Location $RepoRoot
    try {
        # H1: core.quotepath=false avoids octal escape sequences (e.g. \234) that break Windows paths.
        # -z: NUL-terminated paths handle odd filenames without newline ambiguity.
        $output = git -c core.quotepath=false ls-files -z -o -i --exclude-standard 2>$null
        if ($LASTEXITCODE -ne 0) { return @() }
        if ([string]::IsNullOrEmpty($output)) { return @() }
        return @($output -split "`0" | ForEach-Object { $_.Trim("`r") } | Where-Object { $_ })
    }
    finally {
        Pop-Location
    }
}

function Copy-TreeFiltered {
    param(
        [string]$SourceRoot,
        [string]$DestRoot,
        [string[]]$ExcludeSegments,
        [switch]$IsDryRun,
        [switch]$RecordProfileSkips
    )
    if (-not (Test-Path $SourceRoot)) { return }
    if (-not $IsDryRun) {
        New-Item -ItemType Directory -Path $DestRoot -Force | Out-Null
    }
    Get-ChildItem -LiteralPath $SourceRoot -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $name = $_.Name
        if ($ExcludeSegments -contains $name) { return }
        $src = $_.FullName
        $dst = Join-Path $DestRoot $name
        $rel = $src.Substring($SourceRoot.TrimEnd('\').Length).TrimStart('\')
        if (Test-AnyPathSegment -RelativePath $rel -Segments $ExcludeSegments) { return }
        if ($_.PSIsContainer) {
            Copy-TreeFiltered -SourceRoot $src -DestRoot $dst -ExcludeSegments $ExcludeSegments -IsDryRun:$IsDryRun -RecordProfileSkips:$RecordProfileSkips
        }
        else {
            if ($IsDryRun) {
                Write-Host "[dry-run] FILE $src"
            }
            else {
                $null = Copy-Item-MigrationSafe -LiteralSrc $src -LiteralDst $dst -LogLocation 'Copy-TreeFiltered:Copy-Item' -RecordProfileSkips:$RecordProfileSkips
            }
        }
    }
}

function Get-DockerComposeServiceList {
    param([string]$ComposeFile)
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return $null
    }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        $svcs = docker compose -f $ComposeFile config --services 2>$null
        if ($LASTEXITCODE -eq 0 -and $svcs) {
            return ($svcs -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        }
    }
    finally {
        $ErrorActionPreference = $prev
    }
    return $null
}

function Get-DockerComposeVolumeList {
    param([string]$ComposeFile)
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return $null
    }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        $vols = docker compose -f $ComposeFile config --volumes 2>$null
        if ($LASTEXITCODE -eq 0 -and $vols) {
            return ($vols -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        }
    }
    finally {
        $ErrorActionPreference = $prev
    }
    return $null
}

function Get-ComposeFilesUnder {
    param([string]$Root, [int]$MaxDepth = 6)
    $files = @()
    if (-not (Test-Path $Root)) { return $files }
    $files += @(Get-ChildItem -Path $Root -Filter 'docker-compose*.yml' -File -Recurse -Depth $MaxDepth -ErrorAction SilentlyContinue)
    $files += @(Get-ChildItem -Path $Root -Filter 'docker-compose*.yaml' -File -Recurse -Depth $MaxDepth -ErrorAction SilentlyContinue)
    return @($files | Sort-Object FullName -Unique)
}

function Get-TopLevelDirSizes {
    param([string]$Root, [int]$TopN = 15)
    if (-not (Test-Path $Root)) { return @() }
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -Force -ErrorAction SilentlyContinue
    $rows = foreach ($d in $dirs) {
        # Avoid .Sum on Measure-Object under StrictMode when Sum is absent (empty trees / no Length).
        [long]$size = 0
        Get-ChildItem -LiteralPath $d.FullName -Recurse -File -Force -ErrorAction SilentlyContinue |
            ForEach-Object { $size += $_.Length }
        [PSCustomObject]@{ Path = $d.Name; SizeBytes = $size }
    }
    return $rows | Sort-Object SizeBytes -Descending | Select-Object -First $TopN
}

function Build-ConfigHintsSection {
    param([string]$RepoRoot, [string]$RepoLabel)
    $patterns = @('dotenv', 'load_dotenv', 'process\.env', 'os\.environ', 'getenv', 'config/local', '\.env')
    $exts = @('*.py', '*.ts', '*.tsx', '*.js', '*.mjs', '*.cjs', '*.json', '*.toml', '*.yaml', '*.yml')
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("=== $RepoLabel ($RepoRoot) ===")

    $rg = Get-Command rg -ErrorAction SilentlyContinue
    if ($rg) {
        foreach ($pat in $patterns) {
            $hits = @(& rg -l --glob '!**/node_modules/**' --glob '!**/.git/**' --glob '!**/venv/**' --glob '!.venv/**' $pat $RepoRoot 2>$null)
            if ($hits.Count -gt 0) {
                $lines.Add("pattern $pat : $($hits.Count) file(s)")
                foreach ($h in ($hits | Select-Object -First 40)) { $lines.Add("  $h") }
            }
        }
    }
    else {
        $files = Get-ChildItem -Path $RepoRoot -Recurse -Include $exts -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\node_modules\\|\\\.git\\|\\venv\\|\\\.venv\\' } |
            Select-Object -First 2000
        foreach ($f in $files) {
            try {
                $txt = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
                if (-not $txt) { continue }
                foreach ($pat in $patterns) {
                    if ($txt -match $pat) {
                        $lines.Add("$($f.FullName) : matches /$pat/")
                        break
                    }
                }
            }
            catch { }
        }
    }
    $lines.Add('')
    return $lines -join "`r`n"
}

# --- Prepare output ---
if (-not $DryRun) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
    New-Item -ItemType Directory -Path $reposStage -Force | Out-Null
}

$script:ProfileCopySkipped = New-Object System.Collections.Generic.List[string]
$skippedLarge = New-Object System.Collections.Generic.List[string]
$manifestRows = New-Object System.Collections.Generic.List[object]
$dockerLines = New-Object System.Collections.Generic.List[string]
$configHintsAll = New-Object System.Collections.Generic.List[string]
$sizeAuditAll = New-Object System.Collections.Generic.List[string]

foreach ($repo in $RepoRoots) {
    $repoName = Split-Path $repo -Leaf
    $destRepo = Join-Path $reposStage $repoName
    $copiedRel = New-Object System.Collections.Generic.List[string]

    if (-not (Test-Path $repo)) {
        $skippedLarge.Add("[missing] $repo")
        $manifestRows.Add([PSCustomObject]@{
                Repo       = $repoName
                SourcePath = $repo
                Copied     = '(path missing)'
                Skipped    = ''
                Install    = 'Clone from GitHub; restore bundle files into same relative paths.'
            })
        continue
    }

    $hasGit = Test-Path (Join-Path $repo '.git')
    if (-not $hasGit) {
        $skippedLarge.Add("[no .git] $repo - not a git repo; only manual copy / reports run.")
    }

    # Snapshot ignore metadata
    $metaDir = Join-Path $destRepo '_gitignore_snapshot'
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $metaDir -Force | Out-Null
        Get-ChildItem -Path $repo -Filter '.gitignore' -Recurse -File -Depth 12 -ErrorAction SilentlyContinue |
            ForEach-Object {
            $rel = $_.FullName.Substring($repo.Length).TrimStart('\')
            $safe = $rel -replace '[\\/]', '_'
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $metaDir $safe) -Force
        }
        $excludePath = Join-Path $repo '.git\info\exclude'
        if (Test-Path $excludePath) {
            Copy-Item -LiteralPath $excludePath -Destination (Join-Path $metaDir 'git_info_exclude.txt') -Force
        }
    }

    # Ignored untracked files
    $ignoredPaths = @()
    if ($hasGit) {
        $ignoredPaths = Get-GitIgnoredUntrackedPaths -RepoRoot $repo
    }

    foreach ($rel in $ignoredPaths) {
        $relNorm = ($rel -replace '/', '\').Trim()
        if ($relNorm.StartsWith('"') -and $relNorm.EndsWith('"') -and $relNorm.Length -ge 2) {
            $relNorm = $relNorm.Substring(1, $relNorm.Length - 2)
        }
        if (Test-AnyPathSegment -RelativePath $relNorm -Segments $ExcludeDirPatterns) {
            $skippedLarge.Add("$repoName : skipped (excluded segment) $relNorm")
            continue
        }
        $full = Join-Path $repo $relNorm
        $pathOk = $false
        try {
            $pathOk = Test-Path -LiteralPath $full -ErrorAction Stop
        }
        catch {
            [void]$skippedLarge.Add("$repoName : skipped (invalid path) $relNorm")
            continue
        }
        if (-not $pathOk) { continue }

        $targetPath = Join-Path $destRepo $relNorm
        if ($DryRun) {
            Write-Host "[dry-run] FILE $full -> $targetPath"
        }
        else {
            $targetDir = Split-Path $targetPath -Parent
            if ($targetDir -and -not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            Copy-Item -LiteralPath $full -Destination $targetPath -Force
            $copiedRel.Add($relNorm)
        }
    }

    # Optional .cursor/state (large) - only when requested
    if ($IncludeCursorState) {
        $stateDir = Join-Path $repo '.cursor\state'
        if (Test-Path $stateDir) {
            $destState = Join-Path $destRepo '.cursor_state_extra'
            if ($DryRun) {
                Write-Host "[dry-run] COPYTREE $stateDir -> $destState"
            }
            else {
                Copy-TreeFiltered -SourceRoot $stateDir -DestRoot $destState -ExcludeSegments @('Cache', 'GPUCache') -IsDryRun:$false
            }
            $copiedRel.Add('.cursor/state (via IncludeCursorState)')
        }
    }

    # Reports per repo
    $sizeAuditAll.Add("=== $repoName ($repo) ===")
    Get-TopLevelDirSizes -Root $repo | ForEach-Object {
        $sizeAuditAll.Add(("  {0,-40} {1:N0} bytes" -f $_.Path, $_.SizeBytes))
    }
    $sizeAuditAll.Add('')

    $configHintsAll.Add((Build-ConfigHintsSection -RepoRoot $repo -RepoLabel $repoName))

    # Docker compose inventory (software-heavy; cheap to scan from each root)
    $composeFiles = Get-ComposeFilesUnder -Root $repo -MaxDepth 8
    foreach ($cf in $composeFiles) {
        $dockerLines.Add("File: $($cf.FullName)")
        $svcs = Get-DockerComposeServiceList -ComposeFile $cf.FullName
        $vols = Get-DockerComposeVolumeList -ComposeFile $cf.FullName
        if ($svcs) {
            $dockerLines.Add('  services: ' + ($svcs -join ', '))
        }
        else {
            $dockerLines.Add('  services: (run docker compose config --services locally if Docker available)')
        }
        if ($vols) {
            $dockerLines.Add('  named volumes: ' + ($vols -join ', '))
        }
        $dockerLines.Add('  Note: named volumes are not in Git; backup with docker volume export or accept fresh data.')
        $dockerLines.Add('')
    }

    $install = "git clone <remote> $repoName; copy bundle\repos\$repoName\* into repo root for ignored files; install deps per repo (pnpm/npm/pip/uv); docker compose up as needed."
    $copiedSummary = if ($DryRun) {
        '(dry-run: no files written; see console [dry-run] FILE lines)'
    }
    elseif ($copiedRel.Count -gt 0) {
        ($copiedRel | Select-Object -First 200) -join '; '
    }
    else {
        '(none or only snapshot)'
    }
    $manifestRows.Add([PSCustomObject]@{
            Repo       = $repoName
            SourcePath = $repo
            Copied     = $copiedSummary
            Skipped    = 'See reports\skipped_large.txt for excluded-dir skips'
            Install    = $install
        })
}

# Machine profile: Cursor
if ($IncludeAppDataCursor) {
    $appDataCursor = $env:APPDATA + '\Cursor'
    $userCursor = Join-Path $env:USERPROFILE '.cursor'

    if (-not $DryRun) {
        Write-AgentDebugLog -HypothesisId 'H3' -Location 'machine_profile:block' -Message 'profile_copy_start' -Data @{
            IncludeAppDataCursor = [bool]$IncludeAppDataCursor
            appDataCursor        = $appDataCursor
            userCursor           = $userCursor
            profileStage         = $profileStage
        }
        New-Item -ItemType Directory -Path $profileStage -Force | Out-Null
        $cursorExclude = @('Cache', 'CachedData', 'GPUCache', 'Code Cache', 'logs', 'blob_storage', 'Crashpad', 'Service Worker')
        if (Test-Path $appDataCursor) {
            $destApp = Join-Path $profileStage 'AppData_Cursor'
            foreach ($child in (Get-ChildItem -LiteralPath $appDataCursor -Force -ErrorAction SilentlyContinue)) {
                if ($cursorExclude -contains $child.Name) { continue }
                if ($child.PSIsContainer) {
                    Copy-TreeFiltered -SourceRoot $child.FullName -DestRoot (Join-Path $destApp $child.Name) -ExcludeSegments $cursorExclude -IsDryRun:$false -RecordProfileSkips
                }
                else {
                    $null = Copy-Item-MigrationSafe -LiteralSrc $child.FullName -LiteralDst (Join-Path $destApp $child.Name) -LogLocation 'machine_profile:AppData_top_file' -RecordProfileSkips
                }
            }
        }
        if (Test-Path $userCursor) {
            $destU = Join-Path $profileStage 'USERPROFILE_dot_cursor'
            Copy-TreeFiltered -SourceRoot $userCursor -DestRoot $destU -ExcludeSegments $cursorExclude -IsDryRun:$false -RecordProfileSkips
        }
    }
    else {
        Write-Host "[dry-run] Would copy filtered $appDataCursor and $userCursor -> $profileStage"
    }
}

# Write reports
if (-not $DryRun) {
    if ($skippedLarge.Count -eq 0) { [void]$skippedLarge.Add('(none)') }
    if ($dockerLines.Count -eq 0) { [void]$dockerLines.Add('(no docker-compose*.yml or *.yaml found under scanned repo roots)') }
    $skippedLarge | Set-Content -Path (Join-Path $reportsDir 'skipped_large.txt') -Encoding UTF8
    $sizeAuditAll | Set-Content -Path (Join-Path $reportsDir 'SIZE_AUDIT.txt') -Encoding UTF8
    $configHintsAll | Set-Content -Path (Join-Path $reportsDir 'CONFIG_HINTS.txt') -Encoding UTF8
    $dockerLines | Set-Content -Path (Join-Path $reportsDir 'DOCKER_INVENTORY.txt') -Encoding UTF8
    $mpSkips = New-Object System.Collections.Generic.List[string]
    $mpSkips.Add('Files skipped because they were locked (often Chromium/Electron while Cursor is running). Close Cursor and re-run this script to retry copying these paths.')
    $mpSkips.Add('---')
    if ($script:ProfileCopySkipped.Count -gt 0) {
        foreach ($p in $script:ProfileCopySkipped) { $mpSkips.Add($p) }
    }
    else {
        $mpSkips.Add('(none)')
    }
    $mpSkips | Set-Content -Path (Join-Path $reportsDir 'MACHINE_PROFILE_SKIPPED.txt') -Encoding UTF8
}

# Manifest
$manifestText = @"
MIGRATION_MANIFEST - dev node bundle
Generated: $(Get-Date -Format 'o')
Host: $env:COMPUTERNAME
User: $env:USERNAME

SECURITY
------
This archive may contain secrets (.env, orchestrator configs, API keys). Encrypt the zip (e.g. 7-Zip AES) before USB transfer.
Rotate API keys and tokens after restoring on a new machine if the medium was not fully trusted.

SSH AND GIT IDENTITY (not included in repos)
--------------------------------------------
- Copy %USERPROFILE%\.ssh separately if you need the same keys, OR generate new keys on the new PC and add deploy keys.
- Export gpg keys if you sign commits: backup %APPDATA%\gnupg or use a hardware token.

DOCKER NAMED VOLUMES
--------------------
Data in Docker volumes is not in Git. To backup a volume (example):
  docker run --rm -v VOLUME_NAME:/data -v ${env:USERPROFILE}\backup:/backup alpine tar czf /backup/volume.tgz -C /data .
Restore (example):
  docker run --rm -v VOLUME_NAME:/data -v ${env:USERPROFILE}\backup:/backup alpine tar xzf /backup/volume.tgz -C /data

WSL
---
If you use WSL distros, consider: wsl --export <Name> D:\wsl-backup.tar (separate from this bundle).

REPOS
-----
"@

foreach ($row in $manifestRows) {
    $manifestText += "`r`n--- $($row.Repo) ---`r`n"
    $manifestText += "SourcePath: $($row.SourcePath)`r`n"
    $manifestText += "Paths copied (sample): $($row.Copied)`r`n"
    $manifestText += "Install: $($row.Install)`r`n"
}

$manifestText += @"

REPORTS (in bundle\reports)
---------------------------
skipped_large.txt   - paths skipped due to excluded directory segments
SIZE_AUDIT.txt        - largest top-level folders per repo
CONFIG_HINTS.txt      - grep/rg hints for env and config loading
DOCKER_INVENTORY.txt  - compose files and service/volume names (if docker CLI works)
MACHINE_PROFILE_SKIPPED.txt - Cursor profile files skipped because they were locked (see manifest CURSOR PROFILE)

CURSOR PROFILE (in bundle\machine_profile)
------------------------------------------
Filtered copy of %APPDATA%\Cursor and %USERPROFILE%\.cursor (caches excluded).
Some files may be skipped if locked while Cursor is running (e.g. Network\Cookies) — see reports\MACHINE_PROFILE_SKIPPED.txt.
On new PC: merge carefully into the same locations, or diff settings.json first.

"@

if (-not $DryRun) {
    $manifestText | Set-Content -Path (Join-Path $stageRoot 'MIGRATION_MANIFEST.txt') -Encoding UTF8
}
else {
    Write-Host '--- MIGRATION_MANIFEST (preview) ---' -ForegroundColor Cyan
    Write-Host $manifestText
}

# Zip
$zipName = "dev-migration_$ts.zip"
$zipPath = Join-Path $OutputDir $zipName

if (-not $DryRun -and -not $SkipZip) {
    if (Get-Command Compress-Archive -ErrorAction SilentlyContinue) {
        if (Test-Path $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
        Compress-Archive -LiteralPath $stageRoot -DestinationPath $zipPath -Force
        Write-Host "Wrote $zipPath" -ForegroundColor Green
    }
    else {
        Write-Warning 'Compress-Archive not available; skip zip.'
    }
}
elseif ($DryRun) {
    Write-Host "Dry-run: no files written. Output would be under $OutputDir" -ForegroundColor Yellow
}
else {
    Write-Host "SkipZip: staged at $stageRoot" -ForegroundColor Green
}

Write-Host "Done. Stage root: $stageRoot" -ForegroundColor Cyan
