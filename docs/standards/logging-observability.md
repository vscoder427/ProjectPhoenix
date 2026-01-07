# Logging and Observability Standard

This standard defines required logging, metrics, tracing, and alerting across Employa microservices.

## Logging

- Structured JSON logs required
- Correlation IDs in every log entry
- Redaction policy for sensitive data

## Metrics

- Full RED/USE metrics (rate, errors, duration, utilization, saturation, errors)
- Business KPIs tracked per service
- Add an mTLS health dashboard that surfaces SPIRE certificate issuance rates, Envoy handshake latencies, and SPIFFE identity errors; link to this dashboard from the service runbook and release readiness checklist (see [SPIRE/Envoy mTLS Operations](cloudrun-mtls-ops.md)).

## Tracing

- End-to-end OpenTelemetry tracing required
- Sampling policy documented per service

## Error Reporting

- GCL Error Reporting enabled
- SLO-based alerts with paging

## Log Retention

- Retention policy by data class
- Legal hold supported where required
