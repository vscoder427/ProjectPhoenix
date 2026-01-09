# Terraform Backend Setup Guide

This guide walks through setting up the GCS backend for Terraform state management in ProjectPhoenix.

## Overview

Terraform stores infrastructure state in a "backend" - a location where the current state of your infrastructure is stored. For ProjectPhoenix, we use **Google Cloud Storage (GCS)** as the backend, with state locking enabled.

**Why GCS Backend?**
- **Remote state:** Shared across team members and CI/CD
- **State locking:** Prevents concurrent modifications
- **Versioning:** Keep history of state changes
- **Encryption:** Data encrypted at rest
- **Access control:** IAM-based permissions

---

## Prerequisites

Before starting, ensure you have:

1. **GCP Project:** Active GCP project for ProjectPhoenix
2. **gcloud CLI:** Installed and authenticated
   ```bash
   gcloud --version
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. **Terraform:** Version 1.6.0 or newer
   ```bash
   terraform --version
   ```
4. **Permissions:** You must have the following IAM roles:
   - `roles/storage.admin` (to create GCS bucket)
   - `roles/iam.serviceAccountAdmin` (to create Terraform service account)
   - `roles/resourcemanager.projectIamAdmin` (to grant IAM roles)

---

## Step 1: Enable Required GCP APIs

Enable all GCP APIs that Terraform will manage:

```bash
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  compute.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  storage-api.googleapis.com \
  storage-component.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com
```

**Verify APIs are enabled:**
```bash
gcloud services list --enabled
```

---

## Step 2: Create GCS State Backend Bucket

### 2.1 Create the Bucket

```bash
# Set your GCP project ID
export PROJECT_ID=$(gcloud config get-value project)

# Create GCS bucket for Terraform state
gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://employa-terraform-state

# Or use gcloud storage:
gcloud storage buckets create gs://employa-terraform-state \
  --project=$PROJECT_ID \
  --location=us-central1 \
  --uniform-bucket-level-access
```

**Bucket naming:**
- Must be globally unique
- Recommended format: `{company}-terraform-state` or `{project}-tf-state`
- Use lowercase letters, numbers, and hyphens only

### 2.2 Enable Versioning

Keep the last 5 versions of state files for disaster recovery:

```bash
gsutil versioning set on gs://employa-terraform-state

# Verify versioning is enabled
gsutil versioning get gs://employa-terraform-state
```

### 2.3 Configure Lifecycle Policy

Automatically delete old versions after 30 days to control costs:

Create `lifecycle.json`:
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "numNewerVersions": 5,
          "daysSinceNoncurrentTime": 30
        }
      }
    ]
  }
}
```

Apply the lifecycle policy:
```bash
gsutil lifecycle set lifecycle.json gs://employa-terraform-state

# Verify policy
gsutil lifecycle get gs://employa-terraform-state
```

### 2.4 Enable Encryption

GCS encrypts data at rest by default using Google-managed keys. For additional security, you can use Customer-Managed Encryption Keys (CMEK):

```bash
# Create KMS keyring (optional, for CMEK)
gcloud kms keyrings create terraform-state \
  --location=us-central1

# Create encryption key (optional, for CMEK)
gcloud kms keys create state-encryption \
  --location=us-central1 \
  --keyring=terraform-state \
  --purpose=encryption

# Set default encryption key for bucket (optional)
gsutil kms encryption \
  -k projects/$PROJECT_ID/locations/us-central1/keyRings/terraform-state/cryptoKeys/state-encryption \
  gs://employa-terraform-state
```

**Note:** Google-managed encryption is sufficient for most use cases. CMEK adds complexity and cost.

### 2.5 Set IAM Permissions

Lock down bucket access to only the Terraform service account (created in Step 3):

```bash
# Remove public access (should already be blocked by uniform bucket-level access)
gsutil iam ch -d allUsers:objectViewer gs://employa-terraform-state
gsutil iam ch -d allAuthenticatedUsers:objectViewer gs://employa-terraform-state
```

