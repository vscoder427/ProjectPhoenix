# Rate Limiting and Quota Policy

This standard defines rate limits and abuse protection.

## Gateway Limits

- Per-key quotas enforced at API Gateway
- Burst limits configured per service
- Document quotas in the service spec and runbook so attackers/teams know the enforced levels.

## Service Backpressure

- Reject overload with 429
- Use exponential backoff recommendations in docs

## Abuse Handling

- Log and alert on repeated 429/403 patterns
