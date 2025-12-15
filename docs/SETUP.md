# Setup Guide

This guide covers the initial setup and installation of the Flask boilerplate project.

## Prerequisites

- **Python 3.10+** (for local setup)
- **Docker Desktop** (for Dev Container)
- **VS Code** with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) (recommended)
- **PostgreSQL** (recommended for production-like development)
- **Redis** (required for Celery)

## Quick Start: Dev Container (Recommended)

The easiest way to get started is using the included Dev Container. Everything is pre-configured!

### Step 1: Install Required Tools

- [VS Code](https://code.visualstudio.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Step 2: Open in Dev Container

1. Open the project folder in VS Code
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Dev Containers: Reopen in Container"
4. Select and wait for the container to build (~2 minutes on first run)

The container will:
- ✅ Install all Python dependencies
- ✅ Set up PostgreSQL database
- ✅ Start Redis server
- ✅ Configure environment variables

### Step 3: Initialize Database

```bash
flask db upgrade
```

### Step 4: Start Development Server

```bash
python run.py
```

Visit `http://localhost:8000/health` - you should see a healthy response.

### Dev Container Includes

- Python 3.10+
- PostgreSQL database
- Redis cache/broker
- All development tools (pytest, black, ruff, etc.)
- Git, curl, and other utilities

No need to install anything locally!

---

## Alternative: Local Installation

If you prefer to set up locally without Dev Container, follow these steps.

### 1. Clone the Repository

```bash
git clone https://github.com/akstspace/flask-boilerplate.git
cd flask-boilerplate
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

For development (includes testing, linting tools):

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If this file exists
```

Or use the Makefile:

```bash
make install          # Production dependencies
make install-dev      # Development dependencies
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```dotenv
# Application
FLASK_ENV=development
APP_NAME=Flask API
APP_VERSION=1.0.0
SECRET_KEY=your-secret-key-here

# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/flask_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flask_db

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Keycloak (if using authentication)
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=flask-app
KEYCLOAK_CLIENT_SECRET=your-client-secret

# Logging
LOG_LEVEL=DEBUG

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4a. Security: Production Secret Management

⚠️ **IMPORTANT**: The defaults in `docker-compose.yaml` and `.env.example` are for **DEVELOPMENT ONLY**. Never use weak credentials in staging/production.

For production deployments, use a secure secret manager instead of environment files:

#### AWS Secrets Manager

1. Create a secret:
```bash
aws secretsmanager create-secret --name flask-app-secrets \
  --secret-string '{
    "SECRET_KEY": "your-secure-key",
    "DB_PASSWORD": "your-secure-password",
    "KEYCLOAK_CLIENT_SECRET": "your-client-secret"
  }'
```
2. Grant IAM permissions to your ECS/Lambda task role
3. Update `app/core/config.py` to fetch secrets at startup using boto3

#### HashiCorp Vault

1. Enable KV secrets engine and write your secrets
2. Configure Vault agent for automatic secret injection
3. Update app to read from `/var/run/secrets/...` or Vault API

#### Azure Key Vault

1. Create Key Vault: `az keyvault create --resource-group myGroup --name myVault`
2. Add secrets: `az keyvault secret set --vault-name myVault --name SECRET_KEY --value ...`
3. Use Managed Identity for authentication

#### Kubernetes Secrets

1. Create secret:
```bash
kubectl create secret generic flask-secrets \
  --from-literal=SECRET_KEY=value \
  --from-literal=DB_PASSWORD=value
```
2. Reference in deployment via `secretKeyRef`
3. Enable encryption at rest in etcd

#### Docker Secrets (Docker Swarm)

1. Create secrets: `echo "password" | docker secret create db_password -`
2. Reference in docker-compose.yaml
3. Read from `/run/secrets/db_password` in Python

**Security Best Practices:**
- ✅ Generate strong secrets: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- ✅ Rotate secrets regularly (API keys: 90 days, passwords: 30 days)
- ✅ Enable audit logging for secret access
- ✅ Use different secrets per environment
- ✅ Never log or print secrets
- ✅ Use separate service accounts with minimal permissions
- ✅ Enable encryption at rest and in transit

### 5. Initialize the Database

Start PostgreSQL (if not running):

```bash
# Using Docker
docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres

# Or with Docker Compose
docker-compose up -d
```

Initialize the database with Flask-Migrate:

```bash
flask db upgrade
```

This applies all migrations from the `migrations/` directory.

### 6. Start Redis (for Celery)

```bash
# Using Docker
docker run --name redis -p 6379:6379 -d redis

# Or with Docker Compose
docker-compose up -d
```

## Running the Application

### Development Server

```bash
python run.py
```

Or using Makefile:

```bash
make run
```

The app will be available at `http://localhost:8000`.

### Production Server (Gunicorn)

```bash
gunicorn -c gunicorn_config.py run:app
```

Configuration can be customized in `gunicorn_config.py`.

## Database Migrations

Flask-Migrate is used to manage database schema changes. See [DATABASE.md](DATABASE.md) for detailed instructions.

## Celery Worker

To process background tasks, start a Celery worker:

```bash
celery -A app.celery worker --loglevel=info
```

See [CELERY.md](CELERY.md) for details on creating and running tasks.

## Verification

Once running, check the health endpoint:

```bash
curl http://localhost:8000/health
```

You should see:

```json
{
  "status": "healthy",
  "timestamp": "2024-12-15T10:30:00Z"
}
```

## Troubleshooting

### Dev Container Issues

**Container fails to build:**
1. Ensure Docker Desktop is running
2. Pull latest base images: `docker pull mcr.microsoft.com/vscode/devcontainers/python`
3. Delete container and rebuild

**Port already in use:**
- Change port in VS Code Dev Container settings
- Or stop conflicting service: `lsof -i :8000`

### Local Installation Issues

**Import Errors**

If you get import errors, ensure:

1. Virtual environment is activated
2. All dependencies are installed: `pip install -r requirements.txt`
3. Running from the project root directory

**Database Connection Error**

```
sqlalchemy.exc.OperationalError: could not connect to server
```

Check:

1. PostgreSQL is running
2. `DATABASE_URL` is correct in `.env`
3. Database user/password are correct

**Redis Connection Error**

```
ConnectionError: Error 111 connecting to localhost:6379
```

Ensure Redis is running on `localhost:6379` or update `CELERY_BROKER_URL`.

**Module Not Found: `app`**

Run all commands from the project root directory.

## Next Steps

- Review [API.md](API.md) to understand the API structure
- Check [DATABASE.md](DATABASE.md) for model/migration management
- See [CELERY.md](CELERY.md) to learn about background tasks
- Read [TESTING.md](TESTING.md) for testing setup
