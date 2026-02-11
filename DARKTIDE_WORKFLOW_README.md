# Darktide Diagnostic and Fix Workflow

## Overview

This comprehensive workflow implements all recommendations from the security review, providing a safe, diagnostic-driven approach to fixing Darktide SSL timeout issues.

## Architecture

The workflow consists of 6 PowerShell scripts:

- **darktide_common.ps1** - Shared utilities and functions
- **darktide_diagnostic.ps1** - Phase 1: Comprehensive diagnostics
- **darktide_fix.ps1** - Phase 2: Targeted safe fixes
- **darktide_validate.ps1** - Phase 3: Post-fix validation
- **darktide_rollback.ps1** - Phase 4: Restore original state
- **darktide_workflow.ps1** - Main orchestrator script

## Quick Start

### Run Full Workflow

```powershell
# Run as Administrator for firewall changes
.\darktide_workflow.ps1 -Phase All
```

### Run Individual Phases

```powershell
# Diagnostics only
.\darktide_workflow.ps1 -Phase Diagnostic

# Diagnostics + Fixes
.\darktide_workflow.ps1 -Phase Diagnostic,Fix

# Validation only
.\darktide_workflow.ps1 -Phase Validate

# Rollback
.\darktide_workflow.ps1 -Phase Rollback -BackupTimestamp 20251231_160000
```

### Dry Run (No Changes)

```powershell
.\darktide_workflow.ps1 -Phase All -WhatIf
```

## Phase Details

### Phase 1: Diagnostic

**Script:** `darktide_diagnostic.ps1`

**What it does:**
- Enables schannel logging
- Sets up network packet capture guidance
- Analyzes Windows Event Logs for schannel errors
- Compares Darktide vs PowerShell network behavior
- Tests connectivity to backend and revocation servers
- Analyzes system configuration (firewall, certificates, network adapters)
- Generates comprehensive diagnostic report

**Output:**
- HTML diagnostic report in `darktide_reports/`
- CSV export of schannel events
- Console output with findings

**Usage:**
```powershell
.\darktide_diagnostic.ps1
.\darktide_diagnostic.ps1 -Verbose 
.\darktide_diagnostic.ps1 -OutputPath "C:\custom\report.html"
```

### Phase 2: Fix

**Script:** `darktide_fix.ps1`

**What it does:**
- Creates backup of current state (firewall rules, registry, network config)
- Generates automatic rollback script
- Creates restricted firewall rules (backend IPs only, port 443, Private/Domain profiles)
- Tests revocation server connectivity (does NOT disable revocation)
- Logs all changes made

**Security Features:**
- ✅ Does NOT disable certificate revocation globally
- ✅ Creates restricted firewall rules (not broad)
- ✅ All changes are logged and reversible
- ✅ Automatic rollback script generation

**Output:**
- Backup JSON file in `darktide_reports/`
- Rollback script: `darktide_rollback_YYYYMMDD_HHMMSS.ps1`
- Changes log file

**Usage:**
```powershell
# Requires Administrator for firewall changes
.\darktide_fix.ps1

# Dry run
.\darktide_fix.ps1 -WhatIf

# Skip firewall (if not admin)
.\darktide_fix.ps1 -SkipFirewall
```

### Phase 3: Validate

**Script:** `darktide_validate.ps1`

**What it does:**
- Validates backend connectivity (PowerShell baseline)
- Verifies firewall rules are correct
- Monitors Darktide network connections
- Checks for new schannel errors
- Tests authentication flow (with user interaction)
- Monitors for side effects (other apps, system errors)
- Generates validation report with before/after comparison

**Output:**
- HTML validation report
- Before/after state comparison

**Usage:**
```powershell
.\darktide_validate.ps1

# With before state for comparison
.\darktide_validate.ps1 -BeforeStatePath "darktide_reports\backup_20251231_160000.json"
```

### Phase 4: Rollback

**Script:** `darktide_rollback.ps1`

**What it does:**
- Lists available backups
- Restores firewall rules to original state
- Restores certificate revocation settings
- Restores network configuration
- Validates rollback completion

**Usage:**
```powershell
# Interactive (lists available backups)
.\darktide_rollback.ps1

# With specific backup timestamp
.\darktide_rollback.ps1 -BackupTimestamp 20251231_160000

# With backup file path
.\darktide_rollback.ps1 -BackupPath "darktide_reports\backup_20251231_160000.json"

# Dry run
.\darktide_rollback.ps1 -BackupTimestamp 20251231_160000 -WhatIf
```

