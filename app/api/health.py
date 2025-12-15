"""Health check endpoints"""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/", methods=["GET"])
def root_health_check():
    """
    Return basic service health information.
    
    Returns:
        tuple: A pair (response, status_code) where `response` is a Flask JSON response with keys `"status"` (`"healthy"`), `"service"` (`"Flask Application API"`), and `"version"` (`"1.0.0"`), and `status_code` is the integer HTTP status code `200`.
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