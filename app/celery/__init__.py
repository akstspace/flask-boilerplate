"""Celery configuration package"""

from app.celery.celery_config import celery, make_celery

__all__ = ["celery", "make_celery"]
