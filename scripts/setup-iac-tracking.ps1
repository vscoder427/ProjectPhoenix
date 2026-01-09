# Setup IaC Implementation Tracking on GitHub
#
# This script automates the creation of GitHub milestones and issues for the
# Infrastructure as Code (Terraform) implementation across all ProjectPhoenix services.
# It creates 4 milestones (one per phase) and ~30 issues with proper labels, dependencies,
# and acceptance criteria.
#
# Prerequisites:
# - GitHub CLI (gh) must be installed at: C:\Program Files\GitHub CLI\gh.exe
# - User must be authenticated: gh auth login
# - User must have write access to the target repository
#
# Usage:
#   .\scripts\setup-iac-tracking.ps1                    # Creates all milestones and issues
#   .\scripts\setup-iac-tracking.ps1 -DryRun            # Preview what would be created
#   .\scripts\setup-iac-tracking.ps1 -RepoOwner foo -RepoName bar  # Target different repo
#
# Reference: C:\Users\damiy\.claude\plans\wiggly-wondering-island.md

param(
    [Parameter(HelpMessage="GitHub repository owner/organization")]
    [string]$RepoOwner = "vscoder427",

    [Parameter(HelpMessage="GitHub repository name")]
    [string]$RepoName = "ProjectPhoenix",

    [Parameter(HelpMessage="Preview mode - show what would be created without making changes")]
    [switch]$DryRun = $false
)

$ghPath = "C:\Program Files\GitHub CLI\gh.exe"

Write-Host "🚀 Setting up IaC Implementation Tracking" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "⚠️  DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Check if gh CLI is available
if (-not (Test-Path $ghPath)) {
    Write-Host "❌ GitHub CLI not found at $ghPath" -ForegroundColor Red
    Write-Host "Please install GitHub CLI from: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

# Test authentication
Write-Host "🔐 Checking GitHub authentication..." -ForegroundColor Cyan
& $ghPath auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not authenticated with GitHub CLI" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Authenticated" -ForegroundColor Green
Write-Host ""

# Define repository
$repo = "$RepoOwner/$RepoName"
Write-Host "📦 Repository: $repo" -ForegroundColor Cyan
Write-Host ""

# Create Milestones
Write-Host "📍 Creating Milestones..." -ForegroundColor Cyan

$milestones = @(
    @{
        title = "Phase 1: Foundation Standards & Modules"
        description = "Expand IaC standards, create module library, setup guides. **Checkpoint:** Are all 4 modules complete? Does iac-terraform.md cover all topics?"
        dueDate = (Get-Date).AddDays(3).ToString("yyyy-MM-dd")
    },
    @{
        title = "Phase 2: Dave Service Implementation"
        description = "Implement Terraform for Dave service as pilot. **Checkpoint:** Did Dave Terraform apply successfully? Is service healthy?"
        dueDate = (Get-Date).AddDays(6).ToString("yyyy-MM-dd")
    },
    @{
        title = "Phase 3: Golden Service & Templates"
        description = "Apply Terraform to Golden Service, update service templates. **Checkpoint:** Is pattern reusable?"
        dueDate = (Get-Date).AddDays(8).ToString("yyyy-MM-dd")
    },
    @{
        title = "Phase 4: CI/CD Integration"
        description = "Automate Terraform workflows in GitHub Actions. **Checkpoint:** Are all 3 CI/CD workflows functional?"
        dueDate = (Get-Date).AddDays(10).ToString("yyyy-MM-dd")
    }
)

$createdMilestones = @{}

foreach ($milestone in $milestones) {
    $title = $milestone.title
    $desc = $milestone.description
    $due = $milestone.dueDate

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would create milestone: $title" -ForegroundColor Yellow
    } else {
        Write-Host "  Creating: $title" -ForegroundColor White
        $result = & $ghPath api repos/$repo/milestones -f title="$title" -f description="$desc" -f due_on="$due`T23:59:59Z" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $milestoneNumber = ($result | ConvertFrom-Json).number
            $createdMilestones[$title] = $milestoneNumber
            Write-Host "    ✅ Created milestone #$milestoneNumber" -ForegroundColor Green
        } else {
            Write-Host "    ⚠️  Failed to create milestone" -ForegroundColor Red
        }
    }
}

