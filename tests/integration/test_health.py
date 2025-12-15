"""Integration tests for health endpoints"""



class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_health_check(self, client):
        """
        Verify that a GET request to the root ("/") returns HTTP 200 and a JSON body whose "status" is "healthy" and that includes "service" and "version" keys.
        
        Parameters:
            client: Test client used to send requests to the application.
        """
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()

        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data