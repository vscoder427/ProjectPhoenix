# Service Template and Repo Layout

This standard defines the required repository structure and baseline files for all Employa microservices.

## Required Structure

```
service/
  api/
    app/
      main.py
    requirements.txt
  tests/
  docs/
  scripts/
  Dockerfile
  cloudbuild.yaml
  Makefile
  .env.example
  README.md
```

## Required Files

- `api/app/main.py`: FastAPI entry point
- `api/requirements.txt`: runtime dependencies
- `tests/`: unit, integration, and contract tests
- `docs/`: service spec, runbook, and ADRs
- `scripts/`: admin and maintenance scripts
- `Dockerfile`: standard container build
- `cloudbuild.yaml`: Cloud Build pipeline
- `Makefile`: standardized dev/test targets
- `.env.example`: required env vars with comments
- `README.md`: service overview and quickstart

## Required Endpoints

- `GET /health`
- `GET /ready`

## Required README Sections

- Overview
- API Endpoints
- Configuration
- Local Development
- Testing
- Deployment
- Runbook

## Required Docs

- `docs/spec.md`: behavior spec and API contract
- `docs/runbook.md`: deploy/rollback/alerts
- `docs/adr/`: architecture decisions
