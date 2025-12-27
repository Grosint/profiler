import asyncio
import logging
import time
from typing import Any, Dict, Optional

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)


class CircuitBreakerState:
    def __init__(self) -> None:
        self.failures: int = 0
        self.open_until: float = 0.0


class ResilientHTTPClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._timeout = settings.HTTP_CLIENT_TIMEOUT_SECONDS
        self._max_retries = settings.HTTP_CLIENT_MAX_RETRIES
        self._threshold = settings.HTTP_CLIENT_CIRCUIT_BREAKER_THRESHOLD
        self._reset_seconds = settings.HTTP_CLIENT_CIRCUIT_BREAKER_RESET_SECONDS
        self._client = httpx.AsyncClient(timeout=self._timeout)
        self._state = CircuitBreakerState()

    async def _request(
        self, method: str, url: str, *, headers: Optional[Dict[str, str]] = None, **kwargs: Any
    ) -> httpx.Response:
        now = time.time()
        if self._state.open_until > now:
            raise httpx.HTTPError("Circuit breaker is open")

        attempt = 0
        last_exc: Optional[Exception] = None

        while attempt < self._max_retries:
            try:
                response = await self._client.request(method, url, headers=headers, **kwargs)
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error: {response.status_code}", request=response.request, response=response
                    )
                self._state.failures = 0
                return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                attempt += 1
                self._state.failures += 1
                logger.warning(
                    "HTTP request failed",
                    extra={
                        "url": url,
                        "method": method,
                        "attempt": attempt,
                        "max_retries": self._max_retries,
                        "error": str(exc),
                    },
                )
                if self._state.failures >= self._threshold:
                    self._state.open_until = time.time() + self._reset_seconds
                    logger.error(
                        "Circuit breaker opened",
                        extra={"url": url, "threshold": self._threshold, "reset_in": self._reset_seconds},
                    )
                    break
                await asyncio.sleep(min(2**attempt, 10))

        if last_exc:
            raise last_exc
        raise httpx.HTTPError("HTTP request failed with unknown error")

    async def get(self, url: str, *, headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> httpx.Response:
        return await self._request("GET", url, headers=headers, **kwargs)

    async def post(
        self, url: str, *, headers: Optional[Dict[str, str]] = None, json: Any | None = None, **kwargs: Any
    ) -> httpx.Response:
        return await self._request("POST", url, headers=headers, json=json, **kwargs)

    async def close(self) -> None:
        await self._client.aclose()


http_client = ResilientHTTPClient()
