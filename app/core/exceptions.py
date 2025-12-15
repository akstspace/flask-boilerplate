"""Custom exceptions"""


class APIException(Exception):
    """Base API exception"""

    status_code = 500
    message = "An error occurred"

    def __init__(self, message: str | None = None, status_code: int | None = None):
        super().__init__()
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code

    def to_dict(self):
        return {"error": self.__class__.__name__, "message": self.message}


class AuthenticationError(APIException):
    """Authentication failed"""

    status_code = 401
    message = "Authentication required"


class AuthorizationError(APIException):
    """Authorization failed"""

    status_code = 403
    message = "Insufficient permissions"


class ValidationError(APIException):
    """Validation error"""

    status_code = 400
    message = "Validation failed"


class NotFoundError(APIException):
    """Resource not found"""

    status_code = 404
    message = "Resource not found"
