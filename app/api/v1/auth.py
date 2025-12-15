"""Authentication endpoints"""

from flask import g
from flask_restx import Namespace, Resource, fields

from app.core.middleware import require_auth

auth_ns = Namespace("auth", description="Authentication operations")

user_model = auth_ns.model(
    "User",
    {
        "user_id": fields.String(description="User ID"),
        "username": fields.String(description="Username"),
        "email": fields.String(description="Email address"),
        "email_verified": fields.Boolean(description="Email verification status"),
        "name": fields.String(description="Full name"),
        "given_name": fields.String(description="First name"),
        "family_name": fields.String(description="Last name"),
        "roles": fields.List(fields.String, description="Realm roles"),
        "client_roles": fields.List(fields.String, description="Client roles"),
    },
)

user_response = auth_ns.model(
    "UserResponse",
    {
        "user": fields.Nested(user_model),
        "status": fields.String(description="Response status"),
    },
)

error_response = auth_ns.model(
    "ErrorResponse",
    {
        "error": fields.String(description="Error type"),
        "message": fields.String(description="Error message"),
    },
)


@auth_ns.route("/me")
class CurrentUser(Resource):
    @auth_ns.doc("get_current_user", security="Bearer")
    @auth_ns.response(200, "Success", user_response)
    @auth_ns.response(401, "Unauthorized", error_response)
    @require_auth
    def get(self):
        """
        Return information about the currently authenticated user.
        
        Returns:
            tuple: A pair of (response_body, status_code) where `response_body` is a dict containing `user` set to the authenticated user object and `status` set to "success", and `status_code` is 200.
        """
        return {"user": g.user, "status": "success"}, 200
