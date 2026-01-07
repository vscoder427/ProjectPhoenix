# Service Scaffold Checklist

Use this checklist to create a new service that complies with all standards.

## Repository Setup

- [ ] Create repo from golden service reference
- [ ] Add required files and structure
- [ ] Configure CI workflows
- [ ] Add .env.example

## Code Standards

- [ ] Ruff format + lint configured
- [ ] Pyright configured
- [ ] pytest + hypothesis configured
- [ ] Schemathesis contract tests configured

- [ ] Guardrail workflow (`.github/workflows/pre-merge-guardrails.yml`) passes on the service repo and release readiness checks are in place

## Security and Compliance

- [ ] Secret Manager integration
- [ ] Auth middleware in service
- [ ] mTLS for service-to-service
- [ ] HIPAA risk analysis initiated

## Observability

- [ ] OpenTelemetry tracing enabled
- [ ] JSON logging schema implemented
- [ ] SLO alerts configured

## Docs

- [ ] Service spec created
- [ ] Runbook created
- [ ] ADR index created
- [ ] CHANGELOG.md created
