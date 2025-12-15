"""Celery application configuration"""

import os

from celery import Celery

from app.core.config import config_by_name


def make_celery(config_name="development"):
    """
    Create and configure a Celery application instance using a named configuration.
    
    Parameters:
        config_name (str): Key name to select configuration from config_by_name (defaults to "development").
    
    Returns:
        celery (Celery): A Celery instance configured with broker, result backend, serializers, accepted content types, timezone, UTC setting, and autodiscovery of tasks from the "app.tasks" package.
    """
    config = config_by_name[config_name]

    celery = Celery(
        "flask_app",
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND,
    )

    celery.conf.update(
        task_serializer=config.CELERY_TASK_SERIALIZER,
        result_serializer=config.CELERY_RESULT_SERIALIZER,
        accept_content=config.CELERY_ACCEPT_CONTENT,
        timezone=config.CELERY_TIMEZONE,
        enable_utc=config.CELERY_ENABLE_UTC,
    )

    # Autodiscover tasks from the tasks package
    celery.autodiscover_tasks(["app.tasks"])

    return celery


env = os.getenv("FLASK_ENV", "development")
celery = make_celery(env)
