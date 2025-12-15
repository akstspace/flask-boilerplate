"""Test configuration and fixtures"""

import pytest

from app import create_app


@pytest.fixture(scope="session")
def app():
    """Create application for testing"""
    return create_app("testing")

@pytest.fixture(scope="session")
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_token():
    """Mock JWT token for testing"""
    return "Bearer mock-jwt-token-for-testing"
