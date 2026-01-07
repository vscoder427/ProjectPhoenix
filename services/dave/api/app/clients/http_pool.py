"""
HTTP Client Pool

Provides a shared httpx AsyncClient with connection pooling for efficient
external HTTP requests. Reusing connections significantly reduces latency
and resource usage.
"""

import logging
import threading
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Thread-safe singleton for the HTTP client
_http_client: Optional[httpx.AsyncClient] = None
_http_lock = threading.Lock()


def get_http_client() -> httpx.AsyncClient:
    """
    Get the shared HTTP client with connection pooling.

    The client is configured with:
    - Connection pooling (max 100 connections, 20 per host)
    - Reasonable timeouts
    - HTTP/2 support
    - Automatic retries disabled (handled at application level)

    Returns:
        Shared httpx.AsyncClient instance
    """
    global _http_client

    if _http_client is not None:
        return _http_client

    with _http_lock:
        # Double-check after acquiring lock
        if _http_client is None:
            _http_client = httpx.AsyncClient(
                # Connection pool limits
                limits=httpx.Limits(
                    max_connections=100,      # Total connections
                    max_keepalive_connections=20,  # Keep-alive connections
                    keepalive_expiry=30.0,    # Keep-alive timeout in seconds
                ),
                # Timeouts
                timeout=httpx.Timeout(
                    connect=5.0,    # Connection timeout
                    read=30.0,      # Read timeout
                    write=10.0,     # Write timeout
                    pool=10.0,      # Pool wait timeout
                ),
                # Enable HTTP/2
                http2=True,
                # Follow redirects
                follow_redirects=True,
                # User agent
                headers={
                    "User-Agent": "Dave-Service/1.0 (Employa Career Assistant)"
                },
            )
            logger.info("HTTP client pool initialized")

        return _http_client


async def close_http_client():
    """
    Close the shared HTTP client.

    Call this during application shutdown to properly close connections.
    """
    global _http_client

    with _http_lock:
        if _http_client is not None:
            await _http_client.aclose()
            _http_client = None
            logger.info("HTTP client pool closed")


async def fetch_url(
    url: str,
    timeout: Optional[float] = None,
    headers: Optional[dict] = None,
) -> httpx.Response:
    """
    Convenience function to fetch a URL using the pooled client.

    Args:
        url: URL to fetch
        timeout: Optional custom timeout (uses client default if not specified)
        headers: Optional additional headers

    Returns:
        httpx.Response object

    Raises:
        httpx.HTTPError: On network or HTTP errors
    """
    client = get_http_client()

    request_kwargs = {"url": url}
    if timeout:
        request_kwargs["timeout"] = timeout
    if headers:
        request_kwargs["headers"] = headers

    return await client.get(**request_kwargs)
