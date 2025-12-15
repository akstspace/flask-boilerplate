"""Custom exceptions"""


class APIException(Exception):
    """Base API exception"""

    status_code = 500
    message = "An error occurred"

    def __init__(self, message: str | None = None, status_code: int | None = None):
        """
        Initialize the APIException, optionally overriding its default message and HTTP status code.
        
        Parameters:
            message (str | None): If provided, sets the exception's message instead of the class default.
            status_code (int | None): If provided, sets the exception's HTTP status code instead of the class default.
        """
        super().__init__()
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code

    def to_dict(self):
        """
        Serialize the exception into a dictionary suitable for API responses.
        
        The returned dictionary contains two keys: "error" (the exception class name) and "message" (the instance's message).
        
        Returns:
            dict: A mapping with "error" set to the exception class name and "message" set to the exception's message.
        """
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