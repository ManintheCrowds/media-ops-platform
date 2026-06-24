"""Targeted tests for app.main routes and handlers."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from app.main import app, global_exception_handler, validation_exception_handler, root, api_info
from fastapi.exceptions import RequestValidationError


@pytest.mark.unit
class TestMainApp:
    """Cover main application routes and exception handlers."""

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "dashboard" in response.text

    def test_api_info_endpoint(self, client):
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        assert data["endpoints"]["health"] == "/api/health"

    @pytest.mark.asyncio
    async def test_global_exception_handler_debug(self):
        request = MagicMock(spec=Request)
        request.url = "http://test/error"
        with patch("app.main.settings") as mock_settings:
            mock_settings.debug = True
            response = await global_exception_handler(request, RuntimeError("boom"))
        assert response.status_code == 500
        assert response.body

    @pytest.mark.asyncio
    async def test_global_exception_handler_production(self):
        request = MagicMock(spec=Request)
        request.url = "http://test/error"
        with patch("app.main.settings") as mock_settings:
            mock_settings.debug = False
            response = await global_exception_handler(request, RuntimeError("boom"))
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_validation_exception_handler_debug(self):
        request = MagicMock(spec=Request)
        exc = RequestValidationError(errors=[{"loc": ["body"], "msg": "bad", "type": "value_error"}])
        with patch("app.main.settings") as mock_settings:
            mock_settings.debug = True
            response = await validation_exception_handler(request, exc)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validation_exception_handler_production(self):
        request = MagicMock(spec=Request)
        exc = RequestValidationError(errors=[{"loc": ["body"], "msg": "bad", "type": "value_error"}])
        with patch("app.main.settings") as mock_settings:
            mock_settings.debug = False
            response = await validation_exception_handler(request, exc)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_dashboard_without_templates(self):
        request = MagicMock(spec=Request)
        with patch("app.main.templates", None):
            from app.main import dashboard, login_page
            dash = await dashboard(request)
            login = await login_page(request)
        assert dash.status_code == 503
        assert login.status_code == 503

    @pytest.mark.asyncio
    async def test_root_handler(self):
        html = await root()
        assert "Self-Hosted Platform" in html

    @pytest.mark.asyncio
    async def test_api_info_handler(self):
        data = await api_info()
        assert data["endpoints"]["camera"] == "/api/camera"
