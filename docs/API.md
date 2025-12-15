# API Documentation

The Flask boilerplate uses **Flask-RESTX** for API development and Swagger/OpenAPI documentation.

## API Structure

```text
app/api/
├── health.py          # Health check endpoint
└── v1/
    ├── auth.py        # Authentication endpoints
    ├── swagger.py     # Swagger/OpenAPI setup
    └── __init__.py
```

### Versioning

All API endpoints are versioned under `/api/v1/`. This allows multiple API versions to coexist.

## Health Check Endpoint

**GET** `/health`

Returns the application health status.

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2024-12-15T10:30:00Z"
}
```

## Authentication Endpoints

### Get Current User

**GET** `/api/v1/auth/me`

Requires JWT Bearer token in the `Authorization` header.

```bash
curl -H "Authorization: Bearer <your-jwt-token>" \
     http://localhost:8000/api/v1/auth/me
```

Response:

```json
{
  "user": {
    "user_id": "12345",
    "username": "john_doe",
    "email": "john@example.com",
    "email_verified": true,
    "name": "John Doe",
    "given_name": "John",
    "family_name": "Doe",
    "roles": ["user", "admin"],
    "client_roles": ["admin"]
  },
  "status": "success"
}
```

Error Response (401):

```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing token"
}
```

## Adding New Endpoints

### 1. Create a New Namespace

In `app/api/v1/`, create a new file (e.g., `users.py`):

```python
from flask_restx import Namespace, Resource, fields

users_ns = Namespace('users', description='User operations')

user_model = users_ns.model('User', {
    'id': fields.Integer(required=True),
    'username': fields.String(required=True),
    'email': fields.String(required=True),
})

@users_ns.route('/<int:user_id>')
class User(Resource):
    @users_ns.doc('get_user')
    @users_ns.response(200, 'Success', user_model)
    @users_ns.response(404, 'Not Found')
    def get(self, user_id):
        """Get a user by ID"""
        # Your logic here
        return {'id': user_id, 'username': 'john_doe', 'email': 'john@example.com'}, 200
```

### 2. Register the Namespace

In `app/api/v1/swagger.py`, add your namespace to `init_api_namespaces()`:

```python
def init_api_namespaces():
    from app.api.v1.users import users_ns
    api.add_namespace(users_ns, path='/users')
```

### 3. Register Blueprint in App Factory

In `app/__init__.py`, the blueprint is already registered. Your new namespace will be automatically included.

## Authentication with JWT

The boilerplate includes **Keycloak** JWT authentication via the `require_auth` decorator.

### Using the `require_auth` Decorator

```python
from flask_restx import Resource
from app.core.middleware import require_auth

@users_ns.route('/me')
class CurrentUser(Resource):
    @require_auth
    def get(self):
        """Get current authenticated user"""
        from flask import g
        return {'user': g.user}, 200
```

### How It Works

1. Extract Bearer token from `Authorization` header
2. Fetch public key from Keycloak
3. Verify JWT signature and expiration
4. Populate `g.user` with token claims
5. Reject if invalid or expired

### Configuration

Set these environment variables:

```dotenv
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=flask-app
JWT_ALGORITHM=RS256
JWT_VERIFY_EXPIRATION=True
JWT_VERIFY_SIGNATURE=True
```

## Swagger Documentation

Visit the interactive API documentation at:

```text
http://localhost:8000/api/v1/docs
```

This shows all endpoints, request/response schemas, and allows testing directly from the browser.

## Error Handling

Custom API exceptions are defined in `app/core/exceptions.py`:

```python
from app.core.exceptions import APIException

class CustomError(APIException):
    def __init__(self, message):
        super().__init__(message, status_code=400)

raise CustomError("Something went wrong")
```

Standard error responses:

```json
{
  "error": "BadRequest",
  "message": "Invalid input parameters"
}
```

## CORS Configuration

CORS is enabled by default for the origins specified in `CORS_ORIGINS` environment variable:

```dotenv
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Request Validation

Flask-RESTX automatically validates request bodies against defined models. Invalid data returns a 400 Bad Request with validation errors.

## Response Serialization

Use `flask-marshmallow` for advanced serialization. Define schemas in `app/schemas/` and use them with `marshal_with` decorator for automatic response transformation.
