"""Unit tests for middleware"""

from unittest.mock import patch

import pytest
from flask import g

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.middleware import (
    extract_token_from_header,
    optional_auth,
    require_auth,
    require_role,
)


class TestExtractTokenFromHeader:
    """Tests for extract_token_from_header function"""

    def test_extract_token_valid_bearer(self, app):
        """Test extracting valid Bearer token"""
        with app.test_request_context(
            headers={"Authorization": "Bearer test-token-123"}
        ):
            token = extract_token_from_header()
            assert token == "test-token-123"

    def test_extract_token_no_header(self, app):
        """Test with no Authorization header"""
        with app.test_request_context():
            token = extract_token_from_header()
            assert token is None

    def test_extract_token_empty_header(self, app):
        """Test with empty Authorization header"""
        with app.test_request_context(headers={"Authorization": ""}):
            token = extract_token_from_header()
            assert token is None

    def test_extract_token_invalid_format_single_part(self, app):
        """Test with invalid format (single part)"""
        with app.test_request_context(headers={"Authorization": "InvalidToken"}):
            token = extract_token_from_header()
            assert token is None

    def test_extract_token_invalid_format_three_parts(self, app):
        """Test with invalid format (three parts)"""
        with app.test_request_context(
            headers={"Authorization": "Bearer token extra"}
        ):
            token = extract_token_from_header()
            assert token is None

    def test_extract_token_wrong_scheme(self, app):
        """Test with wrong authentication scheme"""
        with app.test_request_context(headers={"Authorization": "Basic token123"}):
            token = extract_token_from_header()
            assert token is None

    def test_extract_token_case_insensitive_bearer(self, app):
        """Test that Bearer is case-insensitive"""
        with app.test_request_context(headers={"Authorization": "bearer token123"}):
            token = extract_token_from_header()
            assert token == "token123"


class TestRequireAuth:
    """Tests for require_auth decorator"""

    @patch("app.core.middleware.auth_service")
    def test_require_auth_success(self, mock_auth_service, app):
        """Test successful authentication"""
        mock_decoded = {"sub": "user-123", "email": "test@example.com"}
        mock_user_info = {
            "user_id": "user-123",
            "email": "test@example.com",
            "username": "testuser",
        }
        mock_auth_service.verify_token.return_value = mock_decoded
        mock_auth_service.extract_user_info.return_value = mock_user_info

        @require_auth
        def protected_view():
            return {"user": g.user}

        with app.test_request_context(
            headers={"Authorization": "Bearer valid-token"}
        ):
            result = protected_view()
            assert result["user"] == mock_user_info
            assert g.user == mock_user_info
            assert g.token == mock_decoded
            mock_auth_service.verify_token.assert_called_once_with("valid-token")

    def test_require_auth_no_token(self, app):
        """Test authentication fails with no token"""

        @require_auth
        def protected_view():
            return {"message": "success"}

        with app.test_request_context():
            with pytest.raises(AuthenticationError) as exc_info:
                protected_view()
            assert exc_info.value.message == "No token provided"

    @patch("app.core.middleware.auth_service")
    def test_require_auth_invalid_token(self, mock_auth_service, app):
        """Test authentication fails with invalid token"""
        mock_auth_service.verify_token.side_effect = AuthenticationError(
            "Invalid token"
        )

        @require_auth
        def protected_view():
            return {"message": "success"}

        with app.test_request_context(
            headers={"Authorization": "Bearer invalid-token"}
        ), pytest.raises(AuthenticationError):
            protected_view()

    @patch("app.core.middleware.auth_service")
    def test_require_auth_unexpected_error(self, mock_auth_service, app):
        """Test authentication handles unexpected errors"""
        mock_auth_service.verify_token.side_effect = Exception("Unexpected error")

        @require_auth
        def protected_view():
            return {"message": "success"}

        with app.test_request_context(
            headers={"Authorization": "Bearer some-token"}
        ):
            with pytest.raises(AuthenticationError) as exc_info:
                protected_view()
            assert exc_info.value.message == "Authentication failed"

    @patch("app.core.middleware.auth_service")
    def test_require_auth_preserves_function_name(self, mock_auth_service, app):
        """Test that decorator preserves original function name"""
        mock_auth_service.verify_token.return_value = {"sub": "user-123"}
        mock_auth_service.extract_user_info.return_value = {"user_id": "user-123"}

        @require_auth
        def my_protected_view():
            """My docstring"""
            return {"message": "success"}

        assert my_protected_view.__name__ == "my_protected_view"
        assert my_protected_view.__doc__ == "My docstring"


