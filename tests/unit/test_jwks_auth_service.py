"""Unit tests for JWKS auth service"""

from unittest.mock import MagicMock, Mock, patch

import jwt
import pytest

from app.core.exceptions import AuthenticationError
from app.services.auth_service import JWKSAuthService, get_auth_service


class TestJWKSAuthService:
    """Tests for JWKS authentication service"""

    @pytest.fixture
    def jwks_app(self, app):
        """Provide the app with JWKS config set."""
        app.config["AUTH_PROVIDER"] = "jwks"
        app.config["JWKS_URL"] = "http://localhost:3000/api/auth/jwks"
        app.config["JWKS_ISSUER"] = "http://localhost:3000"
        app.config["JWKS_AUDIENCE"] = "http://localhost:3000"
        app.config["JWKS_ALGORITHMS"] = "EdDSA,RS256"
        yield app
        # Reset to keycloak after tests
        app.config["AUTH_PROVIDER"] = "keycloak"

    @pytest.fixture
    def auth_service(self, jwks_app):
        """Provide a JWKSAuthService instance inside the app context."""
        with jwks_app.app_context():
            return JWKSAuthService()

    def test_jwks_url_property(self, auth_service, jwks_app):
        """Test jwks_url property reads from config"""
        with jwks_app.app_context():
            assert auth_service.jwks_url == "http://localhost:3000/api/auth/jwks"

    def test_issuer_property(self, auth_service, jwks_app):
        """Test issuer property reads from config"""
        with jwks_app.app_context():
            assert auth_service.issuer == "http://localhost:3000"

    def test_audience_property(self, auth_service, jwks_app):
        """Test audience property reads from config"""
        with jwks_app.app_context():
            assert auth_service.audience == "http://localhost:3000"

    def test_algorithms_property_from_string(self, auth_service, jwks_app):
        """Test algorithms property parses comma-separated string"""
        with jwks_app.app_context():
            assert auth_service.algorithms == ["EdDSA", "RS256"]

    def test_algorithms_property_from_list(self, auth_service, jwks_app):
        """Test algorithms property handles list input"""
        with jwks_app.app_context():
            jwks_app.config["JWKS_ALGORITHMS"] = ["EdDSA", "RS256"]
            assert auth_service.algorithms == ["EdDSA", "RS256"]

    @patch("app.services.auth_service.jwt.decode")
    def test_verify_token_success(self, mock_jwt_decode, auth_service, jwks_app):
        """Test successful token verification"""
        mock_signing_key = MagicMock()
        mock_signing_key.key = "mock-key"

        mock_decoded = {
            "sub": "user-123",
            "email": "test@example.com",
        }
        mock_jwt_decode.return_value = mock_decoded

        with jwks_app.app_context():
            with patch.object(auth_service, "_get_jwks_client") as mock_client:
                mock_client.return_value.get_signing_key_from_jwt.return_value = (
                    mock_signing_key
                )
                result = auth_service.verify_token("mock.jwt.token")

            assert result == mock_decoded
            mock_jwt_decode.assert_called_once()

    @patch("app.services.auth_service.jwt.decode")
    def test_verify_token_expired(self, mock_jwt_decode, auth_service, jwks_app):
        """Test token verification with expired token"""
        mock_signing_key = MagicMock()
        mock_signing_key.key = "mock-key"
        mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token expired")

        with jwks_app.app_context():
            with patch.object(auth_service, "_get_jwks_client") as mock_client:
                mock_client.return_value.get_signing_key_from_jwt.return_value = (
                    mock_signing_key
                )
                with pytest.raises(AuthenticationError):
                    auth_service.verify_token("mock.jwt.token")

    @patch("app.services.auth_service.jwt.decode")
    def test_verify_token_invalid(self, mock_jwt_decode, auth_service, jwks_app):
        """Test token verification with invalid token"""
        mock_signing_key = MagicMock()
        mock_signing_key.key = "mock-key"
        mock_jwt_decode.side_effect = jwt.InvalidTokenError("Invalid")

        with jwks_app.app_context():
            with patch.object(auth_service, "_get_jwks_client") as mock_client:
                mock_client.return_value.get_signing_key_from_jwt.return_value = (
                    mock_signing_key
                )
                with pytest.raises(AuthenticationError):
                    auth_service.verify_token("mock.jwt.token")

    def test_verify_token_jwks_client_error(self, auth_service, jwks_app):
        """Test token verification when JWKS client fails"""
        with jwks_app.app_context():
            with patch.object(auth_service, "_get_jwks_client") as mock_client:
                mock_client.return_value.get_signing_key_from_jwt.side_effect = (
                    Exception("Connection refused")
                )
                with pytest.raises(AuthenticationError):
                    auth_service.verify_token("mock.jwt.token")

    @patch("app.services.auth_service.jwt.decode")
    def test_verify_token_no_audience_skips_aud_check(
        self, mock_jwt_decode, auth_service, jwks_app
    ):
        """Test that audience verification is skipped when JWKS_AUDIENCE is not set"""
        mock_signing_key = MagicMock()
        mock_signing_key.key = "mock-key"
        mock_jwt_decode.return_value = {"sub": "user-123"}

        with jwks_app.app_context():
            jwks_app.config["JWKS_AUDIENCE"] = None
            with patch.object(auth_service, "_get_jwks_client") as mock_client:
                mock_client.return_value.get_signing_key_from_jwt.return_value = (
                    mock_signing_key
                )
                auth_service.verify_token("mock.jwt.token")

            # Check that verify_aud was set to False
            call_kwargs = mock_jwt_decode.call_args
            assert call_kwargs[1]["options"]["verify_aud"] is False

    def test_extract_user_info_complete(self, auth_service, jwks_app):
        """Test extracting complete user info from token"""
        with jwks_app.app_context():
            decoded_token = {
                "sub": "user-123",
                "preferred_username": "testuser",
                "email": "test@example.com",
                "email_verified": True,
                "name": "Test User",
                "given_name": "Test",
                "family_name": "User",
                "image": "https://example.com/avatar.jpg",
                "roles": ["admin", "user"],
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-02T00:00:00Z",
            }

            user_info = auth_service.extract_user_info(decoded_token)

            assert user_info["user_id"] == "user-123"
            assert user_info["username"] == "testuser"
            assert user_info["email"] == "test@example.com"
            assert user_info["email_verified"] is True
            assert user_info["name"] == "Test User"
            assert user_info["image"] == "https://example.com/avatar.jpg"
            assert user_info["roles"] == ["admin", "user"]
            assert user_info["client_roles"] == []
            assert user_info["created_at"] == "2026-01-01T00:00:00Z"
            assert user_info["updated_at"] == "2026-01-02T00:00:00Z"

    def test_extract_user_info_minimal(self, auth_service, jwks_app):
        """Test extracting minimal user info from token"""
        with jwks_app.app_context():
            decoded_token = {"sub": "user-123"}

            user_info = auth_service.extract_user_info(decoded_token)

            assert user_info["user_id"] == "user-123"
            assert user_info["username"] is None
            assert user_info["email"] is None
            assert user_info["email_verified"] is False
            assert user_info["image"] is None
            assert user_info["roles"] == []
            assert user_info["created_at"] is None
            assert user_info["updated_at"] is None

    def test_extract_user_info_camelcase_claims(self, auth_service, jwks_app):
        """Test that camelCase claims (e.g. Better Auth) are handled correctly"""
        with jwks_app.app_context():
            decoded_token = {
                "sub": "asdkjqweloidufhakcdjbnalcbnj",
                "email": "user@example.com",
                "emailVerified": True,
                "name": "Test User",
                "image": "https://example.com/avatar.png",
                "createdAt": "2026-02-15T16:29:16.450Z",
                "updatedAt": "2026-02-15T16:29:16.450Z",
            }

            user_info = auth_service.extract_user_info(decoded_token)

            assert user_info["user_id"] == "asdkjqweloidufhakcdjbnalcbnj"
            assert user_info["email"] == "user@example.com"
            assert user_info["email_verified"] is True
            assert user_info["name"] == "Test User"
            assert user_info["image"] == "https://example.com/avatar.png"
            assert user_info["created_at"] == "2026-02-15T16:29:16.450Z"
            assert user_info["updated_at"] == "2026-02-15T16:29:16.450Z"


