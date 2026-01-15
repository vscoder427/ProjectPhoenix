# Security and Secrets Standard

This standard defines security and secrets management for all Employa microservices.

## Secrets Storage

- Use GCP Secret Manager for all runtime secrets
- Local development uses `.env` with no PHI
- Never commit secrets to the repo

> **Guidance:** use the [Secrets Access Policy](secrets-access-policy.md) when approving human review access or rotation requests.

## Terraform/IaC Secrets Rules (Required)

### Never Hardcode Secrets in Terraform

```hcl
# ❌ WRONG - Hardcoded credential
environment_variables = {
  DB_DSN = "postgresql://user:password@host:5432/db"
}

# ✅ CORRECT - Reference Secret Manager
secrets = {
  DB_DSN = { name = "service-db-dsn", version = "latest" }
}
```

### Never Use Secrets as Variable Defaults

```hcl
# ❌ WRONG - Secret in default value
variable "api_key" {
  default = "sk-abc123..."
}

# ✅ CORRECT - No default, require explicit input
variable "api_key" {
  description = "API key (from Secret Manager)"
  sensitive   = true
}
```

### Connection Strings Are Secrets

Database DSNs, connection strings, and URLs with credentials MUST be stored in Secret Manager, never as plain environment variables:

```hcl
# ❌ WRONG - DSN in environment variables
environment_variables = {
  DAVE_DB_DSN = "postgresql://..."
}

# ✅ CORRECT - DSN as a secret
secrets = {
  DAVE_DB_DSN = { name = "dave-db-dsn", version = "latest" }
}
```

### Migration Cleanup Required

When migrating services (e.g., Supabase → Cloud SQL):
- Remove ALL references to old secrets
- Don't leave orphaned secret references in terraform
- Document migration in code comment with date

### Reference Implementation

See [Dave/infrastructure/terraform/production/main.tf](../../../../Dave/infrastructure/terraform/production/main.tf) for proper Secret Manager usage.

## Pre-commit Secret Detection (Recommended)

Use `detect-secrets` or `gitleaks` to block accidental commits:

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

Patterns to block:
- Passwords in `.tf` files
- API keys in any file
- Connection strings with credentials
- Base64-encoded secrets

## Service Identity

- Workload Identity is required
- Each service uses a dedicated service account with least privilege

## API Protection

- API Gateway auth required for external requests
- Service middleware enforces auth on all endpoints
- mTLS required for service-to-service calls

## Data Classification

- Formal data classification policy required (PHI, PII, internal, public)
- Data handling rules follow HIPAA compliance standard

## Key Rotation

- Automated secret rotation with audit trail
- Rotation schedules documented per secret

- Revoke service account keys and secrets immediately if SPIRE/Envoy reports identity anomalies; log in the incident tracker.
