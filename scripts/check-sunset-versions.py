#!/usr/bin/env python3
"""
Check for sunset API versions that should be removed.
Run in CI to fail if sunset code still exists.
"""
import sys
from pathlib import Path

# Add service paths
dave_path = Path(__file__).parent.parent / "services" / "dave" / "api"
golden_path = Path(__file__).parent.parent / "services" / "golden-service-python" / "api"

def check_service(service_name: str, service_path: Path) -> list[tuple[str, any]]:
    """Check a service for sunset versions."""
    sunset_versions = []

    try:
        sys.path.insert(0, str(service_path))
        from app.routes.versions import DEPRECATION_REGISTRY, is_sunset

        for version, status in DEPRECATION_REGISTRY.items():
            if is_sunset(version):
                sunset_versions.append((version, status))

        # Clean up sys.path
        sys.path.remove(str(service_path))
    except Exception as e:
        print(f"⚠️  Could not check {service_name}: {e}")

    return sunset_versions

def main():
    """Check for sunset versions in all services."""
    all_sunset = []

    # Check Dave service
    dave_sunset = check_service("dave", dave_path)
    if dave_sunset:
        all_sunset.extend([("dave", v, s) for v, s in dave_sunset])

    # Check golden-service-python
    golden_sunset = check_service("golden-service-python", golden_path)
    if golden_sunset:
        all_sunset.extend([("golden-service-python", v, s) for v, s in golden_sunset])

    if all_sunset:
        print("⚠️  SUNSET VERSIONS DETECTED - REMOVE CODE:")
        for service, version, status in all_sunset:
            print(f"\n  Service: {service}")
            print(f"  Version: {version}")
            print(f"  Sunset on: {status.sunset_date}")
            if status.migration_guide:
                print(f"  Migration guide: {status.migration_guide}")

        print("\n⚠️  Action required:")
        print("  1. Remove deprecated router from routes/__init__.py or routes.py")
        print("  2. Delete deprecated route files")
        print("  3. Remove version from DEPRECATION_REGISTRY")
        print("  4. Update docs/api-versions.md")

        return 1

    print("✓ No sunset versions pending removal")
    return 0

if __name__ == "__main__":
    sys.exit(main())
