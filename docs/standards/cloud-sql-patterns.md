# Cloud SQL Patterns Standard

**Status:** Active
**Version:** 1.1
**Last Updated:** 2026-01-15
**Applies To:** All Employa services using Cloud SQL
**Reference Implementation:** [Dave service](../../../Dave/api/app/)

---

## Overview

This standard defines patterns for connecting to and using Cloud SQL PostgreSQL from Cloud Run services. These patterns replace the previous Supabase-based database access.

---

## Architecture

```
┌─────────────────────┐
│  Cloud Run Service  │
│  (FastAPI + asyncpg)│
└──────────┬──────────┘
           │ Unix Socket (via Cloud SQL Proxy sidecar)
           │ Private IP (via VPC Connector)
           ▼
┌─────────────────────┐
│  Cloud SQL          │
│  PostgreSQL 15      │
│  (Private IP only)  │
└─────────────────────┘
```

**Key Points:**
- No public IP on Cloud SQL instances
- All access via VPC or Cloud SQL Proxy
- IAM authentication preferred over passwords

---

## Connection Patterns

### Production (Cloud Run)

Cloud Run services connect via Unix socket using the Cloud SQL Proxy sidecar:

```python
# DSN format for Cloud Run
DAVE_DB_DSN=postgresql://dave_service:PASSWORD@/dave?host=/cloudsql/employa-prod:us-central1:employa-dave
```

**Cloud Run Configuration:**
```yaml
# cloudbuild.yaml or gcloud run deploy
--add-cloudsql-instances=employa-prod:us-central1:employa-dave
--vpc-connector=employa-connector
--vpc-egress=private-ranges-only
```

### Local Development

Developers connect via Cloud SQL Proxy running locally:

```bash
# Terminal 1: Start Cloud SQL Proxy
cloud-sql-proxy employa-prod:us-central1:employa-dave --port=5432

# Terminal 2: Run service
DAVE_DB_DSN=postgresql://dave_service:PASSWORD@localhost:5432/dave \
uvicorn app.main:app --reload
```

---

## Connection Pool Pattern

### Implementation

```python
# app/clients/database.py
import asyncpg
from functools import lru_cache
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages asyncpg connection pools with circuit breaker pattern."""

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_state = "closed"

    async def get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await self._create_pool()
        return self._pool

    async def _create_pool(self) -> asyncpg.Pool:
        """Create asyncpg connection pool with settings."""
        return await asyncpg.create_pool(
            dsn=settings.dave_db_dsn,
            min_size=settings.db_pool_min_size,  # Default: 5
            max_size=settings.db_pool_max_size,  # Default: 15
            command_timeout=settings.db_query_timeout,  # Default: 60.0
            server_settings={
                "application_name": "dave-service",
            },
        )

    async def health_check(self) -> dict:
        """Return pool health status for /health/ready endpoint."""
        try:
            pool = await self.get_pool()
            # Test query
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            return {
                "dave_db": {
                    "status": "healthy",
                    "pool_size": pool.get_size(),
                    "idle_connections": pool.get_idle_size(),
                    "circuit_breaker_state": self._circuit_breaker_state,
                }
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "dave_db": {
                    "status": "unhealthy",
                    "error": str(e),
                    "circuit_breaker_state": self._circuit_breaker_state,
                }
            }

    async def close(self):
        """Close connection pool on shutdown."""
        if self._pool:
            await self._pool.close()
            self._pool = None


@lru_cache(maxsize=1)
def get_db_manager() -> DatabaseManager:
    """Get singleton DatabaseManager instance."""
    return DatabaseManager()
```

### Configuration

```python
# app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Cloud SQL connection
    dave_db_dsn: str  # From Secret Manager in production

    # Pool settings
    db_pool_min_size: int = 5
    db_pool_max_size: int = 15
    db_pool_timeout: float = 30.0
    db_query_timeout: float = 60.0

    class Config:
        env_file = ".env"
```

---

