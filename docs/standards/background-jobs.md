# Background Jobs Standard

This standard defines background job processing and scheduling.

## Job System

- Cloud Tasks only

## Retry Policy

- Standardized retries with backoff
- Dead letter handling required
- Alerting on repeated failures

## Scheduling

- Cloud Workflows for multi-step jobs
- Cloud Scheduler triggers workflows or tasks

## Idempotency

- Required for all background tasks
