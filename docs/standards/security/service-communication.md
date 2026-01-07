# Service-to-Service Communication Standard

This standard defines how services call each other.

## Protocol

- REST over HTTPS is the default
- gRPC allowed only when latency/throughput requires it

## Identity and Transport

- All outbound calls go through the Envoy sidecar for mTLS
- Service identity is verified via SPIFFE IDs

## Timeouts and Retries

- Explicit timeouts on all outbound calls
- Retries with jitter and circuit breakers

## Idempotency

- Required for all write operations across services