class TestRequireRole:
    """Tests for require_role decorator"""

    def test_require_role_success_single_role(self, app):
        """Test successful role check with single role"""

        @require_role("admin")
        def admin_view():
            return {"message": "admin access"}

        with app.test_request_context():
            g.user = {
                "user_id": "user-123",
                "roles": ["admin", "user"],
                "client_roles": [],
            }
            result = admin_view()
            assert result["message"] == "admin access"

    def test_require_role_success_multiple_roles(self, app):
        """Test successful role check with multiple allowed roles"""

        @require_role("admin", "superuser", "moderator")
        def admin_view():
            return {"message": "admin access"}

        with app.test_request_context():
            g.user = {
                "user_id": "user-123",
                "roles": ["moderator"],
                "client_roles": [],
            }
            result = admin_view()
            assert result["message"] == "admin access"

    def test_require_role_success_client_role(self, app):
        """Test successful role check with client role"""

        @require_role("app-admin")
        def admin_view():
            return {"message": "admin access"}

        with app.test_request_context():
            g.user = {
                "user_id": "user-123",
                "roles": [],
                "client_roles": ["app-admin"],
            }
            result = admin_view()
            assert result["message"] == "admin access"

    def test_require_role_no_user(self, app):
        """Test role check fails when no user in context"""

        @require_role("admin")
        def admin_view():
            return {"message": "admin access"}

        with app.test_request_context():
            with pytest.raises(AuthorizationError) as exc_info:
                admin_view()
            assert exc_info.value.message == "Authentication required before role check"

    def test_require_role_insufficient_permissions(self, app):
        """Test role check fails with insufficient permissions"""

        @require_role("admin", "superuser")
        def admin_view():
            return {"message": "admin access"}

        with app.test_request_context():
            g.user = {
                "user_id": "user-123",
                "roles": ["user"],
                "client_roles": [],
            }
            with pytest.raises(AuthorizationError) as exc_info:
                admin_view()
            assert exc_info.value.message == "Requires one of: admin, superuser"

    def test_require_role_no_roles(self, app):
        """Test role check fails when user has no roles"""

        @require_role("admin")
        def admin_view():
            return {"message": "admin access"}

        with app.test_request_context():
            g.user = {"user_id": "user-123"}
            with pytest.raises(AuthorizationError):
                admin_view()

    def test_require_role_preserves_function_name(self, app):
        """Test that decorator preserves original function name"""

        @require_role("admin")
        def my_admin_view():
            """My admin docstring"""
            return {"message": "success"}

        assert my_admin_view.__name__ == "my_admin_view"
        assert my_admin_view.__doc__ == "My admin docstring"


class TestOptionalAuth:
    """Tests for optional_auth decorator"""

    @patch("app.core.middleware.auth_service")
    def test_optional_auth_with_valid_token(self, mock_auth_service, app):
        """Test optional auth with valid token"""
        mock_decoded = {"sub": "user-123"}
        mock_user_info = {"user_id": "user-123", "username": "testuser"}
        mock_auth_service.verify_token.return_value = mock_decoded
        mock_auth_service.extract_user_info.return_value = mock_user_info

        @optional_auth
        def public_view():
            if hasattr(g, "user"):
                return {"authenticated": True, "user": g.user}
            return {"authenticated": False}

        with app.test_request_context(
            headers={"Authorization": "Bearer valid-token"}
        ):
            result = public_view()
            assert result["authenticated"] is True
            assert result["user"] == mock_user_info
            assert g.user == mock_user_info
            assert g.token == mock_decoded

    def test_optional_auth_without_token(self, app):
        """Test optional auth without token"""

        @optional_auth
        def public_view():
            if hasattr(g, "user"):
                return {"authenticated": True, "user": g.user}
            return {"authenticated": False}

        with app.test_request_context():
            result = public_view()
            assert result["authenticated"] is False
            assert not hasattr(g, "user")

    @patch("app.core.middleware.auth_service")
    def test_optional_auth_with_invalid_token(self, mock_auth_service, app):
        """Test optional auth with invalid token (should not fail)"""
        mock_auth_service.verify_token.side_effect = AuthenticationError(
            "Invalid token"
        )

        @optional_auth
        def public_view():
            if hasattr(g, "user"):
                return {"authenticated": True}
            return {"authenticated": False}

        with app.test_request_context(
            headers={"Authorization": "Bearer invalid-token"}
        ):
            result = public_view()
            assert result["authenticated"] is False
            assert not hasattr(g, "user")

    @patch("app.core.middleware.auth_service")
    def test_optional_auth_with_exception(self, mock_auth_service, app):
        """Test optional auth handles exceptions gracefully"""
        mock_auth_service.verify_token.side_effect = Exception("Unexpected error")

        @optional_auth
        def public_view():
            if hasattr(g, "user"):
                return {"authenticated": True}
            return {"authenticated": False}

        with app.test_request_context(
            headers={"Authorization": "Bearer some-token"}
        ):
            result = public_view()
            assert result["authenticated"] is False
            assert not hasattr(g, "user")

    @patch("app.core.middleware.auth_service")
    def test_optional_auth_preserves_function_name(self, mock_auth_service, app):
        """Test that decorator preserves original function name"""

        @optional_auth
        def my_public_view():
            """My public docstring"""
            return {"message": "success"}

        assert my_public_view.__name__ == "my_public_view"
        assert my_public_view.__doc__ == "My public docstring"
