---
name: NIM Cross-Repo Integration
overview: Integrate NVIDIA NIM across software (Docker env passthrough) and local-proto (TOOLS_TO_INTEGRATE, orchestrator config, verify script, credential vault documentation).
status: pending
priority: 4
phase: later
todos: []
isProject: false
---

# NIM Cross-Repo Integration Plan

## Scope

Wire NIM into Docker job-automation-service and local-proto tooling. No NIM worker or task queue in this plan.

---

## Phase 1: Software - Docker NIM Env Passthrough

### 1.1 Update docker-compose.yml

In [job-automation-service/docker-compose.yml](D:\software\job-automation-service\docker-compose.yml), add NIM env vars to the `job-automation-service` service so the container uses NIM when host `.env` has them:

```yaml
environment:
  - DATABASE_URL=postgresql://jobautomation:password@job-automation-db:5432/jobautomation
  - OLLAMA_URL=${OLLAMA_URL:-http://host.docker.internal:11434}
  - LLM_PROVIDER=${LLM_PROVIDER:-ollama}
  - LLM_MODEL=${LLM_MODEL:-llama3.2}
  - OPENAI_API_KEY=${OPENAI_API_KEY:-}
  - OPENAI_BASE_URL=${OPENAI_BASE_URL:-}
```

Source: host `.env` or shell env. Docker Compose reads from `.env` in the compose file directory by default.

### 1.2 Document in README

Add a short note to [job-automation-service/README.md](D:\software\job-automation-service\README.md) (or existing env docs): when running via Docker, set NIM vars in `.env` at `job-automation-service/` or export before `docker compose up`; the container will use NIM when `LLM_PROVIDER=openai` and `OPENAI_API_KEY` is set.

---

## Phase 2: Local-Proto - nim_batch in TOOLS_TO_INTEGRATE

### 2.1 Add nim_batch to CLI table

In [local-proto/docs/TOOLS_TO_INTEGRATE.md](D:\portfolio-harness\local-proto\docs\TOOLS_TO_INTEGRATE.md), add a row to the "CLI / Scripts" table (Tier 1):


| Tool          | Path                             | Risk | Invocation                                                                                |
| ------------- | -------------------------------- | ---- | ----------------------------------------------------------------------------------------- |
| **nim_batch** | D:\software\scripts\nim_batch.py | Low  | `python D:\software\scripts\nim_batch.py "prompt" path` or `--dir dir/ --output-dir out/` |


Include a one-line note: offloads explain, docstrings, summarize to NVIDIA NIM; requires `OPENAI_API_KEY` + `OPENAI_BASE_URL` in env or `.env`.

---

## Phase 3: Local-Proto - Orchestrator and Env

### 3.1 Extend orchestrator_config.json

In [local-proto/.cursor/orchestrator_config.json](D:\portfolio-harness\local-proto.cursor\orchestrator_config.json), add NIM fields (values from env; do not store secrets in JSON):

```json
{
  "ollama_url": "http://localhost:11434",
  "ollama_model": "llama3.2",
  "nim_base_url": "https://integrate.api.nvidia.com/v1",
  "nim_model": "meta/llama-3.1-8b-instruct",
  "cursor_api_key": "",
  ...
}
```

### 3.2 Document in .env.example

In [local-proto/.env.example](D:\portfolio-harness\local-proto.env.example), add:

```
# NVIDIA NIM (optional - for nim_batch, job-automation-service)
# OPENAI_API_KEY=nvapi-...
# OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
```

---

## Phase 4: Local-Proto - NIM Verification Script

### 4.1 Create verify_nim_llm.ps1

Create [local-proto/scripts/verify_nim_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_nim_llm.ps1):

- Params: `$ApiKey` (from env `OPENAI_API_KEY`), `$BaseUrl` (default `https://integrate.api.nvidia.com/v1`), `$Model` (default `meta/llama-3.1-8b-instruct`), `$TimeoutSec` (default 60)
- If `$ApiKey` is empty, exit 0 with "[SKIP] NIM (OPENAI_API_KEY not set)"
- POST to `$BaseUrl/chat/completions` with OpenAI-compatible body: `model`, `messages: [{role: user, content: "Reply with exactly: OK"}]`
- Header: `Authorization: Bearer $ApiKey`
- On success: Write-Host "NIM LLM OK", exit 0
- On failure: Write-Error, exit 1

Reference: [verify_ollama_llm.ps1](D:\portfolio-harness\local-proto\scripts\verify_ollama_llm.ps1) for structure.

### 4.2 Extend pre_install_check.ps1

In [local-proto/scripts/pre_install_check.ps1](D:\portfolio-harness\local-proto\scripts\pre_install_check.ps1):

- Add `-SkipNIM` switch (default false)
- Add block: if `-not $SkipNIM` and `$env:OPENAI_API_KEY`, run `verify_nim_llm.ps1`; if it fails, set `$failed = $true`
- If `OPENAI_API_KEY` not set, skip NIM check (do not fail)
- If `-SkipOllama` is used, consider NIM as alternative: if NIM vars set and NIM verify passes, treat LLM requirement as satisfied. Logic: when `$SkipOllama`, run NIM verify if NIM vars set; if both Ollama and NIM are skipped or unavailable, only fail if neither passes.

Simpler approach: add a separate "6. NIM LLM (optional)" check that runs only when `OPENAI_API_KEY` is set; pass/fail does not block install (informational). Or: when `-SkipOllama`, require NIM verify to pass if NIM vars are set. Document: "Use -SkipOllama when using NIM instead of Ollama; set OPENAI_API_KEY and OPENAI_BASE_URL."

---

## Phase 5: Local-Proto - Credential Vault Documentation

### 5.1 Document NIM in vault usage

Add a section to [local-proto/docs/AI_CREDENTIAL_VAULT_DESIGN.md](D:\portfolio-harness\local-proto\docs\AI_CREDENTIAL_VAULT_DESIGN.md) or create a short note in [local-proto/.env.example](D:\portfolio-harness\local-proto.env.example):

**NIM via credential vault:** Store with `credential_vault_create(site="nvidia_nim", email="https://integrate.api.nvidia.com/v1", password="<api_key>")`. Retrieve with `credential_vault_get("nvidia_nim")`; use `email` as base_url, `password` as api_key. Agents can use this when env vars are not available.

Optional: add a "Supported sites" or "API keys" subsection listing `nvidia_nim` with the email/password convention.

---

## Execution Order

```mermaid
flowchart LR
    A[Phase1_Docker] --> B[Phase2_TOOLS]
    B --> C[Phase3_Orchestrator]
    C --> D[Phase4_VerifyScript]
    D --> E[Phase5_VaultDocs]
```



---

## Out of Scope

- NIM worker (task queue + human review)
- Credential vault schema changes
- MCP server for NIM

---

## Risk

- **Low:** Additive; Docker env passthrough is standard; verify script is optional; no credential vault code changes

