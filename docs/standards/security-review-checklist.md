# Security Review Checklist

Use this checklist before approving a service build or major change.

- [ ] Threat model completed
- [ ] Auth enforced at gateway and service middleware
- [ ] mTLS enabled for service-to-service calls
- [ ] PHI/PII handling reviewed and logged appropriately
- [ ] Secrets only in Secret Manager
- [ ] SAST/SCA/container scans pass
- [ ] SBOM generated and stored
- [ ] Logging redaction verified
- [ ] Incident response and runbook updated
