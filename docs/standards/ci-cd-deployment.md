# CI/CD and Deployment Standard

This standard defines CI/CD pipelines, environments, and deployment practices for all Employa microservices.

## CI Workflow

- Lint + tests + security scans (SAST/SCA)
- Container scanning and IaC scanning required
- All checks required before merge

## Deployment Triggers

- Auto-deploy to dev and staging on merge to `main`
- Manual approval required for prod deploys

## Environments

- Dev, Staging, and Prod environments required
- Shared image promotion pipeline across environments

## Rollout Strategy

- Progressive canary rollouts with automatic rollback on SLO breach

## Artifact Strategy

- Build once, promote the same image to all environments
- Signed container images required

## Release Management

- Release notes required for every production deploy
- Post-deploy verification checklist required
