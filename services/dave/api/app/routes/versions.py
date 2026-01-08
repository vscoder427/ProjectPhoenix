"""
API Version Management
Handles version routing and deprecation tracking
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class APIVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"
    # V2 = "v2"  # Add when needed


class DeprecationStatus(BaseModel):
    """Deprecation status for an API version."""
    version: str
    deprecated: bool
    sunset_date: Optional[datetime] = None
    migration_guide: Optional[str] = None
    days_until_sunset: Optional[int] = None


# Deprecation registry
DEPRECATION_REGISTRY: dict[str, DeprecationStatus] = {
    "v1": DeprecationStatus(
        version="v1",
        deprecated=False,
        sunset_date=None,
        migration_guide=None,
    ),
}


def mark_deprecated(
    version: str,
    sunset_days: int = 30,
    migration_guide: str | None = None,
) -> None:
    """Mark an API version as deprecated."""
    sunset_date = datetime.utcnow() + timedelta(days=sunset_days)
    DEPRECATION_REGISTRY[version] = DeprecationStatus(
        version=version,
        deprecated=True,
        sunset_date=sunset_date,
        days_until_sunset=sunset_days,
        migration_guide=migration_guide or f"https://docs.employa.work/api/{version}/migration",
    )


def get_deprecation_status(version: str) -> DeprecationStatus | None:
    """Get deprecation status for a version."""
    return DEPRECATION_REGISTRY.get(version)


def is_deprecated(version: str) -> bool:
    """Check if a version is deprecated."""
    status = DEPRECATION_REGISTRY.get(version)
    return status.deprecated if status else False


def is_sunset(version: str) -> bool:
    """Check if a version has passed its sunset date."""
    status = DEPRECATION_REGISTRY.get(version)
    if not status or not status.sunset_date:
        return False
    return datetime.utcnow() > status.sunset_date
