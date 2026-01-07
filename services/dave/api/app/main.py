import logging
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config import get_settings, Settings
from .logging import configure_logging, request_logger
# Import the aggregated router from the routes package
from .routes import router as api_router

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger("dave-service")

# --- OpenTelemetry Configuration ---
resource = Resource.create(attributes={
    "service.name": settings.service_name,
    "service.environment": settings.environment
})
trace.set_tracer_provider(TracerProvider(resource=resource))
if settings.otlp_endpoint:
    otlp_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
# -----------------------------------

app = FastAPI(
    title=settings.service_name,
    version="0.1.0",
    description="Dave: Unified AI Gateway",
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

# Include the aggregated router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