---

## Step 3: Create Terraform Service Account

### 3.1 Create Service Account

Create a dedicated service account for Terraform operations:

```bash
export PROJECT_ID=$(gcloud config get-value project)

# Create service account
gcloud iam service-accounts create terraform-automation \
  --display-name="Terraform Automation" \
  --description="Service account for Terraform infrastructure management" \
  --project=$PROJECT_ID

# Capture service account email
export TF_SA_EMAIL="terraform-automation@$PROJECT_ID.iam.gserviceaccount.com"
```

### 3.2 Grant IAM Roles

Grant the Terraform service account permissions to manage infrastructure:

```bash
# Storage Admin - manage GCS state bucket
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$TF_SA_EMAIL" \
  --role="roles/storage.admin"

# Cloud Run Admin - manage Cloud Run services
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$TF_SA_EMAIL" \
  --role="roles/run.admin"

# Service Account Admin - create service accounts for services
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$TF_SA_EMAIL" \
  --role="roles/iam.serviceAccountAdmin"

# Service Account User - assign service accounts to Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$TF_SA_EMAIL" \
  --role="roles/iam.serviceAccountUser"

# Secret Manager Admin - manage secrets
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$TF_SA_EMAIL" \
  --role="roles/secretmanager.admin"

# Project IAM Admin - grant service accounts access to resources
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$TF_SA_EMAIL" \
  --role="roles/resourcemanager.projectIamAdmin"
```

**Security Note:** These are broad permissions. In production, consider using custom roles with least privilege.

### 3.3 Create Service Account Key (Local Development)

For local Terraform development, create a key file:

```bash
# Create key file
gcloud iam service-accounts keys create terraform-key.json \
  --iam-account=$TF_SA_EMAIL

# Secure the key file
chmod 600 terraform-key.json

# Set environment variable for Terraform
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-key.json"
```

**Important:**
- **Never commit `terraform-key.json` to Git**
- Add to `.gitignore`: `terraform-key.json`
- Rotate keys every 90 days
- For CI/CD, use Workload Identity Federation instead (no keys)

### 3.4 Configure Workload Identity Federation (CI/CD)

For GitHub Actions, use Workload Identity Federation (keyless authentication):

```bash
# Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-actions" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-oidc" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-actions" \
  --display-name="GitHub OIDC Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Grant GitHub Actions access to Terraform service account
gcloud iam service-accounts add-iam-policy-binding $TF_SA_EMAIL \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/attribute.repository/vscoder427/ProjectPhoenix"
```

Replace `PROJECT_NUMBER` with your GCP project number (find it with `gcloud projects describe $PROJECT_ID --format='value(projectNumber)'`).

---

## Step 4: Initialize First Service

Now that the backend is ready, initialize Terraform for your first service (e.g., Dave).

### 4.1 Create Terraform Configuration

Navigate to your service's Terraform directory:

```bash
cd ProjectPhoenix/services/dave/infrastructure/terraform/production
```

Create `terraform.tf`:

```hcl
terraform {
  required_version = ">= 1.6.0"

  backend "gcs" {
    bucket  = "employa-terraform-state"
    prefix  = "services/dave/production"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

### 4.2 Initialize Terraform

Initialize Terraform to configure the GCS backend:

```bash
terraform init
```

**Expected output:**
```
Initializing the backend...

Successfully configured the backend "gcs"! Terraform will automatically
use this backend unless the backend configuration changes.

Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
- Installing hashicorp/google v5.x.x...

Terraform has been successfully initialized!
```

### 4.3 Validate Configuration

Check that your Terraform syntax is correct:

```bash
terraform validate
```

**Expected output:**
```
Success! The configuration is valid.
```

### 4.4 Create Plan

Preview what Terraform will create:

```bash
terraform plan
```

Review the plan output carefully. Ensure:
- Resources are correctly named
- IAM permissions are appropriate
- No unexpected deletions or modifications

### 4.5 Apply Infrastructure

Once you're satisfied with the plan, apply it:

```bash
terraform apply
```

Type `yes` when prompted to confirm.

**Expected output:**
```
Apply complete! Resources: X added, 0 changed, 0 destroyed.

