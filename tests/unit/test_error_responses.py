"""Unit tests for app.utils.error_responses (exception handling and response format)."""

import pytest
from fastapi import HTTPException, status

from app.utils.error_responses import (
    create_error_response,
    convert_to_http_exception,
    handle_service_error,
    ErrorCodes,
)


@pytest.mark.unit
class TestCreateErrorResponse:
    """Test create_error_response returns correct JSONResponse."""

    def test_returns_json_response_with_status(self):
        """Test that create_error_response returns JSONResponse with given status code."""
        resp = create_error_response("Something failed", 500)
        assert resp.status_code == 500
        body = resp.body.decode()
        assert "Something failed" in body
        assert "timestamp" in body

    def test_includes_error_code_when_provided(self):
        """Test that error_code is included in response when provided."""
        resp = create_error_response(
            "Not found", 404, error_code=ErrorCodes.NOT_FOUND
        )
        assert resp.status_code == 404
        body = resp.body.decode()
        assert ErrorCodes.NOT_FOUND in body

    def test_includes_details_when_provided(self):
        """Test that details are included when provided."""
        resp = create_error_response(
            "Validation failed", 400,
            details={"field": "url", "reason": "invalid"}
        )
        body = resp.body.decode()
        assert "Validation failed" in body
        assert "field" in body or "url" in body


@pytest.mark.unit
class TestConvertToHttpException:
    """Test convert_to_http_exception maps exceptions to HTTPException."""

    def test_plain_exception_uses_default_status(self):
        """Test that plain Exception gets default 500 status."""
        exc = convert_to_http_exception(Exception("Internal error"))
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 500
        assert exc.detail["error"] == "Internal error"
        assert "timestamp" in exc.detail

    def test_exception_with_status_code_uses_it(self):
        """Test that exception with status_code attribute uses it."""
        class CustomExc(Exception):
            status_code = 403
            message = "Forbidden"
        exc = convert_to_http_exception(CustomExc())
        assert exc.status_code == 403
        assert exc.detail["error"] == "Forbidden"

    def test_exception_with_detail_attribute(self):
        """Test exception with detail attribute (e.g. HTTPException)."""
        inner = HTTPException(status_code=404, detail="Resource missing")
        exc = convert_to_http_exception(inner, default_status=500)
        assert exc.status_code == 404
        assert exc.detail["error"] == "Resource missing"

    def test_error_code_included_when_on_exception(self):
        """Test that error_code from exception is included."""
        class CustomExc(Exception):
            status_code = 400
            message = "Bad request"
            error_code = "VALIDATION_ERROR"
        exc = convert_to_http_exception(CustomExc())
        assert exc.detail.get("error_code") == "VALIDATION_ERROR"


@pytest.mark.unit
class TestHandleServiceError:
    """Test handle_service_error returns appropriate JSONResponse for exception types."""

    def test_value_error_returns_400(self):
        """Test ValueError is mapped to 400."""
        resp = handle_service_error(ValueError("Invalid value"))
        assert resp.status_code == 400
        body = resp.body.decode()
        assert "Invalid value" in body

    def test_permission_error_returns_403(self):
        """Test PermissionError is mapped to 403."""
        resp = handle_service_error(PermissionError("Access denied"))
        assert resp.status_code == 403

    def test_file_not_found_returns_404(self):
        """Test FileNotFoundError is mapped to 404."""
        resp = handle_service_error(FileNotFoundError("File missing"))
        assert resp.status_code == 404

    def test_connection_error_returns_503(self):
        """Test ConnectionError is mapped to 503."""
        resp = handle_service_error(ConnectionError("Service unreachable"))
        assert resp.status_code == 503

    def test_generic_exception_returns_500(self):
        """Test generic Exception returns 500."""
        resp = handle_service_error(RuntimeError("Unexpected"))
        assert resp.status_code == 500

    def test_exception_with_status_code_uses_it(self):
        """Test custom exception with status_code is preserved."""
        class ServiceUnavailable(Exception):
            status_code = 503
            message = "Backend down"
        resp = handle_service_error(ServiceUnavailable())
        assert resp.status_code == 503
