"""
API Router Setup with Versioning
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import Settings, get_settings


def _format_response(status: str, details: Any) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "status": status,
            "details": details,
        },
    )


# Health routes (root level - no versioning)
health_router = APIRouter()


@health_router.get("/health", summary="Health check")
async def health() -> JSONResponse:
    return _format_response("ok", {"service": get_settings().service_name})


@health_router.get("/ready", summary="Readiness probe")
async def ready(settings: Settings = Depends(get_settings)) -> JSONResponse:
    if settings.maintenance_mode:
        raise HTTPException(status_code=503, detail="Service under maintenance")
    return _format_response("ready", {"environment": settings.environment})


# API V1 Routes
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])


@v1_router.get("/ping", summary="Sample status endpoint")
async def ping() -> JSONResponse:
    return _format_response("pong", {"timestamp": "now"})


# Future: API V2 Routes
# v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

# Main router
router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(v1_router)
