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

    if not x_api_key:
        logger.warning("API key not provided in request")
        raise UnauthorizedException()

    if x_api_key != settings.API_KEY:
        logger.warning(f"Invalid API key access attempt - received: {x_api_key[:8]}..., expected: {settings.API_KEY[:8]}...")
        raise UnauthorizedException()

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
