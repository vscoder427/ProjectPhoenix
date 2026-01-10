# Testing and TDD Standard

This standard defines testing requirements and TDD practices for all Employa microservices.

## TDD Policy

- **Test-first development strongly recommended** for all changes
  - TDD produces better-designed, more testable code
  - Creates tight feedback loop for rapid iteration
  - Results in comprehensive tests by default
- **All production code requires comprehensive tests** regardless of when tests are written
- Test-after is acceptable if tests thoroughly verify behavior
- Tier 2 services have flexibility in testing approach (see Standards Governance)

## Test Suite Requirements

- Unit tests
- Integration tests
- Contract tests
- Load tests
- Security tests
- **RLS policy tests** (see [testing-rls-policies.md](testing-rls-policies.md))
  - Required for all Tier 0 services with user-facing tables
  - Tests user isolation, service role bypass, and admin policies
  - Prevents data leakage and HIPAA violations

## Coverage Quality Standards

- **Write comprehensive tests for critical code:**
  - Authentication and authorization flows
  - Business logic with compliance requirements (HIPAA)
  - Data validation preventing security issues
  - Error handling for user-facing failures
- **Write thorough tests for standard code:**
  - API endpoints and service layer
  - Database interactions and query optimization
  - RLS policies (see [testing-rls-policies.md](testing-rls-policies.md) for specific requirements)
- **Coverage validates test quality:**
  - When tests are comprehensive, coverage naturally exceeds 85%
  - Coverage below 85% indicates untested critical paths
  - **Coverage gate (85%) enforced in CI as quality floor, not target**
  - **85% is non-negotiable** - never request exceptions or ask if lower is acceptable

## CI Gates

- Tests, coverage, linting, security scans, and contract tests required
- Gate results should be attached to the release readiness checklist so reviewers can confirm test health before deployment.

## Test Data

- Managed test datasets with masking
- Seed scripts per service
