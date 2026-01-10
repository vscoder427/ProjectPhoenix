# Testing Database Strategy

**Standard Type:** Enterprise Testing Standard
**Status:** Active
**Created:** 2026-01-09
**Updated:** 2026-01-09
**Applies To:** All Employa microservices (Dave, AAMeetings, UserOnboarding, Outreach, CareerIntelligence, ContentCreation, CareerTools)

## Overview

This standard defines Employa's dual database approach for testing: **local Docker PostgreSQL for development/testing** and **cloud Supabase for production integration validation**.

**Key Principle:** Use the simplest database that validates the behavior being tested, escalating to more complex setups only when necessary.

## Why This Standard Exists

**Real Issues Addressed:**
- PostgreSQL container failures with "role supabase_admin does not exist" when using Supabase image locally
- Seed data files using string IDs instead of UUIDs, causing insertion failures
- Unclear guidance on when to use production migrations vs simplified local migrations
- Confusion about Supabase image vs vanilla PostgreSQL for local testing
- Need for stub auth functions (auth.uid(), is_admin_user()) in local environment

**Without This Standard:**
- Teams waste hours debugging Supabase infrastructure dependencies in local testing
- Inconsistent approaches across services lead to flaky tests
- RLS policy testing skipped due to setup complexity
- Cloud database costs increase from constant integration test runs

## Database Testing Pyramid

```
                    ┌─────────────────────────┐
                    │  Cloud Supabase (Final) │  ← Production auth validation
                    │  @pytest.mark.          │     Real JWT, real RLS edge cases
                    │  integration_auth       │     Pre-deployment only
                    └─────────────────────────┘
                              ▲
                              │
                    ┌─────────────────────────┐
                    │  Local Docker PostgreSQL│  ← Most integration tests
                    │  @pytest.mark.          │     RLS logic, business rules
                    │  integration            │     Fast, offline, repeatable
                    └─────────────────────────┘
                              ▲
                              │
                    ┌─────────────────────────┐
                    │  No Database (Mocked)   │  ← Unit tests
                    │  @pytest.mark.unit      │     Fast (<100ms), isolated
                    │                         │     Test data via factories
                    └─────────────────────────┘
```

## Decision Matrix: Which Database to Use

| Test Scenario | Database Choice | Marker | Why |
|--------------|----------------|--------|-----|
| Unit test (logic only) | None (factories + mocks) | `@pytest.mark.unit` | Fastest, no dependencies |
| Repository CRUD logic | Local Docker PostgreSQL | `@pytest.mark.integration` | Tests real SQL, RLS logic |
| Full conversation flow | Local Docker PostgreSQL | `@pytest.mark.integration` | Tests business logic with real DB |
| RLS policy validation | Local Docker PostgreSQL | `@pytest.mark.integration` | Stub auth sufficient for logic |
| JWT token RLS auth | Cloud Supabase | `@pytest.mark.integration_auth` | Need real JWT auth |
| Edge case: auth race conditions | Cloud Supabase | `@pytest.mark.integration_auth` | Need real auth infrastructure |
| Pre-deployment validation | Cloud Supabase | `@pytest.mark.integration_auth` | Final production parity check |

**Rule of Thumb:** If the test doesn't validate auth edge cases or JWT token handling, use local Docker PostgreSQL.

## Local Docker Database Setup

### Stack Components

Each service should have a `docker-compose.local-db.yml` file with:

1. **PostgreSQL** (standard postgres:15-alpine, NOT Supabase image)
2. **PostgREST** (REST API over PostgreSQL)
3. **Kong** (API gateway)
4. **pgAdmin** (database management UI)
5. **Redis** (if rate limiting needed)
6. **Service container** (your FastAPI/Node.js service)

### File Organization

```
services/dave/
├── docker-compose.local-db.yml          # Local development stack
├── docker/
│   └── local-init.sql                   # Simplified local migration
├── supabase/
│   └── migrations/
│       └── 20260109_initial_schema_v2.sql  # Production migration
└── tests/
    ├── conftest.py                      # Test fixtures
    └── integration/                     # Integration tests
        ├── conftest.py                  # Database fixtures
        └── test_*.py                    # Tests using test_db fixture
```

