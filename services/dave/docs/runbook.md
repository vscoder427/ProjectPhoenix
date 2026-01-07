# Golden Service Runbook

## Deploy Checklist

- [ ] Pull base image and rebuild container
- [ ] Run `make test` and `make contract`
- [ ] Generate release readiness checklist (`make release-checklist`)
- [ ] Upload SBOM and security scans to release artifacts folder
- [ ] Approve release via manual gate (see `release-readiness-tracking.md`)
- [ ] Promote image to staging/prod via Cloud Run

## Rollback Checklist

- [ ] Identify last known good Cloud Run revision
- [ ] Redeploy revision and monitor `/health` and `/ready`
- [ ] Verify SLOs and logs remain stable

## Incident Checklist

- [ ] Declare severity level
- [ ] Notify platform ops and security
- [ ] Capture timeline in `docs/decisions.md`
- [ ] Apply mitigation and update runbook
- [ ] Schedule post-mortem with lessons learned

## Language & Tone

- Reinforce recovery-sensitive language in any runbook updates, incident summaries, or operator notes.
- Reference the shared standard at `../../docs/standards/language-tone.md` for preferred terminology, forbidden language, and tone guidance before publishing updates.
