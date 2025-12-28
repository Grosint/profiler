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

    # CORS - Simple: allow everything with "*"
    logger.info("CORS Configuration: allow_origins=['*'] (allows all origins)")

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

    # Request ID middleware + ALWAYS add CORS headers (runs AFTER CORSMiddleware)
    @app.middleware("http")
    async def add_request_id_and_cors(request: Request, call_next: Callable):  # type: ignore[override]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request_logger = logging.getLogger("request")
        request_logger.info("Incoming request", extra={"request_id": request_id, "path": request.url.path, "method": request.method, "origin": request.headers.get("origin")})

        # CRITICAL: Do NOT intercept OPTIONS requests here - let CORSMiddleware handle them
        # The CORSMiddleware (added first) will process OPTIONS requests properly
        # If we intercept here, CORSMiddleware never gets to run (middleware runs in reverse order)

        response = await call_next(request)

        # Simple: ALWAYS add CORS headers to every response (force them)
        # This ensures CORS works even if CORSMiddleware fails for some reason
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "false"
        if request.method == "OPTIONS":
            response.headers["Access-Control-Max-Age"] = "3600"

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
