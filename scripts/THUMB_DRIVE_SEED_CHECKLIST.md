# Thumb-drive workstation seed checklist

Use this with `Invoke-ThumbDriveSeed.ps1`, `export_dev_migration_bundle.ps1`, and `Build-CursorFullEncryptedArchive.ps1` under `D:\software\scripts\`. Treat every bundle as **confidential** until encrypted (7-Zip AES-256 or BitLocker USB).

## What GitHub already carries (clone on the new machine)

After `git clone`, you get most **policy and prose** without USB:

| Area | Repo / path (after clone) |
|------|---------------------------|
| Agent skills and rules | `portfolio-harness/.cursor/skills/`, `portfolio-harness/.cursor/rules/` |
| OSINT tooling | `portfolio-harness/osint-tools/` |
| Pentagi | `portfolio-harness/pentagi/` |
| Obliteratus analysis writeups | `portfolio-harness/docs/obliteratus_analysis/` |
| Frontier ops framing | `portfolio-harness/docs/FRONTIER_OPERATIONS_MANIFESTO.md` |
| Obliteratus implementation | `software/OBLITERATUS-src/` (inside `ManintheCrowds/software`) |

USB is for what **must not** or **does not** live in public Git: ignored files, machine Cursor profile, MCP secrets, local research trees, keys.

## Tier 1: Scripted bundles (run on old PC, copy to USB)

1. **Close Cursor** (reduces locked profile files; see `MACHINE_PROFILE_SKIPPED.txt` if not).
2. **Dev migration bundle** (gitignored artifacts + reports + filtered Cursor profile):

   ```powershell
   Set-Location D:\software\scripts
   .\export_dev_migration_bundle.ps1 -UseDefaultTen -OutputDir 'D:\workstation_seed_<YYYYMMDD>'
   ```

   `-UseDefaultTen` adds `D:\Research` and `D:\ACE-first` to the default eight git roots. If those folders are **not** git repos, you still get **SIZE_AUDIT**, **CONFIG_HINTS**, and **DOCKER_INVENTORY** for them; ignored-file export is limited until you use git or mirror manually (Tier 2).

3. **Cursor-only AES zip** (settings, `mcp.json`, `.cursor` skills, optional Codex):

   ```powershell
   .\Build-CursorFullEncryptedArchive.ps1 -OutputDir 'D:\workstation_seed_<YYYYMMDD>' -IncludeCodex
   ```

   Or use `-StageOnly` first, inspect `cursor_full_*`, then re-run without `-StageOnly` to zip.

4. **One-shot orchestrator** (same folder, prompts for zip password at Cursor step):

   ```powershell
   .\Invoke-ThumbDriveSeed.ps1 -OutputDir 'D:\workstation_seed_<YYYYMMDD>' -UseDefaultTen -IncludeCodex
   ```

5. Open `SEED_INDEX.txt` in the seed folder: it lists artifacts and restore order.

## Tier 2: Large or non-git knowledge trees (`D:\Research`, `D:\ACE-first`)

If these are not git repos (or you need a **full** mirror including tracked + ignored without using Git):

```powershell
$usb = 'E:\seed_adhoc'   # example: thumb drive path
robocopy 'D:\Research' (Join-Path $usb 'Research') /MIR /R:1 /W:1 /XD node_modules .git
robocopy 'D:\ACE-first' (Join-Path $usb 'ACE-first') /MIR /R:1 /W:1 /XD node_modules .git
```

Adjust `/XD` for your largest disposable dirs. Prefer **encrypted** container around `seed_adhoc` if it can hold sensitive notes.

## Tier 3: Identity and signing (never public Git)

- `%USERPROFILE%\.ssh` (or new keys on new PC + update deploy keys).
- `%APPDATA%\gnupg` if you sign commits.
- Git credential manager / Windows Credential Manager entries you rely on (re-auth is often easier than copying blobs).

## Tier 4: Toolchain reproducibility

- **Node**: `node -v`; lockfiles in repos; reinstall with `pnpm i` / `npm ci` rather than copying `node_modules`.
- **Python**: `uv pip freeze` or `pip freeze` from each active venv; or commit `requirements.txt` / `uv.lock` only.
- **Windows packages**: `winget export -o D:\workstation_seed_<id>\winget-packages.json` (optional).
- **Docker**: named volumes are not in Git; see `DOCKER_INVENTORY.txt` and export volumes if you need data, not just images.

## Tier 5: PKM and second-brain (if applicable)

- Obsidian vault path(s), Foam workspace, Excalidraw / Canvas assets **outside** repos.
- `.cursor/state`, handoff files: optional `-IncludeCursorState` on the dev export when you want agent continuity (larger).

## Tier 6: MCP and env (mental model)

- `mcp.json` is in the Cursor archive; **environment variables** referenced there must be recreated on the new PC (names documented in a private note, values from a password manager).
- OAuth-based MCPs (BrowserStack, Google, etc.) usually need **re-login** once.

## Tier 7: After paste on new PC

1. Decrypt / extract bundles.
2. Clone all GitHub repos; restore **ignored** files from `bundle\repos\<name>\` into matching paths.
3. Merge `machine_profile` and encrypted Cursor tree per `MIGRATION_BUNDLE_README.md` and `MANIFEST.txt` inside the Cursor zip.
4. Run each repo’s install and `pytest` / `pnpm test` / CI-equivalent once.
5. **Rotate secrets** if the USB path was not fully trusted.

## Gap analysis (common “we forgot” items)

| Item | Why it slips |
|------|----------------|
| Scheduled tasks / cron | Not in repo |
| Hosts file, corporate proxy PAC | Machine local |
| VPN profiles | Security policy |
| License files (JetBrains, etc.) | Not in Git |
| Local LLM weights / Hugging Face cache | Huge; re-download or separate disk |
| Android SDK / platform-tools | Reinstall or zip separately |
| WSL distros | `wsl --export` per distro |
| Browser extension settings | Often account-synced; otherwise profile export |

This list is intentionally conservative: seed **provenance** (what came from where) and **verification** (one test command per repo) on the new machine, not only files.
