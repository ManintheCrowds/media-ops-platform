---
name: Linux primary Alienware docs
overview: Record Ubuntu 24.04 Desktop as the primary OS on the Alienware+eGPU host (replacing Windows for cost), align scope docs that still say Windows, and add a short operational note on desktop + SSH + optional VPN—without editing any plan files under software/.cursor/plans.
todos:
  - id: ubuntu24-blurb
    content: Add Primary host (Ubuntu Desktop, SSH, optional VPN) to UBUNTU24_CURSOR_ALIGNMENT.md (both trees if mirrored)
    status: completed
  - id: scope-primary-os
    content: Update scope_nas_assistant.md primary host from x64 Windows to Ubuntu LTS Desktop
    status: completed
  - id: decision-log-linux
    content: Append decision-log bullet for Windows replaced by Ubuntu on Alienware + doc refs
    status: completed
isProject: false
---

# Document Linux-on-Alienware as primary host

## Context

You are installing **Ubuntu 24.04 Desktop** on the Alienware (replacing Windows) for cost. The repo already supports Linux ([LINUX_INSTALL.md](D:/portfolio-harness/local-proto/docs/LINUX_INSTALL.md), [UBUNTU24_CURSOR_ALIGNMENT.md](D:/portfolio-harness/local-proto/docs/UBUNTU24_CURSOR_ALIGNMENT.md)), but [scope_nas_assistant.md](D:/portfolio-harness/local-proto/docs/scope_nas_assistant.md) §1 still says primary host is **x64 Windows** — that should be corrected to **x64 Linux (Ubuntu LTS)** so scope matches reality.

## Changes (canonical tree: `portfolio-harness/local-proto`)

### 1. [UBUNTU24_CURSOR_ALIGNMENT.md](D:/portfolio-harness/local-proto/docs/UBUNTU24_CURSOR_ALIGNMENT.md)

After the opening paragraph (before the horizontal rule), add a short **Primary host** subsection:

- Alienware Mini + eGPU is **Ubuntu 24.04 Desktop** (replacing Windows where cost/OS preference applies).
- **Dual use:** local GUI + `openssh-server` for remote access; optional **Tailscale** or **WireGuard** for away-from-LAN access without exposing SSH broadly.
- Link to existing sections (SSH not duplicated as a full tutorial; point to Ubuntu/OpenSSH docs or one-line `sudo apt install openssh-server`).

### 2. [scope_nas_assistant.md](D:/portfolio-harness/local-proto/docs/scope_nas_assistant.md)

- In **§1 Goal**, change the primary host bullet from **x64 Windows** to **x64 Linux (Ubuntu 22.04/24.04 LTS Desktop)** — Cursor, Ollama on eGPU, OpenClaw, MCP — and add a brief note that **Windows on this box is optional / not required** for the documented stack (aligns with decision-log Alienware+eGPU topology).

### 3. [decision-log.md](D:/portfolio-harness/.cursor/state/decision-log.md)

Append under **2026-03-24** (or add a new dated block if you prefer separation) one bullet:

- **Alienware primary OS:** Ubuntu 24.04 LTS Desktop **replaces Windows** as the primary OS on the Alienware+eGPU host (cost / licensing); desktop + SSH + optional Tailscale/WireGuard; scope doc and UBUNTU24 checklist updated. Cross-ref [scope_nas_assistant.md](../../local-proto/docs/scope_nas_assistant.md).

## Sibling mirror (optional parity)

If [D:/local-proto/docs/UBUNTU24_CURSOR_ALIGNMENT.md](D:/local-proto/docs/UBUNTU24_CURSOR_ALIGNMENT.md) and [D:/local-proto/docs/scope_nas_assistant.md](D:/local-proto/docs/scope_nas_assistant.md) exist, apply the **same** substantive edits (adjust relative links for sibling paths per your existing pattern).

## Out of scope

- No changes to `software/.cursor/plans/`*.
- No vendor-specific Tailscale/WireGuard full runbooks (links or one-liners only).

