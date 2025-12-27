from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    def __init__(
        self,
        message: str,
        *,
        error_code: str = "internal_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class UnauthorizedException(BaseAPIException):
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="unauthorized", status_code=401, details=details)


class NotFoundException(BaseAPIException):
    def __init__(self, message: str = "Not Found", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="not_found", status_code=404, details=details)


class BadRequestException(BaseAPIException):
    def __init__(self, message: str = "Bad Request", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="bad_request", status_code=400, details=details)
