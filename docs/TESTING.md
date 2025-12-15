# Testing Guide

This boilerplate uses **pytest** for unit and integration testing with mocking support.

## Testing Stack

- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **conftest.py**: Shared fixtures and configuration

## Project Structure

```
tests/
├── conftest.py              # Global fixtures
├── unit/                    # Unit tests
│   ├── test_auth_service.py
│   ├── test_celery.py
│   ├── test_config.py
│   ├── test_exceptions.py
│   ├── test_middleware.py
│   └── test_tasks.py
└── integration/             # Integration tests
    ├── test_app.py
    ├── test_auth_api.py
    └── test_health.py
```

## Running Tests

### All Tests

```bash
pytest
```

### Specific Test File

```bash
pytest tests/unit/test_auth_service.py
```

### Specific Test Function

```bash
pytest tests/unit/test_auth_service.py::test_verify_token
```

### With Coverage Report

```bash
pytest --cov=app --cov-report=term-missing
```

Or using Makefile:

```bash
make test        # Run all tests
make coverage    # Run with coverage report
```

### Verbose Output

```bash
pytest -v
pytest -vv      # Extra verbose
```

## Test Configuration

Global test configuration in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## Fixtures

Fixtures are reusable test setup defined in `conftest.py`:

```python
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
    """Mock JWT token"""
    return "Bearer mock-jwt-token"
```

### Using Fixtures in Tests

```python
def test_health_check(client):
    """Test health endpoint using the client fixture"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
```

## Unit Tests

Unit tests focus on individual functions/methods in isolation.

### Testing Services

```python
# tests/unit/test_auth_service.py
import pytest
from app.services.auth_service import auth_service
from app.core.exceptions import AuthenticationError

def test_verify_valid_token(mocker):
    """Test token verification with valid token"""
    # Mock the JWKS fetch
    mocker.patch.object(
        auth_service,
        '_get_jwks',
        return_value={
            'keys': [
                {
                    'kid': 'test-key',
                    'kty': 'RSA',
                    'n': 'test-modulus',
                    'e': 'AQAB'
                }
            ]
        }
    )
    
    # Mock JWT verification
    mocker.patch(
        'jwt.decode',
        return_value={'sub': 'user123', 'exp': 9999999999}
    )
    
    token = 'valid.jwt.token'
    result = auth_service.verify_token(token)
    
    assert result['sub'] == 'user123'

def test_verify_invalid_token(mocker):
    """Test token verification with invalid token"""
    mocker.patch('jwt.decode', side_effect=jwt.InvalidTokenError())
    
    with pytest.raises(AuthenticationError):
        auth_service.verify_token('invalid.token')
```

### Testing Exceptions

```python
from app.core.exceptions import APIException, AuthenticationError

def test_authentication_error():
    error = AuthenticationError("Invalid token")
    assert error.status_code == 401
    assert error.message == "Invalid token"
    assert error.to_dict()['error'] == 'AuthenticationError'
```

### Testing Configuration

```python
# tests/unit/test_config.py
from app.core.config import DevelopmentConfig, ProductionConfig

def test_development_config():
    config = DevelopmentConfig()
    assert config.DEBUG is True
    assert config.TESTING is False

def test_production_config():
    config = ProductionConfig()
    assert config.DEBUG is False
```

## Integration Tests

Integration tests verify how components work together.

### Testing API Endpoints

```python
# tests/integration/test_health.py
def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'timestamp' in data

def test_health_endpoint_response_format(client):
    """Verify health response format"""
    response = client.get('/health')
    assert response.content_type == 'application/json'
```

### Testing Authenticated Endpoints

```python
# tests/integration/test_auth_api.py
def test_get_current_user(client, mock_token, mocker):
    """Test /auth/me endpoint"""
    # Mock the auth service
    mock_user = {
        'user_id': '123',
        'username': 'testuser',
        'email': 'test@example.com'
    }
    
    mocker.patch(
        'app.core.middleware.auth_service.verify_token',
        return_value=mock_user
    )
    
    response = client.get(
        '/api/v1/auth/me',
        headers={'Authorization': mock_token}
    )
    
    assert response.status_code == 200
    assert response.json['user']['username'] == 'testuser'

def test_get_current_user_unauthorized(client):
    """Test endpoint without token"""
    response = client.get('/api/v1/auth/me')
    assert response.status_code == 401
```