### Example: docker-compose.local-db.yml

```yaml
version: '3.8'

services:
  # PostgreSQL Database (standard PostgreSQL, NOT Supabase image)
  postgres:
    image: postgres:15-alpine
    container_name: dave-postgres
    environment:
      POSTGRES_DB: dave
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      # Auto-run simplified local schema on startup
      - ./docker/local-init.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # PostgREST (REST API over PostgreSQL)
  postgrest:
    image: postgrest/postgrest:latest
    container_name: dave-postgrest
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      PGRST_DB_URI: postgres://postgres:postgres@postgres:5432/dave
      PGRST_DB_SCHEMA: public
      PGRST_DB_ANON_ROLE: postgres
      PGRST_OPENAPI_SERVER_PROXY_URI: http://localhost:3000
    ports:
      - "3000:3000"

  # pgAdmin (Database Management UI)
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: dave-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

  # Redis (for rate limiting tests)
  redis:
    image: redis:7-alpine
    container_name: dave-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres-data:
```

## Migration Development Patterns

### Production vs Local Migrations

| Aspect | Production Migration | Local Migration |
|--------|---------------------|----------------|
| **Location** | `supabase/migrations/*.sql` | `docker/local-init.sql` |
| **Purpose** | Production schema evolution | Fast local testing |
| **Auth** | Requires Supabase auth (auth.uid() from JWT) | Stub auth functions |
| **Roles** | Requires supabase_admin, authenticated, anon | Standard PostgreSQL roles |
| **Extensions** | Can use Supabase extensions (pg_net, etc.) | Use standard PostgreSQL extensions |
| **Seed Data** | Minimal, production-safe | Can include test-friendly seed data |
| **ID Format** | **MUST use uuid_generate_v4()** | **MUST use uuid_generate_v4()** |

### CRITICAL: UUID Requirements

**❌ WRONG - String IDs (Will Fail):**
```sql
-- This will fail: invalid input syntax for type uuid
INSERT INTO admin_prompts (id, category, name) VALUES
  ('dave-system-001', 'system', 'Dave Core');  -- ❌ String ID
```

**✅ CORRECT - UUID Function:**
```sql
INSERT INTO admin_prompts (id, category, name) VALUES
  (uuid_generate_v4(), 'system', 'Dave Core');  -- ✅ UUID function
```

**Why:** PostgreSQL UUID columns require actual UUIDs, not friendly strings. Always use `uuid_generate_v4()` for ID columns, even in seed data.

### Example: local-init.sql Pattern

```sql
-- =============================================================================
-- Dave Local Database Initialization (Simplified for Testing)
-- =============================================================================
-- Based on: supabase/migrations/20260109_initial_schema_v2.sql
-- Simplified for: Local Docker PostgreSQL (no Supabase auth required)
-- Purpose: Fast local testing without cloud dependencies
--
-- ⚠️  WARNING: LOCAL TESTING ONLY - NOT FOR PRODUCTION
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- SIMPLIFIED AUTH STUB FUNCTIONS (For Local Testing Only)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS auth;

-- Stub auth.uid() function that returns a test user UUID
-- In production: Returns UUID from JWT token
-- In local: Returns UUID from session variable or default test user
CREATE OR REPLACE FUNCTION auth.uid()
RETURNS UUID
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(
        current_setting('auth.current_user_id', true)::uuid,
        '00000000-0000-0000-0000-000000000001'::uuid
    );
$$;

-- Stub is_admin_user() function
-- In production: Checks JWT claims
-- In local: Checks session variable or defaults to false
CREATE OR REPLACE FUNCTION is_admin_user()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(
        current_setting('auth.is_admin', true)::boolean,
        false
    );
$$;

-- =============================================================================
-- SCHEMA (Identical to Production)
-- =============================================================================

CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;

-- RLS Policies (using stub auth functions)
CREATE POLICY "Users can view own conversations"
    ON ai_conversations FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can insert own conversations"
    ON ai_conversations FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Service role bypass (for backend operations)
CREATE POLICY "Service role can manage all conversations"
    ON ai_conversations
    USING (is_admin_user());

-- [Additional tables and policies...]

-- =============================================================================
-- SEED DATA (Test-Friendly)
-- =============================================================================

-- Insert test user conversations (optional)
INSERT INTO ai_conversations (id, user_id, title, status) VALUES
  (uuid_generate_v4(), '00000000-0000-0000-0000-000000000001', 'Test Conversation', 'active');

-- ⚠️  IMPORTANT: Use uuid_generate_v4() for ALL ID columns!
```

