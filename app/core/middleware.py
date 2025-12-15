"""Authentication and authorization middleware"""

from functools import wraps

from flask import g, request

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.services.auth_service import auth_service


def extract_token_from_header():
    """
    Extract JWT token from Authorization header

    Returns:
        str: Token string or None
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header:
        return None

    # Expected format: "Bearer <token>"
    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def require_auth(f):
    """
    Decorator to require valid JWT authentication

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user = g.user
            return {'message': f'Hello {user["username"]}'}
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token_from_header()

        if not token:
            msg = "No token provided"
            raise AuthenticationError(msg)

        try:
            decoded_token = auth_service.verify_token(token)
            g.user = auth_service.extract_user_info(decoded_token)
            g.token = decoded_token
        except AuthenticationError:
            raise
        except Exception:
            msg = "Authentication failed"
            raise AuthenticationError(msg)

        return f(*args, **kwargs)

    return decorated_function


def require_role(*required_roles):
    """
    Decorator to require specific roles

    Usage:
        @app.route('/admin')
        @require_auth
        @require_role('admin', 'superuser')
        def admin_route():
            return {'message': 'Admin access'}
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, "user", None)

            if not user:
                msg = "Authentication required before role check"
                raise AuthorizationError(msg)

            user_roles = user.get("roles", []) + user.get("client_roles", [])

            # Check if user has any of the required roles
            has_role = any(role in user_roles for role in required_roles)

            if not has_role:
                msg = f'Requires one of: {", ".join(required_roles)}'
                raise AuthorizationError(
                    msg
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def optional_auth(f):
    """
    Decorator for optional authentication
    Sets g.user if token is valid, otherwise continues without authentication

    Usage:
        @app.route('/public')
        @optional_auth
        def public_route():
            if hasattr(g, 'user'):
                return {'message': f'Hello {g.user["username"]}'}
            return {'message': 'Hello anonymous'}
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = extract_token_from_header()

            if token:
                decoded_token = auth_service.verify_token(token)
                g.user = auth_service.extract_user_info(decoded_token)
                g.token = decoded_token
        except AuthenticationError:
            # Ignore authentication errors for optional auth
            pass

        return f(*args, **kwargs)

    return decorated_function
