# ProjectPhoenix Infrastructure Modules

Reusable Terraform modules for deploying and managing GCP infrastructure across all ProjectPhoenix services.

## Overview

This directory contains shared Terraform modules that standardize infrastructure deployment. All ProjectPhoenix services use these modules to ensure consistency, security, and operational excellence.

**Benefits:**
- **Consistency:** Same configuration patterns across all services
- **Reusability:** Write once, use everywhere
- **Best Practices:** Modules encode security and operational standards
- **Maintainability:** Update module, all services benefit
- **Testing:** Test modules once, trust everywhere

## Available Modules

### 1. state-backend
Creates GCS bucket for Terraform state with versioning and lifecycle management.

**Use Case:** Bootstrap remote state backend
**Location:** `modules/state-backend/`
**Docs:** [README](modules/state-backend/README.md)

### 2. service-account
Creates service account with IAM role bindings and Workload Identity configuration.

**Use Case:** Service accounts for Cloud Run services and CI/CD
**Location:** `modules/service-account/`
**Docs:** [README](modules/service-account/README.md)

### 3. secret-manager
Creates Secret Manager secrets with IAM access control.

**Use Case:** Manage secret metadata and permissions
**Location:** `modules/secret-manager/`
**Docs:** [README](modules/secret-manager/README.md)

### 4. cloud-run-service
Deploys Cloud Run service with autoscaling, secrets, and environment variables.

**Use Case:** Deploy FastAPI microservices
**Location:** `modules/cloud-run-service/`
**Docs:** [README](modules/cloud-run-service/README.md)

## Quick Start

### 1. Setup Terraform Backend

```bash
# Enable required APIs
gcloud services enable run.googleapis.com secretmanager.googleapis.com storage-api.googleapis.com

# Create state backend bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://employa-terraform-state
gsutil versioning set on gs://employa-terraform-state

# Create Terraform service account
gcloud iam service-accounts create terraform-automation \
  --display-name="Terraform Automation"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:terraform-automation@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"
# ... (see setup guide for full permissions)
```

**Full Guide:** [setup-terraform-backend.md](../docs/guides/setup-terraform-backend.md)

### 2. Deploy a Service

```hcl
# services/dave/infrastructure/terraform/production/main.tf

# Create service account
module "dave_service_account" {
  source = "../../../../infrastructure/modules/service-account"

  project_id   = var.project_id
  account_id   = "dave-service-prod"
  display_name = "Dave Service (Production)"

  roles = [
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter"
  ]
}

# Deploy Cloud Run service
module "dave_service" {
  source = "../../../../infrastructure/modules/cloud-run-service"

  project_id            = var.project_id
  service_name          = "dave-service"
  environment           = "production"
  image                 = "gcr.io/${var.project_id}/dave-service:latest"
  service_account_email = module.dave_service_account.email
  service_tier          = "tier-1"

  secrets = {
    SUPABASE_URL = {
      name    = "supabase-url"
      version = "latest"
    }
  }
}
```

**Full Example:** See [services/dave/infrastructure/terraform/](../services/dave/infrastructure/terraform/)

## Module Usage Guidelines

### 1. Reference Modules by Relative Path

During initial development, use relative paths:

```hcl
module "my_service_account" {
  source = "../../../../infrastructure/modules/service-account"
  # ...
}
```

**Why:** Simple, fast iteration, no versioning complexity.

### 2. Migrate to Git Tags When Stable

Once modules are stable, reference by Git tag:

```hcl
module "my_service_account" {
  source = "git::https://github.com/vscoder427/ProjectPhoenix.git//infrastructure/modules/service-account?ref=v1.0.0"
  # ...
}
```

**Why:** Version locking, independent module updates, change control.

### 3. Follow Module Standards

All modules follow [iac-module-standards.md](../docs/standards/iac-module-standards.md):

- Required files: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md`
- Input validation on all variables
- Comprehensive README with examples
- Sensible defaults for optional parameters

## Directory Structure

```
ProjectPhoenix/
├── infrastructure/
│   ├── modules/
│   │   ├── state-backend/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   ├── versions.tf
│   │   │   └── README.md
│   │   ├── service-account/
│   │   │   └── ... (same structure)
│   │   ├── secret-manager/
│   │   │   └── ... (same structure)
│   │   └── cloud-run-service/
│   │       └── ... (same structure)
│   └── README.md (this file)
└── services/
    └── {service-name}/
        └── infrastructure/
            └── terraform/
                └── production/
                    ├── main.tf
                    ├── variables.tf
                    ├── outputs.tf
                    ├── terraform.tf
                    └── README.md
