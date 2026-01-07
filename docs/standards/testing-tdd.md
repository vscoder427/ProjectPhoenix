# Testing and TDD Standard

This standard defines testing requirements and TDD practices for all Employa microservices.

## TDD Policy

- Strict TDD required for all changes
- Tier 2 services may request a documented exception (see Standards Governance) if they cannot follow strict TDD, but they still must document reasons in the Decision Record (Lite).

## Test Suite Requirements

- Unit tests
- Integration tests
- Contract tests
- Load tests
- Security tests

## Coverage Targets

- 85%+ coverage for critical modules
- Coverage thresholds enforced in CI

## CI Gates

- Tests, coverage, linting, security scans, and contract tests required
- Gate results should be attached to the release readiness checklist so reviewers can confirm test health before deployment.

## Test Data

- Managed test datasets with masking
- Seed scripts per service