## Repository Pattern

### Base Repository

```python
# app/repositories/base.py
from typing import TypeVar, Generic, Optional
from app.clients.database import get_db_manager

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common database operations."""

    def __init__(self):
        self.db_manager = get_db_manager()

    async def execute(self, query: str, *args) -> str:
        """Execute a query (INSERT, UPDATE, DELETE)."""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch_one(self, query: str, *args) -> Optional[dict]:
        """Fetch a single row."""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args) -> list[dict]:
        """Fetch multiple rows."""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetch_val(self, query: str, *args):
        """Fetch a single value."""
        pool = await self.db_manager.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)
```

### User-Scoped Repository

```python
# app/repositories/conversation.py
from app.repositories.base import BaseRepository
from typing import Optional
import uuid


class ConversationRepository(BaseRepository):
    """Repository for user conversations with application-layer authorization."""

    async def get_by_id(self, conversation_id: str, user_id: str) -> Optional[dict]:
        """
        Get conversation by ID.

        Application-layer authorization: Only returns if user_id matches.
        """
        query = """
            SELECT id, user_id, title, created_at, updated_at
            FROM ai_conversations
            WHERE id = $1 AND user_id = $2
        """
        return await self.fetch_one(query, conversation_id, user_id)

    async def list_for_user(self, user_id: str, limit: int = 50) -> list[dict]:
        """List conversations for a user."""
        query = """
            SELECT id, user_id, title, created_at, updated_at
            FROM ai_conversations
            WHERE user_id = $1
            ORDER BY updated_at DESC
            LIMIT $2
        """
        return await self.fetch_all(query, user_id, limit)

    async def create(self, user_id: str, title: str = "New Conversation") -> dict:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        query = """
            INSERT INTO ai_conversations (id, user_id, title)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, title, created_at, updated_at
        """
        return await self.fetch_one(query, conversation_id, user_id, title)
```

---

## Health Check Pattern

```python
# app/api/v1/endpoints/health.py
from fastapi import APIRouter
from app.clients.database import get_db_manager

router = APIRouter()


@router.get("/ready")
async def readiness():
    """
    Readiness probe for Cloud Run.

    Checks database connectivity via asyncpg pool.
    """
    checks = {}
    overall_status = "ready"

    # Check Cloud SQL
    try:
        db_manager = get_db_manager()
        db_health = await db_manager.health_check()

        dave_db = db_health.get("dave_db", {})
        if dave_db.get("status") == "healthy":
            checks["database"] = "ok"
            checks["database_details"] = {
                "pool_size": dave_db.get("pool_size"),
                "idle_connections": dave_db.get("idle_connections"),
                "circuit_breaker": dave_db.get("circuit_breaker_state"),
            }
        else:
            checks["database"] = f"error: {dave_db.get('error', 'unknown')}"
            overall_status = "not_ready"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "not_ready"

    return {
        "status": overall_status,
        "checks": checks,
    }
```

---

## Migration Pattern

### File Structure

```
migrations/
├── 001_initial_schema.sql
├── 002_knowledge_base.sql
└── README.md
```

### Migration File Template

```sql
-- Migration: 00X_description.sql
-- Issue: #XX
-- Date: YYYY-MM-DD
-- Author: Name

-- Description: Brief description of what this migration does

BEGIN;

-- Create tables
CREATE TABLE IF NOT EXISTS my_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    content TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_my_table_user_id ON my_table(user_id);
CREATE INDEX IF NOT EXISTS idx_my_table_created_at ON my_table(created_at DESC);

-- Add comments
COMMENT ON TABLE my_table IS 'Description of what this table stores';

COMMIT;
```

### Timestamp Trigger Pattern

All tables with `updated_at` columns MUST have a trigger to auto-update on modification:

