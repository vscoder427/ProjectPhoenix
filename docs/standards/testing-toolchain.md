# Testing Toolchain Standard

This standard defines required testing tools for all services.

## Test Framework

- pytest + hypothesis
- Tier 0 services must also include integration and contract regression suites in CI gating per the Service Tiering standard.

## Contract Testing

- Schemathesis (OpenAPI-based)

## Load Testing

- k6

## Security Testing

- Semgrep + Bandit + Trivy in CI
- Include scan artifacts in the release readiness checklist so reviewers can verify findings are triaged.
