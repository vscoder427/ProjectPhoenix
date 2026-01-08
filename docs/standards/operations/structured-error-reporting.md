# Structured Error Reporting Standard

This standard defines the schema, logging requirements, and telemetry integrations for every service that reports failures.

## Failure Payload Schema

Every non-2xx response and logged exception should emit the following fields (JSON or log attributes):

| Field | Type | Description |
| --- | --- | --- |
| `error.code` | string | Unique identifier (`SERVICE.DOMAIN.CODE`) that maps to the [Error Codes Registry](../error-codes-registry.md). |
| `error.message` | string | Human-friendly summary suitable for dashboards. |
| `error.details` | object | Optional key/value map for field-level context, validation errors, or exception data. |
| `service.name` | string | Full service name (e.g., `dave`) for correlation. |
| `service.tier` | string | Tier from the Service Tiering standard (Tier 0/1/2). |
| `request.id` | string | Correlation ID from `X-Request-Id` header, generated if missing. |
| `trace.id` | string | OpenTelemetry trace ID if available. |
| `user.id` | string | Authenticated user (if any) subject to PII rules. |
| `tenant.id` | string | Tenant or business unit owning the request. |
| `severity` | string | One of `warning`, `error`, or `critical`. |
| `timestamp` | string | ISO8601 event time (UTC). |

Logs must never include PHI, PII, or secrets other than identifiers explicitly allowed by the [Data Classification Standard](../compliance/data-classification-retention.md).

## Logging and Telemetry

- Use structured JSON logs for errors with the above schema plus `component` and `span.name` when available.
- Emit error spans to OpenTelemetry with status `ERROR`/`UNSET` and attributes matching the schema.
- Push errors to Google Cloud Logging, Error Reporting, and any downstream alerting tooling (PagerDuty, SLO dashboards) that consume severity.
- Tag error logs with `service.tier` and `deployment.environment` so dashboards can filter by criticality.

## Reporting and Alerting

- Every error incident that consumes >10% of the error budget or triggers a severity `critical` alert must:
  1. Create an entry in the service runbook incident checklist.
  2. Reference the error code in the release readiness checklist so it is visible before production releases.
  3. Link the error to `docs/standards/operations/logging-observability.md` dashboards and `docs/standards/compliance/security-review-checklist.md` audits where needed.

## Error Monitoring Checklist

- [ ] `error.code` entry exists in `docs/standards/error-codes-registry.md`.
- [ ] Logs include the structured schema above and omit sensitive data.
- [ ] Alerts for severity `critical` map back to runbook steps.
- [ ] Error Reporting dashboards tie back to traces and SLO burn rates.

Complying services make errors comparable across the fleet and give operators the necessary context to resolve incidents quickly.