```sql
-- Create reusable trigger function (once per database)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to each table
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON my_table
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Best Practice:** Create the trigger function in your first migration (`001_initial_schema.sql`), then apply triggers to each table as they're created.

**Complete Table Template with Trigger:**

```sql
-- Create table
CREATE TABLE IF NOT EXISTS people.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create trigger for updated_at
CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON people.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Applying Migrations

```bash
# Upload to GCS (Cloud SQL can import from GCS)
gsutil cp migrations/00X_name.sql gs://employa-prod-terraform-state/migrations/

# Import to Cloud SQL
gcloud sql import sql employa-dave \
  gs://employa-prod-terraform-state/migrations/00X_name.sql \
  --database=dave

# Note: Cloud SQL service account needs roles/storage.objectViewer on the bucket
```

---

## Schema Design Patterns

### JSONB Fields

Use JSONB for flexible, semi-structured data that may evolve without schema migrations:

**When to Use JSONB:**
- User preferences (notification settings, UI preferences)
- Flexible metadata (tags, custom attributes)
- Permission sets that vary by role
- Skills/capabilities lists
- Configuration that varies by entity type

**When NOT to Use JSONB:**
- Data you need to query frequently (use normalized columns + indexes)
- Foreign key relationships
- Data with strict validation requirements
- Audit-critical fields

**JSONB Column Template:**

```sql
CREATE TABLE IF NOT EXISTS people.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES people.users(id) ON DELETE CASCADE,

    -- Structured columns for queryable data
    recovery_stage TEXT CHECK (recovery_stage IN ('early', 'intermediate', 'advanced', 'long-term')),
    years_in_recovery INTEGER,

    -- JSONB for flexible data
    skills JSONB DEFAULT '[]'::jsonb,
    preferences JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- GIN index for JSONB containment queries (@>, ?)
CREATE INDEX IF NOT EXISTS idx_user_profiles_skills ON people.user_profiles USING GIN (skills);

COMMENT ON COLUMN people.user_profiles.skills IS 'Array of skill objects: [{"name": "Python", "level": "intermediate"}]';
COMMENT ON COLUMN people.user_profiles.preferences IS 'User preferences: {"notifications": {"email": true, "sms": false}}';
```

**Querying JSONB:**

```sql
-- Find users with specific skill
SELECT * FROM people.user_profiles
WHERE skills @> '[{"name": "Python"}]'::jsonb;

-- Extract nested value
SELECT preferences->>'theme' as theme FROM people.user_profiles;

-- Check if key exists
SELECT * FROM people.user_profiles WHERE preferences ? 'notifications';
```

**Python/Pydantic Integration:**

```python
from pydantic import BaseModel
from typing import Optional

class UserPreferences(BaseModel):
    notifications: dict = {"email": True, "sms": False}
    theme: str = "light"
    language: str = "en"

class UserProfile(BaseModel):
    id: str
    user_id: str
    skills: list[dict] = []
    preferences: UserPreferences = UserPreferences()
```

### Schema Prefix Pattern

For multi-service databases (like `employa-core`), use schema prefixes to isolate service data:

```sql
-- Create schema for service
CREATE SCHEMA IF NOT EXISTS people;

-- All tables use schema prefix
CREATE TABLE IF NOT EXISTS people.users (...);
CREATE TABLE IF NOT EXISTS people.organizations (...);

-- Grant access to service role
GRANT USAGE ON SCHEMA people TO people_service;
GRANT ALL ON ALL TABLES IN SCHEMA people TO people_service;
GRANT ALL ON ALL SEQUENCES IN SCHEMA people TO people_service;
```

**Database → Schema Mapping:**

| Database | Schema | Service |
|----------|--------|---------|
| employa-core | `people` | PeopleService |
| employa-core | `billing` | BillingService |
| employa-core | `careers` | CareerServices |
| employa-core | `support` | SupportNetwork |
| employa-core | `content` | ContentEngine |
| employa-dave | `public` | Dave (dedicated DB) |
| employa-partners | `public` | PartnerHub (dedicated DB) |

---

## Seed Data Pattern

Use seed migrations for reference data, system prompts, configuration, and test data.