## Main Orchestrator

**Script:** `darktide_workflow.ps1`

**Features:**
- Runs phases sequentially or individually
- Passes data between phases (diagnostic results → fixes)
- Provides progress feedback
- Handles errors gracefully
- Supports dry-run mode
- Saves workflow state

**Usage Examples:**

```powershell
# Full workflow
.\darktide_workflow.ps1 -Phase All

# Diagnostics only
.\darktide_workflow.ps1 -Phase Diagnostic

# Diagnostics + Fixes (no validation)
.\darktide_workflow.ps1 -Phase Diagnostic,Fix

# Dry run full workflow
.\darktide_workflow.ps1 -Phase All -WhatIf

# Verbose output
.\darktide_workflow.ps1 -Phase All -Verbose

# Skip firewall (if not admin)
.\darktide_workflow.ps1 -Phase All -SkipFirewall
```

## Security Features

### ✅ Safe Practices Implemented

1. **No Global Certificate Revocation Disable**
   - Certificate revocation checking is preserved
   - Only tests connectivity to revocation servers
   - Provides guidance if servers are unreachable

2. **Restricted Firewall Rules**
   - Rules limited to specific backend IPs (18.160.181.0/24)
   - Port 443 only
   - Private/Domain profiles only (NOT Public)
   - Logging enabled for monitoring

3. **Complete Rollback Capability**
   - Automatic backup before any changes
   - Rollback script generated automatically
   - All changes logged and reversible

4. **Comprehensive Validation**
   - Before/after state comparison
   - Side effect monitoring
   - Security verification (certificate revocation still enabled)

## File Structure

```
D:\software\
├── darktide_common.ps1           # Shared utilities
├── darktide_diagnostic.ps1       # Phase 1: Diagnostics
├── darktide_fix.ps1              # Phase 2: Fixes
├── darktide_validate.ps1         # Phase 3: Validation
├── darktide_rollback.ps1         # Phase 4: Rollback
├── darktide_workflow.ps1         # Main orchestrator
└── darktide_reports\              # Generated reports
    ├── diagnostics_*.html
    ├── validation_*.html
    ├── backup_*.json
    ├── changes_*.log
    └── workflow_*.json
```

## Troubleshooting

### Script Not Found Errors

Ensure all scripts are in the same directory and `darktide_common.ps1` is present.

### Administrator Privileges Required

Firewall changes require Administrator privileges. Either:
- Run PowerShell as Administrator
- Use `-SkipFirewall` parameter

### Darktide Not Found

The scripts search standard Steam library locations. If Darktide is installed elsewhere, you may need to modify `Get-DarktidePath` in `darktide_common.ps1`.

### Rollback Issues

If rollback fails:
1. Check backup file exists in `darktide_reports/`
2. Verify backup file is valid JSON
3. Run rollback with `-Verbose` for detailed output
4. Manually restore using backup JSON file

## Best Practices

1. **Always run diagnostics first** to understand the root cause
2. **Review diagnostic report** before applying fixes
3. **Use dry-run mode** (`-WhatIf`) to preview changes
4. **Run validation** after fixes to verify they work
5. **Keep backups** - rollback scripts are automatically generated
6. **Monitor side effects** - validation phase checks for issues

## Comparison to Original Script

| Feature | Original Script | New Workflow |
|---------|----------------|--------------|
| Certificate Revocation | ❌ Disabled globally | ✅ Preserved (secure) |
| Firewall Rules | ❌ Broad (all IPs/ports) | ✅ Restricted (backend IPs only) |
| Diagnostics | ❌ None | ✅ Comprehensive |
| Validation | ❌ None | ✅ Full validation |
| Rollback | ❌ Manual | ✅ Automatic |
| Security | ❌ HIGH risk | ✅ LOW risk |

## Support

For issues or questions:
1. Review diagnostic report for detailed findings
2. Check validation report for before/after comparison
3. Review `DARKTIDE_FIX_REVIEW.md` for security considerations
4. Use rollback if issues occur

## Next Steps After Running Workflow

1. **Test Darktide connection** manually
2. **Review validation report** for any warnings
3. **Monitor Event Viewer** for schannel errors
4. **If issues persist:**
   - Review diagnostic report recommendations
   - Check network connectivity to revocation servers
   - Consider VPN/TAP adapter interference
   - Review antivirus SSL scanning settings



