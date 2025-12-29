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

    # CORS - Read from environment variables
    cors_origins = settings.CORS_ALLOW_ORIGINS
    cors_credentials = settings.CORS_ALLOW_CREDENTIALS

    # Browser security: Cannot use "*" with credentials=True
    # If credentials is True, must use specific origins
    if cors_credentials and "*" in cors_origins:
        logger.warning("CORS_ALLOW_CREDENTIALS is True but origins includes '*'. Setting credentials to False.")
        cors_credentials = False

    logger.info(f"CORS Configuration: allow_origins={cors_origins}, allow_credentials={cors_credentials}")

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,  # From environment variable
        allow_credentials=cors_credentials,  # From environment variable
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
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

        # Handle OPTIONS preflight explicitly as backup
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")
            # Determine allowed origin based on settings
            if "*" in cors_origins:
                allow_origin = "*"
            elif origin and origin in cors_origins:
                allow_origin = origin
            else:
                allow_origin = cors_origins[0] if cors_origins else "*"

            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": allow_origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Credentials": str(cors_credentials).lower(),
                    "Access-Control-Max-Age": "3600",
                    "X-Request-ID": request_id,
                },
            )

        response = await call_next(request)

        # ALWAYS force CORS headers on every response (override any existing ones)
        # This ensures CORS works even if CORSMiddleware fails or headers are stripped
        origin = request.headers.get("origin")
        # Determine allowed origin based on settings
        if "*" in cors_origins:
            allow_origin = "*"
        elif origin and origin in cors_origins:
            allow_origin = origin
        else:
            allow_origin = cors_origins[0] if cors_origins else "*"

        response.headers["Access-Control-Allow-Origin"] = allow_origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = str(cors_credentials).lower()
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
