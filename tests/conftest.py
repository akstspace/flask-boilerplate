"""Test configuration and fixtures"""

import pytest

from app import create_app


@pytest.fixture(scope="session")
def app():
    """
    Create the Flask application configured for testing.
    
    Returns:
        Flask: Application instance configured for the "testing" environment.
    """
    return create_app("testing")

@pytest.fixture(scope="session")
def client(app):
    """
    Create and return a test client for the given application.
    
    Parameters:
        app: The Flask application instance used for testing.
    
    Returns:
        A test client bound to the provided application.
    """
    return app.test_client()


@pytest.fixture
def mock_token():
    """
    Provide a mock Authorization header value containing a JWT for tests.
    
    Returns:
        str: Authorization header string in the form "Bearer mock-jwt-token-for-testing".
    """
    return "Bearer mock-jwt-token-for-testing"