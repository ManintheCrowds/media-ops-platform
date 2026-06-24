"""Targeted tests for services.base BaseServiceClient error handling."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from services.base import BaseServiceClient
from app.exceptions import ServiceError


class _DummyServiceClient(BaseServiceClient):
    """Minimal concrete client for base-class coverage."""

    def _build_headers(self):
        return {}

    def _get_api_base_url(self) -> str:
        return self.base_url

    def _get_ping_endpoint(self) -> str:
        return "/health"


def _response(status_code: int = 200, json_data=None):
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=json_data if json_data is not None else {"ok": True})
    return response


@pytest.mark.unit
class TestBaseServiceClient:
    """Cover _handle_request branches in BaseServiceClient."""

    @pytest.mark.asyncio
    async def test_handle_request_success_200(self):
        client = _DummyServiceClient("http://example:8080")
        async with client:
            result = await client._handle_request(
                AsyncMock(return_value=_response(200, {"value": 1})),
                "test_method",
            )
        assert result == {"value": 1}

    @pytest.mark.asyncio
    async def test_handle_request_success_201(self):
        client = _DummyServiceClient("http://example:8080")
        async with client:
            result = await client._handle_request(
                AsyncMock(return_value=_response(201, {"created": True})),
                "test_method",
            )
        assert result == {"created": True}

    @pytest.mark.asyncio
    async def test_handle_request_success_204_empty_json(self):
        client = _DummyServiceClient("http://example:8080")
        response = _response(204)
        response.json = MagicMock(side_effect=Exception("no body"))
        async with client:
            result = await client._handle_request(
                AsyncMock(return_value=response),
                "test_method",
            )
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_handle_request_non_200_returns_default(self):
        client = _DummyServiceClient("http://example:8080")
        async with client:
            result = await client._handle_request(
                AsyncMock(return_value=_response(500)),
                "test_method",
                default_return=[],
            )
        assert result == []

    @pytest.mark.asyncio
    async def test_handle_request_non_200_raises(self):
        client = _DummyServiceClient("http://example:8080")
        async with client:
            with pytest.raises(ServiceError):
                await client._handle_request(
                    AsyncMock(return_value=_response(500)),
                    "test_method",
                    raise_on_error=True,
                    exception_class=ServiceError,
                )

    @pytest.mark.asyncio
    async def test_handle_request_http_error_returns_default(self):
        client = _DummyServiceClient("http://example:8080")
        async with client:
            result = await client._handle_request(
                AsyncMock(side_effect=httpx.RequestError("boom")),
                "test_method",
                default_return=None,
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_request_http_error_raises(self):
        client = _DummyServiceClient("http://example:8080")
        async with client:
            with pytest.raises(ServiceError):
                await client._handle_request(
                    AsyncMock(side_effect=httpx.RequestError("boom")),
                    "test_method",
                    raise_on_error=True,
                    exception_class=ServiceError,
                )

    @pytest.mark.asyncio
    async def test_handle_request_timeout_raises(self):
        client = _DummyServiceClient("http://example:8080")
        async with client:
            with pytest.raises(ServiceError):
                await client._handle_request(
                    AsyncMock(side_effect=httpx.TimeoutException("slow")),
                    "test_method",
                    raise_on_error=True,
                    exception_class=ServiceError,
                )

    @pytest.mark.asyncio
    async def test_handle_request_unexpected_error_raises(self):
        client = _DummyServiceClient("http://example:8080")
        async with client:
            with pytest.raises(ServiceError):
                await client._handle_request(
                    AsyncMock(side_effect=RuntimeError("unexpected")),
                    "test_method",
                    raise_on_error=True,
                    exception_class=ServiceError,
                )

    @pytest.mark.asyncio
    async def test_ensure_session_creates_client(self):
        client = _DummyServiceClient("http://example:8080")
        assert client._session is None
        await client._ensure_session()
        assert client._session is not None
        await client.__aexit__(None, None, None)
