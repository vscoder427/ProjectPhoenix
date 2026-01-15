# Container Base Image and Cloud Run Configuration

This standard defines container and Cloud Run defaults for services.

## Base Image

- `python:3.12-slim` with hardening (minimal packages, non-root user)
- Always use `-slim` variants to minimize attack surface

## Dockerfile Security Requirements

### Non-Root User (Required)

All production containers MUST run as non-root:

```dockerfile
# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
```

### Python Environment Flags (Required)

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
```

- `PYTHONDONTWRITEBYTECODE=1` - Prevents `.pyc` files (smaller image)
- `PYTHONUNBUFFERED=1` - Ensures logs stream immediately
- `PIP_NO_CACHE_DIR=1` - Reduces image size

### Production Dependencies Only (Required)

Docker builds MUST use only production dependencies:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Never** copy `requirements-dev.txt` to production images. See [Dependency Management](dependency-management.md) for prod/dev separation.

### Layer Ordering (Recommended)

Order Dockerfile commands for optimal cache:

1. System dependencies (rarely change)
2. Python dependencies (change occasionally)
3. Application code (changes frequently)

### Health Check (Required)

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"
```

### Reference Implementation

See [Dave/api/Dockerfile](../../../Dave/api/Dockerfile) for a complete example.

## Concurrency

- Per-service tuning based on load tests
- Record the tuned values, warm instances, and CPU budgets in the service spec and release readiness notes.

## Min Instances

- Per-service policy (critical services may keep 1 warm instance)

## CPU Allocation

- Per-service policy (always-on CPU only where required)
