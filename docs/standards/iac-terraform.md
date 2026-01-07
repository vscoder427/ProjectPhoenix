# Infrastructure as Code (Terraform) Standard

This standard defines Terraform usage and governance.

## State Management

- Remote state required
- State access limited to service accounts
- State locking enabled

## Module Standards

- Use versioned modules
- Module names are service-scoped and descriptive
- No inline ad-hoc resources for production

## Environments

- Separate state per environment (dev/staging/prod)

## Drift Detection

- Weekly drift detection required
- Share drift reports and state change summaries in the release readiness checklist so platform reviewers can confirm infra changes before deployment.
