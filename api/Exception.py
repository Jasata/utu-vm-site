###############################################################################
#
#
# API Exception classes
#
#
#   These JSON API exceptions allow DataObjects to reply with specification
#   defined responses for various exceptional conditions, simply by raising
#   the appropriate exception. Route handlers (in 'route.py') catch these
#   exceptions and route them into api.exception_response() function (found
#   in this file). Exceptions are then converted into HTTP responses.
#

class ApiException(Exception):

    # Used to identify objects based on ApiException and its subclasses.
    # Because, ...I don't know how a better way to do this.
    ApiException = True

    def __init__(
        self,
        message = "Unspecified API Error",
        details = None
    ):
        """Initialize API Exception instance"""
        super().__init__(message)
        self.details = details


    def to_dict(self):
        """Return values of each fields of an jsonapi error"""
        error_dict = {'message' : str(self)}
        # Do not include 'code', because that is used as the response code
        if getattr(self, 'details', None):
            error_dict.update({'details' : getattr(self, 'details')})
        return error_dict



#
# Client side errors (4xx)
#

# 400 Bad Request
# Endpoint / resource does not exist
# (use 405 for existing resource and unsupported method)
class BadRequest(ApiException):
    """Resource does not exist."""
    def __init__(
        self,
        message = "Resource does not exist",
        details = None
    ):
        super().__init__(message, details)
        self.code = 400


# 401 Unauthorized
#
class Unauthorized(ApiException):
    """Insufficient privileges to access requested resource."""
    def __init__(
        self,
        message = "Insufficient privileges to access requested resource!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 401


# 404 Not Found
class NotFound(ApiException):
    """Identified item was not found in the database."""
    def __init__(
        self,
        message = "Entity not found!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 404


# 405 Method Not Allowed
# Combination of URI and method is not supported
class MethodNotAllowed(ApiException):
    """Request method is not supported."""
    def __init__(
        self,
        message = "Requested method is not supported!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 405


# 406 Not Acceptable
class InvalidArgument(ApiException):
    """Provided argument(s) are invalid!"""
    def __init__(
        self,
        message = "Provided argument(s) are invalid!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 406


# 409 Conflict
class Conflict(ApiException):
    """Unique/PK,FK or other constraint violation."""
    def __init__(
        self,
        message = "Unique, primary key, foreign key or other constraint violation!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 409


#
# Server side errors (5xx)
#

# 500 Internal Server Error
class Timeout(ApiException):
    """Processing/polling exceeded allowed timeout."""
    def __init__(
        self,
        message = "Processing/polling exceeded allowed timeout!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 500


# 500 Internal Server Error
class InternalError(ApiException):
    """All other internal processing erros, except timeouts."""
    def __init__(
        self,
        message = "Unspecified internal processing error!",
        details = None
    ):
        super().__init__(message, details)
        self.code = 500


# 501 Not Implemented
# Route exists, implementation does not
# For request to something that is not planned, return 405
class NotImplemented(ApiException):
    """Requested functionality is not yet implemented."""
    def __init__(
        self,
        message = "Requested functionality is not yet implemented.",
        details = None
    ):
        super().__init__(message, details)
        self.code = 501

# 502 Bad Gateway
# Nginx will hand out this response when Flask fails to deliver.

# EOF