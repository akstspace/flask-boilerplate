"""Unit tests for auth service"""

from unittest.mock import Mock, patch

import jwt
import pytest

from app.core.exceptions import AuthenticationError
from app.services.auth_service import KeycloakAuthService


class TestKeycloakAuthService:
    """Tests for Keycloak authentication service"""

    @pytest.fixture
    def auth_service(self, app):
        """Create auth service instance"""
        with app.app_context():
            return KeycloakAuthService()

    @pytest.fixture
    def mock_jwks(self):
        """Mock JWKS response"""
        return {
            "keys": [
                {
                    "kid": "test-kid-123",
                    "kty": "RSA",
                    "alg": "RS256",
                    "use": "sig",
                    "n": "test-n-value",
                    "e": "AQAB",
                }
            ]
        }

    def test_keycloak_url_property(self, auth_service, app):
        """Test keycloak_url property"""
        with app.app_context():
            assert auth_service.keycloak_url == app.config["KEYCLOAK_SERVER_URL"]

    def test_realm_property(self, auth_service, app):
        """Test realm property"""
        with app.app_context():
            assert auth_service.realm == app.config["KEYCLOAK_REALM"]

    def test_certs_url_property(self, auth_service, app):
        """Test certs_url property"""
        with app.app_context():
            expected_url = f"{app.config['KEYCLOAK_SERVER_URL']}/realms/{app.config['KEYCLOAK_REALM']}/protocol/openid-connect/certs"
            assert auth_service.certs_url == expected_url

    @patch("app.services.auth_service.requests.get")
    def test_get_jwks_success(self, mock_get, auth_service, mock_jwks, app):
        """Test successful JWKS retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = mock_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Clear cache before test
        auth_service._get_jwks.cache_clear()

        with app.app_context():
            result = auth_service._get_jwks()
            assert result == mock_jwks
            mock_get.assert_called_once()

    @patch("app.services.auth_service.requests.get")
    def test_get_jwks_failure(self, mock_get, auth_service, app):
        """Test JWKS retrieval failure"""
        mock_get.side_effect = Exception("Connection error")

        # Clear cache before test
        auth_service._get_jwks.cache_clear()

        with app.app_context(), pytest.raises(AuthenticationError):
            auth_service._get_jwks()

    @patch("app.services.auth_service.requests.get")
    def test_get_jwks_http_error(self, mock_get, auth_service, app):
        """Test JWKS retrieval with HTTP error"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        # Clear cache before test
        auth_service._get_jwks.cache_clear()

        with app.app_context(), pytest.raises(AuthenticationError):
            auth_service._get_jwks()

    def test_get_public_key_by_kid_invalid_jwks(self, auth_service):
        """Test getting public key with invalid JWKS"""
        with patch.object(auth_service, "_get_jwks", return_value={}):
            with pytest.raises(ValueError, match="Invalid JWKS response"):
                auth_service._get_public_key_by_kid("test-kid")

    def test_get_public_key_by_kid_not_found(self, auth_service, mock_jwks):
        """Test getting public key with non-existent kid"""
        with patch.object(auth_service, "_get_jwks", return_value=mock_jwks):
            with pytest.raises(ValueError, match="Public key with kid .* not found"):
                auth_service._get_public_key_by_kid("non-existent-kid")

    @patch("jose.jwk.construct")
    def test_get_public_key_by_kid_success(self, mock_construct, auth_service, mock_jwks):
        """Test successful public key retrieval"""
        mock_key = Mock()
        mock_key.to_pem.return_value = b"-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----"
        mock_construct.return_value = mock_key

        with patch.object(auth_service, "_get_jwks", return_value=mock_jwks):
            result = auth_service._get_public_key_by_kid("test-kid-123")

            assert "BEGIN PUBLIC KEY" in result
            mock_construct.assert_called_once()

    @patch.object(KeycloakAuthService, "_get_public_key_by_kid")
    @patch("app.services.auth_service.jwt.get_unverified_header")
    @patch("app.services.auth_service.jwt.decode")
    def test_verify_token_success(
        self, mock_jwt_decode, mock_get_header, mock_get_key, auth_service, app
    ):
        """Test successful token verification"""
        mock_get_header.return_value = {"kid": "test-kid-123"}
        mock_get_key.return_value = "mock-public-key"
        mock_decoded = {
            "sub": "user-123",
            "preferred_username": "testuser",
            "email": "test@example.com",
        }
        mock_jwt_decode.return_value = mock_decoded

        with app.app_context():
            result = auth_service.verify_token("mock.jwt.token")

            assert result == mock_decoded
            mock_get_header.assert_called_once_with("mock.jwt.token")
            mock_get_key.assert_called_once_with("test-kid-123")

    @patch("app.services.auth_service.jwt.get_unverified_header")
    def test_verify_token_missing_kid(self, mock_get_header, auth_service, app):
        """Test token verification with missing kid"""
        mock_get_header.return_value = {}

        with app.app_context(), pytest.raises(AuthenticationError):
            auth_service.verify_token("mock.jwt.token")

    @patch.object(KeycloakAuthService, "_get_public_key_by_kid")
    @patch("app.services.auth_service.jwt.get_unverified_header")
    @patch("app.services.auth_service.jwt.decode")
    def test_verify_token_expired(
        self, mock_jwt_decode, mock_get_header, mock_get_key, auth_service, app
    ):
        """Test token verification with expired token"""
        mock_get_header.return_value = {"kid": "test-kid-123"}
        mock_get_key.return_value = "mock-public-key"
        mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token expired")

        with app.app_context(), pytest.raises(AuthenticationError):
            auth_service.verify_token("mock.jwt.token")

    @patch.object(KeycloakAuthService, "_get_public_key_by_kid")
    @patch("app.services.auth_service.jwt.get_unverified_header")
    @patch("app.services.auth_service.jwt.decode")
    def test_verify_token_invalid(
        self, mock_jwt_decode, mock_get_header, mock_get_key, auth_service, app
    ):
        """Test token verification with invalid token"""
        mock_get_header.return_value = {"kid": "test-kid-123"}
        mock_get_key.return_value = "mock-public-key"
        mock_jwt_decode.side_effect = jwt.InvalidTokenError("Invalid token")

        with app.app_context(), pytest.raises(AuthenticationError):
            auth_service.verify_token("mock.jwt.token")

    @patch.object(KeycloakAuthService, "_get_public_key_by_kid")
    @patch("app.services.auth_service.jwt.get_unverified_header")
    def test_verify_token_key_error(self, mock_get_header, mock_get_key, auth_service, app):
        """Test token verification with key retrieval error"""
        mock_get_header.return_value = {"kid": "test-kid-123"}
        mock_get_key.side_effect = ValueError("Key not found")

        with app.app_context(), pytest.raises(AuthenticationError):
            auth_service.verify_token("mock.jwt.token")

    @patch.object(KeycloakAuthService, "_get_public_key_by_kid")
    @patch("app.services.auth_service.jwt.get_unverified_header")
    @patch("app.services.auth_service.jwt.decode")
    def test_verify_token_unexpected_error(
        self, mock_jwt_decode, mock_get_header, mock_get_key, auth_service, app
    ):
        """Test token verification with unexpected error"""
        mock_get_header.return_value = {"kid": "test-kid-123"}
        mock_get_key.return_value = "mock-public-key"
        mock_jwt_decode.side_effect = Exception("Unexpected error")

        with app.app_context(), pytest.raises(AuthenticationError):
            auth_service.verify_token("mock.jwt.token")

    def test_extract_user_info_complete(self, auth_service, app):
        """Test extracting complete user info from token"""
        with app.app_context():
            decoded_token = {
                "sub": "user-123",
                "preferred_username": "testuser",
                "email": "test@example.com",
                "email_verified": True,
                "name": "Test User",
                "given_name": "Test",
                "family_name": "User",
                "realm_access": {"roles": ["admin", "user"]},
                "resource_access": {
                    app.config["KEYCLOAK_CLIENT_ID"]: {"roles": ["app-admin"]}
                },
            }

            user_info = auth_service.extract_user_info(decoded_token)

            assert user_info["user_id"] == "user-123"
            assert user_info["username"] == "testuser"
            assert user_info["email"] == "test@example.com"
            assert user_info["email_verified"] is True
            assert user_info["name"] == "Test User"
            assert user_info["given_name"] == "Test"
            assert user_info["family_name"] == "User"
            assert user_info["roles"] == ["admin", "user"]
            assert user_info["client_roles"] == ["app-admin"]

    def test_extract_user_info_minimal(self, auth_service, app):
        """Test extracting minimal user info from token"""
        with app.app_context():
            decoded_token = {"sub": "user-123"}

            user_info = auth_service.extract_user_info(decoded_token)

            assert user_info["user_id"] == "user-123"
            assert user_info["username"] is None
            assert user_info["email"] is None
            assert user_info["email_verified"] is False
            assert user_info["name"] is None
            assert user_info["given_name"] is None
            assert user_info["family_name"] is None
            assert user_info["roles"] == []
            assert user_info["client_roles"] == []

    def test_extract_user_info_no_realm_access(self, auth_service, app):
        """Test extracting user info without realm access"""
        with app.app_context():
            decoded_token = {"sub": "user-123", "preferred_username": "testuser"}

            user_info = auth_service.extract_user_info(decoded_token)

            assert user_info["roles"] == []

    def test_extract_user_info_no_resource_access(self, auth_service, app):
        """Test extracting user info without resource access"""
        with app.app_context():
            decoded_token = {"sub": "user-123", "preferred_username": "testuser"}

            user_info = auth_service.extract_user_info(decoded_token)

            assert user_info["client_roles"] == []
