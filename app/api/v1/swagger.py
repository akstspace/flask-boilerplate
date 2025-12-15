"""Swagger/OpenAPI documentation configuration"""

from flask import Blueprint
from flask_restx import Api

# Create API blueprint
api_v1_blueprint = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Configure Swagger API
api = Api(
    api_v1_blueprint,
    version="1.0.0",
    title="Flask Application API",
    description="A Flask API with PostgreSQL, Celery, Redis, and Keycloak authentication",
    doc="/docs",
    authorizations={
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": 'JWT Authorization header using the Bearer scheme. Example: "Bearer {token}"',
        }
    },
    security="Bearer",
)


def init_api_namespaces():
    """
    Register and attach v1 API namespaces to the module's Api instance.
    
    Specifically makes the authentication namespace available at the '/auth' path (exposed under the blueprint prefix as '/api/v1/auth').
    """
    from app.api.v1.auth import auth_ns

    api.add_namespace(auth_ns, path="/auth")