"""Authentication and authorization middleware"""

from functools import wraps

from flask import g, request

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.services.auth_service import auth_service


def extract_token_from_header():
    """
    Extract the Bearer JWT token from the current request's Authorization header.
    
    Returns:
        The token string if the Authorization header contains a well-formed Bearer token, `None` otherwise.
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
    Require a valid JWT for the wrapped Flask route.
    
    If a valid token is provided and verified, sets `g.user` to the extracted user information and `g.token` to the decoded token, then calls the wrapped function. If no token is provided or verification fails, raises AuthenticationError.
    
    Returns:
        function: A decorated route function that enforces JWT authentication.
    
    Raises:
        AuthenticationError: If no token is provided or token verification fails.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Ensure the request includes a valid Bearer JWT, populate flask.g with user and token, and then call the wrapped function.
        
        On success, sets g.user to the extracted user information and g.token to the decoded token before invoking the wrapped function.
        
        Raises:
            AuthenticationError: If no token is provided, if token verification fails, or if another error occurs during authentication. The function propagates AuthenticationError from the verification step and raises `AuthenticationError("No token provided")` when the Authorization header is missing.
        
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
    Create a decorator that enforces the current request's user has at least one of the specified roles.
    
    Parameters:
        required_roles (str): One or more role names that are acceptable for access.
    
    Returns:
        function: A decorator that, when applied to a view, checks the authenticated user's roles and allows execution only if at least one required role is present.
    
    Raises:
        AuthorizationError: If there is no authenticated user on the request or the user lacks all of the specified roles.
    """

    def decorator(f):
        """
        Enforces that the authenticated user has at least one of the roles specified when the decorator was created.
        
        Wraps a view/function to verify that Flask's `g.user` exists and that the user's combined `roles` and `client_roles` include at least one of the required roles. If validation passes, the original function is called with its arguments; otherwise an AuthorizationError is raised.
        
        Parameters:
            f (callable): The function to wrap.
        
        Returns:
            callable: A wrapper that performs the authentication and role check before invoking `f`.
        
        Raises:
            AuthorizationError: If no authenticated user is present or if the user lacks any of the required roles.
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
    Allow routes to accept an optional JWT and populate Flask's request context when present.
    
    If a valid Bearer token is provided in the Authorization header, verifies the token and sets g.user to the extracted user information and g.token to the decoded token. If no token is present or token verification fails, authentication errors are ignored and the wrapped function is called without setting g.user.
    
    Returns:
        function: A decorator that wraps a view function and applies optional authentication.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Attempt optional JWT authentication; if successful, populate Flask's `g` with user and token, then invoke the wrapped function.
        
        If a well-formed Bearer token is present and verification succeeds, sets `g.user` to extracted user information and `g.token` to the decoded token. Authentication errors are suppressed and do not prevent the wrapped function from being called.
        
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