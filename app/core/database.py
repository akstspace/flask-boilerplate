"""Database initialization and utilities"""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()


def init_db(app):
    """
    Configure SQLAlchemy, Marshmallow, and Flask-Migrate for the given Flask application.
    
    Parameters:
        app (flask.Flask): The Flask application instance to initialize extensions on. When app.config["TESTING"] is truthy, all database tables are created within the application's context.
    """
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    # In testing mode, create tables directly
    if app.config.get("TESTING"):
        with app.app_context():
            db.create_all()