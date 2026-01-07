"""
Request Correlation Middleware

Adds correlation IDs to all requests for distributed tracing and debugging.
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

logger = logging.getLogger(__name__)


def get_correlation_id() -> Optional[str]:
    """Get the current request's correlation ID."""
    return correlation_id_var.get()


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds correlation IDs to requests.

    Features:
    - Generates unique correlation ID for each request
    - Accepts X-Correlation-ID or X-Request-ID header from upstream
    - Adds correlation ID to response headers
    - Makes correlation ID available via context variable
    """

    HEADER_NAMES = ["X-Correlation-ID", "X-Request-ID", "X-Trace-ID"]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Try to get correlation ID from incoming headers
        correlation_id = None
        for header in self.HEADER_NAMES:
            correlation_id = request.headers.get(header)
            if correlation_id:
                break

        # Generate new correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Set context variable for use in logging
        token = correlation_id_var.set(correlation_id)

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response
        finally:
            # Reset context variable
            correlation_id_var.reset(token)


class CorrelationLogFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.

    Usage:
        handler = logging.StreamHandler()
        handler.addFilter(CorrelationLogFilter())
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(correlation_id)s] %(levelname)s %(message)s'
        ))
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "no-request"
        return True
