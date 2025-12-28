import logging
import uuid
from typing import Callable

from fastapi import FastAPI, Request
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

    logger.info(f"CORS Configuration: allow_origins={settings.CORS_ALLOW_ORIGINS}")
    logger.info(f"CORS Raw String: {settings.CORS_ALLOW_ORIGINS_STR}")
    logger.warning(f"CORS Environment Variable: {os.getenv('CORS_ALLOW_ORIGINS', 'NOT SET - using default *')}")

    # CORS Configuration Fix:
    # If allow_credentials=True, we CANNOT use ["*"] - must specify exact origins
    # If origins is ["*"], we must disable credentials
    cors_origins = settings.CORS_ALLOW_ORIGINS
    cors_credentials = settings.CORS_ALLOW_CREDENTIALS

    if "*" in cors_origins and cors_credentials:
        logger.warning("CORS: allow_credentials=True with origins=['*'] is invalid. Disabling credentials.")
        cors_credentials = False

    # #region agent log
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-config", "hypothesisId": "C", "location": "main.py:create_app", "message": "CORS middleware configuration", "data": {"allow_origins": cors_origins, "allow_credentials": cors_credentials, "allow_methods": settings.CORS_ALLOW_METHODS}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion

    # CORS - Ensure middleware is added before other middleware
    # FastAPI CORSMiddleware must be added first to handle preflight OPTIONS requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentials,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=["*"],  # Explicitly allow all headers for CORS
        expose_headers=["*"],  # Expose all headers
    )

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Callable):  # type: ignore[override]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request_logger = logging.getLogger("request")

        # #region agent log
        import json
        import os
        origin = request.headers.get("origin", "NO_ORIGIN")
        try:
            current_settings = get_settings()
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-request", "hypothesisId": "B", "location": "main.py:add_request_id", "message": "Incoming request", "data": {"method": request.method, "path": str(request.url.path), "origin": origin, "user_agent": request.headers.get("user-agent", "NO_UA")[:50], "allowed_origins": current_settings.CORS_ALLOW_ORIGINS, "origin_in_allowed": origin in current_settings.CORS_ALLOW_ORIGINS or "*" in current_settings.CORS_ALLOW_ORIGINS}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion

        request_logger.info("Incoming request", extra={"request_id": request_id, "path": request.url.path, "method": request.method, "origin": request.headers.get("origin")})
        response = await call_next(request)

        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-response", "hypothesisId": "B", "location": "main.py:add_request_id", "message": "Response headers", "data": {"status_code": response.status_code, "access_control_allow_origin": response.headers.get("access-control-allow-origin", "NOT_SET"), "access_control_allow_methods": response.headers.get("access-control-allow-methods", "NOT_SET"), "access_control_allow_headers": response.headers.get("access-control-allow-headers", "NOT_SET")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
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

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_database()

    return app


app = create_app()
