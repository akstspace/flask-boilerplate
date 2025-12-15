"""Unit tests for Celery configuration"""

from unittest.mock import MagicMock, patch


class TestCeleryConfig:
    """Tests for Celery configuration"""

    @patch("app.celery.celery_config.config_by_name")
    def test_make_celery(self, mock_config):
        """Test make_celery function"""
        from app.celery.celery_config import make_celery

        # Mock config
        mock_conf = MagicMock()
        mock_conf.CELERY_BROKER_URL = "redis://localhost:6379/0"
        mock_conf.CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
        mock_conf.CELERY_TASK_SERIALIZER = "json"
        mock_conf.CELERY_RESULT_SERIALIZER = "json"
        mock_conf.CELERY_ACCEPT_CONTENT = ["json"]
        mock_conf.CELERY_TIMEZONE = "UTC"
        mock_conf.CELERY_ENABLE_UTC = True
        mock_config.__getitem__.return_value = mock_conf

        celery_app = make_celery("development")

        assert celery_app is not None
        assert celery_app.main == "flask_app"

    def test_celery_instance_exists(self):
        """Test that celery instance is created"""
        from app.celery import celery

        assert celery is not None
        assert celery.main == "flask_app"

    def test_celery_tasks_imported(self):
        """Test that tasks are imported and registered"""
        from app.celery import celery

        # Check that tasks are registered
        task_names = list(celery.tasks.keys())
        registered_app_tasks = [t for t in task_names if t.startswith("app.tasks")]

        assert len(registered_app_tasks) > 0
