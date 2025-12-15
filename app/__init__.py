"""Application factory and initialization"""

from flask import Flask, jsonify
from loguru import logger

from app.core.config import get_config
from app.core.database import init_db
from app.core.exceptions import APIException
from app.core.logging import setup_logging


def create_app(config_name="development"):
    """
    Create and configure the Flask application.
    
    Parameters:
        config_name (str): Configuration name, e.g. "development", "production", or "testing".
    
    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)

    # Setup logging
    setup_logging(app)

    logger.info(f"Starting application with {config_name} configuration")

    # Initialize database
    init_db(app)

    # Import models to register them with SQLAlchemy
    from app import models # noqa: F401

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    return app


def register_error_handlers(app: Flask):
    """
    Register centralized JSON error handlers on the given Flask application.
    
    Registers handlers for:
    - APIException: returns the exception's dictionary payload as JSON with the exception's status code.
    - 404 Not Found: returns JSON {"error": "NotFound", "message": "The requested resource was not found"} with status 404.
    - 500 Internal Server Error: logs the error and returns JSON {"error": "InternalServerError", "message": "An internal error occurred"} with status 500.
    """

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """
        Convert a custom API exception into a JSON HTTP response.
        
        Parameters:
            error (APIException): Exception object exposing `to_dict()` for the response body and `status_code` for the HTTP status.
        
        Returns:
            flask.wrappers.Response: JSON response with the exception data and the exception's HTTP status code.
        """
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        """
        Return a JSON response for HTTP 404 Not Found errors.
        
        Parameters:
            error: The caught 404 exception provided by Flask's error handling.
        
        Returns:
            A tuple of (JSON response body, int) where the body is
            {"error": "NotFound", "message": "The requested resource was not found"}
            and the status code is 404.
        """
        return (
            jsonify(
                {"error": "NotFound", "message": "The requested resource was not found"}
            ),
            404,
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        """
        Return a standardized JSON response for internal server errors.
        
        Parameters:
            error: The exception or error instance that triggered the handler.
        
        Returns:
            A tuple of (JSON response, int) where the JSON body contains
            {"error": "InternalServerError", "message": "An internal error occurred"} and the status code is 500.
        """
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
    """
    Register application blueprints and initialize API namespaces.
    
    Registers the health-check blueprint and the API v1 blueprint after calling init_api_namespaces() to set up its namespaces.
    """

    # Register health check
    from app.api.health import health_bp

    app.register_blueprint(health_bp)

    # Register API v1
    from app.api.v1.swagger import api_v1_blueprint, init_api_namespaces

    init_api_namespaces()
    app.register_blueprint(api_v1_blueprint)