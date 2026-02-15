"""Application factory and initialization"""

from flask import Flask, jsonify
from loguru import logger

from app.core.config import get_config
from app.core.database import init_db
from app.core.exceptions import APIException
from app.core.logging import setup_logging


def create_app(config_name="development"):
    """
    Create and configure a Flask application instance.
    
    Parameters:
        config_name (str): Configuration name to load (e.g., "development", "production", "testing").
    
    Returns:
        Flask: A Flask application instance configured with the selected settings, logging, database, error handlers, and blueprints.
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

    # Initialize auth service (cached for request lifetime)
    from app.services.auth_service import init_auth_service

    init_auth_service(app)

    # Import models to register them with SQLAlchemy
    from app import models # noqa: F401

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    return app


def register_error_handlers(app: Flask):
    """
    Register global HTTP error handlers on the given Flask application.
    
    Registers handlers for:
    - APIException: returns the exception's dict payload as JSON with the exception's status code.
    - 404 Not Found: returns JSON with error "NotFound" and a standard message, status 404.
    - 500 Internal Server Error: logs the error and returns JSON with error "InternalServerError" and a standard message, status 500.
    """

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """
        Create a JSON HTTP response from a custom API exception.
        
        Converts the exception's dictionary representation into a JSON response and sets the response HTTP status code to the exception's status_code.
        
        Parameters:
            error (APIException): The custom API exception instance providing `to_dict()` and `status_code`.
        
        Returns:
            response (flask.wrappers.Response): A Flask JSON response whose body is `error.to_dict()` and whose status code is `error.status_code`.
        """
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        """
        Return a JSON response for a missing resource with HTTP status 404.
        
        Returns:
            tuple: (Flask response, int) where the response body is JSON with keys
                `error` set to `"NotFound"` and `message` describing that the
                requested resource was not found, and the int is the HTTP status code 404.
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
        Return a JSON response for unhandled internal server errors.
        
        Parameters:
            error (Exception): The exception instance that triggered the handler.
        
        Returns:
            tuple: A pair (response, status_code) where `response` is a JSON payload with keys
            "error" (value "InternalServerError") and "message" (a user-facing message), and
            `status_code` is 500.
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
    Register the application's blueprints and initialize API v1 namespaces.
    
    Registers the health-check blueprint and the API v1 blueprint, and initializes API v1 Swagger namespaces so their routes and documentation are available on the given Flask application.
    
    Parameters:
        app (Flask): The Flask application instance to register blueprints on.
    """

    # Register health check
    from app.api.health import health_bp

    app.register_blueprint(health_bp)

    # Register API v1
    from app.api.v1.swagger import api_v1_blueprint, init_api_namespaces

    init_api_namespaces()
    app.register_blueprint(api_v1_blueprint)