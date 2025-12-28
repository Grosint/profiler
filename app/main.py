import logging
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_database
from app.core.error_handlers import init_error_handlers
from app.core.logging import setup_logging
from app.api.endpoints import profiler as profiler_router
from app.api.endpoints import health as health_router
from app.api.endpoints import post as post_router


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    logger = logging.getLogger(__name__)

    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
    )

    # CORS - Log configuration for debugging
    # #region agent log
    import json
    import os
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-debug", "hypothesisId": "A", "location": "main.py:create_app", "message": "CORS configuration", "data": {"cors_allow_origins": settings.CORS_ALLOW_ORIGINS, "cors_allow_origins_str": settings.CORS_ALLOW_ORIGINS_STR, "cors_allow_credentials": settings.CORS_ALLOW_CREDENTIALS, "cors_allow_methods": settings.CORS_ALLOW_METHODS, "cors_allow_headers": settings.CORS_ALLOW_HEADERS, "env_cors_origins": os.getenv("CORS_ALLOW_ORIGINS", "NOT_SET")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion

    # CORS - Simple: allow everything with "*"
    logger.info("CORS Configuration: allow_origins=['*'] (allows all origins)")

    # #region agent log
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-config", "hypothesisId": "C", "location": "main.py:create_app", "message": "CORS middleware configuration", "data": {"allow_origins": ["*"], "allow_credentials": False, "allow_methods": ["*"], "allow_headers": ["*"]}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion

    # CORS - Simple: allow everything
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=False,  # Must be False when using "*"
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],  # All common methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["*"],  # Expose all headers
        max_age=3600,
    )

    # #region agent log
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-middleware", "hypothesisId": "D", "location": "main.py:create_app", "message": "CORS middleware added", "data": {"allow_origins": ["*"], "allow_credentials": False, "middleware_added": True}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion

    # Request ID middleware + ALWAYS add CORS headers (runs AFTER CORSMiddleware)
    @app.middleware("http")
    async def add_request_id_and_cors(request: Request, call_next: Callable):  # type: ignore[override]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request_logger = logging.getLogger("request")

        # #region agent log
        import json
        import os
        origin = request.headers.get("origin", "NO_ORIGIN")
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-request", "hypothesisId": "B", "location": "main.py:add_request_id_and_cors", "message": "Incoming request", "data": {"method": request.method, "path": str(request.url.path), "origin": origin, "user_agent": request.headers.get("user-agent", "NO_UA")[:50]}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion

        request_logger.info("Incoming request", extra={"request_id": request_id, "path": request.url.path, "method": request.method, "origin": request.headers.get("origin")})

        # CRITICAL: Do NOT intercept OPTIONS requests here - let CORSMiddleware handle them
        # The CORSMiddleware (added first) will process OPTIONS requests properly
        # If we intercept here, CORSMiddleware never gets to run (middleware runs in reverse order)

        response = await call_next(request)

        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-request", "hypothesisId": "B", "location": "main.py:add_request_id_and_cors", "message": "Response from call_next", "data": {"status_code": response.status_code, "method": request.method, "path": str(request.url.path), "cors_origin_before": response.headers.get("access-control-allow-origin", "NOT_SET"), "all_headers": dict(response.headers)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion

        # Simple: ALWAYS add CORS headers to every response (force them)
        # This ensures CORS works even if CORSMiddleware fails for some reason
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "false"
        if request.method == "OPTIONS":
            response.headers["Access-Control-Max-Age"] = "3600"

        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-request", "hypothesisId": "B", "location": "main.py:add_request_id_and_cors", "message": "CORS headers after forcing", "data": {"cors_origin_after": response.headers.get("access-control-allow-origin", "NOT_SET"), "cors_methods": response.headers.get("access-control-allow-methods", "NOT_SET")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion

        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-response", "hypothesisId": "B", "location": "main.py:add_request_id_and_cors", "message": "Response headers", "data": {"status_code": response.status_code, "method": request.method, "path": str(request.url.path), "access_control_allow_origin": response.headers.get("access-control-allow-origin", "NOT_SET"), "access_control_allow_methods": response.headers.get("access-control-allow-methods", "NOT_SET"), "access_control_allow_headers": response.headers.get("access-control-allow-headers", "NOT_SET")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion

        response.headers["X-Request-ID"] = request_id
        return response

    # Routers
    app.include_router(
        profiler_router.router,
        prefix=settings.API_V1_PREFIX,
        tags=["profiles"],
    )
    app.include_router(
        post_router.router,
        prefix=settings.API_V1_PREFIX,
        tags=["posts"],
    )
    app.include_router(
        health_router.router,
        prefix=settings.API_V1_PREFIX,
        tags=["health"],
    )

    # Error handlers
    init_error_handlers(app)

    # NOTE: Removed explicit OPTIONS handler - CORSMiddleware handles OPTIONS requests properly
    # Having both causes conflicts and prevents CORSMiddleware from working correctly

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_database()

    return app


app = create_app()