### Seed File Structure

```
migrations/
├── 001_initial_schema.sql      # Tables, indexes, triggers
├── 002_seed_reference_data.sql # Enums, lookup tables
├── 003_seed_system_prompts.sql # AI prompts, templates
└── data/
    └── test_users.sql          # Test data (not for production)
```

### Idempotent Seed Pattern

Seeds MUST be idempotent (safe to run multiple times):

```sql
-- Migration: 002_seed_reference_data.sql
-- Description: Seed reference data for permission types

BEGIN;

-- Use ON CONFLICT DO NOTHING for insert-only seeds
INSERT INTO people.permission_types (code, name, description) VALUES
    ('admin', 'Administrator', 'Full system access'),
    ('member', 'Member', 'Standard member access'),
    ('viewer', 'Viewer', 'Read-only access')
ON CONFLICT (code) DO NOTHING;

-- Use ON CONFLICT DO UPDATE for seeds that may change
INSERT INTO people.system_settings (key, value, description) VALUES
    ('max_org_members', '100', 'Maximum members per organization'),
    ('session_timeout_minutes', '60', 'User session timeout')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

COMMIT;

-- Log completion
DO $$ BEGIN RAISE NOTICE 'Seed data applied at %', NOW(); END $$;
```

### AI Prompt Seed Pattern

For services with AI prompts (like Dave), use versioned prompts:

```sql
-- Insert prompt definition
INSERT INTO admin_prompts (category, name, description)
VALUES ('system', 'welcome_message', 'Initial greeting for new users')
ON CONFLICT (category, name) DO NOTHING;

-- Insert versioned content
INSERT INTO admin_prompt_versions (prompt_id, version_number, content, commit_message)
SELECT
    p.id,
    1,
    E'Hello! Welcome to Employa. How can I help you today?',
    'Initial version'
FROM admin_prompts p
WHERE p.category = 'system' AND p.name = 'welcome_message'
AND NOT EXISTS (
    SELECT 1 FROM admin_prompt_versions WHERE prompt_id = p.id
);

-- Set current version
UPDATE admin_prompts SET current_version_id = (
    SELECT id FROM admin_prompt_versions WHERE prompt_id = admin_prompts.id LIMIT 1
) WHERE category = 'system' AND name = 'welcome_message' AND current_version_id IS NULL;
```

### Test Data Seeds

Keep test data separate from production seeds:

```sql
-- migrations/data/test_users.sql
-- WARNING: Test data only - do not apply to production

BEGIN;

-- Only insert if test environment
DO $$
BEGIN
    IF current_setting('app.environment', true) = 'test' THEN
        INSERT INTO people.users (id, email, display_name) VALUES
            ('00000000-0000-0000-0000-000000000001', 'test@example.com', 'Test User'),
            ('00000000-0000-0000-0000-000000000002', 'admin@example.com', 'Test Admin')
        ON CONFLICT DO NOTHING;
    ELSE
        RAISE NOTICE 'Skipping test data - not in test environment';
    END IF;
END $$;

COMMIT;
```

**Reference Implementation:** [Dave/migrations/20251229_dave_system_prompts.sql](../../../Dave/migrations/20251229_dave_system_prompts.sql)

---

## IAM Requirements

### Cloud Run Service Account

The Cloud Run service account needs:

| Role | Purpose |
|------|---------|
| `roles/cloudsql.client` | Connect to Cloud SQL |
| `roles/aiplatform.user` | Use Vertex AI (if applicable) |
| `roles/storage.objectViewer` | Read from GCS (if applicable) |
| `roles/secretmanager.secretAccessor` | Access secrets |

### Cloud SQL Service Account

For importing migrations from GCS:

```bash
# Get Cloud SQL service account
gcloud sql instances describe employa-dave \
  --format="value(serviceAccountEmailAddress)"

# Grant storage access
gsutil iam ch serviceAccount:SA_EMAIL:objectViewer gs://BUCKET_NAME
```

