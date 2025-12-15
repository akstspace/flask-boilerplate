"""Health check endpoints"""

from flask import Blueprint, jsonify

from app.core.config import BaseConfig

health_bp = Blueprint("health", __name__)


@health_bp.route("/", methods=["GET"])
def root_health_check():
    """
    Provide a JSON health check containing the service status, service name, and version.
    
    Returns:
        tuple: A tuple (response, status_code) where `response` is a JSON object with keys
        `status` (string), `service` (string from BaseConfig.APP_NAME), and `version`
        (string from BaseConfig.APP_VERSION), and `status_code` is the HTTP status code 200.
    """
    return (
        jsonify(
            {
                "status": "healthy",
                "service": BaseConfig.APP_NAME,
                "version": BaseConfig.APP_VERSION,
            }
        ),
        200,
    )