### Testing with Database

Tests use an in-memory SQLite database (configured in `TestingConfig`):

```python
# tests/integration/test_users.py
import pytest
from app.models.user import User
from app.core.database import db

def test_create_user(app):
    """Test user creation"""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        
        # Verify
        retrieved = User.query.filter_by(username='testuser').first()
        assert retrieved is not None
        assert retrieved.email == 'test@example.com'
```

## Testing Celery Tasks

### Mocking Celery

```python
# tests/unit/test_tasks.py
import pytest
from app.tasks.sample_tasks import add_numbers

def test_add_numbers_task(mocker):
    """Test Celery task"""
    # Mock the Celery task to run synchronously
    mocker.patch.object(add_numbers, 'delay', side_effect=add_numbers.run)
    
    result = add_numbers.delay(4, 6)
    assert result == 10

def test_email_task_failure(mocker):
    """Test task retry on failure"""
    mock_send_email = mocker.patch('app.tasks.send_email')
    mock_send_email.side_effect = Exception("SMTP failed")
    
    with pytest.raises(Exception):
        mock_send_email()
```

### Using `CELERY_TASK_ALWAYS_EAGER`

For testing, you can make Celery execute tasks synchronously:

```python
# In conftest.py
@pytest.fixture
def app():
    app = create_app("testing")
    # Execute Celery tasks immediately
    app.config['CELERY_TASK_ALWAYS_EAGER'] = True
    app.config['CELERY_TASK_EAGER_PROPAGATES'] = True
    return app
```

Then tasks run immediately:

```python
def test_task_execution(app):
    with app.app_context():
        result = add_numbers.delay(5, 3)
        assert result == 8  # Result immediately available
```

## Testing Middleware

```python
# tests/unit/test_middleware.py
import pytest
from app.core.middleware import extract_token_from_header

def test_extract_valid_token():
    """Test token extraction"""
    auth_header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    token = extract_token_from_header(auth_header)
    assert token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

def test_extract_invalid_token():
    """Test with invalid format"""
    auth_header = "InvalidFormat token"
    with pytest.raises(AuthenticationError):
        extract_token_from_header(auth_header)
```

## Coverage Reports

Generate coverage reports:

```bash
# Terminal output
pytest --cov=app --cov-report=term-missing

# HTML report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

Target coverage:

```bash
# Fail if coverage < 80%
pytest --cov=app --cov-fail-under=80
```

## Best Practices

1. **Isolation**: Mock external dependencies (API calls, databases, brokers)
2. **Clarity**: Use descriptive test names like `test_verify_token_with_expired_token`
3. **Setup/Teardown**: Use fixtures for common setup
4. **One assertion per test**: Focus on single behavior
5. **Parametrization**: Test multiple cases with `@pytest.mark.parametrize`

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("admin", True),
    ("user", False),
    ("guest", False),
])
def test_is_admin(input, expected):
    assert User(role=input).is_admin() == expected
```

## Debugging Tests

### Verbose Output

```bash
pytest -vv -s tests/unit/test_auth.py
```

### Drop into Debugger

```python
def test_something():
    breakpoint()  # Test execution pauses here
    # Use `n`, `s`, `c` to step through
```

### Print Statements

```bash
pytest -s tests/unit/test_auth.py  # Show print() output
```

## Common Issues

### ImportError: No module named 'app'

Run pytest from project root:

```bash
cd /path/to/flask-boilerplate
pytest
```

### Database locked (SQLite)

If using SQLite, ensure only one test accesses it at a time. Use `scope="function"` fixtures.

### Celery tasks not executing

Use `CELERY_TASK_ALWAYS_EAGER` configuration in test config.

## Next Steps

- Review test examples in `tests/unit/` and `tests/integration/`
- Add tests for new features before implementing
- Run `make coverage` regularly to check coverage
