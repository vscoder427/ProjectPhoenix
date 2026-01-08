"""
Deprecation Middleware Template

Adds RFC 8594 deprecation headers to API responses for deprecated versions.

USAGE:
1. Copy this file to: services/{service-name}/api/app/middleware/deprecation.py
2. No changes needed - works as-is
3. Register in main.py: app.add_middleware(DeprecationMiddleware)
"""
import logging
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.routes.versions import get_deprecation_status, is_sunset

logger = logging.getLogger(__name__)


class DeprecationMiddleware(BaseHTTPMiddleware):
    """Add deprecation warnings to API responses."""

    async def dispatch(self, request: Request, call_next):
        # Extract API version from path
        path_parts = request.url.path.strip("/").split("/")

        api_version = None
        if len(path_parts) >= 2 and path_parts[0] == "api":
            api_version = path_parts[1]  # e.g., "v1"

        # Check if version is sunset (should be blocked)
        if api_version and is_sunset(api_version):
            logger.warning(
                f"Request to sunset API version: {api_version}",
                extra={"path": request.url.path, "client": request.client.host}
            )
            return Response(
                content=f'{{"error": "API version {api_version} has been sunset"}}',
                status_code=410,  # Gone
                media_type="application/json",
            )

        # Process request
        response = await call_next(request)

        # Add deprecation headers if needed
        if api_version:
            dep_status = get_deprecation_status(api_version)
            if dep_status and dep_status.deprecated:
                # RFC 8594 Deprecation header
                response.headers["Deprecation"] = "true"

                if dep_status.sunset_date:
                    # RFC 8594 Sunset header (HTTP date format)
                    sunset_str = dep_status.sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
                    response.headers["Sunset"] = sunset_str

                if dep_status.migration_guide:
                    response.headers["Link"] = f'<{dep_status.migration_guide}>; rel="deprecation"'

                # Custom header for days remaining
                if dep_status.days_until_sunset:
                    response.headers["X-API-Deprecation-Days-Remaining"] = str(
                        dep_status.days_until_sunset
                    )

                # Log deprecated usage
                logger.warning(
                    f"Deprecated API usage: {api_version}",
                    extra={
                        "path": request.url.path,
                        "sunset_date": dep_status.sunset_date,
                        "client": request.client.host,
                    }
                )

        return response
