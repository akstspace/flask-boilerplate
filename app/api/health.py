"""Health check endpoints"""

from flask import Blueprint, jsonify

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
                "service": "Flask Application API",
                "version": "1.0.0",
            }
        ),
        200,
    )
