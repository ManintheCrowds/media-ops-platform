"""LLM client factory for provider-agnostic cloud/local switching."""

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


async def generate_via_llm(system_content: str, user_content: str) -> Optional[str]:
    """Generate text via configured LLM provider (Ollama, OpenAI, or Anthropic).

    Uses LLM_PROVIDER and LLM_MODEL from config. Falls back to Ollama if cloud
    provider is selected but API key is missing.

    Args:
        system_content: System prompt (e.g. role/instructions).
        user_content: User prompt (e.g. cover letter request).

    Returns:
        Generated text, or None if generation failed.
    """
    provider = (settings.llm_provider or "ollama").lower()
    model = settings.llm_model or "llama3.2"

    # Try cloud providers first if configured
    if provider == "openai" and settings.openai_api_key:
        return await _generate_openai(system_content, user_content, model)
    if provider == "anthropic" and settings.anthropic_api_key:
        return await _generate_anthropic(system_content, user_content, model)

    # Default: Ollama (local)
    return await _generate_ollama(system_content, user_content, model)


async def _generate_ollama(system_content: str, user_content: str, model: str) -> Optional[str]:
    """Generate via Ollama /api/chat (OpenAI-compatible or native)."""
    import httpx

    base_url = (settings.ollama_url or "http://localhost:11434").rstrip("/")
    url = f"{base_url}/api/chat"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9},
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            message = result.get("message", {})
            content = (message.get("content") or "").strip()
            return content if content else None
    except Exception as e:
        logger.warning(f"Ollama generation failed: {e}")
        return None


async def _generate_openai(system_content: str, user_content: str, model: str) -> Optional[str]:
    """Generate via OpenAI API (or OpenAI-compatible endpoint like Ollama /v1)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,
        )
        content = (response.choices[0].message.content or "").strip()
        return content if content else None
    except Exception as e:
        logger.warning(f"OpenAI generation failed: {e}")
        return None


async def _generate_anthropic(system_content: str, user_content: str, model: str) -> Optional[str]:
    """Generate via Anthropic API."""
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_content,
            messages=[{"role": "user", "content": user_content}],
        )
        if response.content and len(response.content) > 0:
            block = response.content[0]
            if hasattr(block, "text"):
                return (block.text or "").strip() or None
        return None
    except Exception as e:
        logger.warning(f"Anthropic generation failed: {e}")
        return None


async def is_ollama_available() -> bool:
    """Check if Ollama service is available."""
    import httpx

    base_url = (settings.ollama_url or "http://localhost:11434").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/api/tags")
            return response.status_code == 200
    except Exception:
        return False