---

## Secret Management

### Production

Secrets stored in GCP Secret Manager and injected as environment variables:

```yaml
# Cloud Run service configuration
env:
  - name: DAVE_DB_DSN
    valueFrom:
      secretKeyRef:
        name: dave-db-dsn
        key: latest
```

### Local Development

For local development, use Application Default Credentials:

```bash
# Authenticate (one time)
gcloud auth application-default login

# Secrets can be stored in local .env file
# .env is in .gitignore
```

---

## Testing Pattern

### Integration Tests with Test Database

```python
# tests/conftest.py
import pytest
import asyncpg
from app.clients.database import DatabaseManager


@pytest.fixture
async def test_db():
    """Create test database connection."""
    pool = await asyncpg.create_pool(
        dsn=os.environ.get("TEST_DB_DSN"),
        min_size=1,
        max_size=5,
    )

    # Clean slate for each test
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE ai_conversations CASCADE")

    yield pool

    await pool.close()


@pytest.fixture
async def conversation_repo(test_db):
    """Repository with test database."""
    repo = ConversationRepository()
    repo.db_manager._pool = test_db
    return repo
```

### Unit Tests with Mocked Database

```python
# tests/unit/test_conversation_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_repo():
    """Mock repository for unit tests."""
    repo = AsyncMock()
    repo.get_by_id.return_value = {
        "id": "test-id",
        "user_id": "user-123",
        "title": "Test Conversation",
    }
    return repo


async def test_get_conversation(mock_repo):
    """Test getting a conversation."""
    service = ConversationService(repo=mock_repo)

    result = await service.get_conversation("test-id", "user-123")

    assert result["id"] == "test-id"
    mock_repo.get_by_id.assert_called_once_with("test-id", "user-123")
```

---

## SSL Mode Configuration

### Standard Policy

For services connected via VPC Connector, `ALLOW_UNENCRYPTED_AND_ENCRYPTED` is acceptable:

| Scenario | SSL Mode | Rationale |
|----------|----------|-----------|
| Cloud Run → Cloud SQL (VPC) | `ALLOW_UNENCRYPTED` | VPC encrypts in transit |
| External client → Cloud SQL | `ENCRYPTED_ONLY` | Public network requires encryption |
| PHI databases (optional) | Client certificates | Defense in depth |

### Configuration

```bash
# Standard (VPC-connected services)
gcloud sql instances patch INSTANCE \
  --ssl-mode=ALLOW_UNENCRYPTED_AND_ENCRYPTED

# Strict (if required by compliance)
gcloud sql instances patch INSTANCE \
  --ssl-mode=ENCRYPTED_ONLY \
  --require-ssl
```

**Note:** VPC Connector provides encryption in transit for all traffic between Cloud Run and Cloud SQL. The SSL mode setting applies to the PostgreSQL connection layer, which is secondary when using VPC.

---

## asyncpg Serialization Patterns

### JSONB Columns

asyncpg requires explicit `json.dumps()` for JSONB columns:

```python
import json

# ✅ CORRECT - Serialize dicts for JSONB
context_value = json.dumps(context) if context else json.dumps({})
metadata_value = json.dumps(metadata) if metadata else json.dumps({})

query = """
    INSERT INTO ai_conversations (id, user_id, context, metadata)
    VALUES ($1, $2, $3, $4)
"""
await conn.execute(query, conv_id, user_id, context_value, metadata_value)

# ❌ WRONG - Passing dict directly
await conn.execute(query, conv_id, user_id, context, metadata)  # Fails!
```

### text[] Array Columns

For PostgreSQL `text[]` columns, pass Python lists directly:

```python
# ✅ CORRECT - Pass lists for text[]
resources = ["resource1", "resource2"]
suggestions = ["suggestion1", "suggestion2"]

query = """
    INSERT INTO ai_messages (id, resources, follow_up_suggestions)
    VALUES ($1, $2, $3)
"""
await conn.execute(query, msg_id, resources, suggestions)
```

