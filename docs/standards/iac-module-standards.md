# Terraform Module Standards

This standard defines how to build, document, test, and maintain reusable Terraform modules for ProjectPhoenix.

## Overview

Terraform modules are the building blocks of our Infrastructure as Code. Well-designed modules promote reusability, consistency, and maintainability across all ProjectPhoenix services.

**Compliance:** All shared modules in `infrastructure/modules/` must follow this standard.

---

## Module Structure

Every Terraform module must include the following files:

```
infrastructure/modules/{module-name}/
├── main.tf           # Resource definitions (required)
├── variables.tf      # Input variables (required)
├── outputs.tf        # Output values (required)
├── versions.tf       # Terraform and provider version constraints (required)
├── README.md         # Module documentation (required)
├── examples/         # Usage examples (recommended)
│   └── basic/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── tests/            # Test scenarios (future)
    └── basic_test.go
```

### Required Files

#### 1. main.tf
Contains all resource definitions for the module. Group related resources together with comments.

**Best Practices:**
- Use `locals` block for computed values used multiple times
- Add comments explaining non-obvious resource configurations
- Use `count` or `for_each` for conditional resources

**Example:**
```hcl
# Main service account resource
resource "google_service_account" "main" {
  account_id   = var.account_id
  display_name = var.display_name
  description  = var.description
  project      = var.project_id
}

# Grant IAM roles to service account
resource "google_project_iam_member" "roles" {
  for_each = toset(var.roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.main.email}"
}
```

#### 2. variables.tf
Defines all input variables with types, descriptions, defaults, and validations.

**Requirements:**
- Every variable must have a `description`
- Every variable must have an explicit `type`
- Required variables have no `default` value
- Optional variables have sensible `default` values
- Use `validation` blocks for constraints
- Mark sensitive variables with `sensitive = true`

**Example:**
```hcl
variable "project_id" {
  description = "GCP project ID where the service account will be created"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "account_id" {
  description = "Service account ID (e.g., 'dave-service-prod'). Must be 6-30 characters."
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.account_id))
    error_message = "Account ID must be 6-30 characters, lowercase letters, digits, and hyphens."
  }
}

variable "roles" {
  description = "List of IAM roles to grant to the service account (e.g., ['roles/secretmanager.secretAccessor'])"
  type        = list(string)
  default     = []
}
```

#### 3. outputs.tf
Defines all output values that consuming modules/services need.

**Requirements:**
- Every output must have a `description`
- Mark sensitive outputs with `sensitive = true`
- Output structured data using objects/maps when beneficial
- Include common attributes callers will need

**Example:**
```hcl
output "email" {
  description = "Email address of the service account (format: {account_id}@{project_id}.iam.gserviceaccount.com)"
  value       = google_service_account.main.email
}

output "name" {
  description = "Fully qualified name of the service account"
  value       = google_service_account.main.name
}

output "account_id" {
  description = "Service account ID (same as input)"
  value       = google_service_account.main.account_id
}
```

#### 4. versions.tf
Specifies Terraform and provider version constraints.

**Requirements:**
- Require Terraform >= 1.6.0
- Use pessimistic constraints (`~>`) for providers
- Document why specific versions are required (if non-standard)

**Example:**
```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}
```

#### 5. README.md
Comprehensive module documentation following the template below.

---

## Module Documentation Template

Every module's `README.md` must include these sections:

### 1. Purpose
One paragraph explaining what the module does and when to use it.

**Example:**
```markdown
# Service Account Module

Creates a GCP service account with IAM role bindings and optional Workload Identity configuration.
Use this module to provision service accounts for Cloud Run services, GitHub Actions, or other workloads.
```

### 2. Usage
Basic example showing how to call the module.

**Example:**
````markdown
## Usage

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
    "roles/logging.logWriter"
  ]
}
```
````

### 3. Requirements
Prerequisites for using the module.

**Example:**
```markdown
## Requirements

- Terraform >= 1.6.0
- Google Cloud Provider ~> 5.0
- GCP project with Service Account Admin role
- Required GCP APIs enabled:
  - `iam.googleapis.com`
  - `cloudresourcemanager.googleapis.com`
```

### 4. Inputs
Table of all input variables.

**Format:**
```markdown
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_id | GCP project ID | `string` | n/a | yes |
| account_id | Service account ID | `string` | n/a | yes |
| display_name | Display name | `string` | n/a | yes |
| roles | IAM roles to grant | `list(string)` | `[]` | no |
```

**Tip:** Use `terraform-docs` to auto-generate this table:
```bash
terraform-docs markdown table . > README.md
```

### 5. Outputs
Table of all output values.

**Format:**
```markdown
## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| email | Service account email address | no |
| name | Fully qualified service account name | no |
| account_id | Service account ID | no |
```

### 6. Resources
List of GCP resources created by the module.

**Example:**
```markdown
## Resources Created

