# Manual workstation migration (copy paths)

Use this when you are **not** relying on `Invoke-ThumbDriveSeed.ps1` or the bundle scripts. Copy each block to the other PC (USB, network share, or cloud you trust), then merge on the destination.

**Security:** Treat anything under Cursor, `.env`, `.ssh`, and MCP config as **secrets**. Prefer BitLocker on the USB or an encrypted archive (7-Zip AES) before the stick leaves your sight.

Related automation docs (optional): [MIGRATION_BUNDLE_README.md](MIGRATION_BUNDLE_README.md), [THUMB_DRIVE_SEED_CHECKLIST.md](THUMB_DRIVE_SEED_CHECKLIST.md).

---

## 1. Git repositories (clone + merge ignored files)

On the **new** PC: clone from GitHub/Git remote as usual. On the **old** PC: copy anything that is **ignored by Git** but that you still need (`.env`, local tooling, large artifacts you do not push). Typical roots on this workstation:

```text
D:\software
D:\portfolio-harness
D:\openharness
D:\scp
D:\moltbook-watchtower
D:\Arc_Forge
D:\prusa_XL_soft
D:\VibeLedger
D:\Research
D:\ACE-first
```

Per-repo, common **manual** picks (only if present and you need them):

```text
D:\software\.env
D:\software\.cursor\state
D:\portfolio-harness\.env
```

Adjust drive letter and repo list to match your machine. Use each repo’s `.gitignore` as the guide for what Git will **not** carry; anything important listed there must be copied by hand or exported separately.

---

## 2. Cursor / editor profile (old PC → new PC)

Close **Cursor** (and VS Code if it shares the same profile) before copying so fewer files are locked.

### Roaming Cursor (settings, extensions, MCP, etc.)

```text
%APPDATA%\Cursor
```

Full path pattern (replace `YourUser`):

```text
C:\Users\YourUser\AppData\Roaming\Cursor
```

**High-signal subpaths** (copy tree or merge file-by-file on the new PC):

```text
%APPDATA%\Cursor\User
%APPDATA%\Cursor\User\settings.json
%APPDATA%\Cursor\User\keybindings.json
%APPDATA%\Cursor\User\snippets
%APPDATA%\Cursor\User\globalStorage
%APPDATA%\Cursor\User\mcp.json
```

**Usually skip** (large or regen-on-launch; safe to omit unless you know you need them):

```text
%APPDATA%\Cursor\Cache
%APPDATA%\Cursor\CachedData
%APPDATA%\Cursor\GPUCache
%APPDATA%\Cursor\Code Cache
%APPDATA%\Cursor\logs
%APPDATA%\Cursor\blob_storage
%APPDATA%\Cursor\Crashpad
%APPDATA%\Cursor\Service Worker
%APPDATA%\Cursor\DawnGraphiteCache
%APPDATA%\Cursor\DawnWebGPUCache
%APPDATA%\Cursor\Network
%APPDATA%\Cursor\History
%APPDATA%\Cursor\workspaceStorage
```

### Project-level Cursor (rules, skills, hooks)

```text
%USERPROFILE%\.cursor
```

Example:

```text
C:\Users\YourUser\.cursor
```

### Codex (if you use it)

```text
%USERPROFILE%\.codex
```

Example:

```text
C:\Users\YourUser\.codex
```

### VS Code user folder (optional parity)

If you still use VS Code with shared habits:

```text
%APPDATA%\Code\User
```

---

## 3. SSH and signing keys (not in Git)

```text
%USERPROFILE%\.ssh
```

GPG (if you sign commits):

```text
%APPDATA%\gnupg
```

---

## 4. Local and Cursor documentation in this repo

Copy the **scripts** folder docs you have been using (paths on the **old** PC repo):

```text
D:\software\scripts\MIGRATION_BUNDLE_README.md
D:\software\scripts\THUMB_DRIVE_SEED_CHECKLIST.md
D:\software\scripts\MANUAL_WORKSTATION_MIGRATION_PATHS.md
```

Optional: governance and AI entry docs at repo root / `docs\` (only if you want the same references on the new machine):

```text
D:\software\docs\AI_DOCUMENTATION_INDEX.md
D:\software\.cursorrules
```

---

## 5. On the new PC (merge order)

1. Install Cursor; sign in if you use account sync.
2. **Exit Cursor completely.**
3. Merge **Roaming** `User\` files (especially `settings.json`, `mcp.json`) rather than blind overwrite—diff first.
4. Merge `%USERPROFILE%\.cursor\` into the same path on the new user profile.
5. Restore `%USERPROFILE%\.codex\` if you copied it.
6. Restore `%USERPROFILE%\.ssh\` (or generate new keys and re-add deploy keys).
7. Re-open Cursor; re-authenticate OAuth MCPs and any tools that stored tokens in `globalStorage`.

---

## 6. Quick checklist

- [ ] Ten (or your chosen) repo roots copied / recloned + ignored files merged  
- [ ] `%APPDATA%\Cursor\User\` (at least `settings.json`, `mcp.json`)  
- [ ] `%USERPROFILE%\.cursor\`  
- [ ] `%USERPROFILE%\.codex\` (if used)  
- [ ] `%USERPROFILE%\.ssh\` (if needed)  
- [ ] `%APPDATA%\gnupg\` (if signing)  
- [ ] This `MANUAL_WORKSTATION_MIGRATION_PATHS.md` (or whole `scripts\` doc set) on the USB  
