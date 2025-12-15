"""Unit tests for exceptions"""

from app.core.exceptions import (
    APIException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)


class TestExceptions:
    """Test custom exceptions"""

    def test_api_exception(self):
        """Test base APIException"""
        error = APIException()
        assert error.status_code == 500
        assert error.message == "An error occurred"

        error_dict = error.to_dict()
        assert error_dict["error"] == "APIException"
        assert error_dict["message"] == "An error occurred"

    def test_api_exception_custom_message(self):
        """Test APIException with custom message"""
        error = APIException(message="Custom error", status_code=400)
        assert error.status_code == 400
        assert error.message == "Custom error"

    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError()
        assert error.status_code == 401
        assert error.message == "Authentication required"

    def test_authorization_error(self):
        """Test AuthorizationError"""
        error = AuthorizationError()
        assert error.status_code == 403
        assert error.message == "Insufficient permissions"

    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError()
        assert error.status_code == 400
        assert error.message == "Validation failed"

    def test_not_found_error(self):
        """Test NotFoundError"""
        error = NotFoundError()
        assert error.status_code == 404
        assert error.message == "Resource not found"
