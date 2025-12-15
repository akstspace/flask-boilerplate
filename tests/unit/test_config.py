"""Unit tests for configuration"""

import os

from app.core.config import (
    BaseConfig,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    get_config,
)


class TestConfig:
    """Test configuration classes"""

    def test_base_config(self):
        """Test base configuration"""
        config = BaseConfig()
        assert os.getenv("APP_NAME", "Flask API") == config.APP_NAME
        assert config.API_V1_PREFIX == "/api/v1"
        assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False

    def test_development_config(self):
        """Test development configuration"""
        config = DevelopmentConfig()
        assert config.DEBUG is True
        assert config.SQLALCHEMY_ECHO is True
        assert config.LOG_LEVEL == "DEBUG"

    def test_production_config(self):
        """Test production configuration"""
        config = ProductionConfig()
        assert config.DEBUG is False
        assert config.TESTING is False

    def test_testing_config(self):
        """Test testing configuration"""
        config = TestingConfig()
        assert config.TESTING is True
        assert "sqlite" in config.SQLALCHEMY_DATABASE_URI
        assert config.CELERY_TASK_ALWAYS_EAGER is True

    def test_get_config(self):
        """
        Verify get_config resolves configuration names to their corresponding config classes and defaults to DevelopmentConfig for unknown names.
        
        Checks:
        - "development" returns a class that is a subclass of BaseConfig.
        - "testing" returns the TestingConfig class.
        - an invalid name returns DevelopmentConfig.
        """
        config = get_config("development")
        assert isinstance(config, type)
        assert issubclass(config, BaseConfig)

        config = get_config("testing")
        assert config == TestingConfig

        # Test default
        config = get_config("invalid")
        assert config == DevelopmentConfig