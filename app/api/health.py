"""Health check endpoints"""

from flask import Blueprint, jsonify

from app.core.config import BaseConfig

health_bp = Blueprint("health", __name__)


@health_bp.route("/", methods=["GET"])
def root_health_check():
    """
    Root health check endpoint
    Returns basic service information
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
