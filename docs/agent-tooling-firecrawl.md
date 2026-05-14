# Firecrawl setup for Cursor Cloud Agents

**Purpose:** Make web research reliable for future agents without ad hoc CLI installs or browser-login stalls.  
**Audience:** Humans configuring Cursor Cloud Agent environments and agents verifying research tooling.  
**Related:** [AI Documentation Index](AI_DOCUMENTATION_INDEX.md), [Development Guide](DEVELOPMENT.md), [Research notes](research/README.md).

## Why this exists

Some research workflows prefer the Firecrawl CLI for search and page extraction. In the 2026-05-14 local-first research session, the CLI had to be installed manually and then blocked on interactive browser authentication. Future agents should start with Firecrawl already installed and authenticated through an environment secret.

## Target state

A fresh Cursor Cloud Agent can run:

```bash
firecrawl --version --auth-status
firecrawl --status
```

Expected:

```text
authenticated: true
```

or equivalent status output showing that `FIRECRAWL_API_KEY` is loaded.

## Configuration requirements

1. **Install the CLI in the agent image or startup script**

   ```bash
   npm install -g firecrawl-cli
   ```

2. **Provide `FIRECRAWL_API_KEY` as an environment secret**

   - Do not commit it to this repository.
   - Do not place it in tracked docs, examples, or shell history.
   - Prefer the Cursor Cloud Agent environment configuration or secret store over a repo `.env` file.

3. **Verify non-interactively**

   ```bash
   firecrawl --version --auth-status
   firecrawl --status
   ```

   If `authenticated: false`, the environment is not ready for unattended agents.

4. **Keep scratch output out of git**

   Research output should go under `.firecrawl/`, which is ignored by this repo.

## Agent workflow

Before starting a web-heavy research task:

```bash
firecrawl --version --auth-status
```

If authenticated:

```bash
mkdir -p .firecrawl/<topic>
firecrawl search "<query>" --json -o ".firecrawl/<topic>/search.json"
```

If not authenticated:

- Do not run a browser-login loop during autonomous research unless the user is actively available to authenticate.
- Record that Firecrawl is unavailable and use the approved fallback for the task.
- Include a note in the final summary that the cloud environment needs Firecrawl setup.

## Cursor environment setup agent prompt

Use this prompt at [cursor.com/onboard](https://cursor.com/onboard) to make the setup durable for future agents:

```text
Configure the Cursor Cloud Agent environment for /workspace so future agents can use Firecrawl without ad hoc installs. Install firecrawl-cli globally in the agent startup/image, provide FIRECRAWL_API_KEY through the cloud agent secret/environment configuration (do not write it to the repo), verify `firecrawl --version --auth-status` and `firecrawl --status` return authenticated status in a fresh agent, and keep `.firecrawl/` scratch output ignored by git.
```

## Security notes

- Treat `FIRECRAWL_API_KEY` as a secret with the same care as API tokens.
- Rotate the key if it appears in logs, commits, screenshots, or shared transcripts.
- Avoid scraping private, authenticated, or sensitive user data unless the user explicitly authorizes that task and the data-handling path is documented.
- Do not store raw third-party page dumps in git unless licensing and provenance are clear; summarize and cite instead.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `firecrawl: command not found` | CLI not installed in the image/startup script | Add `npm install -g firecrawl-cli` to environment setup. |
| `authenticated: false` | Missing or invalid `FIRECRAWL_API_KEY` | Add/rotate the secret in the cloud agent environment. |
| Browser auth URL appears | CLI is trying interactive login | Stop and configure `FIRECRAWL_API_KEY` instead for unattended agents. |
| `.firecrawl/` appears in git status | Ignore rule missing or overridden | Ensure `.firecrawl/` is present in `.gitignore`. |
