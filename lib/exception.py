from fastapi import HTTPException

HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_REQUEST_TIMEOUT = 408
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_GATEWAY_TIMEOUT = 504


class ProxyException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(
            status_code=status_code,
            detail=detail,
        )


class UserFaceException(ProxyException):
    pass


class DependencyException(ProxyException):
    pass


class UserAuthorizationException(UserFaceException):
    def __init__(self):
        super().__init__(
            status_code=HTTP_UNAUTHORIZED,
            detail="Authorization denied. Please log-out and try to log-ing again.",
        )


class UserAuthorizationExpiredException(UserFaceException):
    def __init__(self):
        super().__init__(
            status_code=HTTP_UNAUTHORIZED,
            detail="Authorization expired. Reset cookie expected.",
        )


# Database
class UserNotFoundException(UserFaceException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=HTTP_NOT_FOUND,
            detail=detail,
        )


class ResourceNotFoundException(UserFaceException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=HTTP_NOT_FOUND,
            detail=detail,
        )


class UserUpdateException(UserFaceException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=HTTP_BAD_REQUEST,
            detail=detail,
        )


class PaymentException(UserFaceException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=HTTP_BAD_REQUEST,
            detail=detail,
        )


# OAuth2.0
class UserProfileNotFound(UserFaceException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=HTTP_NOT_FOUND,
            detail=detail,
        )


class CanNotFoundEndPoint(DependencyException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=HTTP_SERVICE_UNAVAILABLE,
            detail=detail,
        )
