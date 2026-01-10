# Cloud Run Service Module

Creates a Google Cloud Run service with best practices for ProjectPhoenix microservices, including resource limits, autoscaling, environment variables, secrets, and IAM configuration.

## Purpose

This module standardizes Cloud Run service deployments across ProjectPhoenix. Use this module for all FastAPI microservices to ensure consistency, security, and operational excellence.

## Usage

### Basic Service

```hcl
module "dave_service" {
  source = "../../../../infrastructure/modules/cloud-run-service"

  project_id = var.project_id
  service_name = "dave-service"
  environment = "production"
  image = "gcr.io/${var.project_id}/dave-service:${var.image_tag}"
  service_account_email = module.dave_service_account.email
  service_tier = "tier-1"

  memory = "512Mi"
  cpu    = "1"
  min_instances = 0
  max_instances = 10

  environment_variables = {
    ENVIRONMENT        = "production"
    LOG_LEVEL          = "info"
    PYTHONUNBUFFERED   = "1"
  }

  secrets = {
    SUPABASE_URL = {
      name    = "supabase-url"
      version = "latest"
    }
    SUPABASE_SERVICE_KEY = {
      name    = "supabase-service-key"
      version = "latest"
    }
    GEMINI_API_KEY = {
      name    = "gemini-api-key"
      version = "latest"
    }
  }

  labels = {
    cost_center = "engineering"
  }
}
```

### Public Service (Unauthenticated Access)

```hcl
module "public_api" {
  source = "../../../../infrastructure/modules/cloud-run-service"

  # ... other config ...

  allow_unauthenticated = true  # Allow public access
  ingress              = "all"  # Accept traffic from anywhere
}
```

### Private Service (VPC Access)

```hcl
module "internal_service" {
  source = "../../../../infrastructure/modules/cloud-run-service"

  # ... other config ...

  allow_unauthenticated = false
  ingress              = "internal"
  vpc_connector         = "projects/${var.project_id}/locations/${var.region}/connectors/my-vpc-connector"
}
```

## Requirements

- Terraform >= 1.6.0
- Google Cloud Provider ~> 5.0
- GCP project with Cloud Run Admin role
- Required GCP APIs enabled:
  - `run.googleapis.com`
  - `secretmanager.googleapis.com` (if using secrets)
  - `vpcaccess.googleapis.com` (if using VPC connector)

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_id | GCP project ID | `string` | n/a | yes |
| service_name | Base service name (env suffix added automatically) | `string` | n/a | yes |
| environment | Environment (production/staging/dev) | `string` | n/a | yes |
| image | Container image URL | `string` | n/a | yes |
| service_account_email | Service account email | `string` | n/a | yes |
| service_tier | Service tier (tier-0/tier-1/tier-2) | `string` | n/a | yes |
| region | GCP region | `string` | `"us-central1"` | no |
| memory | Memory allocation (e.g., '512Mi', '1Gi') | `string` | `"512Mi"` | no |
| cpu | CPU allocation (1, 2, 4, or 8) | `string` | `"1"` | no |
| min_instances | Minimum instances (0 = scale to zero) | `number` | `0` | no |
| max_instances | Maximum instances | `number` | `10` | no |
| concurrency | Max concurrent requests per instance | `number` | `80` | no |
| timeout_seconds | Request timeout (max 3600) | `number` | `300` | no |
| container_port | Port container listens on | `number` | `8080` | no |
| ingress | Ingress settings (all/internal/internal-and-cloud-load-balancing) | `string` | `"all"` | no |
| allow_unauthenticated | Allow public access | `bool` | `false` | no |
| vpc_connector | VPC connector name | `string` | `""` | no |
| environment_variables | Environment variables | `map(string)` | `{}` | no |
| secrets | Secrets as env vars | `map(object({name, version}))` | `{}` | no |
| labels | Additional labels | `map(string)` | `{}` | no |

## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| service_name | Cloud Run service name | no |
| service_url | Service URL | no |
| service_id | Fully qualified service ID | no |
| service_location | Deployment region | no |
| latest_revision_name | Latest ready revision name | no |

## Resources Created

- `google_cloud_run_service` - Main Cloud Run service
- `google_cloud_run_service_iam_member` - Public access IAM binding (if `allow_unauthenticated = true`)

## Required Permissions

The Terraform service account must have:
- `run.services.create`
- `run.services.get`
- `run.services.update`
- `run.services.delete`
- `run.services.setIamPolicy` (if `allow_unauthenticated = true`)
- `iam.serviceAccounts.actAs` (to assign service account)

**Recommended Roles:**
- `roles/run.admin`
- `roles/iam.serviceAccountUser`

## Resource Sizing Guidelines

### CPU and Memory

| Service Load | CPU | Memory | Use Case |
|--------------|-----|--------|----------|
| Light | 1 | 512Mi | Simple APIs, low traffic |
| Medium | 1 | 1Gi | Standard APIs, moderate traffic |
| Heavy | 2 | 2Gi | Complex processing, high traffic |
| Very Heavy | 4 | 4Gi | ML inference, heavy computation |

### Scaling

| Traffic Pattern | Min | Max | Concurrency |
|-----------------|-----|-----|-------------|
| Low traffic | 0 | 5 | 80 |
| Steady traffic | 1 | 10 | 80 |
| Spiky traffic | 0 | 50 | 80 |
| High traffic | 3 | 100 | 80 |

### Timeout

| Operation | Timeout |
|-----------|---------|
| Fast APIs | 60s |
| Standard APIs | 300s (default) |
| Long-running | 3600s (max) |

## Service Tiers

Service tier determines required standards per [service-tiering.md](../../../docs/standards/service-tiering.md):

### Tier 0 (Critical)
- Auth, PHI/PII, payments, core platform
- **Requirements:** Full observability, SLOs, HIPAA compliance, threat modeling

### Tier 1 (Important)
- User-facing services without direct PHI/PII storage (e.g., Dave)
- **Requirements:** Observability, runbooks, CI/CD gating

### Tier 2 (Low Risk)
- Internal tools, batch jobs, non-critical services
- **Requirements:** Basic logging, secrets management

## Environment Variables

### Standard Variables

All services should include:

```hcl
environment_variables = {
  ENVIRONMENT      = var.environment  # production/staging/dev
  SERVICE_NAME     = var.service_name
  LOG_LEVEL        = "info"
  PYTHONUNBUFFERED = "1"  # Required for Python
}
```

### Service-Specific Variables

Add service-specific config:

```hcl
environment_variables = {
  # Standard vars
  ENVIRONMENT = "production"
  LOG_LEVEL   = "info"

  # Service-specific
  MAX_RETRIES = "3"
  API_TIMEOUT = "30"
}
```

## Secrets Management

### Best Practices

1. **Use Secret Manager:** Never hardcode secrets in env vars
2. **Reference by name:** Use data sources to avoid storing values in state
3. **Use latest version:** Or pin to specific version in production

### Example: Referencing Existing Secrets

```hcl
# Data source to reference existing secret
data "google_secret_manager_secret_version" "supabase_url" {
  secret  = "supabase-url"
  project = var.project_id
}

# Use in Cloud Run service
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

### Secret Version Pinning

```hcl
# Development - use latest
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
    version = "3"
  }
}
```

## Autoscaling

### Scale to Zero (Cost Optimization)

```hcl
min_instances = 0
max_instances = 10
```

**Pros:** No cost when idle
**Cons:** Cold start latency (~2-5 seconds)

### Warm Instances (Performance)

```hcl
min_instances = 1
max_instances = 10
```

**Pros:** No cold starts, instant response
**Cons:** Always-on cost (~$15-30/month per instance)

### Production Recommendations

- **Tier 0:** `min_instances = 2` (high availability)
- **Tier 1:** `min_instances = 1` (balance cost/performance)
- **Tier 2:** `min_instances = 0` (cost optimization)

## Ingress Configuration

### All (Default)
```hcl
ingress = "all"
```
- Accepts traffic from internet and internal sources
- Use for public APIs

### Internal Only
```hcl
ingress = "internal"
```
- Only accepts traffic from VPC and other Cloud Run services
- Use for private services

### Internal + Load Balancer
```hcl
ingress = "internal-and-cloud-load-balancing"
```
- Accepts traffic from VPC and Cloud Load Balancer
- Use for services behind load balancer

## Testing

### Test Scenario 1: Basic Deployment
1. Deploy service with module
2. Verify service is reachable: `curl https://service-url.run.app/health`
3. Verify correct service account: Check `gcloud run services describe`
4. Verify secrets are accessible from service
5. Verify environment variables are set correctly

