---
name: NIM .env Loading and Tests
overview: Add .env loading to verify_nim_llm.ps1 and pre_install_check.ps1 so they read OPENAI_API_KEY from D:\software\.env or local-proto\.env, then run the full NIM integration test suite.
status: pending
priority: 4
phase: later
todos: []
isProject: false
---

# NIM .env Loading and Integration Tests

## Problem

`verify_nim_llm.ps1` and `pre_install_check.ps1` only read `$env:OPENAI_API_KEY` from the shell. They never load `.env` files, so keys in `D:\software\.env` are invisible. `nim_batch.py` and job-automation-service already load `.env`; the PowerShell scripts should align.

---

## Phase 1: Add .env Loading to PowerShell Scripts

### 1.1 Create shared Load-DotEnv helper

Add a small `Load-DotEnv` function that can be dot-sourced or inlined. It will:

- Accept a file path; return silently if file does not exist
- Parse `KEY=value` lines (skip comments, empty lines)
- Strip surrounding quotes from values
- Set `[Environment]::SetEnvironmentVariable($key, $val, 'Process')` so child processes and subsequent script logic see the vars

**Search order for NIM vars:** Try each path; first file that exists gets loaded. Do not overwrite vars already set in the shell (optional: only set if `$env:OPENAI_API_KEY` is empty).

**Paths to try (in order):**

1. `local-proto\.env` — `Join-Path $RepoRoot "local-proto" | Join-Path -ChildPath ".env"`
2. `D:\software\.env` — use `$env:SOFTWARE_ROOT` if set, else `D:\software`

### 1.2 Update [verify_nim_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_nim_llm.ps1)

- Add .env loading **before** the `param()` block (params capture `$env:OPENAI_API_KEY` at invocation time).
- Resolve paths: script lives in `local-proto/scripts/`, so `$PSScriptRoot` → `local-proto/scripts/`, parent → `local-proto/`, `.env` at `local-proto/.env`. For software: `$env:SOFTWARE_ROOT` or `D:\software`.
- Inline the Load-DotEnv logic (or dot-source a shared script) and call it for both paths.
- After loading, `$env:OPENAI_API_KEY` will be set when the param `$ApiKey = $env:OPENAI_API_KEY` is evaluated.

**Note:** In PowerShell, `param()` is parsed before any other script runs. So we cannot load .env "before" param in the same script—the param is evaluated when the script is invoked. The fix: load .env in a **separate block that runs first**. Use a `begin` block or put the load logic at the very top before `param`. Actually in PowerShell, you cannot have executable code before `param`—`param` must be first. The workaround: **dot-source a loader script** that runs before the main script, or use a **wrapper**: a small loader script that loads .env then calls the main script. Simpler: **put the load logic in the main script body**—but then `param($ApiKey = $env:OPENAI_API_KEY)` is evaluated before the body runs. So when the script starts, `$ApiKey` is bound from the current `$env:OPENAI_API_KEY` (empty). The body runs later and sets `$env:OPENAI_API_KEY`, but `$ApiKey` is already bound.

**Solution:** Load .env in the script body, then **re-read** the key after loading. Change the logic:

1. At script start (top of script, before param): Not possible.
2. **Alternative:** Use a `begin` block. In PowerShell, `param` is first, then `begin`, `process`, `end`. So we could have `param(...)` and in `begin { Load-DotEnv; $ApiKey = $env:OPENAI_API_KEY }`—but `$ApiKey` is a param, we can't reassign it easily for the rest of the script.
3. **Simpler:** Don't use param default for ApiKey. Use `param($ApiKey)` and at the start of the script: `if (-not $ApiKey) { Load-DotEnv; $ApiKey = $env:OPENAI_API_KEY }`. So we load .env only when ApiKey wasn't passed explicitly.
4. **Simplest:** Load .env unconditionally at the very top of the script (in `begin` block or right after param). Then `$ApiKey = $env:OPENAI_API_KEY` in param will still be evaluated before that. So we need to **not** use param for the key. Use:

```powershell
param(
    [string]$BaseUrl = "https://integrate.api.nvidia.com/v1",
    ...
)
# Load .env before we need the key
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$localProtoDir = Split-Path -Parent $scriptDir
$softwareRoot = if ($env:SOFTWARE_ROOT) { $env:SOFTWARE_ROOT } else { "D:\software" }
foreach ($p in @(
    (Join-Path $localProtoDir ".env"),
    (Join-Path $softwareRoot ".env")
)) {
    if (Test-Path $p) {
        Get-Content $p | ForEach-Object { ... }
        break  # or load both, latter overwrites
    }
}
$ApiKey = $env:OPENAI_API_KEY
if ([string]::IsNullOrWhiteSpace($ApiKey)) { ... }
```

