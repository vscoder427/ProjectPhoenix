# Service Account Module

Creates a GCP service account with IAM role bindings and optional Workload Identity configuration for external workloads (GitHub Actions, etc.).

## Purpose

Use this module to provision service accounts for Cloud Run services, GitHub Actions workflows, or other workloads that need to authenticate to GCP. The module handles IAM role assignments and Workload Identity Federation bindings.

## Usage

### Basic Service Account with IAM Roles

```hcl
module "dave_service_account" {
  source = "../../../../infrastructure/modules/service-account"

  project_id   = var.project_id
  account_id   = "dave-service-prod"
  display_name = "Dave Service (Production)"
  description  = "Service account for Dave AI career coach service"

  roles = [
    "roles/secretmanager.secretAccessor",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/cloudprofiler.agent"
  ]
}
```

### Service Account with Workload Identity (GitHub Actions)

```hcl
module "github_actions_sa" {
  source = "../../../../infrastructure/modules/service-account"

  project_id   = var.project_id
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions Deployer"
  description  = "Service account for GitHub Actions CI/CD pipelines"

  roles = [
    "roles/run.admin",
    "roles/iam.serviceAccountUser"
  ]

  workload_identity_bindings = [
    "principalSet://iam.googleapis.com/projects/${var.project_number}/locations/global/workloadIdentityPools/github-actions/attribute.repository/vscoder427/ProjectPhoenix"
  ]
}
```

## Requirements

- Terraform >= 1.6.0
- Google Cloud Provider ~> 5.0
- GCP project with Service Account Admin role
- Required GCP APIs enabled:
  - `iam.googleapis.com`
  - `cloudresourcemanager.googleapis.com`
  - `iamcredentials.googleapis.com` (for Workload Identity)

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_id | GCP project ID where the service account will be created | `string` | n/a | yes |
| account_id | Service account ID (6-30 chars, lowercase, digits, hyphens) | `string` | n/a | yes |
| display_name | Human-readable display name for the service account | `string` | n/a | yes |
| description | Description of the service account's purpose | `string` | `""` | no |
| roles | List of IAM roles to grant at project level | `list(string)` | `[]` | no |
| workload_identity_bindings | List of Workload Identity principals that can impersonate this SA | `list(string)` | `[]` | no |

## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| email | Service account email address | no |
| name | Fully qualified service account name | no |
| account_id | Service account ID (same as input) | no |
| unique_id | Unique numeric ID of the service account | no |
| member | IAM member string (format: serviceAccount:{email}) | no |

## Resources Created

- `google_service_account` - Main service account
- `google_project_iam_member` - IAM role bindings (one per role in `roles` list)
- `google_service_account_iam_member` - Workload Identity bindings (one per binding in `workload_identity_bindings` list)

## Required Permissions

The Terraform service account must have:
- `iam.serviceAccounts.create`
- `iam.serviceAccounts.get`
- `iam.serviceAccounts.update`
- `iam.serviceAccounts.delete`
- `resourcemanager.projects.setIamPolicy` (for role bindings)

**Recommended Roles:**
- `roles/iam.serviceAccountAdmin`
- `roles/resourcemanager.projectIamAdmin`

## Common IAM Roles for Cloud Run Services

### Minimal Permissions
```hcl
roles = [
  "roles/logging.logWriter"  # Write logs to Cloud Logging
]
```

### Secrets Access
```hcl
roles = [
  "roles/secretmanager.secretAccessor",  # Read secrets from Secret Manager
  "roles/logging.logWriter"
]
```

### Full Observability
```hcl
roles = [
  "roles/secretmanager.secretAccessor",  # Read secrets
  "roles/cloudtrace.agent",              # Write traces
  "roles/logging.logWriter",             # Write logs
  "roles/cloudprofiler.agent",           # Write profiling data
  "roles/monitoring.metricWriter"        # Write custom metrics
]
```

### Database Access (Cloud SQL)
```hcl
roles = [
  "roles/cloudsql.client",               # Connect to Cloud SQL
  "roles/secretmanager.secretAccessor",
  "roles/logging.logWriter"
]
```

## Workload Identity Federation

