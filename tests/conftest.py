"""Test configuration and fixtures"""

import pytest

from app import create_app


@pytest.fixture(scope="session")
def app():
    """
    Create a Flask application configured for testing.
    
    Returns:
        app (Flask): Flask application instance configured with the "testing" settings.
    """
    return create_app("testing")

@pytest.fixture(scope="session")
def client(app):
    """
    Create a Flask test client for the provided application.
    
    Parameters:
        app (Flask): The Flask application instance to create a test client for.
    
    Returns:
        A test client configured for the given app.
    """
    return app.test_client()


@pytest.fixture
def mock_token():
    """
    Provide a mock Authorization header value containing a JWT-like bearer token for tests.
    
    Returns:
        str: A string suitable for an HTTP `Authorization` header, e.g. "Bearer mock-jwt-token-for-testing".
    """
    return "Bearer mock-jwt-token-for-testing"