# Golden Service Reference

This document defines the reference implementation that every service must mirror.

## Purpose

- Provide a working, compliant baseline that passes every standard
- Serve as the source for scaffolding and CI enforcement

## Required Components

### Repo Structure

```
service/
  api/
    app/
      main.py
      config.py
      logging.py
    requirements.in
    requirements.txt
  tests/
  docs/
    spec.md
    runbook.md
    adr/
      README.md
  scripts/
  Dockerfile
  cloudbuild.yaml
  Makefile
  .env.example
  CHANGELOG.md
  README.md
```

### Must-Pass Checks

- Ruff format and lint
- Pyright type checking
- pytest + hypothesis
- Schemathesis contract tests
- k6 load tests (baseline)
- Semgrep + Bandit + Trivy
- SBOM generation (CycloneDX)

### Required Runtime Features

- /health and /ready
- OpenAPI published and versioned
- Auth middleware + gateway validation
- Structured logging + OpenTelemetry
- Config validation on startup

## Reference Build Pipeline

- Build once and promote across environments
- Signed container images
- Canary rollout with auto rollback