### UUID Columns

UUID columns return `uuid.UUID` objects. Convert to strings for Pydantic:

```python
from pydantic import BaseModel

class Resource(BaseModel):
    id: str  # Expects string, not UUID

# When fetching from database:
row = await conn.fetchrow("SELECT id, title FROM knowledge_base WHERE id = $1", kb_id)

# ✅ CORRECT - Convert UUID to string
resource = Resource(
    id=str(row["id"]),  # row["id"] is uuid.UUID
    title=row["title"],
)

# ❌ WRONG - Passing UUID directly
resource = Resource(id=row["id"], title=row["title"])  # Validation error!
```

---

## Anonymous User Session Pattern

For public-facing services (like chat), generate UUIDs for anonymous users:

```python
from uuid import uuid4

async def optional_auth(...) -> AuthContext:
    """Allow anonymous access with session tracking."""

    if api_key:
        # Authenticated user
        return await verify_api_key(api_key)

    if bearer:
        # JWT authenticated
        user_id = get_user_id_from_token(bearer.credentials)
        return AuthContext(user_id=user_id, ...)

    # Anonymous - generate session UUID
    return AuthContext(
        api_key=None,
        is_admin=False,
        user_id=str(uuid4()),  # Enables conversation tracking
        user_type="anonymous",
        tier="free",
    )
```

**Benefits:**
- No login barrier for public services
- Conversation tracking within session
- Follow-up messages work correctly
- Database foreign key constraints satisfied

**Reference:** [Dave middleware/auth.py](../../../Dave/api/app/middleware/auth.py)

---

## Troubleshooting

### Connection Refused

**Symptom:** `could not connect to server: Connection refused`

**Causes:**
1. Cloud SQL Proxy not running (local dev)
2. VPC Connector not configured (Cloud Run)
3. Cloud SQL instance not running

**Fix:**
```bash
# Local: Start Cloud SQL Proxy
cloud-sql-proxy employa-prod:us-central1:employa-dave --port=5432

# Cloud Run: Verify VPC connector
gcloud run services describe SERVICE --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-connector'])"
```

### Permission Denied

**Symptom:** `FATAL: password authentication failed for user`

**Causes:**
1. Wrong password in DSN
2. User doesn't exist in Cloud SQL
3. User doesn't have grants on database

**Fix:**
```bash
# Reset password
gcloud sql users set-password dave_service --instance=employa-dave --password=NEW_PASSWORD

# Verify grants (connect via Cloud SQL Proxy)
psql -h localhost -U postgres -d dave
\du  -- List users
GRANT ALL ON ALL TABLES IN SCHEMA public TO dave_service;
```

### Pool Exhausted

**Symptom:** `asyncpg.exceptions.TooManyConnectionsError`

**Causes:**
1. Connection leak (not closing connections)
2. Pool too small for traffic
3. Long-running queries blocking connections

**Fix:**
```python
# Increase pool size
DB_POOL_MAX_SIZE=30

# Add query timeout
DB_QUERY_TIMEOUT=30.0

# Ensure connections are released
async with pool.acquire() as conn:  # Always use context manager
    await conn.fetch(query)
# Connection automatically released here
```

---

## Related Standards

- [service-scaffold-checklist.md](../templates/service-scaffold-checklist.md) - Authorization strategy section
- [config-secrets-implementation.md](config-secrets-implementation.md) - Secret Manager patterns
- [container-cloudrun.md](container-cloudrun.md) - Cloud Run configuration

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.2 | 2026-01-16 | Claude Opus 4.5 | Added: SSL mode config, asyncpg serialization, anonymous user sessions |
| 1.1 | 2026-01-15 | Claude Opus 4.5 | Added: Timestamp triggers, JSONB patterns, Schema prefix mapping, Seed data patterns |
| 1.0 | 2026-01-13 | Claude + Team | Initial standard based on Dave service migration |