### When to Use Supabase Image vs Standard PostgreSQL

| Use Case | Image | Why |
|----------|-------|-----|
| **Local testing** | `postgres:15-alpine` | Simpler, no Supabase role dependencies |
| **Testing Supabase extensions** | `supabase/postgres:15.x.x.xxx` | Need pg_net, pg_cron, etc. |
| **Testing auth edge cases** | Cloud Supabase | Need real JWT auth |
| **Production** | Supabase Cloud | Managed service |

**Recommendation:** Default to `postgres:15-alpine` for local testing. Switch to Supabase image only if you need Supabase-specific extensions.

## Test Isolation Strategies

### Strategy 1: Unique Test IDs (Recommended)

Use predictable test user IDs that can be cleaned up:

```python
# conftest.py
TEST_USER_PATTERN = "00000000-0000-0000-0000-%"

@pytest.fixture
async def test_db(test_db_url, test_db_service_key):
    client = create_client(test_db_url, test_db_service_key)

    yield client

    # Cleanup: Delete test data by pattern
    await asyncio.to_thread(
        client.table("ai_messages")
        .delete()
        .like("conversation_id", TEST_USER_PATTERN)
        .execute
    )

    await asyncio.to_thread(
        client.table("ai_conversations")
        .delete()
        .like("user_id", TEST_USER_PATTERN)
        .execute
    )
```

### Strategy 2: Transaction Rollback (Advanced)

For PostgreSQL-native tests (not Supabase client):

```python
@pytest.fixture
async def db_transaction():
    conn = await asyncpg.connect("postgresql://localhost/dave")
    tx = conn.transaction()
    await tx.start()

    yield conn

    await tx.rollback()  # Rollback all test changes
    await conn.close()
```

### Strategy 3: Separate Test Schema

For complex scenarios requiring full isolation:

```sql
-- Create test schema
CREATE SCHEMA IF NOT EXISTS test;

-- Copy tables to test schema
CREATE TABLE test.ai_conversations (LIKE public.ai_conversations INCLUDING ALL);
```

## RLS Policy Testing

### Local RLS Testing Pattern

Local testing validates RLS **logic** using stub auth functions:

```python
@pytest.mark.integration
async def test_rls_policy_blocks_other_users(test_db):
    """
    Verify RLS policies prevent accessing other users' data.

    Uses stub auth functions (local testing).
    """
    user_a_id = "00000000-0000-0000-0000-000000000001"
    user_b_id = "00000000-0000-0000-0000-000000000002"

    # Create conversation for User A
    conv_a = ConversationFactory.create(user_id=user_a_id)
    result_a = test_db.table("ai_conversations").insert(conv_a).execute()

    # User A can see their conversation
    user_a_convs = (
        test_db.table("ai_conversations")
        .select("*")
        .eq("user_id", user_a_id)
        .execute()
    )
    assert len(user_a_convs.data) >= 1

    # User A CANNOT see User B's conversations
    # (RLS enforced at PostgreSQL level using stub auth.uid())
```

### Cloud RLS Testing Pattern

Cloud testing validates real JWT auth integration:

```python
@pytest.mark.integration_auth  # Requires cloud Supabase
async def test_rls_with_real_jwt_tokens(cloud_supabase_client):
    """
    Verify RLS policies work with real JWT tokens.

    Tests edge cases like:
    - Expired tokens properly denied
    - Token refresh flows
    - Role claim validation
    """
    # Use real Supabase auth
    session = await cloud_supabase_client.auth.sign_in_with_password({
        "email": "test@example.com",
        "password": "test-password"
    })

    # Query with JWT authentication
    result = cloud_supabase_client.table("ai_conversations").select("*").execute()

    # RLS enforces access based on JWT claims
```

