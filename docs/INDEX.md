# Documentation Index

Welcome to the Flask Boilerplate documentation. This guide covers setup, development, deployment, and best practices.

## Quick Navigation

### Getting Started
- **[SETUP.md](SETUP.md)** - Installation, environment configuration, and verification
  - **Dev Container setup** (recommended, all tools pre-installed)
  - Local Python environment setup
  - Database initialization with Flask-Migrate
  - Running the development server
  - Health check verification

### Development Guides
- **[API.md](API.md)** - API endpoints and Flask-RESTX usage
  - Available endpoints (health, auth)
  - Creating new endpoints
  - Authentication with JWT
  - Error handling and CORS
  
- **[DATABASE.md](DATABASE.md)** - SQLAlchemy, Flask-Migrate, models
  - Creating and managing models
  - Database migrations with Flask-Migrate
  - CRUD operations
  - Working with transactions

- **[CELERY.md](CELERY.md)** - Background tasks and job queue
  - Task creation and execution
  - Redis broker setup
  - Task monitoring with Flower
  - Scheduled/periodic tasks

- **[TESTING.md](TESTING.md)** - Unit and integration testing
  - pytest setup and usage
  - Writing tests with fixtures and mocks
  - Testing Celery tasks
  - Coverage reporting

## Stack Overview

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | Flask 3.1 | Core web server |
| **API** | Flask-RESTX | REST API with Swagger |
| **Database** | SQLAlchemy 2.0 + PostgreSQL | Data persistence |
| **Migrations** | Flask-Migrate | Database schema versioning |
| **ORM** | SQLAlchemy | Object-relational mapping |
| **Task Queue** | Celery 5.6 | Async task processing |
| **Broker** | Redis | Message broker |
| **Authentication** | JWT + Keycloak | Secure API access |
| **Testing** | pytest | Unit and integration tests |
| **WSGI Server** | Gunicorn | Production server |
| **Reverse Proxy** | Nginx | Load balancing, SSL |

## Common Tasks

### Set up local development
1. Follow [SETUP.md](SETUP.md)
2. Run `make install-dev`
3. Create `.env` file with `FLASK_ENV=development`
4. Start with `python run.py`

### Add a new API endpoint
1. Read [API.md](API.md) - Creating New Endpoints
2. Define your endpoint in `app/api/v1/`
3. Register namespace in `app/api/v1/swagger.py`
4. Write tests in `tests/integration/`

### Add a database model
1. Create model in `app/models/`
2. Follow [DATABASE.md](DATABASE.md) - Creating Models
3. Run `flask db migrate -m "Add new model"`
4. Run `flask db upgrade`
5. Write tests

### Create a background task
1. Follow [CELERY.md](CELERY.md) - Creating Tasks
2. Define task in `app/tasks/`
3. Start Celery worker
4. Call task with `.delay()` from endpoints
5. Test with [TESTING.md](TESTING.md) - Testing Celery Tasks

### Write tests
1. Read [TESTING.md](TESTING.md)
2. Add test file to `tests/unit/` or `tests/integration/`
3. Use fixtures from `conftest.py`
4. Run `pytest` or `make coverage`

## Project Structure

```
flask-boilerplate/
├── app/
│   ├── api/              # API endpoints
│   │   ├── health.py     # Health check
│   │   └── v1/           # API v1
│   │       ├── auth.py   # Auth endpoints
│   │       └── swagger.py # API setup
│   ├── celery/           # Celery tasks
│   ├── core/             # Core utilities
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database setup
│   │   ├── middleware.py # Auth middleware
│   │   └── exceptions.py # Custom exceptions
│   ├── models/           # Database models
│   ├── schemas/          # Request/response schemas
│   ├── services/         # Business logic
│   └── tasks/            # Celery tasks
├── tests/                # Unit & integration tests
├── migrations/           # Database migrations
├── docs/                 # Documentation (this folder)
├── run.py               # Application entry point
├── gunicorn_config.py   # Gunicorn configuration
├── Dockerfile           # Docker image definition
├── docker-compose.yaml  # Multi-container setup
├── Makefile             # Common commands
├── requirements.txt     # Python dependencies
└── pytest.ini          # pytest configuration
```

## Environment Variables Reference

```dotenv
# Application
FLASK_ENV=development|production|testing
SECRET_KEY=your-secret-key
APP_NAME=Flask API
APP_VERSION=1.0.0

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Keycloak
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=flask-app

# Logging
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
```

## Useful Commands

```bash
# Development
make install-dev          # Install dev dependencies
make run                  # Start dev server
make test                 # Run tests
make coverage             # Coverage report

# Database
flask db migrate -m "message"  # Create migration
flask db upgrade          # Apply migrations
flask db downgrade        # Revert migration

# Celery
celery -A app.celery worker --loglevel=info
celery -A app.celery beat --loglevel=info
flower -A app.celery --port=5555

# Production
gunicorn -c gunicorn_config.py run:app

# Docker
docker-compose up -d      # Start all services
docker-compose down       # Stop all services
```

## Key Concepts

### Authentication Flow
1. Client sends JWT token in `Authorization: Bearer <token>` header
2. `@require_auth` decorator validates token with Keycloak
3. Token claims are available in `g.user`
4. Unauthorized requests return 401

### Task Execution Flow
1. Endpoint calls `task.delay()` with arguments
2. Task is queued in Redis broker
3. Celery worker picks up and executes
4. Result is stored in Redis result backend
5. Endpoint can poll for result if needed

### Database Schema Management
1. Create/modify model in `app/models/`
2. Run `flask db migrate` to auto-generate migration
3. Review generated migration file
4. Run `flask db upgrade` to apply changes
5. Commit migration file to version control

## Support & Troubleshooting

See the Troubleshooting section in each guide:
- [SETUP.md - Troubleshooting](SETUP.md#troubleshooting)
- [CELERY.md - Troubleshooting](CELERY.md#troubleshooting)
- [DEPLOYMENT.md - Troubleshooting](DEPLOYMENT.md#troubleshooting)
- [TESTING.md - Common Issues](TESTING.md#common-issues)

## ⚠️ Warning

This Flask boilerplate is still under testing and **not recommended for production use yet**. Use in production at your own risk and ensure proper security hardening, testing, and monitoring.

---

**Last Updated**: December 2024
