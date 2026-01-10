# Secret Manager Module

Creates Google Secret Manager secrets with IAM access control for service accounts.

## Purpose

This module manages Secret Manager secret **metadata and IAM permissions only**. It does NOT create or store secret values in Terraform state. Secret values must be created manually or via separate secure process.

**Use this module to:**
- Create secret placeholders with proper IAM access
- Grant service accounts permission to read secrets
- Manage secret lifecycle independently of secret values

**Do NOT use this module to:**
- Store secret values in Terraform state (security risk)
- Manage secret versions (use `gcloud` or GCP Console)

## Usage

### Creating New Secrets

```hcl
# Create secret metadata (no value stored in Terraform)
module "supabase_url_secret" {
  source = "../../../../infrastructure/modules/secret-manager"

  project_id = var.project_id
  secret_id  = "supabase-url"

  accessor_service_accounts = [
    module.dave_service_account.email,
    module.user_onboarding_service_account.email
  ]

  labels = {
    service = "shared"
    tier    = "tier-1"
  }
}

# After applying, manually add the secret value:
# echo -n "https://your-supabase-url.supabase.co" | \
#   gcloud secrets versions add supabase-url --data-file=-
```

### Referencing Existing Secrets

For secrets that already exist (recommended for production):

```hcl
# Use data source to reference existing secret
data "google_secret_manager_secret_version" "supabase_url" {
  secret  = "supabase-url"
  project = var.project_id
}

# Reference in Cloud Run service
module "dave_service" {
  source = "../../../../infrastructure/modules/cloud-run-service"
  # ...

  secrets = {
    SUPABASE_URL = {
      name    = "supabase-url"
      version = "latest"
    }
  }
}
```

## Requirements

- Terraform >= 1.6.0
- Google Cloud Provider ~> 5.0
- GCP project with Secret Manager Admin role
- Required GCP APIs enabled:
  - `secretmanager.googleapis.com`

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_id | GCP project ID where the secret will be created | `string` | n/a | yes |
| secret_id | Secret ID (must be unique within project) | `string` | n/a | yes |
| accessor_service_accounts | List of service account emails that can access this secret | `list(string)` | `[]` | no |
| labels | Additional labels to apply to the secret | `map(string)` | `{}` | no |

## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| secret_id | ID of the created secret | no |
| secret_name | Fully qualified name of the secret | no |

## Resources Created

- `google_secret_manager_secret` - Secret metadata (no value stored)
- `google_secret_manager_secret_iam_member` - IAM bindings (one per accessor service account)

## Required Permissions

The Terraform service account must have:
- `secretmanager.secrets.create`
- `secretmanager.secrets.get`
- `secretmanager.secrets.update`
- `secretmanager.secrets.delete`
- `secretmanager.secrets.setIamPolicy`

**Recommended Role:** `roles/secretmanager.admin`

## Secret Value Management

### Creating Secret Values (Manual)

After Terraform creates the secret metadata, add the value manually:

```bash
# Option 1: From stdin
echo -n "your-secret-value" | \
  gcloud secrets versions add SECRET_ID --data-file=-

# Option 2: From file
gcloud secrets versions add SECRET_ID --data-file=secret-value.txt

# Option 3: Using GCP Console
# Navigate to Secret Manager > Select secret > Add Version
```

### Updating Secret Values

```bash
# Add new version (previous versions remain accessible)
echo -n "new-secret-value" | \
  gcloud secrets versions add SECRET_ID --data-file=-

# View all versions
gcloud secrets versions list SECRET_ID

# Destroy old version (cannot be undone)
gcloud secrets versions destroy VERSION_NUMBER --secret=SECRET_ID
```

### Rotating Secrets

Best practice: Add new version, update applications, then destroy old version.

```bash
# 1. Add new version
echo -n "new-api-key" | gcloud secrets versions add api-key --data-file=-

# 2. Update Cloud Run service to use new version (or restart to pick up "latest")
gcloud run services update SERVICE_NAME --region=REGION

# 3. Verify new version works
# Test application functionality

# 4. Destroy old version
gcloud secrets versions destroy OLD_VERSION --secret=api-key
```

## Security Best Practices

### 1. Never Store Values in Terraform

**Bad:**
```hcl
# NEVER DO THIS - stores secret in state file
resource "google_secret_manager_secret_version" "bad" {
  secret      = google_secret_manager_secret.main.id
  secret_data = "my-api-key"  # ❌ Stored in plain text in state
}
```

**Good:**
```hcl
# Use this module (creates metadata only)
module "api_key_secret" {
  source = "../../../../infrastructure/modules/secret-manager"
  # ...
}

# Then manually add value via gcloud
# echo -n "my-api-key" | gcloud secrets versions add api-key --data-file=-
```

### 2. Least Privilege Access

Grant `secretAccessor` role only to service accounts that need the secret:

```hcl
accessor_service_accounts = [
  module.dave_service.email  # ✅ Only Dave needs this secret
]
# Don't grant to all service accounts
```

### 3. Use Secret Versions

In production, reference specific secret versions (not "latest"):

