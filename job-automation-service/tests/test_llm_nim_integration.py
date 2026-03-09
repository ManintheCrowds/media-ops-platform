"""Optional NIM integration test. Skips when OPENAI_API_KEY is not set."""

import os
import pytest
from app.services.llm_client import generate_via_llm

_nim_available = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("NVIDIA_API_KEY"))


@pytest.mark.asyncio
@pytest.mark.skipif(not _nim_available, reason="OPENAI_API_KEY or NVIDIA_API_KEY not set")
async def test_nim_generate_via_llm():
    """Verify generate_via_llm returns non-empty response from NIM when configured."""
    result = await generate_via_llm("Be brief.", "Say OK in one word.")
    assert result is not None
    assert len(result.strip()) > 0
