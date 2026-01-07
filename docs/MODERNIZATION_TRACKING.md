# Modernization Tracking Board

This repository now includes a lightweight tracking page that mirrors the phases in
[`docs/MODERNIZATION_SCOPE.md`](MODERNIZATION_SCOPE.md) while giving the team a single
reference for the status of each service as we modernize it.

## Tracking Matrix

| Service | Phase | Current Status | Next Milestone | Release Checklist |
|--------|-------|----------------|----------------|-------------------|
| Dave | Phase 1 – Pathfinder | Golden Service scaffold finalized | Validate Cloud Run cutover | `docs/releases/dave/.../readiness.md` (generated via workflow) |
| CareerIntelligence | Phase 2 – Core Business Logic | TBD | Establish contract tests | `docs/releases/careerintelligence/.../readiness.md` |
| UserOnboarding | Phase 2 – Core Business Logic | TBD | Complete onboarding runbook | `docs/releases/useronboarding/.../readiness.md` |
| AAMeetings | Phase 2 – Core Business Logic | TBD | Migrate scheduling logic | `docs/releases/aameetings/.../readiness.md` |
| CareerTools | Phase 4 – Supporting Services | TBD | Ship resume tooling build | `docs/releases/careertools/.../readiness.md` |
| Marketing | Phase 4 – Supporting Services | TBD | Align acquisition pipelines | `docs/releases/marketing/.../readiness.md` |
| Outreach | Phase 4 – Supporting Services | TBD | Harden messaging canvas | `docs/releases/outreach/.../readiness.md` |
| ContentCreation | Phase 4 – Supporting Services | TBD | Operationalize content platform | `docs/releases/contentcreation/.../readiness.md` |

Fill in the `Current Status` and `Next Milestone` columns as you make progress. Link each row to the release checklist artifact once generated so reviewers can see whether the “Strict Governance Gate” from Section 4 of the scope document has been satisfied.

## GitHub Project + Issue-Based Progress

1. Create a GitHub Project (classic board or new Projects) named `Project Phoenix Modernization` with columns such as _Backlog_, _In Flight_, _Readiness_, and _Done_.
2. Add a card per service that links to the service spec under `docs/services/<service>/`.
3. Whenever a release readiness checklist is generated, update the card or linked issue to show the artifact path and tag (use the automation below to keep the board in sync).

## Automation Hook

The `.github/workflows/release-readiness.yml` workflow now accepts an optional
`tracking_issue` input. When you run the workflow manually (via `workflow_dispatch`), pass
`tracking_issue` in the inputs (for example, the issue number that tracks the service).
The workflow will post a comment on that issue summarizing the checklist location, which keeps
project cards, issues, and auditors aware of every completed release gate.

If you publish a real release (`release.published`), the same artifact is still stored under
`docs/releases/<service>/<YYYY-MM-DD>-<tag>/` and will be referenced by the pre-merge guardrails
workflow before any merge to `main` is allowed.
