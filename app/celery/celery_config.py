"""Celery application configuration"""

import os

from celery import Celery

from app.core.config import config_by_name


def make_celery(config_name="development"):
    """
    Create and configure a Celery application using the named configuration.
    
    The function selects a configuration from `config_by_name` by `config_name`, instantiates a Celery app named "flask_app", and applies configuration values for broker, result backend, serializers, accepted content, timezone, and UTC enablement. It also enables autodiscovery of tasks from the "app.tasks" package.
    
    Parameters:
        config_name (str): Key identifying which configuration to load from `config_by_name`. Defaults to "development".
    
    Returns:
        celery (Celery): A configured Celery application instance.
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