### Test Scenario 2: Autoscaling
1. Deploy with `min_instances = 0, max_instances = 5`
2. Observe instance count with no traffic (should be 0)
3. Send burst of traffic: `ab -n 1000 -c 50 https://service-url.run.app/`
4. Observe instance count scale up
5. Wait 15 minutes with no traffic
6. Verify instances scale back to 0

### Test Scenario 3: Resource Limits
1. Deploy with `memory = 512Mi, cpu = 1`
2. Trigger memory-intensive operation
3. Verify service doesn't OOM (check logs)
4. If needed, increase memory and redeploy

### Test Scenario 4: Secret Rotation
1. Deploy service using secret
2. Add new secret version in Secret Manager
3. Redeploy service (new revision)
4. Verify service uses new secret version

## Troubleshooting

### Error: Service Fails to Deploy

**Error:** `The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable`

**Cause:** Container not listening on correct port.

**Fix:** Ensure container listens on port 8080 (default) or override with `container_port`:
```python
# Python/FastAPI
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Error: Permission Denied

**Error:** `Error creating Cloud Run service: googleapi: Error 403: Permission 'run.services.create' denied`

**Cause:** Terraform service account lacks Cloud Run Admin role.

**Fix:**
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:terraform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Error: Service Account Impersonation Failed

**Error:** `Error: failed to impersonate service account`

**Cause:** Terraform service account can't act as the Cloud Run service account.

**Fix:**
```bash
gcloud iam service-accounts add-iam-policy-binding SERVICE_ACCOUNT_EMAIL \
  --member="serviceAccount:terraform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### Error: Secret Not Found

**Error:** Service starts but crashes with "secret not found"

**Cause:** Secret doesn't exist or service account can't access it.

**Fix:**
1. Verify secret exists: `gcloud secrets describe SECRET_NAME`
2. Verify secret has a version: `gcloud secrets versions list SECRET_NAME`
3. Grant access: `gcloud secrets add-iam-policy-binding SECRET_NAME --member="serviceAccount:SA_EMAIL" --role="roles/secretmanager.secretAccessor"`

### Warning: Cold Start Latency

**Issue:** First request after idle takes 3-5 seconds.

**Cause:** Container needs to start (`min_instances = 0`).

**Fix:**
- Set `min_instances = 1` for warm instances
- Optimize container image size
- Use startup probes to warm up faster

## Migration Notes

### Importing Existing Cloud Run Service

```bash
# Import service
terraform import module.dave_service.google_cloud_run_service.main projects/PROJECT_ID/locations/REGION/services/SERVICE_NAME

# Import IAM binding (if public)
terraform import 'module.dave_service.google_cloud_run_service_iam_member.public_access[0]' "projects/PROJECT_ID/locations/REGION/services/SERVICE_NAME roles/run.invoker allUsers"
```

Then run `terraform plan` to verify configuration matches.

## References

- [IaC Standard](../../../docs/standards/iac-terraform.md)
- [Module Standards](../../../docs/standards/iac-module-standards.md)
- [Service Tiering](../../../docs/standards/service-tiering.md)
- [Cloud Run Resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_service)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)
