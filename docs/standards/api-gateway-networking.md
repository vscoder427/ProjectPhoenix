# API Gateway and Networking Standard

This standard defines ingress, routing, and network security for services.

## API Gateway

- GCP API Gateway is required for public ingress
- JWT validation enforced at the gateway
- Per-key quotas and rate limits enforced at the gateway

## Service Authentication

- Services enforce auth in middleware (defense in depth)

## mTLS

- mTLS required for all service-to-service traffic

## Network Policies

- Services are private by default
- Public endpoints exposed only via the gateway