- `google_service_account` - Main service account
- `google_project_iam_member` - IAM role bindings (one per role)
- `google_service_account_iam_member` - Workload Identity bindings (if configured)
```

### 7. Permissions
IAM permissions required to use this module.

**Example:**
```markdown
## Required Permissions

The Terraform service account must have:
- `iam.serviceAccounts.create`
- `iam.serviceAccounts.get`
- `iam.serviceAccounts.update`
- `iam.serviceAccounts.delete`
- `resourcemanager.projects.setIamPolicy`

**Recommended Role:** `roles/iam.serviceAccountAdmin`
```

### 8. Examples
Link to example usage in `examples/` directory.

**Example:**
```markdown
## Examples

- [Basic Usage](./examples/basic/) - Simple service account with IAM roles
- [Workload Identity](./examples/workload-identity/) - Service account with GitHub Actions Workload Identity
```

### 9. Migration Notes (Optional)
Guidance for migrating existing resources to this module.

**Example:**
```markdown
## Migration from Manual Configuration

To import an existing service account:

```bash
terraform import module.dave_service_account.google_service_account.main projects/{project_id}/serviceAccounts/{email}
```

Then run `terraform plan` to verify no changes are detected.
```

---

## Input/Output Patterns

### Variable Grouping
Group related variables using objects to reduce parameter count and improve readability.

**Bad:**
```hcl
variable "env_var_1_name" { ... }
variable "env_var_1_value" { ... }
variable "env_var_2_name" { ... }
variable "env_var_2_value" { ... }
```

**Good:**
```hcl
variable "environment_variables" {
  description = "Environment variables for Cloud Run service"
  type        = map(string)
  default     = {}
}

# Usage:
environment_variables = {
  LOG_LEVEL   = "info"
  ENVIRONMENT = "production"
}
```

### Sensible Defaults
Provide defaults that work for 80% of use cases.

**Example:**
```hcl
variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "us-central1"
}

variable "memory" {
  description = "Memory allocation (e.g., '512Mi', '1Gi')"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimum number of instances (0 = scale to zero)"
  type        = number
  default     = 0
}
```

### Flexible Overrides
Allow callers to override defaults when needed.

**Example:**
```hcl
variable "labels" {
  description = "Additional labels to apply (merged with default labels)"
  type        = map(string)
  default     = {}
}

locals {
  default_labels = {
    managed_by = "terraform"
    module     = "cloud-run-service"
  }

  # Merge default labels with user-provided labels
  final_labels = merge(local.default_labels, var.labels)
}
```

### Composition Outputs
Output structured data for easy composition.

**Example:**
```hcl
output "service" {
  description = "Cloud Run service details (for passing to other modules)"
  value = {
    name     = google_cloud_run_service.main.name
    url      = google_cloud_run_service.main.status[0].url
    location = google_cloud_run_service.main.location
    project  = google_cloud_run_service.main.project
  }
}

# Consuming module can access nested values:
# module.cloud_run.service.url
```

---

## Testing Strategy

### Manual Testing (Current)
1. **Create test service:** Deploy module in a test GCP project
2. **Verify resources:** Check GCP Console to confirm resources created correctly
3. **Test functionality:** Verify the resource works as expected (e.g., service account can access secrets)
4. **Clean up:** Run `terraform destroy` to remove test resources

### Document Test Scenarios
Include test scenarios in module README:

**Example:**
```markdown
## Testing

### Test Scenario 1: Basic Service Account
1. Create service account with 2 IAM roles
2. Verify email format is correct
3. Verify IAM bindings applied
4. Test service account can access Secret Manager

