# Infrastructure as Code (Terraform) Standard

This standard defines Terraform usage, governance, and best practices for all ProjectPhoenix services.

## Overview

Infrastructure as Code (IaC) ensures all GCP infrastructure is version-controlled, reproducible, and auditable. All ProjectPhoenix services must use Terraform to manage Cloud Run services, IAM, secrets, and related resources.

**Compliance:** Required for Tier 0, Tier 1, and Tier 2 services (per [service-tiering.md](./service-tiering.md)).

---

## Directory Structure

### Shared Modules
Reusable Terraform modules live in the ProjectPhoenix repository:

```
ProjectPhoenix/
└── infrastructure/
    └── modules/
        ├── cloud-run-service/
        ├── service-account/
        ├── secret-manager/
        └── state-backend/
```

Each module must include:
- `main.tf` - Resource definitions
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `versions.tf` - Terraform and provider version constraints
- `README.md` - Module documentation
- `examples/` - Usage examples (optional but recommended)

### Per-Service Configuration
Each service's Terraform configuration lives in its own directory:

```
services/
└── {service-name}/
    └── infrastructure/
        └── terraform/
            ├── production/
            │   ├── main.tf
            │   ├── variables.tf
            │   ├── outputs.tf
            │   ├── terraform.tf
            │   └── README.md
            ├── staging/ (future)
            └── dev/ (future)
```

**Environment Strategy:** Implement production environment first. Staging and dev environments can be added later using the same module structure.

---

## Naming Conventions

Terraform code follows [coding-conventions.md](./coding-conventions.md):

### Resources
Format: `{service}-{type}-{env}`

Examples:
- `dave-service-prod` (Cloud Run service)
- `dave-sa-prod` (Service account)
- `supabase-url-secret` (Secret Manager secret)

### Modules
Use `kebab-case` for module directory names:
- `cloud-run-service`
- `service-account`
- `secret-manager`

### Variables and Locals
Use `snake_case` for variables and local values:
- `project_id`
- `service_account_email`
- `min_instances`

### Constants
Use `UPPER_SNAKE_CASE` for constant values:
- `DEFAULT_REGION`
- `MAX_TIMEOUT_SECONDS`

---

## State Management

### Backend Configuration
All Terraform state must be stored remotely in Google Cloud Storage with state locking enabled.

**State Organization:** One Terraform state per service (reduces blast radius, simplifies access control).

#### Example Backend Configuration
File: `services/{service}/infrastructure/terraform/production/terraform.tf`

```hcl
terraform {
  required_version = ">= 1.6.0"

  backend "gcs" {
    bucket  = "employa-terraform-state"
    prefix  = "services/{service-name}/production"
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

**Note:** Replace `{service-name}` with actual service name (e.g., `dave`, `golden-service-python`).

### State Access Control
- State bucket access limited to Terraform service accounts
- State locking enabled (automatic with GCS backend)
- State versioning enabled (keep last 5 versions)
- Manual state edits prohibited

### State Backup
Before major infrastructure changes:
```bash
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate
```

---

## Variable Standards

### Required Metadata
All variables must include:
- **Type:** Explicit type constraint
- **Description:** Clear description of purpose and usage
- **Validation:** Validation rules where applicable
- **Sensitive:** Mark sensitive values with `sensitive = true`

### Example Variable Definition
```hcl
variable "project_id" {
  description = "GCP project ID where resources will be created"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "memory" {
  description = "Memory allocation for Cloud Run service (e.g., '512Mi', '1Gi')"
  type        = string
  default     = "512Mi"
  validation {
    condition     = can(regex("^[0-9]+(Mi|Gi)$", var.memory))
    error_message = "Memory must be specified in Mi or Gi (e.g., '512Mi', '2Gi')."
  }
}

variable "supabase_service_key" {
  description = "Supabase service role key (stored in Secret Manager)"
  type        = string
  sensitive   = true
}
```

### Required vs Optional Variables
- **Required:** No default value, caller must provide
- **Optional:** Sensible default value provided

---

## Output Standards

### Required Metadata
All outputs must include:
- **Description:** Explanation of the output value
- **Sensitive:** Mark sensitive outputs with `sensitive = true`
- **Value:** The actual output value

### Example Output Definition
```hcl
output "service_url" {
  description = "Public URL of the Cloud Run service"
  value       = module.cloud_run_service.service_url
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = module.service_account.email
}

output "secret_ids" {
  description = "IDs of secrets created for this service"
  value       = {
    supabase_url = google_secret_manager_secret.supabase_url.id
    gemini_key   = google_secret_manager_secret.gemini_key.id
  }
  sensitive = true
}
```

---

## Tagging and Labeling

All GCP resources must include standardized labels for cost tracking, compliance, and operations.

### Required Labels
- `service` - Service name (e.g., `dave`, `golden-service-python`)
- `environment` - Environment name (`production`, `staging`, `dev`)
- `managed_by` - Always `terraform`
- `tier` - Service tier from [service-tiering.md](./service-tiering.md) (`tier-0`, `tier-1`, `tier-2`)
- `cost_center` - Cost center or team responsible (e.g., `engineering`, `product`)

### Example Labels
```hcl
locals {
  common_labels = {
    service      = "dave"
    environment  = var.environment
    managed_by   = "terraform"
    tier         = "tier-1"
    cost_center  = "engineering"
  }
}

resource "google_cloud_run_service" "main" {
  name     = "${var.service_name}-${var.environment}"
  location = var.region

  metadata {
    labels = local.common_labels
  }
  # ... rest of configuration
}
```

**Tier Mapping:**
- **Tier 0 (critical):** Auth, PHI/PII, payments, core platform
- **Tier 1 (important):** User-facing services without direct PHI/PII storage (e.g., Dave)
- **Tier 2 (low risk):** Internal tools, batch jobs, non-critical services

---

## Provider Version Pinning

### Terraform Version
Require Terraform 1.6.0 or newer for all services:
```hcl
terraform {
  required_version = ">= 1.6.0"
}
```

### Provider Versions
Use pessimistic version constraints (`~>`) to allow patch updates but prevent breaking changes:

```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"  # Allow 5.x, block 6.0
    }
  }
}
```

**Rationale:** `~> 5.0` allows updates to 5.1, 5.2, etc., but blocks major version 6.0 which may introduce breaking changes.

---

## Module Versioning

### Initial Phase (Relative Paths)
Use relative paths to reference shared modules during initial implementation:

```hcl
module "cloud_run_service" {
  source = "../../../../infrastructure/modules/cloud-run-service"

