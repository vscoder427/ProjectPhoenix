# Caching Standard

This standard defines caching patterns and policies.

## Cache Technology

- Hybrid caching: MemoryStore (Redis) + in-memory per instance

## Strategy

- Cache-aside pattern

## TTL Policy

- Per-endpoint TTL defined in service spec
- Stale-while-revalidate where safe

## Invalidation

- TTL + explicit invalidation events
- Versioned cache keys required
