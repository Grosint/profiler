import logging
from typing import Annotated, Optional

from fastapi import Depends, Header

from .config import get_settings
from .exceptions import UnauthorizedException

logger = logging.getLogger(__name__)


async def api_key_auth(x_api_key: Annotated[Optional[str], Header(alias="x-api-key")] = None) -> str:
    """
    Simple API key auth dependency for external callers.
    """
    settings = get_settings()

    # #region agent log
    import json
    import os
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "api-key-auth", "hypothesisId": "C", "location": "security.py:api_key_auth", "message": "API key authentication check", "data": {"received_key": x_api_key[:8] + "..." if x_api_key else "NOT_PROVIDED", "received_key_length": len(x_api_key) if x_api_key else 0, "expected_key_length": len(settings.API_KEY) if settings.API_KEY else 0, "keys_match": x_api_key == settings.API_KEY if x_api_key else False, "env_api_key": os.getenv("API_KEY", "NOT_SET")[:8] + "..." if os.getenv("API_KEY") else "NOT_SET"}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion

    if not x_api_key:
        logger.warning("API key not provided in request")
        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "api-key-auth", "hypothesisId": "C", "location": "security.py:api_key_auth", "message": "API key missing", "data": {"error": "x-api-key header not provided"}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        raise UnauthorizedException()

    if x_api_key != settings.API_KEY:
        logger.warning(f"Invalid API key access attempt - received: {x_api_key[:8]}..., expected: {settings.API_KEY[:8]}...")
        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "api-key-auth", "hypothesisId": "C", "location": "security.py:api_key_auth", "message": "API key mismatch", "data": {"received_first_8": x_api_key[:8], "expected_first_8": settings.API_KEY[:8]}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        raise UnauthorizedException()

    # #region agent log
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "api-key-auth", "hypothesisId": "C", "location": "security.py:api_key_auth", "message": "API key authentication successful", "data": {}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion

    return x_api_key


async def internal_service_auth(
    x_internal_token: Annotated[Optional[str], Header(alias="x-internal-token")] = None,
) -> str:
    """
    Simple internal service-to-service auth dependency.
    """
    settings = get_settings()
    if not settings.INTERNAL_SERVICE_TOKEN:
        # If not configured, treat as disabled / allow-by-default for local dev.
        return ""
    if not x_internal_token or x_internal_token != settings.INTERNAL_SERVICE_TOKEN:
        logger.warning("Invalid internal service token access attempt")
        raise UnauthorizedException()
    return x_internal_token