  service_name = "dave-service"
  project_id   = var.project_id
  # ... other inputs
}
```

**Pros:**
- Simple to implement
- No versioning complexity
- Fast iteration during development

**Cons:**
- Tighter coupling between services and modules
- Changes to modules affect all services immediately

### Future Phase (Git Tags)
Once modules are stable, migrate to Git tag-based versioning:

```hcl
module "cloud_run_service" {
  source = "git::https://github.com/vscoder427/ProjectPhoenix.git//infrastructure/modules/cloud-run-service?ref=v1.2.3"

  service_name = "dave-service"
  project_id   = var.project_id
  # ... other inputs
}
```

**Migration Path:**
1. Test module changes in one service using relative paths
2. Once stable, tag module version (e.g., `v1.0.0`)
3. Update services to reference Git tag
4. Follow [versioning-strategy.md](./versioning-strategy.md) for semantic versioning

---

## Environments

ProjectPhoenix requires support for three environments per [ci-cd-deployment.md](./ci-cd-deployment.md):

- **Production:** Live user-facing services
- **Staging:** Pre-production testing environment (identical config to production)
- **Dev:** Development and experimentation environment

### Implementation Strategy
1. **Phase 1:** Implement production environment first (critical path for Dave launch)
2. **Phase 2:** Add staging environment (for testing infrastructure changes)
3. **Phase 3:** Add dev environment (for experimentation)

### Environment-Specific Values
Use separate `terraform/` directories for each environment:
```
services/{service}/infrastructure/terraform/
├── production/
│   ├── main.tf
│   ├── variables.tf (environment = "production")
│   └── terraform.tf (state prefix: services/{service}/production)
├── staging/
│   ├── main.tf (same as production)
│   ├── variables.tf (environment = "staging")
│   └── terraform.tf (state prefix: services/{service}/staging)
└── dev/
    └── ... (same pattern)