```

## Testing Modules

### Manual Testing

1. **Create test configuration** in `examples/` directory within module
2. **Deploy to test GCP project**
3. **Verify resources** created correctly
4. **Test functionality** (e.g., service account can access secrets)
5. **Clean up** with `terraform destroy`

### Future: Automated Testing

Planned integration with Terratest for automated testing:

```go
func TestCloudRunService(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../examples/basic",
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    serviceUrl := terraform.Output(t, terraformOptions, "service_url")
    assert.Contains(t, serviceUrl, "run.app")
}
```

## Contributing to Modules

### Adding a New Module

1. **Create module directory:** `infrastructure/modules/my-module/`
2. **Create required files:** main.tf, variables.tf, outputs.tf, versions.tf, README.md
3. **Follow standards:** Validate inputs, add descriptions, use sensible defaults
4. **Document thoroughly:** Usage examples, inputs/outputs table, troubleshooting
5. **Test manually:** Deploy to test project and verify functionality
6. **Submit PR:** Platform team reviews for standards compliance

### Updating Existing Modules

1. **Check breaking changes:** Do changes break existing users?
2. **Test thoroughly:** Deploy to test project first
3. **Update README:** Document new inputs, outputs, or behavior changes
4. **Version appropriately:**
   - **Patch (v1.0.0 → v1.0.1):** Bug fixes, no breaking changes
   - **Minor (v1.0.0 → v1.1.0):** New features, backward-compatible
   - **Major (v1.0.0 → v2.0.0):** Breaking changes to inputs/outputs
5. **Submit PR:** Platform team reviews

### Review Process

All module changes require platform team approval:

- **Standards compliance:** Follows iac-module-standards.md
- **Security review:** IAM permissions, secret handling
- **Documentation:** README complete and accurate
- **Breaking changes:** Major version bump required
- **Testing:** Manual testing complete

## Module Versioning

### Phase 1: Relative Paths (Current)

Services reference modules using relative paths:

```hcl
source = "../../../../infrastructure/modules/cloud-run-service"
```

**Status:** All modules use this approach initially

### Phase 2: Git Tags (Future)

Modules tagged with semantic versions:

```bash
git tag -a modules/cloud-run-service/v1.0.0 -m "Initial stable release"
git push origin modules/cloud-run-service/v1.0.0
```

Services reference by tag:

```hcl
source = "git::https://github.com/vscoder427/ProjectPhoenix.git//infrastructure/modules/cloud-run-service?ref=v1.0.0"
```

**Migration:** Once modules are stable and tested in production

## Common Patterns

### Pattern 1: Complete Service Deployment

```hcl
# 1. Create service account
module "service_account" {
  source = "../../../../infrastructure/modules/service-account"
  # ...
}

# 2. Grant secret access (if needed)
module "secret" {
  source = "../../../../infrastructure/modules/secret-manager"

  accessor_service_accounts = [
    module.service_account.email
  ]
}

# 3. Deploy Cloud Run service
module "service" {
  source = "../../../../infrastructure/modules/cloud-run-service"

  service_account_email = module.service_account.email
  secrets = {
    SECRET_VAR = {
      name    = module.secret.secret_id
      version = "latest"
    }
  }
}
```

### Pattern 2: Shared Secrets (Multiple Services)

```hcl
# Create secret with multiple accessors
module "shared_secret" {
  source = "../../../../infrastructure/modules/secret-manager"

  secret_id = "supabase-url"
  accessor_service_accounts = [
    module.service_a.service_account_email,
    module.service_b.service_account_email,
    module.service_c.service_account_email
  ]
}
```

### Pattern 3: Environment-Specific Configuration

```hcl
# Use locals to vary config by environment
locals {
  is_production = var.environment == "production"

  min_instances = local.is_production ? 1 : 0
  max_instances = local.is_production ? 10 : 5
  memory        = local.is_production ? "1Gi" : "512Mi"
}

module "service" {
  source = "../../../../infrastructure/modules/cloud-run-service"

  min_instances = local.min_instances
  max_instances = local.max_instances
  memory        = local.memory
  # ...
}
```

## Standards & Documentation

- **IaC Standard:** [docs/standards/iac-terraform.md](../docs/standards/iac-terraform.md)
- **Module Standards:** [docs/standards/iac-module-standards.md](../docs/standards/iac-module-standards.md)
- **Setup Guide:** [docs/guides/setup-terraform-backend.md](../docs/guides/setup-terraform-backend.md)
- **Service Tiering:** [docs/standards/service-tiering.md](../docs/standards/service-tiering.md)

## Support

- **Questions:** Create GitHub Discussion in ProjectPhoenix repo
- **Bug Reports:** Create GitHub Issue with `module` label
- **Feature Requests:** Create GitHub Issue with `enhancement` label
- **Urgent Issues:** Tag platform team in Slack `#infrastructure` channel

## License

Internal use only - Employa.work / ProjectPhoenix
