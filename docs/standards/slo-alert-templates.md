# SLO and Alerting Templates

This standard defines SLO templates and alerting thresholds.

## SLO Template

- Availability: 99.9%
- Error rate: < 1% for 5 minutes
- Latency: p95 < 500ms for core endpoints

## Alerting Template

- Page on SLO breach
- Warn on 50% of error budget consumed in 24 hours
- Alert on sustained 5xx spikes (>= 2% for 5 minutes)

> Track SLO reviews and burn-rate trends in the [Service Ownership Checklist](../templates/service-ownership-checklist.md) during monthly health reviews.
