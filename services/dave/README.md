# Golden Service Python

This repository is the canonical FastAPI microservice that mirrors the standards in `EmployaServices`. Clone it to bootstrap every new service with logging, SPIRE/Envoy mTLS, CI/CD, and release readiness automation.

## Quickstart

```bash
cp .env.example .env
pip install -r requirements.txt
make run
```

The service exposes `/health`, `/ready`, and `/api/v1/ping` and emits structured JSON logs with `request_id` for tracing.

## Testing

- `make lint` — Ruff formatting and linting.
- `make typecheck` — Pyright type analysis.
- `make test` — Pytest + Hypothesis.
- `make contract` — Schemathesis against `docs/openapi/v1.yaml`.

## Release Readiness

Run `pwsh -File scripts/build-release-checklist.ps1 -ServiceName golden-service-python -ReleaseTag <tag>` to generate the checklist stored under `docs/releases/<service>/<tag>/`. Attach SBOMs, security scans, drift summaries, and config diffs to that folder before manual approval (see `docs/standards/release-readiness.md`).

## Observability

Instrumentation is wired with `opentelemetry-instrumentation-fastapi` and the structured logger defined in `api/app/logging.py`. Read the SPIRE/Envoy ops guide (`docs/standards/cloudrun-mtls-ops.md`) for monitoring requirements.

## Language & Tone

Follow the enterprise Language & Tone (Recovery Sensitive) standard (`../../docs/standards/language-tone.md`) when writing UI copy, notifications, runbooks, and documentation so the service stays consistent with Employa’s brand voice.
