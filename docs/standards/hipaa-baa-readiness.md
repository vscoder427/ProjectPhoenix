# HIPAA BAA Readiness Checklist

Use this checklist to prepare for HIPAA compliance and verify vendor readiness.

## Vendor Inventory

- [ ] List all vendors that store or process PHI
- [ ] Confirm which services transmit PHI
- [ ] Identify data flows involving PHI

## Required BAAs

- [ ] Google Cloud (Cloud Run, Secret Manager, Logging)
- [ ] Supabase (Postgres, Storage, Auth)
- [ ] Email/SMS providers (if PHI passes through)
- [ ] Analytics/Monitoring vendors (if PHI passes through)
- [ ] Any AI/LLM providers (if PHI passes through)

## Data Flow Validation

- [ ] PHI does not transit through non-BAA systems
- [ ] PHI is encrypted in transit and at rest
- [ ] PHI is minimized in logs and analytics

## Access Controls

- [ ] Per-service least-privilege access to PHI
- [ ] Role-based access for staff
- [ ] Regular access reviews

## Audit and Monitoring

- [ ] Centralized audit logs for PHI access
- [ ] Alerting on anomalous access patterns
- [ ] Log retention policy aligned with HIPAA requirements

## Incident Response

- [ ] Breach response plan documented
- [ ] Notification timelines documented
- [ ] Tabletop exercises scheduled
