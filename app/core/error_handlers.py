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
    # #region agent log
    import json
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "error-response", "hypothesisId": "E", "location": "error_handlers.py:_error_response", "message": "Error response created", "data": {"status_code": status_code, "error_code": error_code, "has_cors_headers": "Access-Control-Allow-Origin" in response.headers, "cors_origin": response.headers.get("Access-Control-Allow-Origin", "NOT_SET")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion
    # Add CORS headers to error responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    # #region agent log
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "error-response", "hypothesisId": "E", "location": "error_handlers.py:_error_response", "message": "CORS headers added to error response", "data": {"cors_origin": response.headers.get("Access-Control-Allow-Origin", "NOT_SET")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion
    return response


def init_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseAPIException)
    async def handle_base_api_exception(request: Request, exc: BaseAPIException) -> JSONResponse:  # type: ignore[override]
        # #region agent log
        import json
        origin = request.headers.get("origin", "NO_ORIGIN")
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "error-handler", "hypothesisId": "E", "location": "error_handlers.py:handle_base_api_exception", "message": "BaseAPIException caught", "data": {"error_code": exc.error_code, "status_code": exc.status_code, "path": request.url.path, "origin": origin, "method": request.method}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        logger.warning(
            "Handled BaseAPIException",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
            },
        )
        response = _error_response(exc.message, exc.error_code, exc.status_code, exc.details)
        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "error-handler", "hypothesisId": "E", "location": "error_handlers.py:handle_base_api_exception", "message": "Error response returned", "data": {"status_code": response.status_code, "cors_origin": response.headers.get("Access-Control-Allow-Origin", "NOT_SET")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        return response

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[override]
        # #region agent log
        import json
        origin = request.headers.get("origin", "NO_ORIGIN")
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "error-handler", "hypothesisId": "E", "location": "error_handlers.py:handle_generic_exception", "message": "Generic exception caught", "data": {"exception_type": type(exc).__name__, "path": request.url.path, "origin": origin, "method": request.method}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        logger.exception("Unhandled exception", extra={"path": request.url.path})
        response = _error_response("Internal Server Error", "internal_error", 500)
        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "error-handler", "hypothesisId": "E", "location": "error_handlers.py:handle_generic_exception", "message": "Generic error response returned", "data": {"status_code": response.status_code, "cors_origin": response.headers.get("Access-Control-Allow-Origin", "NOT_SET")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        return response
