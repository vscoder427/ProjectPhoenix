from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import Settings, get_settings

router = APIRouter()


def _format_response(status: str, details: Any) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "status": status,
            "details": details,
        },
    )


@router.get("/health", summary="Health check")
async def health() -> JSONResponse:
    return _format_response("ok", {"service": get_settings().service_name})


@router.get("/ready", summary="Readiness probe")
async def ready(settings: Settings = Depends(get_settings)) -> JSONResponse:
    if settings.maintenance_mode:
        raise HTTPException(status_code=503, detail="Service under maintenance")
    return _format_response("ready", {"environment": settings.environment})


@router.get("/api/v1/ping", summary="Sample status endpoint")
async def ping() -> JSONResponse:
    return _format_response("pong", {"timestamp": "now"})
