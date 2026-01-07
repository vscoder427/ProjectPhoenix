# Runbook Templates

This standard provides templates for service runbooks.

## Deploy Checklist

- [ ] Build and scan image
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Approve production deploy
- [ ] Verify key endpoints
- Release deploy checklist should be completed as part of the [Release Readiness Checklist](release-readiness.md).

## Rollback Checklist

- [ ] Identify last known good revision
- [ ] Roll back Cloud Run revision
- [ ] Verify health and error rates

## Incident Checklist

- [ ] Declare severity level
- [ ] Notify stakeholders
- [ ] Capture timeline
- [ ] Apply mitigation
- [ ] Post-mortem scheduled