Outputs:

service_url = "https://dave-service-xxxxxxxxxx-uc.a.run.app"
```

---

## Verification

After setup, verify everything works:

### 1. Check State File

Verify state is stored in GCS:

```bash
gsutil ls gs://employa-terraform-state/services/dave/production/
```

You should see `default.tfstate`.

### 2. View State

Download and inspect the state file:

```bash
terraform state list
terraform state show google_cloud_run_service.main
```

### 3. Check State Locking

Try running two `terraform plan` commands simultaneously. The second should wait for the first to complete (state locking in action).

---

## Troubleshooting

### Error: Backend Initialization Failed

**Error:** `Error: Failed to get existing workspaces: storage: bucket doesn't exist`

**Cause:** GCS bucket doesn't exist or Terraform can't access it.

**Fix:**
1. Verify bucket exists: `gsutil ls gs://employa-terraform-state`
2. Check IAM permissions on bucket
3. Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set correctly

### Error: Permission Denied

**Error:** `Error: googleapi: Error 403: Permission 'storage.objects.create' denied`

**Cause:** Service account lacks permissions to write to GCS bucket.

**Fix:**
```bash
# Grant Storage Object Admin role
gsutil iam ch serviceAccount:$TF_SA_EMAIL:roles/storage.objectAdmin gs://employa-terraform-state
```

### Error: State Locked

**Error:** `Error: Error locking state: resource temporarily unavailable`

**Cause:** Previous Terraform operation didn't complete (crashed or was interrupted).

**Fix:**
```bash
# Force unlock (use the LOCK_ID from error message)
terraform force-unlock <LOCK_ID>
```

### Error: Terraform Version Mismatch

**Error:** `Error: state snapshot was created by Terraform v1.7.0, which is newer than current v1.6.0`

**Cause:** State file was created with a newer Terraform version.

**Fix:** Upgrade Terraform to match or exceed the version in the error:
```bash
# On macOS
brew upgrade terraform

# On Windows (with Chocolatey)
choco upgrade terraform

# Or download from https://www.terraform.io/downloads
```

---

## Best Practices

1. **One bucket per environment:** Use different buckets for dev/staging/prod
   - `employa-terraform-state-dev`
   - `employa-terraform-state-staging`
   - `employa-terraform-state-prod`

2. **State prefixes:** Use consistent naming for state prefixes:
   - `services/{service-name}/{environment}`
   - Example: `services/dave/production`

3. **Access control:** Limit bucket access to:
   - Terraform service account (read/write)
   - Platform team (read-only for debugging)
   - Block all other access

4. **Backup before major changes:**
   ```bash
   terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate
   ```

5. **Never edit state manually:** Use `terraform state` commands only

6. **Rotate service account keys:** Every 90 days for local development keys

7. **Use Workload Identity for CI/CD:** Avoid long-lived service account keys

---

## Next Steps

Now that your Terraform backend is configured:

1. **Build modules:** Create reusable Terraform modules in `infrastructure/modules/`
2. **Deploy services:** Use modules to deploy Dave, Golden Service, etc.
3. **Set up CI/CD:** Configure GitHub Actions workflows for `terraform plan` and `terraform apply`
4. **Enable drift detection:** Schedule weekly drift detection jobs

---

## References

- **IaC Standard:** [iac-terraform.md](../standards/iac-terraform.md)
- **Module Standards:** [iac-module-standards.md](../standards/iac-module-standards.md)
- **GCS Backend Docs:** https://www.terraform.io/docs/language/settings/backends/gcs.html
- **Workload Identity Federation:** https://cloud.google.com/iam/docs/workload-identity-federation
- **Terraform State:** https://www.terraform.io/docs/language/state/index.html
