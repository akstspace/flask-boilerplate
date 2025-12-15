"""Integration tests for health endpoints"""



class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_health_check(self, client):
        """Test root health check endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()

        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
