# API Gateway Patterns Standard

**Status:** Active
**Version:** 1.0
**Last Updated:** 2026-01-16
**Applies To:** Public-facing Employa services on Cloud Run
**Reference Implementation:** [Dave service](../../../Dave/)

---

## Overview

Google API Gateway provides a managed proxy layer for Cloud Run services. This standard defines when and how to use API Gateway for public-facing services.

---

## When to Use API Gateway

### Required (Standard Policy)

Use API Gateway for **all public-facing services** that need unauthenticated access:

| Scenario | Use API Gateway |
|----------|-----------------|
| Public API (chat, webhooks) | Yes |
| Internal service-to-service | No |
| Admin endpoints only | No |
| Org policy blocks `allUsers` | Yes (mandatory) |

### Why API Gateway?

1. **Org Policy Compliance:** GCP organization policies often block `allUsers` IAM on Cloud Run
2. **Rate Limiting:** Built-in rate limiting and quota management
3. **Monitoring:** Unified API metrics and logging
4. **Security:** JWT validation at the gateway level

---

## Architecture

```
                    Internet
                        │
                        ▼
              ┌─────────────────┐
              │  API Gateway    │ ← Public URL
              │  (Managed)      │ ← Rate limiting
              │  service-gw-*   │ ← JWT validation
              └────────┬────────┘
                       │ IAM-authenticated call
                       ▼
              ┌─────────────────┐
              │   Cloud Run     │ ← Private (require auth)
              │ (Authenticated) │ ← Business logic
              │ service-prod-*  │ ← Actual API
              └────────┬────────┘
                       │ VPC Connector
                       ▼
              ┌─────────────────┐
              │   Cloud SQL     │
              │ (Private IP)    │
              └─────────────────┘
```

---

## Configuration

### OpenAPI Specification

Create `openapi-gateway.yaml` in your service:

```yaml
swagger: "2.0"
info:
  title: Service API Gateway
  version: 1.0.0
schemes:
  - https
produces:
  - application/json

# Backend configuration
x-google-backend:
  address: https://SERVICE-NAME-HASH.REGION.run.app
  deadline: 60.0
  jwt_audience: https://SERVICE-NAME-HASH.REGION.run.app

# Define all public paths
paths:
  /health:
    get:
      summary: Health check
      operationId: health
      responses:
        '200':
          description: Service is healthy

  /api/v1/chat/message:
    post:
      summary: Send a message
      operationId: chat_message
      responses:
        '200':
          description: Response from service
```

### Key Configuration Options

| Field | Description | Example |
|-------|-------------|---------|
| `x-google-backend.address` | Cloud Run service URL | `https://dave-service-xxx.run.app` |
| `x-google-backend.deadline` | Request timeout (seconds) | `60.0` |
| `x-google-backend.jwt_audience` | JWT audience for IAM auth | Same as address |

### Service Account

Create a dedicated service account for the gateway:

```bash
# Create service account
gcloud iam service-accounts create SERVICE-api-gateway \
  --display-name="SERVICE API Gateway"

# Grant Cloud Run invoker role
gcloud run services add-iam-policy-binding SERVICE-NAME \
  --member="serviceAccount:SERVICE-api-gateway@PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## Deployment

### Create Gateway

```bash
# Create API config
gcloud api-gateway api-configs create SERVICE-config-v1 \
  --api=SERVICE-api \
  --openapi-spec=openapi-gateway.yaml \
  --backend-auth-service-account=SERVICE-api-gateway@PROJECT.iam.gserviceaccount.com

# Create gateway
gcloud api-gateway gateways create SERVICE-gateway \
  --api=SERVICE-api \
  --api-config=SERVICE-config-v1 \
  --location=us-central1
```

### Get Gateway URL

```bash
gcloud api-gateway gateways describe SERVICE-gateway \
  --location=us-central1 \
  --format="value(defaultHostname)"
```

Result: `SERVICE-gateway-HASH.uc.gateway.dev`

---

## CI/CD Integration

### Workflow Addition

Add to your release workflow:

```yaml
- name: Verify deployment health
  run: |
    GATEWAY_URL="https://SERVICE-gateway-HASH.uc.gateway.dev"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/health")

    if [ "$HTTP_CODE" = "200" ]; then
      echo "Health check passed"
    else
      echo "Health check failed (HTTP $HTTP_CODE)"
      exit 1
    fi
```

### Health Check URLs

| Environment | URL to Check |
|-------------|--------------|
| Development | Direct Cloud Run URL (with auth) |
| Staging | API Gateway URL |
| Production | API Gateway URL |

---

## Security Considerations

### Authentication Layers

1. **API Gateway:** Validates incoming requests (optional API key, rate limits)
2. **Cloud Run IAM:** Gateway service account authenticates to Cloud Run
3. **Application Auth:** X-API-Key or Bearer token for application-level auth

### Do NOT Expose Directly

Never add `allUsers` IAM binding to Cloud Run services:

```yaml
# ❌ WRONG - Bypasses API Gateway
gcloud run services add-iam-policy-binding SERVICE \
  --member="allUsers" \
  --role="roles/run.invoker"

# ✅ CORRECT - Only gateway service account
gcloud run services add-iam-policy-binding SERVICE \
  --member="serviceAccount:SERVICE-api-gateway@PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## Naming Convention

| Resource | Pattern | Example |
|----------|---------|---------|
| API | `{service}-api` | `dave-api` |
| Config | `{service}-config-v{N}` | `dave-config-v1` |
| Gateway | `{service}-gateway` | `dave-gateway` |
| Service Account | `{service}-api-gateway` | `dave-api-gateway` |

---

## Cost Considerations

API Gateway pricing (as of 2026):
- First 2M calls/month: Free
- Additional: $3 per million calls

For most Employa services, this is negligible.

---

## Troubleshooting

### 403 Forbidden from Gateway

**Cause:** Service account doesn't have `roles/run.invoker`

**Fix:**
```bash
gcloud run services add-iam-policy-binding SERVICE-NAME \
  --member="serviceAccount:SERVICE-api-gateway@PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 503 Service Unavailable

**Cause:** Cloud Run service not responding

**Check:**
```bash
# Direct health check (requires auth)
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://SERVICE-HASH.run.app/health
```

### Config Update Not Reflected

**Cause:** Need to create new config version

**Fix:**
```bash
# Create new config
gcloud api-gateway api-configs create SERVICE-config-v2 \
  --api=SERVICE-api \
  --openapi-spec=openapi-gateway.yaml \
  --backend-auth-service-account=...

# Update gateway to use new config
gcloud api-gateway gateways update SERVICE-gateway \
  --location=us-central1 \
  --api-config=SERVICE-config-v2
```

---

## Reference Implementation

Dave service demonstrates this pattern:

- **Gateway URL:** `https://dave-gateway-e0p3s1hs.uc.gateway.dev`
- **Service Account:** `dave-api-gateway@employa-prod.iam.gserviceaccount.com`
- **Config:** [Dave/api/openapi-gateway.yaml](../../../Dave/api/openapi-gateway.yaml)
- **Workflow:** [Dave/.github/workflows/release.yml](../../../Dave/.github/workflows/release.yml)

---

## Related Standards

- [cloud-sql-patterns.md](cloud-sql-patterns.md) - Database connectivity
- [ci-cd-deployment.md](ci-cd-deployment.md) - Deployment workflow
- [container-cloudrun.md](container-cloudrun.md) - Cloud Run configuration

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | Claude Opus 4.5 | Initial standard based on Dave deployment |