## Test Markers and Organization

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests with local database (Docker)
    integration_auth: Integration tests requiring cloud Supabase (real auth)
    slow: Slow-running tests (>1 second)
    security: Security-focused tests (injection, auth, IDOR)
    contract: Contract tests against OpenAPI spec
```

### Test Execution Examples

```bash
# Fast unit tests (no database)
pytest tests/unit/ -m unit

# Integration tests with local database
pytest tests/integration/ -m integration

# Cloud auth integration tests (requires Supabase)
pytest tests/integration/ -m integration_auth

# All tests EXCEPT cloud auth
pytest tests/ -m "not integration_auth"

# Only security tests
pytest tests/ -m security
```

## Performance Optimization

### Connection Pooling

```python
# conftest.py - Session-scoped database connection
@pytest.fixture(scope="session")
def db_pool():
    """
    Session-scoped database connection pool.

    Reuses connections across tests for performance.
    """
    pool = create_pool(
        "postgresql://postgres:postgres@localhost:5432/dave",
        min_size=2,
        max_size=10
    )

    yield pool

    pool.close()
```

### Parallel Test Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto  # Auto-detect CPU count

# Run integration tests in parallel
pytest tests/integration/ -m integration -n 4
```

### Test Data Caching

```python
# Cache expensive test data setup
@pytest.fixture(scope="session")
def seed_knowledge_base(db_pool):
    """
    Seed knowledge base once per session.

    Expensive operation (embeddings, indexing) cached.
    """
    # Setup expensive data
    # ...

    yield seed_data

    # Cleanup once at end
```

## Common Pitfalls and Solutions

### Pitfall 1: Using Supabase Image Locally

**Problem:** `role "supabase_admin" does not exist`

**Solution:** Use standard `postgres:15-alpine` image with stub auth functions.

### Pitfall 2: String IDs in Seed Data

**Problem:** `invalid input syntax for type uuid: "dave-system-001"`

**Solution:** Always use `uuid_generate_v4()` for UUID columns.

### Pitfall 3: Forgetting to Clean Test Data

**Problem:** Tests fail on second run due to duplicate data.

**Solution:** Use fixture cleanup or transaction rollback patterns.

### Pitfall 4: Testing Auth with Local Database Only

**Problem:** RLS auth edge cases not validated before deployment.

**Solution:** Mark auth tests with `@pytest.mark.integration_auth` and run against cloud Supabase in CI/CD.

### Pitfall 5: Slow Integration Tests

**Problem:** Integration tests take >10s each.

**Solution:**
- Use connection pooling
- Run tests in parallel (`pytest -n auto`)
- Cache expensive setup (session-scoped fixtures)

## CI/CD Integration

### GitHub Actions Workflow Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/unit/ -m unit --cov

  integration-tests-local:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: psql -U postgres -f docker/local-init.sql
      - run: pytest tests/integration/ -m integration

  integration-tests-cloud:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/integration/ -m integration_auth
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
```

## Migration Testing Checklist

Before deploying a database migration:

- [ ] Migration runs successfully on local PostgreSQL
- [ ] Migration includes RLS policies for all new tables
- [ ] RLS logic tested with stub auth (local)
- [ ] Integration tests pass with local database
- [ ] Migration runs successfully on cloud Supabase
- [ ] RLS auth tested with real JWT (cloud)
- [ ] Rollback script tested
- [ ] Performance impact measured (on staging)

## References

- [db-isolation-migrations.md](db-isolation-migrations.md) - Database isolation standard
- [database-rls-policies.md](database-rls-policies.md) - RLS policy requirements
- [testing-rls-policies.md](testing-rls-policies.md) - RLS testing patterns
- [PostgreSQL Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase Local Development](https://supabase.com/docs/guides/local-development)

## Changelog

### 2026-01-09 - Initial Version
- Defined dual database strategy (local Docker + cloud Supabase)
- Documented migration development patterns
- Added UUID requirements and common pitfalls
- Created stub auth function patterns
- Established test markers and decision matrix
