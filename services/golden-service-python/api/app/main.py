import logging
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from .config import get_settings, Settings
from .logging import configure_logging, request_logger
from .routes import router
from .middleware.deprecation import DeprecationMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from . import __version__

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger("golden-service")

app = FastAPI(
    title=settings.service_name,
    version=__version__,
    description="Golden Service base for Employa microservices",
)

FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    request.state.request_id = request_id
    adapter = request_logger(logger, request_id)
    adapter.info("request.start", path=request.url.path, method=request.method)
    response = await call_next(request)
    adapter.info("request.end", status_code=response.status_code)
    response.headers["X-Request-Id"] = request_id
    return response


@app.get("/metadata", summary="Service metadata")
async def metadata(settings: Settings = Depends(get_settings)) -> JSONResponse:
    return JSONResponse(
        content={
            "service": settings.service_name,
            "environment": settings.environment,
            "version": app.version,
        }
    )

app.include_router(router)

# Add deprecation middleware
app.add_middleware(DeprecationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