Actually, loading both is better—softwareenv may have the key, local-proto might not. So: try local-proto first, then software; for each existing file, load it. Process scope means later loads overwrite earlier. So load software last if we want it to take precedence. User said they have it in softwareenv, so we want that to win. Order: local-proto first, then software (software overwrites).

### 1.3 Update [pre_install_check.ps1](D:\portfolio-harness\local-proto\scripts\pre_install_check.ps1)

- Add .env loading **before** the NIM check block (step 6, around line 139).
- Use same paths: `$localProto\.env` and `$env:SOFTWARE_ROOT\.env` or `D:\software\.env`.
- Reuse the same Load-DotEnv logic—either inline a copy or dot-source a shared `_load_dotenv.ps1` from `local-proto/scripts/`.
- After loading, `$env:OPENAI_API_KEY` will be set when the condition `$env:OPENAI_API_KEY` is checked at line 140.

**Implementation choice:** Inline the Load-DotEnv logic in both scripts to avoid a new file and dot-source complexity. Keep it short (~15 lines).

---

## Phase 2: Test All NVIDIA NIM Integration

### 2.1 Test verify_nim_llm.ps1 (standalone)

```powershell
# Clear env to simulate fresh shell, then run (should load from D:\software\.env)
$env:OPENAI_API_KEY = $null
& D:\portfolio-harness\local-proto\scripts\verify_nim_llm.ps1
# Expect: "NIM LLM OK: ..." and exit 0
```

### 2.2 Test pre_install_check.ps1 with NIM step

```powershell
# Run full pre_install_check (or with -SkipOllama -SkipTier1 to speed up)
& D:\portfolio-harness\local-proto\scripts\pre_install_check.ps1 -SkipOllama -SkipTier1
# Expect: Step 6 "[PASS] NIM LLM" when OPENAI_API_KEY is in .env
```

### 2.3 Test nim_batch.py

```powershell
cd D:\software
python scripts/nim_batch.py "Explain in one sentence what this script does." scripts/nim_batch.py
# Expect: Non-empty response
```

### 2.4 Test job-automation-service NIM (Python)

```powershell
cd D:\software\job-automation-service
python -c "import asyncio; from app.services.llm_client import generate_via_llm; print(asyncio.run(generate_via_llm('Be brief.', 'Say OK')))"
# Expect: "OK" or similar
```

### 2.5 Test job-automation-service pytest

```powershell
cd D:\software\job-automation-service
pytest tests/test_llm_nim_integration.py -v
# Expect: test_nim_generate_via_llm PASSED (when OPENAI_API_KEY in .env)
```

### 2.6 (Optional) Docker smoke test

```powershell
cd D:\software\job-automation-service
# Ensure .env has LLM_PROVIDER=openai, OPENAI_API_KEY, OPENAI_BASE_URL
docker compose up -d job-automation-service
# Hit health or a simple LLM endpoint; verify NIM responds
```

---

## File Changes Summary


| File                                                                                    | Change                                                                                                                                        |
| --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| [verify_nim_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_nim_llm.ps1)       | Add Load-DotEnv block after param; load from local-protoenv and softwareenv; then use $env:OPENAI_API_KEY for $ApiKey when param not provided |
| [pre_install_check.ps1](D:\portfolio-harness\local-proto\scripts\pre_install_check.ps1) | Add Load-DotEnv block before step 6 (NIM check); same paths                                                                                   |


---

## Load-DotEnv Logic (inline)

```powershell
function Load-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $k = $matches[1].Trim(); $v = $matches[2].Trim() -replace '^["'']|["'']$'
            [Environment]::SetEnvironmentVariable($k, $v, 'Process')
        }
    }
}
$lpEnv = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "local-proto\.env"  # adjust
$swEnv = Join-Path ($env:SOFTWARE_ROOT ?? "D:\software") ".env"
Load-DotEnv $lpEnv; Load-DotEnv $swEnv
```

**Path resolution for verify_nim_llm.ps1:** Script is at `local-proto/scripts/verify_nim_llm.ps1`. So `$PSScriptRoot` = `local-proto/scripts/`, parent = `local-proto/`, so `local-proto/.env` = `Join-Path (Split-Path $PSScriptRoot -Parent) ".env"`. For software: `$env:SOFTWARE_ROOT` or `D:\software`.

**Path resolution for pre_install_check.ps1:** It already has `$localProto = Join-Path $RepoRoot "local-proto"` and `$RepoRoot`. So `$localProto\.env` and `Join-Path ($env:SOFTWARE_ROOT ?? "D:\software") ".env"`. PowerShell 5 doesn't have `??`; use `if ($env:SOFTWARE_ROOT) { $env:SOFTWARE_ROOT } else { "D:\software" }`.

---

## Risk

**Low:** Additive changes; no credential storage changes; .env loading is best-effort (skip if file missing).