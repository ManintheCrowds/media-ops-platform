# NVIDIA NIM Offload Guide

Use NVIDIA NIM to offload development tasks and reduce Cursor usage. NIM is an OpenAI-compatible API with free tier for prototyping.

## Quick Setup

1. **API key:** Get one at [build.nvidia.com](https://build.nvidia.com/settings/api-keys)
2. **Env vars:** Add to `.env` (software root or job-automation-service):

```env
OPENAI_API_KEY=<your-nvidia-api-key>
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
```

For `nim_batch.py`, also supported: `NVIDIA_API_KEY`

## Tier 1: job-automation-service

Set in `job-automation-service/.env`:

```env
LLM_PROVIDER=openai
LLM_MODEL=meta/llama-3.1-8b-instruct
OPENAI_API_KEY=<your-nvidia-api-key>
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
```

Cover letters, agents, and any flow using `generate_via_llm` will use NIM.

## Tier 2: nim_batch.py Script

Standalone script for ad-hoc offload tasks. Run from terminal (not Cursor):

```bash
# Explain code
python scripts/nim_batch.py "explain this code" job-automation-service/app/services/cover_letter.py

# Add docstrings (code-focused model)
python scripts/nim_batch.py "add docstrings" path/to/module.py --model mistralai/codestral-22b-instruct-v0.1

# Summarize logs
python scripts/nim_batch.py "summarize" path/to/log.txt --output summary.txt

# Batch mode: process directory
python scripts/nim_batch.py "add docstrings" --dir job-automation-service/app/services/
python scripts/nim_batch.py "summarize" --dir logs/ --glob "*.log" --output-dir summaries/
```

**Dependencies:** `pip install openai python-dotenv` (or use job-automation-service venv)

**Env:** Loads `.env` from software root. Uses `NVIDIA_API_KEY` or `OPENAI_API_KEY` + `OPENAI_BASE_URL`.

## Quick Wins Verification

```powershell
# Smoke test nim_batch.py
cd D:\software
python scripts/nim_batch.py "Explain in one sentence what this script does." scripts/nim_batch.py

# Smoke test job-automation-service NIM path
cd job-automation-service
python -c "import asyncio; from app.services.llm_client import generate_via_llm; print(asyncio.run(generate_via_llm('Be brief.', 'Say OK')))"
```

## PowerShell Aliases

Source `scripts/nim_aliases.ps1` for shortcuts:

```powershell
. D:\software\scripts\nim_aliases.ps1
# Or add to $PROFILE for persistent use

nim-explain job-automation-service/app/services/cover_letter.py
nim-docs path/to/module.py
nim-summary path/to/log.txt
```

## NIM Models (org/model format)

| Model | Use case |
|-------|----------|
| `meta/llama-3.1-8b-instruct` | General |
| `mistralai/codestral-22b-instruct-v0.1` | Code |
| `ibm/granite-34b-code-instruct` | Code |
| `google/codegemma-7b` | Code |
| `deepseek-ai/deepseek-r1` | Reasoning |

Browse full catalog: [build.nvidia.com/explore/discover](https://build.nvidia.com/explore/discover)

## Offload Discipline

- **Use Cursor for:** Navigation, multi-file edits, debugging, tool use
- **Use NIM for:** Long generations, batch analysis, simple code tasks, explain/refactor/docstrings