Write-Host ""

# Define Issues
Write-Host "📝 Creating Issues..." -ForegroundColor Cyan

$issues = @(
    # Phase 1: Foundation (8 issues)
    @{
        title = "[Phase 1][Standards] Expand iac-terraform.md to 250+ lines"
        body = @"
## Task Details

**Phase:** Phase 1
**Priority:** Critical
**Estimated Effort:** 4 hours
**Dependencies:** None

## Description

Expand the core IaC standard document from 25 lines to 250+ lines with comprehensive, actionable guidance for Terraform implementation across all ProjectPhoenix services.

## Acceptance Criteria

- [ ] Directory structure standards defined
- [ ] Naming conventions documented (resources, modules, variables)
- [ ] Variable standards defined (required/optional, validation, sensitive)
- [ ] Output standards defined
- [ ] Tagging/labeling requirements specified
- [ ] State management patterns documented
- [ ] Backend configuration template provided
- [ ] Provider version pinning strategy defined
- [ ] Security & compliance section added
- [ ] Drift detection process documented
- [ ] Change management workflow defined

## Files to Create/Modify

- [ ] ``ProjectPhoenix/docs/standards/iac-terraform.md`` - EXPAND

## Testing/Validation

- [ ] Document reviewed by platform team
- [ ] Examples are valid and tested
- [ ] Links to other standards are correct

## Notes

This document establishes the foundation for all Terraform work. It must be comprehensive enough that engineers can implement infrastructure without constant clarification.
"@
        labels = @("phase-1", "standards", "critical")
        milestone = "Phase 1: Foundation Standards & Modules"
    },
    @{
        title = "[Phase 1][Standards] Create iac-module-standards.md"
        body = @"
## Task Details

**Phase:** Phase 1
**Priority:** High
**Estimated Effort:** 3 hours
**Dependencies:** None

## Description

Create comprehensive module standards document (200+ lines) defining structure, documentation, testing, and ownership requirements for Terraform modules.

## Acceptance Criteria

- [ ] Module structure requirements defined
- [ ] Module documentation standards specified
- [ ] Input/output patterns documented
- [ ] Testing approach defined
- [ ] Versioning strategy documented
- [ ] Module ownership model defined

## Files to Create/Modify

- [ ] ``ProjectPhoenix/docs/standards/iac-module-standards.md`` - NEW

## Testing/Validation

- [ ] Document reviewed by platform team
- [ ] Standards align with iac-terraform.md

## Notes

This complements iac-terraform.md by providing module-specific guidance.
"@
        labels = @("phase-1", "standards", "high-priority")
        milestone = "Phase 1: Foundation Standards & Modules"
    },
    @{
        title = "[Phase 1][Guide] Create setup-terraform-backend.md"
        body = @"
## Task Details

**Phase:** Phase 1
**Priority:** Critical
**Estimated Effort:** 2 hours
**Dependencies:** None

## Description

Create step-by-step guide (150+ lines) for setting up Terraform state backend in GCS, including prerequisites, API enablement, bucket creation, service account setup, and troubleshooting.

## Acceptance Criteria

- [ ] Prerequisites section (GCP project, gcloud, Terraform, permissions)
- [ ] Step 1: Enable required GCP APIs
- [ ] Step 2: Create GCS state backend bucket
- [ ] Step 3: Create Terraform service account
- [ ] Step 4: Initialize first service
- [ ] Troubleshooting section

## Files to Create/Modify

- [ ] ``ProjectPhoenix/docs/guides/setup-terraform-backend.md`` - NEW

## Testing/Validation

- [ ] Follow guide from scratch in test project
- [ ] All commands execute successfully
- [ ] Troubleshooting section addresses common issues

## Notes

This is a one-time setup guide. Must be clear enough for team members to execute independently.
"@
        labels = @("phase-1", "guide", "critical")
        milestone = "Phase 1: Foundation Standards & Modules"
    },
    @{
        title = "[Phase 1][Module] Create state-backend module"
        body = @"
## Task Details

**Phase:** Phase 1
**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** #[iac-terraform.md issue], #[iac-module-standards.md issue]

## Description

Create Terraform module to bootstrap GCS bucket for Terraform state storage with versioning, lifecycle, encryption, and labels.

## Acceptance Criteria

- [ ] main.tf creates google_storage_bucket with proper config
- [ ] variables.tf defines inputs (project_id, region, bucket_name, lifecycle_days)
- [ ] outputs.tf exports bucket_name, bucket_url
- [ ] versions.tf pins Terraform and provider versions
- [ ] README.md with usage examples
- [ ] Versioning enabled
- [ ] Lifecycle policy configured (keep 5 versions)
- [ ] Encryption at rest enabled

## Files to Create/Modify

- [ ] ``ProjectPhoenix/infrastructure/modules/state-backend/main.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/state-backend/variables.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/state-backend/outputs.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/state-backend/versions.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/state-backend/README.md`` - NEW

## Testing/Validation

- [ ] ``terraform validate`` passes
- [ ] ``terraform fmt -check`` passes
- [ ] Module applies successfully in dev project
- [ ] Bucket created with correct configuration

## Notes

This is a one-time bootstrap module. It creates the bucket that will store all other Terraform state files.
"@
        labels = @("phase-1", "module", "high-priority")
        milestone = "Phase 1: Foundation Standards & Modules"
    },
    @{
        title = "[Phase 1][Module] Create cloud-run-service module"
        body = @"
## Task Details

**Phase:** Phase 1
**Priority:** Critical
**Estimated Effort:** 4 hours
**Dependencies:** #[iac-terraform.md issue], #[iac-module-standards.md issue]

## Description

Create reusable Terraform module for Cloud Run services with best practices, including scaling, secrets injection, environment variables, and IAM configuration.

## Acceptance Criteria

- [ ] main.tf creates google_cloud_run_service resource
- [ ] variables.tf defines 15+ inputs (service_name, image, memory, cpu, scaling, secrets, env vars, labels)
- [ ] outputs.tf exports service_name, service_url, service_id
- [ ] versions.tf pins Terraform and provider versions
- [ ] README.md with comprehensive usage examples
- [ ] examples/basic/ directory with working example
- [ ] Secret injection from Secret Manager
- [ ] Environment variable support
- [ ] Scaling configuration (min/max instances, concurrency)
- [ ] Proper labeling for cost tracking

## Files to Create/Modify

- [ ] ``ProjectPhoenix/infrastructure/modules/cloud-run-service/main.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/cloud-run-service/variables.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/cloud-run-service/outputs.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/cloud-run-service/versions.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/cloud-run-service/README.md`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/cloud-run-service/examples/basic/main.tf`` - NEW

## Testing/Validation

- [ ] ``terraform validate`` passes
- [ ] ``terraform fmt -check`` passes
- [ ] Example applies successfully in dev project
- [ ] Service is accessible and healthy
- [ ] Secrets are injected correctly

## Notes

This is the most complex module and will be used by ALL services. Must be flexible yet opinionated.
"@
        labels = @("phase-1", "module", "critical")
        milestone = "Phase 1: Foundation Standards & Modules"
    },
    @{
        title = "[Phase 1][Module] Create service-account module"
        body = @"
## Task Details

**Phase:** Phase 1
**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** #[iac-terraform.md issue], #[iac-module-standards.md issue]

## Description

Create Terraform module to provision service accounts with IAM role bindings and optional Workload Identity configuration.

## Acceptance Criteria

- [ ] main.tf creates google_service_account resource
- [ ] variables.tf defines inputs (project_id, account_id, display_name, roles list)
- [ ] outputs.tf exports email, name, account_id
- [ ] versions.tf pins Terraform and provider versions
- [ ] README.md with usage examples
- [ ] IAM role bindings created via google_project_iam_member
- [ ] Support for Workload Identity bindings

## Files to Create/Modify

- [ ] ``ProjectPhoenix/infrastructure/modules/service-account/main.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/service-account/variables.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/service-account/outputs.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/service-account/versions.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/service-account/README.md`` - NEW

## Testing/Validation

- [ ] ``terraform validate`` passes
- [ ] ``terraform fmt -check`` passes
- [ ] Module applies successfully in dev project
- [ ] Service account created with correct roles

## Notes

Follows least privilege principle. Each service gets dedicated service account with scoped permissions.
"@
        labels = @("phase-1", "module", "high-priority")
        milestone = "Phase 1: Foundation Standards & Modules"
    },
    @{
        title = "[Phase 1][Module] Create secret-manager module"
        body = @"
## Task Details

**Phase:** Phase 1
**Priority:** High
**Estimated Effort:** 3 hours
**Dependencies:** #[iac-terraform.md issue], #[iac-module-standards.md issue]

## Description

Create Terraform module for Secret Manager secrets with IAM access control. **Important:** Uses data sources to reference existing secrets, does NOT create secret values.

## Acceptance Criteria

- [ ] main.tf creates google_secret_manager_secret resource
- [ ] variables.tf defines inputs (project_id, secret_id, accessor_service_accounts list)
- [ ] outputs.tf exports secret_id, secret_name
- [ ] versions.tf pins Terraform and provider versions
- [ ] README.md with usage examples and security notes
- [ ] IAM bindings for accessor service accounts
- [ ] Documentation on using data sources for existing secrets

## Files to Create/Modify

- [ ] ``ProjectPhoenix/infrastructure/modules/secret-manager/main.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/secret-manager/variables.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/secret-manager/outputs.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/secret-manager/versions.tf`` - NEW
- [ ] ``ProjectPhoenix/infrastructure/modules/secret-manager/README.md`` - NEW

## Testing/Validation

- [ ] ``terraform validate`` passes
- [ ] ``terraform fmt -check`` passes
- [ ] Module applies successfully in dev project
- [ ] IAM bindings grant correct access

## Notes

SECURITY: Never store secret values in Terraform state. Use data sources to reference existing secrets in production.
"@
        labels = @("phase-1", "module", "high-priority", "security")
        milestone = "Phase 1: Foundation Standards & Modules"
    },
    @{
        title = "[Phase 1][Docs] Create infrastructure/README.md"
        body = @"
## Task Details

**Phase:** Phase 1
**Priority:** Medium
**Estimated Effort:** 1 hour
**Dependencies:** All Phase 1 module issues

## Description

Create README for infrastructure/ directory with overview of module library, usage guidelines, contribution process, and links to standards.

## Acceptance Criteria

- [ ] Overview of module library
- [ ] List of available modules with descriptions
- [ ] Usage guidelines
- [ ] Contribution process
- [ ] Testing requirements
- [ ] Links to standards documents

## Files to Create/Modify

- [ ] ``ProjectPhoenix/infrastructure/README.md`` - NEW

## Testing/Validation

- [ ] All links are valid
- [ ] Module list is complete and accurate

## Notes

This is the entry point for engineers working with infrastructure modules.
"@
        labels = @("phase-1", "documentation", "medium-priority")
        milestone = "Phase 1: Foundation Standards & Modules"
    },

    # Phase 2: Dave Service (6 issues)
    @{
        title = "[Phase 2][Dave] Create Terraform directory structure"
        body = @"
## Task Details

**Phase:** Phase 2
**Priority:** Critical
**Estimated Effort:** 0.5 hours
**Dependencies:** All Phase 1 issues

## Description

Create directory structure for Dave service Terraform configuration at ``services/dave/infrastructure/terraform/production/``.

## Acceptance Criteria

- [ ] Directory created: ``services/dave/infrastructure/terraform/production/``
- [ ] .gitkeep file added (or initial files committed)

## Files to Create/Modify

- [ ] ``ProjectPhoenix/services/dave/infrastructure/terraform/production/`` - NEW (directory)

## Testing/Validation

- [ ] Directory exists and is committed to git

## Notes

This establishes the pattern that ALL services will follow: ``services/{service}/infrastructure/terraform/{environment}/``.
"@
        labels = @("phase-2", "dave", "critical")
        milestone = "Phase 2: Dave Service Implementation"
    },
    @{
        title = "[Phase 2][Dave] Write terraform.tf (backend config)"
        body = @"
## Task Details

**Phase:** Phase 2
**Priority:** Critical
**Estimated Effort:** 0.5 hours
**Dependencies:** #[Dave directory structure issue]

## Description

Create ``terraform.tf`` with backend configuration for GCS state storage and provider configuration.

## Acceptance Criteria

- [ ] Terraform version constraint: >= 1.6.0
- [ ] GCS backend configured (bucket: employa-terraform-state, prefix: services/dave/production)
- [ ] Google provider version: ~> 5.0
- [ ] Provider configuration with project and region variables

## Files to Create/Modify

- [ ] ``ProjectPhoenix/services/dave/infrastructure/terraform/production/terraform.tf`` - NEW

## Testing/Validation

- [ ] ``terraform init`` succeeds
- [ ] ``terraform validate`` passes

## Notes

This file connects Dave's Terraform to the shared state backend.
"@
        labels = @("phase-2", "dave", "critical")
        milestone = "Phase 2: Dave Service Implementation"
    },
    @{
        title = "[Phase 2][Dave] Write variables.tf"
        body = @"
## Task Details

**Phase:** Phase 2
**Priority:** High
**Estimated Effort:** 1 hour
**Dependencies:** #[Dave terraform.tf issue]

## Description

Create ``variables.tf`` with all input variables for Dave service (project_id, region, image_tag, environment, scaling config).

## Acceptance Criteria

- [ ] project_id variable (default: employa-production)
- [ ] region variable (default: us-central1)
- [ ] image_tag variable (default: latest)
- [ ] environment variable (default: production)
- [ ] min_instances variable (default: 0)
- [ ] max_instances variable (default: 10)
- [ ] memory variable (default: 512Mi) with validation
- [ ] cpu variable (default: 1) with validation

## Files to Create/Modify

- [ ] ``ProjectPhoenix/services/dave/infrastructure/terraform/production/variables.tf`` - NEW

## Testing/Validation

- [ ] ``terraform validate`` passes
- [ ] All variables have descriptions
- [ ] Validation blocks work correctly

## Notes

These variables will be overridden in CI/CD (e.g., image_tag set to git SHA).
"@
        labels = @("phase-2", "dave", "high-priority")
        milestone = "Phase 2: Dave Service Implementation"
    },
    @{
        title = "[Phase 2][Dave] Write main.tf (resource definitions)"
        body = @"
## Task Details

**Phase:** Phase 2
**Priority:** Critical
**Estimated Effort:** 3 hours
**Dependencies:** #[Dave variables.tf issue], #[cloud-run-service module issue], #[service-account module issue]

## Description

Create ``main.tf`` with all resource definitions for Dave service using shared modules: service account, secret IAM bindings, and Cloud Run service.

## Acceptance Criteria

- [ ] Service account module instantiated (dave-service-prod)
- [ ] Data sources for existing secrets (Supabase URL/key, Gemini API key)
- [ ] IAM bindings for service account to access secrets
- [ ] Cloud Run service module instantiated with proper config
- [ ] Environment variables set (ENVIRONMENT, SERVICE_NAME, LOG_LEVEL, PYTHONUNBUFFERED)
- [ ] Secrets injected (SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY)
- [ ] Labels applied (service, environment, managed_by, tier, cost_center)

## Files to Create/Modify

- [ ] ``ProjectPhoenix/services/dave/infrastructure/terraform/production/main.tf`` - NEW

## Testing/Validation

- [ ] ``terraform validate`` passes
- [ ] ``terraform plan`` shows resources to create
- [ ] Plan output reviewed and approved

## Notes

This is the core configuration that deploys Dave. Review carefully before applying.
"@
        labels = @("phase-2", "dave", "critical")
        milestone = "Phase 2: Dave Service Implementation"
    },
    @{
        title = "[Phase 2][Dave] Write outputs.tf"
        body = @"
## Task Details

**Phase:** Phase 2
**Priority:** Medium
**Estimated Effort:** 0.5 hours
**Dependencies:** #[Dave main.tf issue]

## Description

Create ``outputs.tf`` with outputs for Dave service (service URL, service name, service account email, project ID, region).

## Acceptance Criteria

- [ ] service_url output
- [ ] service_name output
- [ ] service_account_email output
- [ ] project_id output
- [ ] region output
- [ ] All outputs have descriptions

## Files to Create/Modify

- [ ] ``ProjectPhoenix/services/dave/infrastructure/terraform/production/outputs.tf`` - NEW

## Testing/Validation

- [ ] ``terraform validate`` passes
- [ ] ``terraform output`` works after apply

## Notes

Outputs are used by CI/CD and for manual verification.
"@
        labels = @("phase-2", "dave", "medium-priority")
        milestone = "Phase 2: Dave Service Implementation"
    },
    @{
        title = "[Phase 2][Dave] Initialize, Plan, Apply, and Document"
        body = @"
## Task Details

**Phase:** Phase 2
**Priority:** Critical
**Estimated Effort:** 3 hours
**Dependencies:** #[Dave outputs.tf issue]

## Description

Initialize Terraform state, run plan, apply configuration, validate deployment, and document learnings in LEARNINGS.md.

## Acceptance Criteria

- [ ] ``terraform init`` succeeds
- [ ] ``terraform validate`` passes
- [ ] ``terraform plan`` reviewed and approved
- [ ] ``terraform apply`` deploys Dave to Cloud Run
- [ ] Service URL is accessible
- [ ] ``/health`` endpoint returns 200 OK
- [ ] All secrets are accessible by service
- [ ] LEARNINGS.md created with issues, permissions, patterns, time

## Files to Create/Modify

- [ ] ``ProjectPhoenix/services/dave/infrastructure/terraform/LEARNINGS.md`` - NEW
- [ ] ``ProjectPhoenix/services/dave/infrastructure/terraform/production/README.md`` - NEW

## Testing/Validation

- [ ] Dave service is healthy and responding
- [ ] No errors in Cloud Run logs
- [ ] Terraform state is saved to GCS

## Notes

This is the critical milestone: Dave deployed via Terraform. Document everything for future services.
"@
        labels = @("phase-2", "dave", "critical")
        milestone = "Phase 2: Dave Service Implementation"
    },

    # Phase 3: Golden Service & Templates (3 issues)
    @{
        title = "[Phase 3][Golden] Apply Terraform to Golden Service"
        body = @"
## Task Details

**Phase:** Phase 3
**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** All Phase 2 issues

## Description

Create Terraform configuration for Golden Service (simpler than Dave - no Supabase/Gemini secrets) by copying and adapting Dave's pattern.

## Acceptance Criteria

- [ ] Directory created: ``services/golden-service-python/infrastructure/terraform/production/``
- [ ] terraform.tf configured
- [ ] variables.tf defined
- [ ] main.tf created (simpler than Dave)
- [ ] outputs.tf created
- [ ] README.md created
- [ ] Terraform applied successfully
- [ ] Service is accessible and healthy

## Files to Create/Modify

- [ ] ``ProjectPhoenix/services/golden-service-python/infrastructure/terraform/production/`` - NEW (all files)

## Testing/Validation

- [ ] ``terraform validate`` passes
- [ ] ``terraform apply`` succeeds
- [ ] Golden Service is healthy

## Notes

Golden Service serves as the reference template for future services.
"@
        labels = @("phase-3", "golden-service", "high-priority")
        milestone = "Phase 3: Golden Service & Templates"
    },
    @{
        title = "[Phase 3][Templates] Update service-template.md"
        body = @"
## Task Details

**Phase:** Phase 3
**Priority:** High
**Estimated Effort:** 1 hour
**Dependencies:** #[Golden Service issue]

## Description

Update service template standard to include ``infrastructure/terraform/production/`` directory structure with all required files.

## Acceptance Criteria

- [ ] infrastructure/ directory added to required structure
- [ ] All Terraform files documented (main.tf, variables.tf, outputs.tf, terraform.tf, README.md)
- [ ] Description of what each file contains
- [ ] Links to IaC standards

## Files to Create/Modify

- [ ] ``ProjectPhoenix/docs/standards/service-template.md`` - MODIFY

## Testing/Validation

- [ ] Documentation is clear and complete
- [ ] Structure matches Golden Service

## Notes

All future services must follow this template.
"@
        labels = @("phase-3", "templates", "high-priority")
        milestone = "Phase 3: Golden Service & Templates"
    },
    @{
        title = "[Phase 3][Templates] Update service-scaffold-checklist.md"
        body = @"
## Task Details

**Phase:** Phase 3
**Priority:** Medium
**Estimated Effort:** 1 hour
**Dependencies:** #[service-template.md issue]

## Description

Add Terraform setup items to service scaffold checklist.

## Acceptance Criteria

- [ ] Checklist item: Create infrastructure/terraform/production/ directory
- [ ] Checklist item: Configure Terraform backend
- [ ] Checklist item: Define service-specific variables
- [ ] Checklist item: Instantiate modules in main.tf
- [ ] Checklist item: Define outputs
- [ ] Checklist item: Initialize and plan
- [ ] Checklist item: Review plan with platform team
- [ ] Checklist item: Apply infrastructure

## Files to Create/Modify

- [ ] ``ProjectPhoenix/docs/templates/service-scaffold-checklist.md`` - MODIFY

## Testing/Validation

- [ ] Checklist is complete
- [ ] Order of operations is correct

## Notes

This guides engineers through setting up infrastructure for new services.
"@
        labels = @("phase-3", "templates", "medium-priority")
        milestone = "Phase 3: Golden Service & Templates"
    },

    # Phase 4: CI/CD Integration (5 issues)
    @{
        title = "[Phase 4][CI/CD] Create terraform-plan.yml workflow"
        body = @"
## Task Details

**Phase:** Phase 4
**Priority:** Critical
**Estimated Effort:** 3 hours
**Dependencies:** All Phase 3 issues

## Description

Create GitHub Actions workflow to automatically run ``terraform plan`` on PRs with infrastructure changes and post plan output as PR comment.

## Acceptance Criteria

- [ ] Trigger: PR with changes to services/*/infrastructure/terraform/** or infrastructure/modules/**
- [ ] Change detection using dorny/paths-filter
- [ ] Per-service jobs (plan-dave, plan-golden)
- [ ] GCP authentication via Workload Identity
- [ ] Plan output saved as artifact
- [ ] Plan posted as PR comment

## Files to Create/Modify

- [ ] ``ProjectPhoenix/.github/workflows/terraform-plan.yml`` - NEW

## Testing/Validation

- [ ] Workflow triggers on infrastructure PRs
- [ ] Plan output appears in PR comments
- [ ] Artifacts are saved

## Notes

This provides visibility and review before infrastructure changes are applied.
"@
        labels = @("phase-4", "ci-cd", "critical")
        milestone = "Phase 4: CI/CD Integration"
    },
    @{
        title = "[Phase 4][CI/CD] Create terraform-apply.yml workflow"
        body = @"
## Task Details

**Phase:** Phase 4
**Priority:** Critical
**Estimated Effort:** 3 hours
**Dependencies:** #[terraform-plan.yml issue]

## Description

Create GitHub Actions workflow for manual Terraform apply with approval gate for production environment.

## Acceptance Criteria

- [ ] Trigger: workflow_dispatch (manual)
- [ ] Inputs: service, environment, image_tag, auto_approve flag
- [ ] Environment protection for production
- [ ] GCP authentication via Workload Identity
- [ ] Steps: Init → Plan → Apply
- [ ] Service URL output after apply

## Files to Create/Modify

- [ ] ``ProjectPhoenix/.github/workflows/terraform-apply.yml`` - NEW

## Testing/Validation

- [ ] Manual trigger works
- [ ] Production requires approval
- [ ] Apply succeeds and outputs service URL

## Notes

This is the controlled way to apply infrastructure changes to production.
"@
        labels = @("phase-4", "ci-cd", "critical")
        milestone = "Phase 4: CI/CD Integration"
    },
    @{
        title = "[Phase 4][CI/CD] Create terraform-drift-detection.yml workflow"
        body = @"
## Task Details

**Phase:** Phase 4
**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** #[terraform-plan.yml issue]

## Description

Create GitHub Actions workflow for weekly drift detection that creates GitHub issues when infrastructure drift is detected.

## Acceptance Criteria

- [ ] Trigger: Weekly schedule (Monday 9 AM UTC) + manual dispatch
- [ ] Matrix: Run for all services x environments
- [ ] Drift detection: terraform plan -detailed-exitcode
- [ ] Automatic issue creation if drift detected
- [ ] Issue labels: infrastructure, drift-detection, needs-triage
- [ ] Success summary logged

## Files to Create/Modify

- [ ] ``ProjectPhoenix/.github/workflows/terraform-drift-detection.yml`` - NEW

## Testing/Validation

- [ ] Workflow runs on schedule
- [ ] Drift creates issues with correct labels
- [ ] No drift logs success

## Notes

Weekly drift detection ensures infrastructure stays in sync with Terraform definitions.
"@
        labels = @("phase-4", "ci-cd", "high-priority")
        milestone = "Phase 4: CI/CD Integration"
    },
    @{
        title = "[Phase 4][CI/CD] Update semantic-release.yml for Terraform"
        body = @"
## Task Details

**Phase:** Phase 4
**Priority:** Medium
**Estimated Effort:** 1 hour
**Dependencies:** #[terraform-apply.yml issue]

## Description

Add optional step to semantic-release workflow to update infrastructure after Docker build if AUTO_DEPLOY_INFRASTRUCTURE variable is set.

## Acceptance Criteria

- [ ] New step added after Docker build
- [ ] Conditional: if AUTO_DEPLOY_INFRASTRUCTURE == true
- [ ] Runs terraform apply with new image tag
- [ ] Error handling if apply fails

## Files to Create/Modify

- [ ] ``ProjectPhoenix/.github/workflows/semantic-release.yml`` - MODIFY

## Testing/Validation

- [ ] Workflow still works without AUTO_DEPLOY_INFRASTRUCTURE
- [ ] Infrastructure updates when flag is set

## Notes

This enables fully automated deployments once confidence is high.
"@
        labels = @("phase-4", "ci-cd", "medium-priority")
        milestone = "Phase 4: CI/CD Integration"
    },
    @{
        title = "[Phase 4][CI/CD] Update pre-merge-guardrails.yml for Terraform"
        body = @"
## Task Details

**Phase:** Phase 4
**Priority:** High
**Estimated Effort:** 2 hours
**Dependencies:** All Phase 4 workflow issues

## Description

Add Terraform validation steps to pre-merge guardrails workflow: check required files exist, check modules are used correctly, run terraform fmt.

## Acceptance Criteria

- [ ] Validation step: Check required Terraform files exist per service
- [ ] Validation step: Check modules use shared infrastructure/modules/
- [ ] Validation step: Run terraform fmt -check -recursive for all services
- [ ] Block merge if validation fails

## Files to Create/Modify

- [ ] ``ProjectPhoenix/.github/workflows/pre-merge-guardrails.yml`` - MODIFY

## Testing/Validation

- [ ] Validation catches missing files
- [ ] Validation catches formatting issues
- [ ] PR cannot merge with invalid Terraform

## Notes

This enforces IaC standards before code merges.
"@
        labels = @("phase-4", "ci-cd", "high-priority")
        milestone = "Phase 4: CI/CD Integration"
    }
)

$issueNumbers = @{}

foreach ($issue in $issues) {
    $title = $issue.title
    $body = $issue.body
    $labels = $issue.labels -join ","
    $milestone = $issue.milestone

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would create issue: $title" -ForegroundColor Yellow
    } else {
        Write-Host "  Creating: $title" -ForegroundColor White

        # Get milestone number
        $milestoneNumber = $createdMilestones[$milestone]

        # Create issue
        $cmd = "$ghPath issue create --repo $repo --title `"$title`" --body `"$body`" --label `"$labels`""
        if ($milestoneNumber) {
            $cmd += " --milestone $milestoneNumber"
        }

        $result = Invoke-Expression $cmd 2>&1
        if ($LASTEXITCODE -eq 0) {
            # Extract issue number from URL
            $issueUrl = $result | Select-String -Pattern "https://github.com/$repo/issues/(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
            $issueNumbers[$title] = $issueUrl
            Write-Host "    ✅ Created issue #$issueUrl" -ForegroundColor Green
        } else {
            Write-Host "    ⚠️  Failed to create issue: $result" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "✅ IaC Tracking Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "  - Milestones: $($milestones.Count)" -ForegroundColor White
Write-Host "  - Issues: $($issues.Count)" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Create GitHub Project Board at: https://github.com/$repo/projects/new" -ForegroundColor White
Write-Host "  2. Add all issues to the project" -ForegroundColor White
Write-Host "  3. Create columns: Backlog, Phase 1, Phase 2, Phase 3, Phase 4, Done" -ForegroundColor White
Write-Host "  4. Start working on Phase 1 issues!" -ForegroundColor White
Write-Host ""