```

**Best Practice:** Keep `main.tf` identical across environments. Use variables to parameterize environment-specific values.

---

## Security and Compliance

### Secret Management
- **All secrets via Secret Manager:** Never hardcode secrets in Terraform files
- **Use Data Sources:** Reference existing secrets, don't create secret values in Terraform:
  ```hcl
  data "google_secret_manager_secret_version" "supabase_url" {
    secret  = "supabase-url"
    project = var.project_id
  }
  ```
- **Never in State:** Secret values should not be stored in Terraform state
- **IAM for Access:** Grant service accounts access to secrets via IAM bindings

### Service Account Best Practices
- **Least Privilege:** Grant only required IAM roles
- **Workload Identity:** Use Workload Identity Federation for CI/CD authentication
- **Per-Service Accounts:** Each service gets its own service account
- **Document Permissions:** Include IAM role justifications in module README

### Audit Logging
Enable audit logging for all Terraform-managed infrastructure:
- Track who applied changes
- Log all `terraform apply` operations
- Store logs in Cloud Logging for 365+ days

---

## Drift Detection

### Weekly Automation
Run drift detection every Monday at 9 AM UTC using GitHub Actions (see Phase 4 of implementation plan).

### Process
1. **Detect:** Run `terraform plan -detailed-exitcode` for each service
2. **Report:** If drift detected (exit code 2), create GitHub issue with:
   - Service name and environment
   - Full `terraform plan` output
   - Labels: `infrastructure`, `drift-detection`, `needs-triage`
3. **Remediate:** Platform team reviews issue and either:
   - Applies Terraform to fix drift
   - Updates Terraform to match manual changes
   - Reverts manual changes

### Drift Sources
- Manual changes via GCP Console
- Changes via `gcloud` CLI
- Changes from Cloud Build (for non-Terraform managed resources)

**Goal:** Zero tolerance for drift. All infrastructure changes must go through Terraform.

---

## Change Management

### Terraform Plan on PR
Every pull request with Terraform changes triggers automated `terraform plan`:
1. GitHub Actions detects changes to `services/*/infrastructure/terraform/**` or `infrastructure/modules/**`
2. Runs `terraform init && terraform plan` for affected services
3. Posts plan output as PR comment
4. Requires platform team approval before merge

### Manual Approval for Apply
- `terraform plan` runs automatically on PR
- `terraform apply` requires manual approval (workflow_dispatch)
- Production applies require additional approval in GitHub Environments

### Platform Team Review
Terraform changes require review from:
- **Platform Team:** Module quality, state management, security
- **Security Team:** IAM permissions, secret management (for Tier 0 services)
- **Another Engineer:** Code quality, standards adherence

---

## GCP Project Naming

Use `$PROJECT_ID` variable in all examples and documentation. Do not hardcode specific project names (e.g., `employa-production`).

**Rationale:** ProjectPhoenix services are isolated for cutover from existing services. Using `$PROJECT_ID` provides flexibility for different project naming schemes.

### Example
```hcl
variable "project_id" {
  description = "GCP project ID (e.g., from Cloud Build substitution or manual override)"
  type        = string
}

resource "google_cloud_run_service" "main" {
  name     = var.service_name
  location = var.region
  project  = var.project_id
  # ...
}
```

In Cloud Build, `$PROJECT_ID` is automatically substituted by GCP.

---

## Required Terraform Files

Every service's `terraform/production/` directory must include:

1. **`main.tf`** - Resource instantiation (modules, data sources)
2. **`variables.tf`** - Input variable definitions
3. **`outputs.tf`** - Output value definitions
4. **`terraform.tf`** - Backend and provider configuration
5. **`README.md`** - Service-specific deployment instructions

### Minimal Example Structure
```hcl
# main.tf
module "service_account" {
  source = "../../../../infrastructure/modules/service-account"
  # ...
}

module "cloud_run_service" {
  source = "../../../../infrastructure/modules/cloud-run-service"
  # ...
}

# variables.tf
variable "project_id" { ... }
variable "region" { ... }
variable "environment" { ... }

# outputs.tf
output "service_url" { ... }
output "service_account_email" { ... }

# terraform.tf
terraform {
  backend "gcs" { ... }
  required_providers { ... }
}
```

---

## Initialization and Usage

### First-Time Setup
1. **Prerequisites:** Install Terraform 1.6+, gcloud CLI, authenticate to GCP
2. **Enable APIs:** `gcloud services enable` (see setup guide)
3. **Create State Bucket:** See [setup-terraform-backend.md](../guides/setup-terraform-backend.md)
4. **Initialize Terraform:**
   ```bash
   cd services/{service}/infrastructure/terraform/production
   terraform init
   ```

### Standard Workflow
```bash
# 1. Initialize (first time or after backend changes)
terraform init

# 2. Format code (before committing)
terraform fmt -recursive

# 3. Validate syntax
terraform validate

# 4. Preview changes
terraform plan

# 5. Apply changes (manual approval required for production)
terraform apply
```

### CI/CD Integration
- **terraform plan:** Automatic on PR
- **terraform apply:** Manual trigger via GitHub Actions workflow_dispatch

---

## Troubleshooting

### State Lock Error
**Error:** `Error locking state: resource temporarily unavailable`

**Cause:** Previous Terraform operation did not complete (crashed or interrupted).

**Fix:**
```bash
# List locks
terraform force-unlock <LOCK_ID>

# If lock is stale (> 30 minutes old), force unlock
terraform force-unlock -force <LOCK_ID>
```

### Permission Denied
**Error:** `Error: googleapi: Error 403: Permission denied`

**Cause:** Terraform service account lacks required IAM roles.

**Fix:** Grant required roles (see module README for specific permissions).

### Backend Initialization Failed
**Error:** `Error: Failed to get existing workspaces`

**Cause:** State bucket does not exist or is inaccessible.

**Fix:** Create state bucket manually or run bootstrap script (see setup guide).

---

## References

- **Module Standards:** [iac-module-standards.md](./iac-module-standards.md)
- **Setup Guide:** [setup-terraform-backend.md](../guides/setup-terraform-backend.md)
- **Service Tiering:** [service-tiering.md](./service-tiering.md)
- **CI/CD Standard:** [ci-cd-deployment.md](./ci-cd-deployment.md)
- **Versioning Strategy:** [versioning-strategy.md](./versioning-strategy.md)
- **Coding Conventions:** [coding-conventions.md](./coding-conventions.md)
- **Terraform Docs:** https://www.terraform.io/docs
- **Google Provider Docs:** https://registry.terraform.io/providers/hashicorp/google/latest/docs
