# State Backend Module

Creates a Google Cloud Storage bucket for Terraform state storage with versioning, lifecycle management, and security best practices.

## Purpose

This module bootstraps the GCS backend infrastructure needed for Terraform remote state. Use this module once per GCP project to create the state bucket, then configure other Terraform projects to use this bucket as their backend.

## Usage

```hcl
module "terraform_state_backend" {
  source = "../../../../infrastructure/modules/state-backend"

  project_id  = var.project_id
  bucket_name = "employa-terraform-state"
  region      = "us-central1"

  keep_versions  = 5
  lifecycle_days = 30

  labels = {
    environment = "production"
    team        = "platform"
  }
}
```

## Requirements

- Terraform >= 1.6.0
- Google Cloud Provider ~> 5.0
- GCP project with Storage Admin role
- Required GCP APIs enabled:
  - `storage-api.googleapis.com`
  - `storage-component.googleapis.com`

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_id | GCP project ID where the state bucket will be created | `string` | n/a | yes |
| bucket_name | Name of the GCS bucket for Terraform state (must be globally unique) | `string` | n/a | yes |
| region | GCP region for the state bucket | `string` | `"us-central1"` | no |
| keep_versions | Number of state file versions to keep (older versions are deleted) | `number` | `5` | no |
| lifecycle_days | Delete non-current versions after this many days | `number` | `30` | no |
| force_destroy | Allow bucket deletion even if it contains objects (use with caution in production) | `bool` | `false` | no |
| labels | Additional labels to apply to the bucket | `map(string)` | `{}` | no |

## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| bucket_name | Name of the created GCS bucket | no |
| bucket_url | GCS URL of the bucket (format: gs://bucket-name) | no |
| bucket_self_link | Self-link (URI) of the bucket | no |

## Resources Created

- `google_storage_bucket` - GCS bucket with versioning and lifecycle rules

## Required Permissions

The Terraform service account must have:
- `storage.buckets.create`
- `storage.buckets.get`
- `storage.buckets.update`
- `storage.buckets.delete`

**Recommended Role:** `roles/storage.admin`

## Features

### Versioning
State file versioning is automatically enabled, keeping the last N versions (default: 5). This allows rollback if state corruption occurs.

### Lifecycle Management
Old versions are automatically deleted after 30 days (configurable) to control storage costs while maintaining recent history.

### Security
- **Uniform bucket-level access:** Enforced for consistent IAM permissions
- **No public access:** Bucket is private by default
- **Encryption at rest:** Google-managed encryption keys

### Labels
Default labels applied:
- `purpose = "terraform-state"`
- `managed_by = "terraform"`

Additional labels can be provided via the `labels` variable.

## Bootstrap Process

This module has a chicken-and-egg problem: you need a state bucket to use remote state, but this module creates the state bucket.

**Solution:** Bootstrap the state backend module using local state, then migrate to remote state.

### Step 1: Create with Local State

```bash
cd ProjectPhoenix/infrastructure/bootstrap
terraform init  # Uses local state
terraform apply
```

### Step 2: Migrate to Remote State

After the bucket is created, configure the backend in `versions.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket  = "employa-terraform-state"
    prefix  = "infrastructure/state-backend"
  }
}
```

Then migrate:
```bash
terraform init -migrate-state
```

Terraform will ask if you want to copy the state to the new backend. Type `yes`.

### Step 3: Verify Remote State

```bash
# Check that local state is gone
ls terraform.tfstate  # Should not exist

# Verify state in GCS
gsutil ls gs://employa-terraform-state/infrastructure/state-backend/
```

## Testing

### Test Scenario 1: Basic Bucket Creation
1. Apply module configuration
2. Verify bucket exists: `gsutil ls gs://{bucket_name}`
3. Verify versioning enabled: `gsutil versioning get gs://{bucket_name}`
4. Verify lifecycle policy: `gsutil lifecycle get gs://{bucket_name}`

### Test Scenario 2: State Storage
1. Create bucket with this module
2. Configure another Terraform project to use this bucket as backend
3. Apply that project and verify state file appears in bucket
4. Make a change and reapply
5. Verify state versioning (should see multiple versions)

### Test Scenario 3: Bucket Deletion Protection
1. Set `force_destroy = false` (default)
2. Create bucket and store some state files
3. Try to destroy the module
4. Verify Terraform prevents deletion (bucket contains objects)

## Troubleshooting

### Error: Bucket name already exists

**Error:** `Error creating bucket: googleapi: Error 409: You already own this bucket`

**Cause:** Bucket names are globally unique. Someone else owns this name, or you deleted it recently (30-day grace period).

**Fix:** Choose a different bucket name or wait 30 days if you recently deleted it.

### Error: Permission Denied

**Error:** `Error creating bucket: googleapi: Error 403: Permission denied`

**Cause:** Terraform service account lacks Storage Admin role.

**Fix:**
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### Error: API Not Enabled

**Error:** `Error creating bucket: googleapi: Error 403: Cloud Storage API has not been used`

**Cause:** Storage API not enabled in GCP project.

**Fix:**
```bash
gcloud services enable storage-api.googleapis.com
```

## Migration Notes

### Importing Existing Bucket

If you created the state bucket manually and want to manage it with Terraform:

```bash
terraform import module.terraform_state_backend.google_storage_bucket.terraform_state employa-terraform-state
```

Then run `terraform plan` to verify no changes are detected.

## References

- [IaC Standard](../../../docs/standards/iac-terraform.md)
- [Module Standards](../../../docs/standards/iac-module-standards.md)
- [Setup Guide](../../../docs/guides/setup-terraform-backend.md)
- [GCS Bucket Resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket)
