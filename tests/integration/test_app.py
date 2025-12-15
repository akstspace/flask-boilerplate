"""Integration tests for application factory"""

from app import create_app


class TestApplicationFactory:
    """Test application factory"""

    def test_create_app_development(self):
        """Test creating app with development config"""
        app = create_app("development")
        assert app.config["DEBUG"] is True
        assert app.config["TESTING"] is False

    def test_create_app_testing(self):
        """Test creating app with testing config"""
        app = create_app("testing")
        assert app.config["TESTING"] is True
        assert "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]

    def test_create_app_default(self):
        """Test creating app with default config"""
        app = create_app()
        assert app is not None
        assert hasattr(app, "config")

    def test_blueprints_registered(self, app):
        """Test that blueprints are registered"""
        blueprint_names = [bp.name for bp in app.blueprints.values()]

        assert "health" in blueprint_names
        assert "api_v1" in blueprint_names

    def test_error_handlers_registered(self, client):
        """
        Verify that the application's error handlers produce the expected JSON for unknown routes.
        
        Asserts that a GET to a non-existent endpoint returns a 404 response whose JSON body contains an "error" key with value "NotFound".
        """
        # Test 404 handler
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "NotFound"