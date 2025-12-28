import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import BaseAPIException

logger = logging.getLogger(__name__)


def _error_response(
    message: str, error_code: str, status_code: int, details: Dict[str, Any] | None = None
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "message": message,
                "code": error_code,
                "details": details or {},
            },
        },
    )
    # Add CORS headers to error responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    return response


def init_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseAPIException)
    async def handle_base_api_exception(request: Request, exc: BaseAPIException) -> JSONResponse:  # type: ignore[override]
        logger.warning(
            "Handled BaseAPIException",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
            },
        )
        return _error_response(exc.message, exc.error_code, exc.status_code, exc.details)

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[override]
        logger.exception("Unhandled exception", extra={"path": request.url.path})
        return _error_response("Internal Server Error", "internal_error", 500)
