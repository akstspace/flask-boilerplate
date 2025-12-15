"""Integration tests for authentication endpoints"""

from unittest.mock import patch


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_auth_me_without_token(self, client):
        """Test /api/v1/auth/me without token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert "message" in data

    def test_auth_me_with_invalid_token(self, client):
        """Test /api/v1/auth/me with invalid token"""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    @patch("app.services.auth_service.auth_service.verify_token")
    @patch("app.services.auth_service.auth_service.extract_user_info")
    def test_auth_me_with_valid_token(self, mock_extract, mock_verify, client):
        """Test /api/v1/auth/me with valid token"""
        # Mock token verification
        mock_verify.return_value = {"sub": "123", "preferred_username": "testuser"}
        mock_extract.return_value = {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "roles": ["user"],
            "client_roles": [],
        }

        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer valid-token"}
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["status"] == "success"
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"

    def test_api_v1_docs_accessible(self, client):
        """Test that API v1 documentation is accessible"""
        response = client.get("/api/v1/docs")

        # Should redirect to docs page or return 200
        assert response.status_code in [200, 301, 302, 308]
