# Dependency Management Standard

This standard defines how dependencies are managed and updated across services.

## Tooling

- Use pip-tools (`requirements.in` compiled to `requirements.txt`)

## Locking Policy

- Lockfiles required for all environments

## Production vs Development Dependencies (Required)

All Python services MUST separate production and development dependencies:

### File Structure

```
service/
├── requirements.txt      # Production only - used in Docker builds
└── requirements-dev.txt  # Development/testing - NOT in production image
```

### requirements.txt (Production)

Contains ONLY runtime dependencies:

- Web framework (fastapi, uvicorn, gunicorn)
- Database clients (asyncpg, supabase)
- AI/ML libraries (google-generativeai)
- Monitoring (prometheus-fastapi-instrumentator)
- Security (python-jose, slowapi)

### requirements-dev.txt (Development)

Starts with `-r requirements.txt` then adds test/dev tools:

```
-r requirements.txt

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
respx>=0.20.0
freezegun>=1.2.0
hypothesis>=6.100.0

# Linting & Type Checking
ruff>=0.1.0
mypy>=1.8.0
```

### CI/CD Pattern

```yaml
# Testing job - uses dev dependencies
- run: pip install -r requirements-dev.txt
- run: pytest tests/

# Build job - uses production only
- run: docker build .  # Dockerfile copies only requirements.txt
```

### Why This Matters

Test dependencies in production images:
- ❌ Increase attack surface (pytest can execute arbitrary code)
- ❌ Increase image size (50-100MB wasted)
- ❌ Violate principle of least privilege

### Reference Implementation

See [Dave/api/requirements.txt](../../../Dave/api/requirements.txt) and [Dave/api/requirements-dev.txt](../../../Dave/api/requirements-dev.txt).

## Update Cadence

- Weekly automated dependency updates with review
- Include license review and risk notes in the SBOM/supply-chain review (see [Supply Chain and SBOM](compliance/supply-chain-sbom.md)).
