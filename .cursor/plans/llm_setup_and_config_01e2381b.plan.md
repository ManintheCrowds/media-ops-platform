---
name: LLM Setup and Config
overview: Install job-automation-service dependencies, configure LLM provider/model in .env, and pull Ollama model for local use.
status: pending
priority: 4
phase: later
todos: []
isProject: false
---

# LLM Setup and Configuration Plan

## 1. Install Dependencies

Run from the job-automation-service directory:

```bash
cd D:\software\job-automation-service
pip install -r requirements.txt
```

This installs `openai` and `anthropic` (added for provider switching) plus existing deps. Optional: use a venv first (`python -m venv venv` then activate).

---

## 2. Set LLM_PROVIDER and LLM_MODEL in .env

**Current state:** [.env.example](D:\software\job-automation-service.env.example) still has `OLLAMA_MODEL=llama2`. The new config uses `LLM_PROVIDER` and `LLM_MODEL`.

**Actions:**

- Update `.env.example` to add LLM vars and deprecate `OLLAMA_MODEL`:

```
  # LLM Configuration (ollama | openai | anthropic)
  LLM_PROVIDER=ollama
  LLM_MODEL=llama3.2

  # Ollama (when LLM_PROVIDER=ollama)
  OLLAMA_URL=http://localhost:11434
  

```

- Add the same vars to `.env` (or ensure they exist). If `.env` is missing, copy from `.env.example` first.

**Cloud switching:** For OpenAI set `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4o`, and `OPENAI_API_KEY=sk-...`. For Anthropic set `LLM_PROVIDER=anthropic`, `LLM_MODEL=claude-3-5-sonnet`, and `ANTHROPIC_API_KEY=sk-ant-...`.

---

## 3. Pull Ollama Model for Local Use

With Ollama installed and running:

```bash
ollama pull llama3.2
```

Or for stronger instruction-following:

```bash
ollama pull mistral
```

Verify with `ollama list`. Default config uses `llama3.2`; if you pull `mistral`, set `LLM_MODEL=mistral` in `.env`.

---

## Execution Order

```mermaid
flowchart LR
    A[pip install] --> B[Update .env]
    B --> C[ollama pull]
```



