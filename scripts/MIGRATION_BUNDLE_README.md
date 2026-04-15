# Dev migration bundle (`export_dev_migration_bundle.ps1`)

Exports **non-GitHub** artifacts from default `D:\` repo roots (ignored-but-present files, `.gitignore` snapshots, reports) plus a **filtered** Cursor profile (`%APPDATA%\Cursor`, `%USERPROFILE%\.cursor`) for moving to a second development PC via USB.

**Thumb-drive orchestration:** run `Invoke-ThumbDriveSeed.ps1` (see `THUMB_DRIVE_SEED_CHECKLIST.md`) to create `SEED_INDEX.txt`, the dev bundle, and an AES-256 Cursor zip in one folder.

## Prerequisites

- **Git** in `PATH`
- Optional: **Docker** (for `DOCKER_INVENTORY.txt` service/volume names via `docker compose config`)
- Optional: **rg** (ripgrep) for faster `CONFIG_HINTS.txt` generation

## Dry run (required first pass)

1. Run with **`-DryRun`** and optionally **one small repo** to validate paths quickly:

   ```powershell
   Set-Location D:\software\scripts
   .\export_dev_migration_bundle.ps1 -DryRun -RepoRoots @('D:\moltbook-watchtower')
   ```

   That command only lists **moltbook-watchtower**. It does **not** build a full multi-repo bundle.

2. Review console output:
   - **`[dry-run] FILE`** lines: files that would be copied (secrets may appear in paths).
   - **Manifest preview** at the end.

3. Open your repo **`.gitignore`** files: if something important is still missing, it may be **tracked** (already on GitHub) or under an **excluded directory** (see `ExcludeDirPatterns` in the script). Add a segment to `-ExcludeDirPatterns` only to skip *more* paths; remove a default exclude only if you intentionally want to copy huge trees (e.g. `node_modules`).

4. When satisfied, run a **full dry-run** with default eight roots (no `-RepoRoots`):

   ```powershell
   .\export_dev_migration_bundle.ps1 -DryRun
   ```

5. If the list is huge or includes test temp dirs, extend **`-ExcludeDirPatterns`** (e.g. `.pytest-tmp` is excluded by default).

## Full export

```powershell
Set-Location D:\software\scripts
.\export_dev_migration_bundle.ps1
```

The script prints the list of repository roots at the start. You should see **eight** lines by default, or **ten** with **`-UseDefaultTen`**, under `Migration bundle: N repository / tree root(s)`. If you see **1**, you passed **`-RepoRoots`** with a single path (often left over from a dry-run). Fix:

- Run **without** `-RepoRoots`, or
- Pass **`-UseDefaultEight`** or **`-UseDefaultTen`** to force the default path lists.

Optional:

- **`-UseDefaultEight`** – use the built-in list of eight `D:\...` roots (overrides a narrow `-RepoRoots`).
- **`-UseDefaultTen`** – same eight roots plus `D:\Research` and `D:\ACE-first` (useful for workstation seed; non-git trees still get size/config/docker reports).
- **`-ConfirmSingleRepo`** – suppress the warning when you intentionally export **one** repo only.
- **`-OutputDir 'D:\migration_export_custom'`** – override staging folder (default: `D:\migration_export_<timestamp>`).
- **`-SkipZip`** – stage files only; create the zip manually (e.g. 7-Zip with AES).
- **`-IncludeCursorState`** – also copy `.cursor\state` into each repo’s bundle (larger; handoff/context files).
- **`-SkipMachineCursorProfile`** – skip machine-level Cursor profile (`%APPDATA%\Cursor` + `%USERPROFILE%\.cursor` staging in `machine_profile`).
- **`-DebugMigrationLog`** – append NDJSON debug lines to `D:\software\debug-91f5e8.log` (optional; not needed for normal exports).

### Troubleshooting: Copy-Item failed on `AppData\Roaming\Cursor\Network\Cookies` (file in use)

Chromium/Electron locks cookie and network DB files while **Cursor is running**. The script **skips** locked paths, logs a warning, and lists them in **`bundle\reports\MACHINE_PROFILE_SKIPPED.txt`**, then continues (manifest, zip, Done). To copy those files too, **close Cursor** (and related processes if needed) and run the export again, or accept the skips—settings and most profile data still copy.

### Troubleshooting: zip only contains one repo (e.g. moltbook-watchtower)

You almost certainly ran with **`-RepoRoots @('D:\moltbook-watchtower')`** (or one path). That is **by design**: only those roots are staged. Run a **full export** without `-RepoRoots`, or with **`-UseDefaultEight`** / **`-UseDefaultTen`**, then check `bundle\repos\` for the expected folder count before copying to USB.

Output layout:

- `bundle\MIGRATION_MANIFEST.txt` – security notice, SSH checklist, Docker volume notes, per-repo install hints.
- `bundle\reports\` – `skipped_large.txt`, `SIZE_AUDIT.txt`, `CONFIG_HINTS.txt`, `DOCKER_INVENTORY.txt`, `MACHINE_PROFILE_SKIPPED.txt` (locked profile files skipped, if any).
- `bundle\repos\<name>\` – ignored files + `_gitignore_snapshot\`.
- `bundle\machine_profile\` – filtered Cursor profile.
- `dev-migration_<timestamp>.zip` – sibling of `bundle\` under `OutputDir`.

## After copy on the new PC

1. Clone repos from GitHub; restore **ignored** files from `bundle\repos\<name>\` into the same relative paths.
2. Merge **machine_profile** into `%APPDATA%\Cursor` and `%USERPROFILE%\.cursor` (diff `settings.json` first).
3. Copy **`%USERPROFILE%\.ssh`** separately if you rely on existing keys (not part of this bundle by default).
4. Reinstall language deps (`pnpm`/`npm`/`pip`/`uv`) from lockfiles; **do not** rely on copying `node_modules` unless you must work offline.
5. **Rotate secrets** if the USB path was not fully trusted.

## Encryption

Treat the zip as **confidential**. Prefer **7-Zip** (or similar) with **AES-256** and a strong password before moving the file to USB.
