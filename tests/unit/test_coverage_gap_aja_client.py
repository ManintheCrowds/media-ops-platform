"""Targeted tests for services.video_encoder.aja_client to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from services.video_encoder.aja_client import AJAHELOClient, AJAHELOEndpoints
from app.exceptions import EncoderConnectionError, EncoderRecordingError


def _mock_response(status: int, json_data=None, json_error=None):
    response = MagicMock()
    response.status = status
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    if json_error:
        response.json = AsyncMock(side_effect=json_error)
    else:
        response.json = AsyncMock(return_value=json_data or {})
    return response


@pytest.mark.unit
class TestAJAHELOClient:
    """Cover AJA HELO client request and error handling paths."""

    @pytest.mark.asyncio
    async def test_handle_api_error_json_body(self):
        client = AJAHELOClient("192.168.1.10")
        response = MagicMock()
        response.status = 400
        response.json = AsyncMock(return_value={"error": "bad request"})
        with pytest.raises(EncoderRecordingError, match="Invalid request"):
            await client._handle_api_error(response)

    @pytest.mark.asyncio
    async def test_handle_api_error_non_json_body(self):
        client = AJAHELOClient("192.168.1.10")
        response = MagicMock()
        response.status = 401
        response.json = AsyncMock(side_effect=ValueError("not json"))
        with pytest.raises(EncoderConnectionError, match="Authentication required"):
            await client._handle_api_error(response)

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        client = AJAHELOClient("192.168.1.10")
        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=_mock_response(200, {"ok": True}))
        client.session = mock_session
        result = await client._make_request("GET", AJAHELOEndpoints.SYSTEM_STATUS)
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_make_request_lazy_creates_session(self):
        client = AJAHELOClient("192.168.1.10")
        client.session = None
        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=_mock_response(200, {"ok": True}))
        with patch("aiohttp.ClientSession", return_value=mock_session) as mock_cls:
            result = await client._make_request("GET", AJAHELOEndpoints.SYSTEM_STATUS)
        mock_cls.assert_called_once()
        assert client.session is mock_session
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_make_request_raises_on_4xx(self):
        client = AJAHELOClient("192.168.1.10")
        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=_mock_response(400, {"error": "bad"}))
        client.session = mock_session
        with pytest.raises(EncoderRecordingError, match="Invalid request"):
            await client._make_request("GET", AJAHELOEndpoints.SYSTEM_STATUS)

    @pytest.mark.asyncio
    async def test_make_request_retries_connector_error(self):
        client = AJAHELOClient("192.168.1.10")
        client._connection_retries = 2
        mock_session = MagicMock()
        mock_session.request = MagicMock(
            side_effect=[
                aiohttp.ClientConnectorError(MagicMock(), OSError("refused")),
                _mock_response(200, {"ok": True}),
            ]
        )
        client.session = mock_session
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client._make_request("GET", AJAHELOEndpoints.SYSTEM_STATUS)
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_make_request_connector_error_exhausted(self):
        client = AJAHELOClient("192.168.1.10")
        client._connection_retries = 1
        mock_session = MagicMock()
        mock_session.request = MagicMock(
            side_effect=aiohttp.ClientConnectorError(MagicMock(), OSError("refused"))
        )
        client.session = mock_session
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(EncoderConnectionError, match="Failed to connect"):
                await client._make_request("GET", AJAHELOEndpoints.SYSTEM_STATUS)

    @pytest.mark.asyncio
    async def test_start_stream_with_config(self):
        client = AJAHELOClient("192.168.1.10")
        client.configure_stream = AsyncMock(return_value={"configured": True})
        client._make_request = AsyncMock(return_value={"started": True})
        result = await client.start_stream(config={"bitrate": 5000})
        client.configure_stream.assert_awaited_once()
        assert result == {"started": True}

    @pytest.mark.asyncio
    async def test_stop_recording(self):
        client = AJAHELOClient("192.168.1.10")
        client._make_request = AsyncMock(return_value={"stopped": True})
        result = await client.stop_recording()
        assert result == {"stopped": True}

    @pytest.mark.asyncio
    async def test_get_full_status_partial_failures(self):
        client = AJAHELOClient("192.168.1.10")
        client._make_request = AsyncMock(
            side_effect=[
                {"system": "ok"},
                EncoderConnectionError("stream down"),
                {"recording": "ok"},
                {"network": "ok"},
            ]
        )
        status = await client.get_full_status()
        assert status["system"] == {"system": "ok"}
        assert status["streaming"] is None
        assert len(status["errors"]) == 1

    @pytest.mark.asyncio
    async def test_get_full_status_outer_exception(self):
        client = AJAHELOClient("192.168.1.10")
        with patch(
            "services.video_encoder.aja_client.asyncio.gather",
            side_effect=Exception("gather failed"),
        ):
            with pytest.raises(EncoderConnectionError, match="Failed to get device status"):
                await client.get_full_status()

    @pytest.mark.asyncio
    async def test_handle_api_error_status_branches(self):
        client = AJAHELOClient("192.168.1.10")
        cases = [
            (403, EncoderConnectionError, "Operation not permitted"),
            (404, EncoderConnectionError, "Resource not found"),
            (409, EncoderRecordingError, "Operation conflict"),
            (500, EncoderConnectionError, "API error"),
        ]
        for status, exc_type, match in cases:
            response = MagicMock()
            response.status = status
            response.json = AsyncMock(return_value={"error": "detail"})
            with pytest.raises(exc_type, match=match):
                await client._handle_api_error(response)

    @pytest.mark.asyncio
    async def test_make_request_client_error_raises(self):
        client = AJAHELOClient("192.168.1.10")
        mock_session = MagicMock()
        mock_session.request = MagicMock(side_effect=aiohttp.ClientError("broken"))
        client.session = mock_session
        with pytest.raises(EncoderConnectionError, match="Connection error"):
            await client._make_request("GET", AJAHELOEndpoints.SYSTEM_STATUS)

    @pytest.mark.asyncio
    async def test_start_recording_with_config(self):
        client = AJAHELOClient("192.168.1.10")
        client.configure_recording = AsyncMock(return_value={"configured": True})
        client._make_request = AsyncMock(return_value={"recording": True})
        result = await client.start_recording(config={"format": "mp4"})
        client.configure_recording.assert_awaited_once()
        assert result == {"recording": True}

    @pytest.mark.asyncio
    async def test_stop_stream_and_reboot(self):
        client = AJAHELOClient("192.168.1.10")
        client._make_request = AsyncMock(return_value={"ok": True})
        assert await client.stop_stream() == {"ok": True}
        assert await client.reboot_device() == {"ok": True}

    @pytest.mark.asyncio
    async def test_configure_and_status_helpers(self):
        client = AJAHELOClient("192.168.1.10")
        client._make_request = AsyncMock(return_value={"ok": True})
        assert await client.configure_stream({"bitrate": 1}) == {"ok": True}
        assert await client.configure_recording({"format": "mp4"}) == {"ok": True}
        assert await client.get_network_stats() == {"ok": True}
        assert await client.get_media_status() == {"ok": True}

    @pytest.mark.asyncio
    async def test_context_manager_closes_session(self):
        client = AJAHELOClient("192.168.1.10")
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with client:
                assert client.session is mock_session
        mock_session.close.assert_awaited_once()
