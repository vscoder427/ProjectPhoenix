"""
Authentication Middleware

API key-based authentication for Dave Service.
Supports multiple authentication methods:
- X-API-Key header (for n8n and service-to-service)
- Bearer token (for admin access)
"""

import logging
import secrets
from typing import Optional

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from employa_auth.jwt_validator import get_user_id_from_token

logger = logging.getLogger(__name__)

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class AuthContext:
    """Authentication context with user info."""

    def __init__(
        self,
        api_key: str | None = None,
        is_admin: bool = False,
        user_id: str | None = None,
        user_type: str = "anonymous",
        tier: str = "free",
    ):
        self.api_key = api_key
        self.is_admin = is_admin
        self.user_id = user_id
        self.user_type = user_type  # job_seeker, employer, treatment_center
        self.tier = tier  # free, basic, premium, admin


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> AuthContext:
    """
    Verify API key from X-API-Key header.

    Returns AuthContext with authentication details.
    Raises HTTPException if invalid.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Include X-API-Key header.",
        )

    # Check against configured API keys using constant-time comparison
    # to prevent timing attacks
    if settings.dave_api_key and secrets.compare_digest(api_key, settings.dave_api_key):
        return AuthContext(
            api_key=api_key,
            is_admin=False,
            tier="basic",
        )

    if settings.admin_api_key and secrets.compare_digest(api_key, settings.admin_api_key):
        return AuthContext(
            api_key=api_key,
            is_admin=True,
            tier="admin",
        )

    # TODO: Validate against database-stored API keys
    # This would allow per-user API keys with different tiers

    raise HTTPException(
        status_code=401,
        detail="Invalid API key.",
    )


async def verify_admin_key(
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> AuthContext:
    """
    Verify admin-level access.

    Accepts either:
    - X-API-Key header with admin key
    - Bearer token with admin key

    Raises HTTPException if not admin.
    """
    # Try API key first
    key = api_key
    if not key and bearer:
        key = bearer.credentials

    if not key:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required.",
        )

    # Verify admin key using constant-time comparison
    if settings.admin_api_key and secrets.compare_digest(key, settings.admin_api_key):
        return AuthContext(
            api_key=key,
            is_admin=True,
            tier="admin",
        )

    raise HTTPException(
        status_code=403,
        detail="Admin access required.",
    )


async def optional_auth(
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> AuthContext:
    """
    Optional authentication - returns anonymous context if no key provided.

    SECURITY: If an API key IS provided but is invalid, we reject the request
    with 401 rather than silently treating it as anonymous. This prevents
    attackers from using invalid keys to bypass authentication.

    Useful for endpoints that work differently for authenticated vs anonymous users.
    """
    if api_key:
        # Key was provided - it MUST be valid, otherwise reject
        # (Don't silently degrade to anonymous, that's a security bypass)
        return await verify_api_key(api_key)

    if bearer:
        # Bearer token provided - must be valid JWT
        user_id = get_user_id_from_token(f"Bearer {bearer.credentials}")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token.")
        return AuthContext(
            api_key=None,
            is_admin=False,
            user_id=user_id,
            user_type="authenticated",
            tier="free",
        )

    # No credentials provided = anonymous access (if endpoint allows it)
    return AuthContext(
        api_key=None,
        is_admin=False,
        user_type="anonymous",
        tier="free",
    )


async def verify_user_or_admin(
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> AuthContext:
    """
    Require either a valid user JWT or an admin API key.

    Used for user-scoped endpoints to prevent IDOR access.
    """
    if api_key:
        ctx = await verify_api_key(api_key)
        if ctx.is_admin:
            return ctx
        raise HTTPException(status_code=403, detail="User authentication required.")

    if bearer:
        # Allow admin API key passed as bearer token if needed
        if settings.admin_api_key and secrets.compare_digest(bearer.credentials, settings.admin_api_key):
            return AuthContext(
                api_key=bearer.credentials,
                is_admin=True,
                tier="admin",
            )

        user_id = get_user_id_from_token(f"Bearer {bearer.credentials}")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token.")
        return AuthContext(
            api_key=None,
            is_admin=False,
            user_id=user_id,
            user_type="authenticated",
            tier="free",
        )

    raise HTTPException(status_code=401, detail="Authentication required.")


# Dependency shortcuts
RequireAuth = Depends(verify_api_key)
RequireAdmin = Depends(verify_admin_key)
OptionalAuth = Depends(optional_auth)
RequireUserOrAdmin = Depends(verify_user_or_admin)
