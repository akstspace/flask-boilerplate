# Database Guide

This boilerplate uses **SQLAlchemy** for ORM and **Flask-Migrate** for schema management.

## Technology Stack

- **SQLAlchemy 2.0**: Python ORM for database operations
- **Flask-SQLAlchemy**: Flask integration for SQLAlchemy
- **Flask-Migrate**: Alembic wrapper for migrations
- **PostgreSQL**: Recommended database for production

## Database Configuration

Database connection is configured in `app/core/config.py`:

```python
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/flask_db"
)
```

Environment variables:

```dotenv
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/flask_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flask_db
```

For development, you can use SQLite:

```dotenv
DATABASE_URL=sqlite:///dev.db
```

## Creating Models

Models are defined in `app/models/`. Each model inherits from `db.Model`:

```python
# app/models/user.py
from app.core.database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<User {self.username}>'
```

### Model Registration

Models must be imported in `app/__init__.py` so SQLAlchemy knows about them:

```python
# This is already done in the factory
from app import models  # noqa: F401
```

## Flask-Migrate (Database Migrations)

Flask-Migrate wraps **Alembic** for version-controlled schema changes.

### Initialize Migrations (First Time Only)

```bash
flask db init
```

This creates the `migrations/` directory.

### Create a Migration

After modifying a model, create a migration:

```bash
flask db migrate -m "Add username field to users"
```

This generates a new file in `migrations/versions/` with the schema changes.

### Review the Migration

Before applying, review the generated migration file to ensure it's correct:

```python
# migrations/versions/xxxx_add_username_field_to_users.py

def upgrade():
    op.add_column('users', sa.Column('username', sa.String(80), nullable=False))

def downgrade():
    op.drop_column('users', 'username')
```

### Apply Migrations

```bash
flask db upgrade
```

This applies all pending migrations to your database.

### Revert Migrations

```bash
flask db downgrade  # Revert one migration
flask db downgrade base  # Revert all migrations
```

### View Migration History

```bash
flask db history
```

### Manual Migrations

Create a custom migration when auto-detection doesn't work:

```bash
flask db revision -m "Custom migration description"
```

Then edit the generated file in `migrations/versions/`:

```python
def upgrade():
    op.execute("CREATE INDEX idx_users_email ON users(email)")

def downgrade():
    op.execute("DROP INDEX idx_users_email")
```

## Working with Models in Python

### Create (INSERT)

```python
from app.core.database import db
from app.models.user import User

new_user = User(username='john_doe', email='john@example.com')
db.session.add(new_user)
db.session.commit()
```

### Read (SELECT)

```python
# Get by primary key
user = User.query.get(1)

# Get by filter
user = User.query.filter_by(username='john_doe').first()

# Get all
users = User.query.all()

# Count
count = User.query.count()
```

### Update (UPDATE)

```python
user = User.query.get(1)
user.email = 'newemail@example.com'
db.session.commit()
```

### Delete (DELETE)

```python
user = User.query.get(1)
db.session.delete(user)
db.session.commit()
```

## Using in Flask Application Context

When working outside a request context (e.g., in Celery tasks), use the app context:

```python
from flask import current_app
from app.core.database import db
from app.models.user import User

def my_task():
    with current_app.app_context():
        users = User.query.all()
        # Do something with users
```

## Transactions

Use transactions for multi-step operations:

```python
try:
    user1 = User(username='alice', email='alice@example.com')
    user2 = User(username='bob', email='bob@example.com')
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    raise
```

## Database CLI Commands

```bash
# Show current database URL
flask db current

# Show current revision
flask db current

# Show upgrade/downgrade route
flask db upgrade --help
flask db downgrade --help

# Merge branches (if using branching)
flask db merge -m "Merge migrations"
```

## Common Issues

### `Table already exists`

This usually means a migration was applied manually. Check the Alembic version table:

```sql
SELECT * FROM alembic_version;
```

### `No such table`

Make sure migrations are applied:

```bash
flask db upgrade
```

### Model changes not detected

Flask-Migrate's auto-detect has limitations (e.g., column renames). Create a manual migration:

```bash
flask db revision -m "Rename column"
```

Then edit the migration file directly.

## Testing with Different Databases

For tests, the boilerplate uses an in-memory SQLite database. This is configured in `app/core/config.py`:

```python
class TestingConfig(BaseConfig):
    TESTING = True
    # SQLALCHEMY_DATABASE_URI automatically uses SQLite in memory
```

Tests create and drop tables automatically; no migrations needed.

## Next Steps

- Review [API.md](API.md) for using models in endpoints
- See [CELERY.md](CELERY.md) for database operations in background tasks
- Check [TESTING.md](TESTING.md) for database testing setup
