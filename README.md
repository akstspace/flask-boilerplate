
# Flask Boilerplate

A lightweight Flask application boilerplate with support for structured app layout, Celery background tasks, Flask-Migrate database migrations.

> **⚠️ WARNING**: This library is still under testing and **not recommended for production use yet**. Use at your own risk.

## Quick Links

📚 **[Full Documentation](docs/INDEX.md)** - Start here for complete guides

### Documentation Index
- **[Setup Guide](docs/SETUP.md)** - Installation, environment setup, database initialization
- **[API Guide](docs/API.md)** - Endpoints, authentication, Flask-RESTX
- **[Database Guide](docs/DATABASE.md)** - SQLAlchemy, Flask-Migrate, models
- **[Celery Guide](docs/CELERY.md)** - Background tasks, Redis, task monitoring
- **[Testing Guide](docs/TESTING.md)** - pytest, fixtures, unit & integration tests
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production setup, Gunicorn, Nginx, Docker

## Key Features

- ✅ **Modular Architecture** - Clean separation of concerns with organized `app/` package
- ✅ **Versioned APIs** - Flask-RESTX with Swagger/OpenAPI documentation
- ✅ **Database Management** - SQLAlchemy ORM with Flask-Migrate for schema versioning
- ✅ **Async Tasks** - Celery background job queue with Redis broker
- ✅ **JWT Authentication** - Keycloak integration with Bearer token validation
- ✅ **Comprehensive Testing** - pytest with fixtures, mocks, and coverage reports
- ✅ **Production Ready** - Gunicorn WSGI server, Nginx reverse proxy, Docker support
- ✅ **Structured Logging** - Centralized logging with configurable levels

## Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Flask 3.1 + Flask-RESTX |
| **API** | OpenAPI/Swagger with Flask-RESTX |
| **Database** | PostgreSQL + SQLAlchemy 2.0 |
| **Migrations** | Flask-Migrate (Alembic wrapper) |
| **Auth** | JWT + Keycloak |
| **Tasks** | Celery 5.6 + Redis |
| **Testing** | pytest + pytest-cov + pytest-mock |
| **Server** | Gunicorn + Nginx |
| **Containers** | Docker + Docker Compose |

## Setup

### Option 1: Dev Container (Recommended)

The project includes a Dev Container configuration. Open in VS Code:

1. Install [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open the project folder in VS Code
3. Press `Cmd+Shift+P` and select **"Dev Containers: Reopen in Container"**
4. Wait for the container to build (first time takes ~2 min)
5. Terminal automatically opens with all dependencies installed

Then:
```bash
flask db upgrade
python run.py
```

### Option 2: Local Installation

```bash
# Clone and install
git clone https://github.com/akstspace/flask-boilerplate.git
cd flask-boilerplate
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Edit .env with your settings

# Initialize database
flask db upgrade

# Start development server
python run.py
```

Visit `http://localhost:8000/health` to verify.

**For detailed setup**: See [Setup Guide](docs/SETUP.md)

## Common Commands

```bash
# Development
make install-dev    # Install dev dependencies
make run           # Start dev server
make test          # Run all tests
make coverage      # Generate coverage report

# Database
flask db migrate -m "description"  # Create migration
flask db upgrade   # Apply migrations
flask db downgrade # Revert migration

# Celery
celery -A app.celery worker --loglevel=info
celery -A app.celery beat --loglevel=info    # Periodic tasks

# Production
gunicorn -c gunicorn_config.py run:app

# Docker
docker-compose up -d   # Start all services
docker-compose down    # Stop services
```

## Project Structure

```
app/
├── api/              # HTTP API endpoints
│   ├── health.py     # Health check
│   └── v1/           # API v1 (auth, etc.)
├── celery/           # Celery task configuration
├── core/             # Core utilities
│   ├── config.py     # Configuration management
│   ├── database.py   # SQLAlchemy & migrations setup
│   ├── middleware.py # JWT authentication
│   ├── exceptions.py # Custom exceptions
│   └── logging.py    # Logging configuration
├── models/           # SQLAlchemy ORM models
├── schemas/          # Request/response schemas
├── services/         # Business logic (auth_service, etc.)
└── tasks/            # Celery background tasks

tests/
├── conftest.py       # pytest fixtures
├── unit/             # Unit tests
└── integration/      # Integration tests

docs/                 # Documentation (detailed guides)
```

## Key Endpoints

```
GET  /health               # Health check
GET  /api/v1/auth/me       # Current user (requires auth)
GET  /api/v1/docs            # API documentation (Swagger UI)
```

## Environment Variables

```dotenv
# Application
FLASK_ENV=development
SECRET_KEY=your-secret-key
APP_NAME=Flask API

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db_name

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Authentication
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=flask-app

# Logging
LOG_LEVEL=DEBUG
```

See [Setup Guide](docs/SETUP.md#environment-configuration) for full reference.

## Documentation

Each major feature has detailed documentation:

- **Getting Started?** → [Setup Guide](docs/SETUP.md)
- **Building APIs?** → [API Guide](docs/API.md)
- **Working with Data?** → [Database Guide](docs/DATABASE.md)
- **Background Jobs?** → [Celery Guide](docs/CELERY.md)
- **Writing Tests?** → [Testing Guide](docs/TESTING.md)

**[→ Full Documentation Index](docs/INDEX.md)**

## Quick Examples

### Add a New Endpoint

```python
# app/api/v1/users.py
from flask_restx import Namespace, Resource, fields
from app.core.middleware import require_auth

users_ns = Namespace('users', description='User operations')

@users_ns.route('/<int:user_id>')
class User(Resource):
    @require_auth  # Requires JWT token
    def get(self, user_id):
        """Get user by ID"""
        return {'id': user_id, 'name': 'John'}, 200
```

See [API Guide](docs/API.md#adding-new-endpoints) for more.

### Create a Database Model

```python
# app/models/user.py
from app.core.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Then migrate:
flask db migrate -m "Add user model"
flask db upgrade
```

See [Database Guide](docs/DATABASE.md#creating-models) for more.

### Create a Background Task

```python
# app/tasks/email_tasks.py
from app.celery import celery

@celery.task(name='app.tasks.send_email')
def send_email(recipient, subject):
    """Send email asynchronously"""
    # Your email logic here
    return f"Email sent to {recipient}"

# Call from endpoint:
from flask_restx import Resource
result = send_email.delay('user@example.com', 'Hello!')
return {'task_id': result.id}, 202
```

See [Celery Guide](docs/CELERY.md#creating-tasks) for more.

### Write Tests

```python
# tests/integration/test_api.py
def test_health_endpoint(client):
    """Test health check"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_protected_endpoint(client, mocker):
    """Test authenticated endpoint"""
    mocker.patch('app.core.middleware.auth_service.verify_token',
                 return_value={'user_id': '123'})
    response = client.get('/api/v1/auth/me',
                         headers={'Authorization': 'Bearer token'})
    assert response.status_code == 200
```

See [Testing Guide](docs/TESTING.md) for more.

## Support

- 📖 **Documentation** → [docs/](docs/)
- 🐛 **Issues** → Open an issue on the repository
- 💬 **Discussions** → Use GitHub Discussions

---

**Remember**: This boilerplate is under testing