class TestGetAuthService:
    """Tests for the get_auth_service factory function"""

    def test_returns_keycloak_by_default(self, app):
        """Test that Keycloak service is returned by default"""
        from app.services.auth_service import KeycloakAuthService, init_auth_service

        with app.app_context():
            app.config["AUTH_PROVIDER"] = "keycloak"
            init_auth_service(app)
            service = get_auth_service()
            assert isinstance(service, KeycloakAuthService)

    def test_returns_jwks_when_configured(self, app):
        """Test that JWKS service is returned when configured"""
        from app.services.auth_service import init_auth_service

        with app.app_context():
            app.config["AUTH_PROVIDER"] = "jwks"
            app.config["JWKS_URL"] = "http://localhost:3000/api/auth/jwks"
            init_auth_service(app)
            service = get_auth_service()
            assert isinstance(service, JWKSAuthService)
            # Reset
            app.config["AUTH_PROVIDER"] = "keycloak"
            init_auth_service(app)

    def test_raises_for_unknown_provider(self, app):
        """Test that unknown provider raises ValueError"""
        from app.services.auth_service import init_auth_service

        with app.app_context():
            app.config["AUTH_PROVIDER"] = "unknown"
            with pytest.raises(ValueError, match="Unknown AUTH_PROVIDER"):
                init_auth_service(app)
            # Reset
            app.config["AUTH_PROVIDER"] = "keycloak"
            init_auth_service(app)

    def test_case_insensitive(self, app):
        """Test that provider name is case insensitive"""
        from app.services.auth_service import init_auth_service

        with app.app_context():
            app.config["AUTH_PROVIDER"] = "JWKS"
            app.config["JWKS_URL"] = "http://localhost:3000/api/auth/jwks"
            init_auth_service(app)
            service = get_auth_service()
            assert isinstance(service, JWKSAuthService)
            # Reset
            app.config["AUTH_PROVIDER"] = "keycloak"
            init_auth_service(app)