Workload Identity allows external workloads (GitHub Actions, GitLab CI, etc.) to impersonate GCP service accounts without long-lived keys.

### Setup Steps

#### 1. Create Workload Identity Pool

```bash
gcloud iam workload-identity-pools create "github-actions" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

#### 2. Create OIDC Provider

```bash
gcloud iam workload-identity-pools providers create-oidc "github-oidc" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-actions" \
  --display-name="GitHub OIDC Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

#### 3. Get Workload Identity Principal

```bash
# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Workload Identity principal format for specific repository
PRINCIPAL="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/attribute.repository/vscoder427/ProjectPhoenix"
```

#### 4. Use in Module

```hcl
workload_identity_bindings = [
  "principalSet://iam.googleapis.com/projects/123456789/locations/global/workloadIdentityPools/github-actions/attribute.repository/vscoder427/ProjectPhoenix"
]
```

#### 5. Authenticate in GitHub Actions

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/123456789/locations/global/workloadIdentityPools/github-actions/providers/github-oidc'
    service_account: 'github-actions-deployer@project-id.iam.gserviceaccount.com'
```

## Testing

### Test Scenario 1: Basic Service Account
1. Create service account with 2-3 IAM roles
2. Verify service account exists: `gcloud iam service-accounts describe {email}`
3. Verify IAM bindings: `gcloud projects get-iam-policy PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:serviceAccount:{email}"`
4. Test access: Impersonate service account and attempt to access a resource

### Test Scenario 2: Workload Identity
1. Create service account with Workload Identity binding
2. Trigger GitHub Actions workflow
3. Verify workflow can authenticate using OIDC
4. Verify workflow can perform actions with granted roles
5. Verify workflow cannot perform actions outside granted roles (negative test)

### Test Scenario 3: Role Changes
1. Create service account with 2 roles
2. Add a 3rd role via `roles` variable
3. Apply and verify new role is granted
4. Remove 1 role via `roles` variable
5. Apply and verify role is revoked

## Troubleshooting

### Error: Service Account Already Exists

**Error:** `Error creating service account: googleapi: Error 409: Service account {id} already exists`

**Cause:** Service account with this ID already exists in the project.

**Fix:** Import existing service account or choose a different `account_id`:
```bash
terraform import module.my_sa.google_service_account.main projects/PROJECT_ID/serviceAccounts/EMAIL
```

### Error: Permission Denied on IAM Binding

**Error:** `Error setting IAM policy: googleapi: Error 403: Permission 'resourcemanager.projects.setIamPolicy' denied`

**Cause:** Terraform service account lacks Project IAM Admin role.

**Fix:**
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.projectIamAdmin"
```

### Error: Invalid Workload Identity Principal

**Error:** `Error adding IAM binding: Invalid member format`

**Cause:** Workload Identity principal format is incorrect.

**Fix:** Ensure principal format is:
```
principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/attribute.repository/ORG/REPO
```

Note: Use `PROJECT_NUMBER` (numeric), not `PROJECT_ID` (string).

## Security Best Practices

1. **Least Privilege:** Grant only roles needed for the service's function
2. **Avoid `roles/owner`:** Never grant Owner role to service accounts
3. **Avoid `roles/editor`:** Prefer granular roles over Editor
4. **Use Workload Identity:** Avoid creating service account keys when possible
5. **Rotate Keys:** If keys are required, rotate every 90 days
6. **Audit Regularly:** Review service account permissions quarterly

## Migration Notes

### Importing Existing Service Account

If you created a service account manually:

```bash
# Import service account
terraform import module.my_sa.google_service_account.main projects/PROJECT_ID/serviceAccounts/EMAIL

# Import IAM bindings (one per role)
terraform import 'module.my_sa.google_project_iam_member.roles["roles/secretmanager.secretAccessor"]' "PROJECT_ID roles/secretmanager.secretAccessor serviceAccount:EMAIL"
```

Then run `terraform plan` to verify no changes are detected.

## References

- [IaC Standard](../../../docs/standards/iac-terraform.md)
- [Module Standards](../../../docs/standards/iac-module-standards.md)
- [Service Account Resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_service_account)
- [IAM Member Resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam#google_project_iam_member)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