```hcl
# Development - use "latest"
secrets = {
  API_KEY = {
    name    = "api-key"
    version = "latest"
  }
}

# Production - pin to specific version
secrets = {
  API_KEY = {
    name    = "api-key"
    version = "3"  # ✅ Explicit version
  }
}
```

### 4. Audit Secret Access

Enable audit logging to track secret access:

```bash
# View audit logs for secret access
gcloud logging read \
  'resource.type="secretmanager.googleapis.com/Secret"
   protoPayload.methodName="google.cloud.secretmanager.v1.SecretManagerService.AccessSecretVersion"' \
  --limit 50
```

### 5. Rotate Regularly

- API keys: Every 90 days
- Database passwords: Every 180 days
- OAuth secrets: When compromised or annually

## Testing

### Test Scenario 1: Secret Creation and Access
1. Create secret with module (metadata only)
2. Manually add secret value via `gcloud`
3. Verify service account can access secret
4. Verify other service accounts cannot access (negative test)

### Test Scenario 2: IAM Binding Changes
1. Create secret with 1 accessor service account
2. Add 2nd accessor via `accessor_service_accounts` list
3. Apply and verify 2nd service account can now access
4. Remove 1st accessor from list
5. Apply and verify 1st service account can no longer access

### Test Scenario 3: Secret Rotation
1. Create secret and add initial value
2. Deploy Cloud Run service using secret
3. Add new secret version
4. Restart Cloud Run service
5. Verify service uses new version
6. Destroy old version
7. Verify service still works

## Troubleshooting

### Error: Secret Already Exists

**Error:** `Error creating secret: googleapi: Error 409: Secret [SECRET_ID] already exists`

**Cause:** Secret with this ID already exists in the project.

**Fix:** Import existing secret or choose a different `secret_id`:
```bash
terraform import module.my_secret.google_secret_manager_secret.main projects/PROJECT_ID/secrets/SECRET_ID
```

### Error: Permission Denied

**Error:** `Error creating secret: googleapi: Error 403: Permission 'secretmanager.secrets.create' denied`

**Cause:** Terraform service account lacks Secret Manager Admin role.

**Fix:**
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"
```

### Error: Secret Has No Versions

**Error:** Secret exists but Cloud Run service fails to start with "secret version not found"

**Cause:** Secret metadata created but no value added.

**Fix:**
```bash
# Add a version
echo -n "secret-value" | gcloud secrets versions add SECRET_ID --data-file=-
```

### Error: Service Account Cannot Access Secret

**Error:** Cloud Run service fails with "Permission denied on secret"

**Cause:** Service account not granted `secretAccessor` role.

**Fix:** Add service account to `accessor_service_accounts` list and re-apply.

## Common Secret Patterns

### Pattern 1: Shared Secrets (Multiple Services)

```hcl
# Create secret with multiple accessors
module "supabase_url" {
  source = "../../../../infrastructure/modules/secret-manager"

  project_id = var.project_id
  secret_id  = "supabase-url"

  accessor_service_accounts = [
    module.dave.service_account_email,
    module.user_onboarding.service_account_email,
    module.aa_meetings.service_account_email
  ]
}
```

### Pattern 2: Service-Specific Secrets

```hcl
# Create secret for single service
module "gemini_api_key" {
  source = "../../../../infrastructure/modules/secret-manager"

  project_id = var.project_id
  secret_id  = "gemini-api-key"

  accessor_service_accounts = [
    module.dave.service_account_email  # Only Dave uses Gemini
  ]

  labels = {
    service = "dave"
  }
}
```

### Pattern 3: Environment-Specific Secrets

```hcl
# Production secret
module "prod_db_password" {
  source = "../../../../infrastructure/modules/secret-manager"

  project_id = var.project_id
  secret_id  = "postgres-password-prod"

  accessor_service_accounts = [
    module.dave_prod.service_account_email
  ]

  labels = {
    environment = "production"
  }
}

# Staging secret (different value)
module "staging_db_password" {
  source = "../../../../infrastructure/modules/secret-manager"

  project_id = var.project_id
  secret_id  = "postgres-password-staging"

  accessor_service_accounts = [
    module.dave_staging.service_account_email
  ]

  labels = {
    environment = "staging"
  }
}
```

## Migration Notes

### Importing Existing Secrets

If secrets already exist in Secret Manager:

```bash
# Import secret metadata
terraform import module.my_secret.google_secret_manager_secret.main projects/PROJECT_ID/secrets/SECRET_ID

# Import IAM bindings (one per accessor)
terraform import 'module.my_secret.google_secret_manager_secret_iam_member.accessors["dave-service@project.iam.gserviceaccount.com"]' "projects/PROJECT_ID/secrets/SECRET_ID roles/secretmanager.secretAccessor serviceAccount:dave-service@project.iam.gserviceaccount.com"
```

Then run `terraform plan` to verify no changes are detected.

## References

- [IaC Standard](../../../docs/standards/iac-terraform.md)
- [Module Standards](../../../docs/standards/iac-module-standards.md)
- [Secret Manager Resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/secret_manager_secret)
- [Secret Manager IAM](https://cloud.google.com/secret-manager/docs/access-control)
- [Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
