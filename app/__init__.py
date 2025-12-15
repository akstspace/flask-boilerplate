"""Application factory and initialization"""

from flask import Flask, jsonify
from loguru import logger

from app.core.config import get_config
from app.core.database import init_db
from app.core.exceptions import APIException
from app.core.logging import setup_logging


def create_app(config_name="development"):
    """
    Application factory pattern

    Args:
        config_name: Configuration name (development, production, testing)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)

    # Setup logging
    setup_logging(app)

    logger.info(f"Starting application with {config_name} configuration")

    from app import models  # noqa: F401

    # Initialize database
    init_db(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    return app


def register_error_handlers(app: Flask):
    """Register error handlers"""

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """Handle custom API exceptions"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors"""
        return (
            jsonify(
                {"error": "NotFound", "message": "The requested resource was not found"}
            ),
            404,
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal error: {error!s}")
        return (
            jsonify(
                {
                    "error": "InternalServerError",
                    "message": "An internal error occurred",
                }
            ),
            500,
        )


def register_blueprints(app: Flask):
    """Register application blueprints"""

    # Register health check
    from app.api.health import health_bp

    app.register_blueprint(health_bp)

    # Register API v1
    from app.api.v1.swagger import api_v1_blueprint, init_api_namespaces

    init_api_namespaces()
    app.register_blueprint(api_v1_blueprint)