### Test Scenario 2: Workload Identity
1. Create service account with Workload Identity binding
2. Verify GitHub Actions can authenticate using OIDC
3. Verify token exchange works
```

### Future: Terratest Integration
Once modules are stable, add automated tests using Terratest (Go framework).

**Example structure:**
```
tests/
├── basic_test.go
├── workload_identity_test.go
└── go.mod
```

**Sample test:**
```go
func TestServiceAccountBasic(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../examples/basic",
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    email := terraform.Output(t, terraformOptions, "email")
    assert.Contains(t, email, "@")
}
```

---

## Versioning Strategy

### Phase 1: Relative Paths (Current)
During initial development, services reference modules using relative paths:

```hcl
module "service_account" {
  source = "../../../../infrastructure/modules/service-account"
  # ...
}
```

**When to use:**
- Module is new and under active development
- Breaking changes are expected
- Want fast iteration across all services

### Phase 2: Git Tags (Future)
Once modules are stable, version them using Git tags following semantic versioning:

```hcl
module "service_account" {
  source = "git::https://github.com/vscoder427/ProjectPhoenix.git//infrastructure/modules/service-account?ref=v1.2.3"
  # ...
}
```

**Version Format:** `vMAJOR.MINOR.PATCH` (e.g., `v1.0.0`, `v1.2.3`)

**Semantic Versioning Rules:**
- **MAJOR** (v1.0.0 → v2.0.0): Breaking changes to inputs/outputs/behavior
- **MINOR** (v1.0.0 → v1.1.0): New features, backward-compatible
- **PATCH** (v1.0.0 → v1.0.1): Bug fixes, backward-compatible

### Migration Path
1. **Stabilize:** Test module thoroughly in production with relative paths
2. **Tag:** Create initial `v1.0.0` tag
3. **Update services:** Gradually migrate services to use Git tag references
4. **Document:** Add version changelog to module README

**Tag creation:**
```bash
cd ProjectPhoenix
git tag -a modules/service-account/v1.0.0 -m "Initial stable release of service-account module"
git push origin modules/service-account/v1.0.0
```

---

## Module Ownership

### Platform Team Responsibilities
- **Review:** All module changes require platform team approval
- **Maintain:** Keep modules up-to-date with provider updates
- **Support:** Respond to module usage questions
- **Test:** Ensure modules work across all environments
- **Document:** Keep README.md accurate and complete

### Contribution Process
1. **Propose:** Create GitHub issue describing module change
2. **Design:** Discuss approach with platform team
3. **Implement:** Create PR with changes + updated tests
4. **Review:** Platform team reviews for:
   - Compliance with this standard
   - Breaking changes (require major version bump)
   - Security implications
   - Documentation completeness
5. **Merge:** Platform team merges and tags new version (if applicable)

### Support Channels
- **Questions:** GitHub Discussions in ProjectPhoenix repo
- **Bug reports:** GitHub Issues with `module` label
- **Urgent issues:** Tag platform team in Slack `#infrastructure` channel

---

## Module Best Practices

### 1. Single Responsibility
Each module should do one thing well.

**Good:** `service-account` - Creates service account + IAM bindings
**Bad:** `full-service` - Creates service account + Cloud Run + secrets + monitoring

### 2. Avoid Hardcoded Values
Use variables for all configurable values.

**Bad:**
```hcl
resource "google_cloud_run_service" "main" {
  location = "us-central1"  # Hardcoded
  # ...
}
```

**Good:**
```hcl
variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

resource "google_cloud_run_service" "main" {
  location = var.region
  # ...
}
```

### 3. Use Locals for Complex Logic
Don't repeat complex expressions; compute once in `locals`.

**Example:**
```hcl
locals {
  # Compute service name once
  service_name = "${var.service_name}-${var.environment}"

  # Merge default and custom labels
  labels = merge(
    {
      service     = var.service_name
      environment = var.environment
      managed_by  = "terraform"
    },
    var.custom_labels
  )
}
```

### 4. Conditional Resources
Use `count` or `for_each` for optional resources.

**Example:**
```hcl
# Only create public access if explicitly enabled
resource "google_cloud_run_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0

  service  = google_cloud_run_service.main.name
  location = google_cloud_run_service.main.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

### 5. Descriptive Resource Names
Use descriptive names for resources in state.

**Bad:**
```hcl
resource "google_service_account" "sa" { ... }
resource "google_cloud_run_service" "s" { ... }
```

**Good:**
```hcl
resource "google_service_account" "main" { ... }
resource "google_cloud_run_service" "main" { ... }
```

### 6. Validate Inputs
Use validation blocks to catch errors early.

**Example:**
```hcl
variable "memory" {
  description = "Memory allocation"
  type        = string
  default     = "512Mi"

  validation {
    condition     = can(regex("^[0-9]+(Mi|Gi)$", var.memory))
    error_message = "Memory must be specified in Mi or Gi (e.g., '512Mi', '2Gi')."
  }
}
```

### 7. Document Dependencies
Explicitly state module dependencies in README.

**Example:**
```markdown
## Dependencies

This module depends on:
- Service account must exist before creating Cloud Run service
- Secrets must exist in Secret Manager before referencing
- Required GCP APIs must be enabled:
  - `run.googleapis.com`
  - `secretmanager.googleapis.com`
```

---

## Deprecation Policy

When deprecating module features:

1. **Announce:** Add deprecation notice to README with removal timeline (minimum 90 days)
2. **Warn:** Add warning to deprecated variable descriptions
3. **Provide migration path:** Document how to migrate to new approach
4. **Major version bump:** Removal of deprecated features requires major version increment

**Example deprecation notice:**
```hcl
variable "old_variable" {
  description = "DEPRECATED: Use 'new_variable' instead. Will be removed in v2.0.0."
  type        = string
  default     = null
}
```

---

## References

- **Core IaC Standard:** [iac-terraform.md](./iac-terraform.md)
- **Terraform Module Best Practices:** https://www.terraform.io/docs/language/modules/develop/index.html
- **Semantic Versioning:** https://semver.org/
- **terraform-docs:** https://terraform-docs.io/
- **Terratest:** https://terratest.gruntwork.io/
