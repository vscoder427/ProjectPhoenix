import logging
from pythonjsonlogger import jsonlogger

from .config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure JSON-structured logging for the service."""

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(message)s %(name)s "
        "service=%(service)s environment=%(environment)s",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    extra = {"service": settings.service_name, "environment": settings.environment}
    root = logging.LoggerAdapter(root, extra)
    root.debug("structured logging configured", extra=extra)


def request_logger(logger: logging.Logger, request_id: str) -> logging.LoggerAdapter:
    return logging.LoggerAdapter(logger, {"request_id": request_id})
