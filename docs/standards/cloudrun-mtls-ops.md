# SPIRE/Envoy mTLS Operations

This document captures observability and runbook guidance for the SPIFFE/SPIRE+Envoy solution that secures Cloud Run-to-Cloud Run communication.

## Key Components

- **SPIRE server** hosted in the platform project (GCE/VM or GKE) acts as the CA and issues short-lived X.509 certificates for each service.
- **SPIRE agents** run alongside Cloud Run sidecars (Envoy) via multi-container deployments to fetch certificates scoped to the `spiffe://employa/services/<service>` identity.
- **Envoy sidecar** uses SDS to fetch certificates and mTLS configuration. It validates peer SPIFFE IDs and enforces circuit breaking/backpressure.

## Deployment

- SPIRE server is deployed via Terraform (see [IaC standard](iac-terraform.md)) with HA across two zones.
- Service deployments include a second container running the SPIRE agent and configuration to mount the trust bundle.
- Envoy listens on port 8443 for inbound service-to-service traffic and forwards to the application after policy checks.
- Add health checks for Envoy endpoints and SPIRE agent status in Cloud Monitoring dashboards.

## Operational Playbooks

- **Certificate rotation:** SPIRE rotates certs automatically every 24 hours; configure alerts if rotation requests fail >2 times. Use `scripts/rotate-spire-keys.ps1` (create/hook) to force rotation if needed.
- **Trust updates:** When issuing new trust bundles, update Envoy configs via config map reload (if using GKE) or container restart with new `spiffe-bundle.pem`.
- **Failure recovery:** If SPIRE agent loses connectivity, Envoy should route to a safe fallback loop (reject traffic). Document fallback steps in the runbook: (1) restart Envoy container, (2) check SPIRE agent logs (`/run/spire/agent.log`), (3) redeploy via Cloud Run.

## Monitoring

- Export SPIRE metrics (certificate issuance, failures) to Cloud Monitoring and alert if error rate exceeds 1% over 10 minutes.
- Track Envoy mTLS handshake latencies to ensure <50ms overhead per request.

## Incident Response

- Note SPIRE and Envoy incidents in the [Runbook Templates](runbook-templates.md) incident checklist.
- Include mTLS status in the release readiness checklist for each Tier 0 service deployment so reviewers confirm identity is healthy.
