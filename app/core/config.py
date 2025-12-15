"""Application configuration"""

import os

from dotenv import load_dotenv

# Get the project root directory (parent of 'app' directory)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
load_dotenv(os.path.join(basedir, ".env"))


class BaseConfig:
    """Base configuration"""

    # Application
    APP_NAME = os.getenv("APP_NAME", "Flask API")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    API_V1_PREFIX = "/api/v1"

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "flask_db")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )

    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TIMEZONE = "UTC"
    CELERY_ENABLE_UTC = True

    # Keycloak JWT Configuration
    KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080")
    KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
    KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "flask-app")
    KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")

    # JWT Configuration
    JWT_ALGORITHM = "RS256"
    JWT_VERIFY_EXPIRATION = True
    JWT_VERIFY_SIGNATURE = True
    JWT_LEEWAY = 0

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Request/Response
    JSON_SORT_KEYS = False
    RESTX_MASK_SWAGGER = False
    RESTX_VALIDATE = True

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(BaseConfig):
    """Development configuration"""

    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(BaseConfig):
    """Production configuration"""

    DEBUG = False
    TESTING = False

    # Ensure secret key is set in production
    @property
    def SECRET_KEY(self) -> str:
        """
        Retrieve the application's SECRET_KEY from the environment and enforce that a non-default value is set for production.
        
        Returns:
            The SECRET_KEY string from the environment.
        
        Raises:
            ValueError: If SECRET_KEY is not set or equals the default development value "dev-secret-key-change-in-production".
        """
        secret = os.getenv("SECRET_KEY")
        if not secret or secret == "dev-secret-key-change-in-production":
            msg = "SECRET_KEY must be set in production"
            raise ValueError(msg)
        return secret


class TestingConfig(BaseConfig):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    WTF_CSRF_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str | None = None) -> BaseConfig:
    """
    Selects the application configuration class for the given environment name.
    
    Parameters:
        config_name (str | None): Environment name to select the configuration. If None, reads FLASK_ENV from the environment and uses "development" when FLASK_ENV is not set.
    
    Returns:
        The configuration class corresponding to the provided environment name; defaults to DevelopmentConfig if no matching configuration is found.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    return config_by_name.get(config_name, DevelopmentConfig)