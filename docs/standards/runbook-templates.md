# Runbook Templates

This standard provides templates for service runbooks.

## Deploy Checklist

- [ ] Build and scan image
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Approve production deploy
- [ ] Verify key endpoints

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
