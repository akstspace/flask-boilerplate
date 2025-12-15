"""Authentication and authorization middleware"""

from functools import wraps

from flask import g, request

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.services.auth_service import auth_service


def extract_token_from_header():
    """
    Retrieve the Bearer JWT token from the Authorization header.
    
    Returns:
        The token string if the Authorization header is present and formatted as 'Bearer <token>', `None` otherwise.
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
    Require that the request contains a valid Bearer JWT and populate Flask `g` with user and token for the wrapped view.
    
    If a valid Bearer token is present in the Authorization header, verifies the token and sets `g.user` to the extracted user information and `g.token` to the decoded token before invoking the wrapped function.
    
    Returns:
        function: The wrapped view function that enforces authentication and sets request context.
    
    Raises:
        AuthenticationError: If no token is provided or token verification fails.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Enforces presence of a valid Bearer JWT, populates Flask `g.user` and `g.token`, then invokes the wrapped function.
        
        Raises:
        	AuthenticationError: If no token is provided or token verification fails.
        
        Returns:
        	The return value of the wrapped function.
        """
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
    Enforces that the authenticated user has at least one of the specified roles.
    
    Parameters:
        *required_roles (str): One or more role names; the user must have at least one to proceed.
    
    Returns:
        function: A decorator that wraps a view and performs the role check.
    
    Raises:
        AuthorizationError: If there is no authenticated user or the user lacks any of the required roles.
    """

    def decorator(f):
        """
        Enforces that the current request's authenticated user has at least one of the required roles.
        
        The decorated function checks Flask's `g.user` for roles (including `client_roles`) and raises AuthorizationError if no user is authenticated or if none of the required roles are present. If the check passes, the original function is invoked.
        
        Returns:
            function: A wrapper that performs the role check before calling the original function.
        
        Raises:
            AuthorizationError: If authentication is missing or the user lacks all required roles.
        """
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
    Allow a route to accept requests with or without valid authentication and populate g.user when a valid token is provided.
    
    If an Authorization Bearer token is present and valid, verifies the token and sets g.user and g.token for the request. Authentication errors are ignored so the route proceeds unauthenticated when no token or an invalid token is provided.
    
    Returns:
        The wrapped function that applies optional authentication to the original route.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Attempt optional authentication by extracting and verifying a Bearer token from the Authorization header; if verification succeeds, populate `g.user` and `g.token` before invoking the wrapped function.
        
        If no token is present or token verification fails with an AuthenticationError, the request proceeds without authentication context.
        
        Returns:
            The return value of the wrapped function.
        """
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