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

## Database Security (RLS Policies)

**Standard:** [database-rls-policies.md](../standards/database-rls-policies.md)

**Migration Requirements:**
- [ ] RLS enabled in the same migration as CREATE TABLE (never deploy tables without RLS)
- [ ] All user-facing tables have RLS policies following standard templates
- [ ] Naming convention followed: `{operation}_{scope}_{resource}`
- [ ] Service role bypass policy exists for all tables (`auth.role() = 'service_role'`)
- [ ] WITH CHECK clauses included for UPDATE/INSERT policies
- [ ] No overly broad `USING (true)` policies without status/timestamp filters

**Testing Requirements:**
- [ ] Automated RLS test suite created (see [testing-rls-policies.md](../standards/testing-rls-policies.md))
- [ ] Tests verify user isolation (User A cannot access User B's data)
- [ ] Tests verify service role bypass works for backend operations
- [ ] Tests verify admin policies (if admin-only tables exist)
- [ ] Tests verify public read policies (if public tables exist)
- [ ] RLS tests run in CI/CD pipeline before deployment

## Observability

- [ ] OpenTelemetry tracing enabled
- [ ] JSON logging schema implemented
- [ ] SLO alerts configured

## Docs

- [ ] Service spec created
- [ ] Runbook created
- [ ] ADR index created
- [ ] CHANGELOG.md created
