# Testing RLS Policies

**Status:** ✅ Active
**Owner:** Platform Team
**Related Standards:** [database-rls-policies.md](database-rls-policies.md), [testing-tdd.md](testing-tdd.md)

---

## Overview

Row Level Security (RLS) policies are the last line of defense for protecting user data in a multi-tenant PostgreSQL database. A misconfigured RLS policy can expose Protected Health Information (PHI) and violate HIPAA compliance.

**Critical Principle:** RLS policies MUST be tested with the same rigor as application code.

This standard defines automated testing requirements for all Supabase RLS policies in ProjectPhoenix services.

---

## Why Test RLS Policies?

### Security Incidents Prevented by RLS Testing

**Real-world example from Employa codebase:**
```sql
-- BEFORE (Vulnerable - missing RLS):
CREATE TABLE employer_profiles (...);
-- RLS not enabled - any authenticated user could read any employer profile

-- AFTER (Secure):
ALTER TABLE employer_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_employer_profiles" ON employer_profiles
  FOR SELECT USING (true); -- Intentionally public (jobs require employer data)
```

**What Could Go Wrong Without Testing:**
1. **Data Leakage:** User A reads User B's conversations, job applications, resume data
2. **Unauthorized Writes:** User A updates User B's profile, deletes their jobs
3. **Privilege Escalation:** Regular user accesses admin-only settings
4. **Service Lockout:** Backend service can't access data due to overly restrictive policies
5. **Recursive Policy Issues:** Joined tables without policies block legitimate queries

**Historical Example from Employa:**
- 69 tables initially created without RLS (bulk fix: migration `20260105000001`)
- `employer_profiles` missing public read policy blocked anonymous job views
- No automated tests existed to catch these issues

### HIPAA Compliance Requirement

RLS testing is **mandatory** for HIPAA compliance:
- **§164.308(a)(4):** Information Access Management - verify only authorized users access PHI
- **§164.312(a)(1):** Access Control - test that technical safeguards work as designed

**Audit Trail:** RLS test results demonstrate due diligence during compliance audits.

---

## Testing Scope

### What MUST Be Tested

**All Tier 0 Services (User-Facing):**
- ✅ Dave (ai_conversations, ai_messages, admin_prompts)
- ✅ Warp (users, jobs, applications, companies, resumes)
- ✅ AAMeetings (meetings - if user-specific data exists)
- ✅ CareerIntelligence (assessments, recommendations)
- ✅ UserOnboarding (onboarding_progress)
- ✅ Outreach (outreach_leads, campaigns)

**Tables Requiring RLS Tests:**
- All tables with `user_id`, `employer_id`, `owner_id`, or similar foreign keys
- All tables with PHI/PII (resumes, applications, conversations, assessments)
- All admin-only tables (settings, audit logs)
- All public tables (jobs, meetings) - verify public read works

### What Can Be Skipped

- **System tables:** `migrations`, `schema_version`
- **Lookup tables:** `timezones`, `countries`, `states` (no user data)
- **Service-only tables:** `analytics_events` (no authenticated user access)

**Exception:** Even service-only tables should have a test verifying service role bypass works.

---

## Test Setup

### Supabase Test Fixtures (pytest)

**File:** `tests/conftest.py`

```python
import pytest
import os
from supabase import create_client, Client
from typing import Generator

@pytest.fixture(scope="session")
def supabase_url() -> str:
    """Supabase project URL from environment."""
    url = os.getenv("SUPABASE_URL")
    if not url:
        pytest.skip("SUPABASE_URL not set")
    return url

@pytest.fixture(scope="session")
def supabase_service_key() -> str:
    """Service role key (bypasses RLS)."""
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not key:
        pytest.skip("SUPABASE_SERVICE_KEY not set")
    return key

@pytest.fixture(scope="session")
def supabase_anon_key() -> str:
    """Anonymous key (respects RLS)."""
    key = os.getenv("SUPABASE_ANON_KEY")
    if not key:
        pytest.skip("SUPABASE_ANON_KEY not set")
    return key

@pytest.fixture
def supabase_service(supabase_url: str, supabase_service_key: str) -> Client:
    """Supabase client with service role (bypasses RLS)."""
    return create_client(supabase_url, supabase_service_key)

@pytest.fixture
def supabase_anon(supabase_url: str, supabase_anon_key: str) -> Client:
    """Supabase client with anon key (respects RLS)."""
    return create_client(supabase_url, supabase_anon_key)

@pytest.fixture
def test_user_a(supabase_service: Client) -> Generator[dict, None, None]:
    """Create test user A and clean up after test."""
    user = supabase_service.auth.admin.create_user({
        "email": "test-user-a@example.com",
        "password": "test-password-123",
        "email_confirm": True
    })

    yield user.user

    # Cleanup
    supabase_service.auth.admin.delete_user(user.user.id)

@pytest.fixture
def test_user_b(supabase_service: Client) -> Generator[dict, None, None]:
    """Create test user B and clean up after test."""
    user = supabase_service.auth.admin.create_user({
        "email": "test-user-b@example.com",
        "password": "test-password-456",
        "email_confirm": True
    })

    yield user.user

    # Cleanup
    supabase_service.auth.admin.delete_user(user.user.id)

@pytest.fixture
def authenticated_client_a(
    supabase_url: str,
    supabase_anon_key: str,
    test_user_a: dict
) -> Client:
    """Supabase client authenticated as User A."""
    client = create_client(supabase_url, supabase_anon_key)
    client.auth.sign_in_with_password({
        "email": "test-user-a@example.com",
        "password": "test-password-123"
    })
    return client

@pytest.fixture
def authenticated_client_b(
    supabase_url: str,
    supabase_anon_key: str,
    test_user_b: dict
) -> Client:
    """Supabase client authenticated as User B."""
    client = create_client(supabase_url, supabase_anon_key)
    client.auth.sign_in_with_password({
        "email": "test-user-b@example.com",
        "password": "test-password-456"
    })
    return client
```

---

## Core Test Scenarios

### Scenario 1: User Isolation (User-Owned Resources)

**Requirement:** User A cannot access User B's data.

**Example: AI Conversations**

```python
# File: tests/test_rls_ai_conversations.py

import pytest
from supabase import Client

def test_user_cannot_read_other_users_conversations(
    supabase_service: Client,
    authenticated_client_a: Client,
    authenticated_client_b: Client,
    test_user_a: dict,
    test_user_b: dict
):
    """Test that User A cannot read User B's conversations."""

    # ARRANGE: Create conversation owned by User B (using service role)
    conversation_b = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_b["id"],
        "title": "User B's Private Conversation",
        "status": "active"
    }).execute()

    conversation_b_id = conversation_b.data[0]["id"]

    # ACT: User A attempts to read User B's conversation
    result = authenticated_client_a.table("ai_conversations").select("*").eq(
        "id", conversation_b_id
    ).execute()

    # ASSERT: User A gets empty result (RLS blocks access)
    assert len(result.data) == 0, "User A should not see User B's conversation"

    # CLEANUP
    supabase_service.table("ai_conversations").delete().eq(
        "id", conversation_b_id
    ).execute()


def test_user_cannot_update_other_users_conversations(
    supabase_service: Client,
    authenticated_client_a: Client,
    test_user_b: dict
):
    """Test that User A cannot update User B's conversations."""

    # ARRANGE
    conversation_b = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_b["id"],
        "title": "Original Title",
        "status": "active"
    }).execute()

    conversation_b_id = conversation_b.data[0]["id"]

    # ACT: User A attempts to update User B's conversation
    result = authenticated_client_a.table("ai_conversations").update({
        "title": "Hacked Title"
    }).eq("id", conversation_b_id).execute()

    # ASSERT: Update fails (RLS blocks)
    assert len(result.data) == 0, "User A should not be able to update User B's conversation"

    # Verify original title unchanged
    verify = supabase_service.table("ai_conversations").select("title").eq(
        "id", conversation_b_id
    ).execute()
    assert verify.data[0]["title"] == "Original Title"

    # CLEANUP
    supabase_service.table("ai_conversations").delete().eq(
        "id", conversation_b_id
    ).execute()


def test_user_cannot_delete_other_users_conversations(
    supabase_service: Client,
    authenticated_client_a: Client,
    test_user_b: dict
):
    """Test that User A cannot delete User B's conversations."""

    # ARRANGE
    conversation_b = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_b["id"],
        "title": "User B's Conversation",
        "status": "active"
    }).execute()

    conversation_b_id = conversation_b.data[0]["id"]

    # ACT: User A attempts to delete User B's conversation
    result = authenticated_client_a.table("ai_conversations").delete().eq(
        "id", conversation_b_id
    ).execute()

    # ASSERT: Delete fails (RLS blocks)
    assert len(result.data) == 0, "User A should not be able to delete User B's conversation"

    # Verify conversation still exists
    verify = supabase_service.table("ai_conversations").select("id").eq(
        "id", conversation_b_id
    ).execute()
    assert len(verify.data) == 1, "Conversation should still exist"

    # CLEANUP
    supabase_service.table("ai_conversations").delete().eq(
        "id", conversation_b_id
    ).execute()
```

---

### Scenario 2: Child Resource Access (via Parent Join)

**Requirement:** User can only access child records if they own the parent.

**Example: AI Messages (child of AI Conversations)**

```python
# File: tests/test_rls_ai_messages.py

def test_user_cannot_read_messages_in_other_users_conversation(
    supabase_service: Client,
    authenticated_client_a: Client,
    test_user_b: dict
):
    """Test that User A cannot read messages in User B's conversation."""

    # ARRANGE: Create conversation + message owned by User B
    conversation_b = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_b["id"],
        "title": "User B's Conversation",
        "status": "active"
    }).execute()

    conversation_b_id = conversation_b.data[0]["id"]

    message_b = supabase_service.table("ai_messages").insert({
        "conversation_id": conversation_b_id,
        "role": "user",
        "content": "User B's private message"
    }).execute()

    message_b_id = message_b.data[0]["id"]

    # ACT: User A attempts to read User B's message
    result = authenticated_client_a.table("ai_messages").select("*").eq(
        "id", message_b_id
    ).execute()

    # ASSERT: User A gets empty result (RLS blocks via parent join)
    assert len(result.data) == 0, "User A should not see messages in User B's conversation"

    # CLEANUP
    supabase_service.table("ai_messages").delete().eq("id", message_b_id).execute()
    supabase_service.table("ai_conversations").delete().eq("id", conversation_b_id).execute()
```

---

### Scenario 3: Public Read Policies

**Requirement:** Anonymous and authenticated users can read public resources.

**Example: Jobs (Public Read, Owner Write)**

```python
# File: tests/test_rls_jobs.py

def test_anonymous_user_can_read_active_jobs(
    supabase_service: Client,
    supabase_anon: Client,
    test_user_a: dict
):
    """Test that anonymous users can view active published jobs."""

    # ARRANGE: Create active published job
    job = supabase_service.table("jobs").insert({
        "employer_id": test_user_a["id"],
        "title": "Software Engineer",
        "status": "active",
        "published_at": "2026-01-01T00:00:00Z"  # Past date = published
    }).execute()

    job_id = job.data[0]["id"]

    # ACT: Anonymous user reads jobs
    result = supabase_anon.table("jobs").select("*").eq("id", job_id).execute()

    # ASSERT: Anonymous user sees the job
    assert len(result.data) == 1, "Anonymous user should see active published jobs"
    assert result.data[0]["title"] == "Software Engineer"

    # CLEANUP
    supabase_service.table("jobs").delete().eq("id", job_id).execute()


def test_anonymous_user_cannot_read_draft_jobs(
    supabase_service: Client,
    supabase_anon: Client,
    test_user_a: dict
):
    """Test that anonymous users cannot view draft jobs."""

    # ARRANGE: Create draft job (not published)
    job = supabase_service.table("jobs").insert({
        "employer_id": test_user_a["id"],
        "title": "Secret Job",
        "status": "draft",
        "published_at": None
    }).execute()

    job_id = job.data[0]["id"]

    # ACT: Anonymous user attempts to read draft job
    result = supabase_anon.table("jobs").select("*").eq("id", job_id).execute()

    # ASSERT: Anonymous user gets empty result
    assert len(result.data) == 0, "Anonymous user should not see draft jobs"

    # CLEANUP
    supabase_service.table("jobs").delete().eq("id", job_id).execute()


def test_employer_can_manage_own_jobs(
    supabase_service: Client,
    authenticated_client_a: Client,
    test_user_a: dict
):
    """Test that employers can create, update, delete their own jobs."""

    # ACT 1: Create job as authenticated employer
    result = authenticated_client_a.table("jobs").insert({
        "employer_id": test_user_a["id"],
        "title": "New Job",
        "status": "draft"
    }).execute()

    # ASSERT 1: Job created successfully
    assert len(result.data) == 1
    job_id = result.data[0]["id"]

    # ACT 2: Update own job
    update_result = authenticated_client_a.table("jobs").update({
        "title": "Updated Job Title"
    }).eq("id", job_id).execute()

    # ASSERT 2: Update succeeded
    assert len(update_result.data) == 1
    assert update_result.data[0]["title"] == "Updated Job Title"

    # ACT 3: Delete own job
    delete_result = authenticated_client_a.table("jobs").delete().eq("id", job_id).execute()

    # ASSERT 3: Delete succeeded
    assert len(delete_result.data) == 1

    # CLEANUP: Verify deletion
    verify = supabase_service.table("jobs").select("id").eq("id", job_id).execute()
    assert len(verify.data) == 0
```

---

### Scenario 4: Service Role Bypass

**Requirement:** Backend services with service_role key can access all data (bypass RLS).

```python
# File: tests/test_rls_service_role.py

def test_service_role_can_access_all_conversations(
    supabase_service: Client,
    test_user_a: dict,
    test_user_b: dict
):
    """Test that service role bypasses RLS and sees all conversations."""

    # ARRANGE: Create conversations for both users
    conv_a = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_a["id"],
        "title": "User A's Conversation",
        "status": "active"
    }).execute()

    conv_b = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_b["id"],
        "title": "User B's Conversation",
        "status": "active"
    }).execute()

    conv_a_id = conv_a.data[0]["id"]
    conv_b_id = conv_b.data[0]["id"]

    # ACT: Service role reads all conversations
    result = supabase_service.table("ai_conversations").select("*").in_(
        "id", [conv_a_id, conv_b_id]
    ).execute()

    # ASSERT: Service role sees both conversations (bypasses RLS)
    assert len(result.data) == 2, "Service role should bypass RLS and see all data"

    # CLEANUP
    supabase_service.table("ai_conversations").delete().in_(
        "id", [conv_a_id, conv_b_id]
    ).execute()


def test_service_role_can_delete_any_conversation(
    supabase_service: Client,
    test_user_a: dict
):
    """Test that service role can perform admin operations."""

    # ARRANGE
    conv = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_a["id"],
        "title": "Test Conversation",
        "status": "active"
    }).execute()

    conv_id = conv.data[0]["id"]

    # ACT: Service role deletes conversation
    result = supabase_service.table("ai_conversations").delete().eq(
        "id", conv_id
    ).execute()

    # ASSERT: Deletion succeeded
    assert len(result.data) == 1

    # Verify deletion
    verify = supabase_service.table("ai_conversations").select("id").eq(
        "id", conv_id
    ).execute()
    assert len(verify.data) == 0
```

---

### Scenario 5: Admin-Only Resources

**Requirement:** Only users with admin role can access admin tables.

```python
# File: tests/test_rls_admin_settings.py

def test_regular_user_cannot_read_admin_settings(
    supabase_service: Client,
    authenticated_client_a: Client
):
    """Test that regular users cannot access admin settings."""

    # ARRANGE: Create admin setting
    setting = supabase_service.table("admin_settings").insert({
        "key": "test_setting",
        "value": "secret_value"
    }).execute()

    setting_id = setting.data[0]["id"]

    # ACT: Regular user attempts to read admin settings
    result = authenticated_client_a.table("admin_settings").select("*").eq(
        "id", setting_id
    ).execute()

    # ASSERT: Regular user gets empty result
    assert len(result.data) == 0, "Regular user should not access admin settings"

    # CLEANUP
    supabase_service.table("admin_settings").delete().eq("id", setting_id).execute()


def test_admin_user_can_read_admin_settings(
    supabase_service: Client,
    supabase_url: str,
    supabase_anon_key: str,
    test_user_a: dict
):
    """Test that admin users can access admin settings."""

    # ARRANGE: Grant admin role to test_user_a
    supabase_service.table("users").update({
        "is_admin": True
    }).eq("id", test_user_a["id"]).execute()

    # Create admin setting
    setting = supabase_service.table("admin_settings").insert({
        "key": "test_admin_setting",
        "value": "admin_value"
    }).execute()

    setting_id = setting.data[0]["id"]

    # ACT: Admin user reads admin settings
    admin_client = create_client(supabase_url, supabase_anon_key)
    admin_client.auth.sign_in_with_password({
        "email": "test-user-a@example.com",
        "password": "test-password-123"
    })

    result = admin_client.table("admin_settings").select("*").eq(
        "id", setting_id
    ).execute()

    # ASSERT: Admin user sees the setting
    assert len(result.data) == 1, "Admin user should access admin settings"
    assert result.data[0]["value"] == "admin_value"

    # CLEANUP
    supabase_service.table("admin_settings").delete().eq("id", setting_id).execute()
    supabase_service.table("users").update({
        "is_admin": False
    }).eq("id", test_user_a["id"]).execute()
```

---

## Test Data Management

### Creating Test Users

**Best Practice:** Use Supabase Admin API to create test users programmatically.

```python
def create_test_user(supabase_service: Client, email: str, password: str) -> dict:
    """Create test user with Supabase Admin API."""
    user = supabase_service.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True  # Skip email verification
    })
    return user.user

def delete_test_user(supabase_service: Client, user_id: str):
    """Delete test user and all associated data."""
    supabase_service.auth.admin.delete_user(user_id)
```

### Test Data Isolation

**Pattern:** Use unique identifiers to avoid test collisions.

```python
import uuid

def test_user_isolation_with_unique_data(supabase_service: Client):
    # Use UUID in test data to avoid conflicts
    unique_title = f"Test Conversation {uuid.uuid4()}"

    conversation = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_id,
        "title": unique_title,
        "status": "active"
    }).execute()

    # Test logic...

    # Cleanup by unique title
    supabase_service.table("ai_conversations").delete().eq(
        "title", unique_title
    ).execute()
```

### Cleanup Strategies

**Option 1: Fixture Cleanup (Preferred)**
```python
@pytest.fixture
def test_conversation(supabase_service: Client, test_user_a: dict):
    """Create test conversation with automatic cleanup."""
    conv = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_a["id"],
        "title": "Test Conversation",
        "status": "active"
    }).execute()

    yield conv.data[0]

    # Automatic cleanup after test
    supabase_service.table("ai_conversations").delete().eq(
        "id", conv.data[0]["id"]
    ).execute()
```

**Option 2: Manual Cleanup in Test**
```python
def test_example(supabase_service: Client):
    # Arrange
    record = create_test_record()

    try:
        # Act & Assert
        ...
    finally:
        # Cleanup (always runs, even if test fails)
        delete_test_record(record["id"])
```

---

## CI/CD Integration

### GitHub Actions Workflow

**File:** `.github/workflows/rls-tests.yml`

```yaml
name: RLS Policy Tests

on:
  pull_request:
    paths:
      - 'supabase/migrations/**'
      - 'tests/test_rls_*.py'
  push:
    branches:
      - main

jobs:
  test-rls:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest supabase

      - name: Run RLS tests
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_TEST_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_TEST_ANON_KEY }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_TEST_SERVICE_KEY }}
        run: |
          pytest tests/test_rls_*.py -v --tb=short

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: rls-test-results
          path: pytest-report.xml
```

### Test Environment Setup

**Requirement:** Use a dedicated Supabase project for testing (NOT production).

**Setup Steps:**
1. Create test Supabase project: `https://your-project-test.supabase.co`
2. Run all migrations in test project
3. Store test credentials in GitHub Secrets:
   - `SUPABASE_TEST_URL`
   - `SUPABASE_TEST_ANON_KEY`
   - `SUPABASE_TEST_SERVICE_KEY`

**Why Separate Test Database?**
- Avoids polluting production data
- Allows destructive tests (delete all records, etc.)
- Faster test execution (no RLS on real user data)

---

## Coverage Requirements

### Tier 0 Services (User-Facing)

**Mandatory RLS Test Coverage:**
- ✅ All user-owned tables (conversations, profiles, applications)
- ✅ All child resource tables (messages, attachments)
- ✅ All public read tables (jobs, meetings)
- ✅ All admin-only tables (settings, audit logs)
- ✅ Service role bypass (at least one test per service)

**Minimum Test Count:**
- **Small service** (1-5 tables): 5-10 RLS tests
- **Medium service** (6-15 tables): 15-25 RLS tests
- **Large service** (16+ tables): 30+ RLS tests

### Example Test Coverage Matrix

**Dave Service (5 tables):**

| Table | User Isolation | Child Access | Public Read | Service Role | Admin Only | Total Tests |
|-------|---------------|--------------|-------------|--------------|------------|-------------|
| ai_conversations | ✅ (4) | - | - | ✅ (1) | - | 5 |
| ai_messages | ✅ (4) | ✅ (2) | - | ✅ (1) | - | 7 |
| admin_prompts | - | - | ✅ (2) | ✅ (1) | ✅ (2) | 5 |
| admin_prompt_versions | - | ✅ (2) | - | ✅ (1) | ✅ (2) | 5 |
| admin_prompt_variables | - | ✅ (2) | - | ✅ (1) | ✅ (2) | 5 |
| **TOTAL** | | | | | | **27 tests** |

---

## Running Tests Locally

### Setup

```bash
# Install dependencies
pip install pytest supabase

# Set environment variables (use test database)
export SUPABASE_URL="https://your-project-test.supabase.co"
export SUPABASE_ANON_KEY="your-test-anon-key"
export SUPABASE_SERVICE_KEY="your-test-service-key"
```

### Run All RLS Tests

```bash
pytest tests/test_rls_*.py -v
```

### Run Tests for Specific Table

```bash
pytest tests/test_rls_ai_conversations.py -v
```

### Run with Coverage Report

```bash
pytest tests/test_rls_*.py --cov=tests --cov-report=html
```

---

## Common Testing Pitfalls

### Pitfall 1: Using Service Role for User Tests

**Wrong:**
```python
def test_user_isolation(supabase_service: Client):
    # Service role bypasses RLS - test will always pass!
    result = supabase_service.table("ai_conversations").select("*").execute()
```

**Correct:**
```python
def test_user_isolation(authenticated_client_a: Client):
    # Authenticated client respects RLS
    result = authenticated_client_a.table("ai_conversations").select("*").execute()
```

### Pitfall 2: Not Cleaning Up Test Data

**Problem:** Test data accumulates, polluting test database.

**Solution:** Always use fixtures with cleanup or try/finally blocks.

### Pitfall 3: Testing Against Production Database

**Problem:** Tests modify real user data, violate HIPAA compliance.

**Solution:** Always use dedicated test Supabase project.

### Pitfall 4: Missing WITH CHECK Tests

**Problem:** Only testing SELECT policies, not INSERT/UPDATE constraints.

**Solution:** Test all CRUD operations (Create, Read, Update, Delete).

### Pitfall 5: Assuming Policies Are Transitive

**Problem:** Parent table has RLS, but child table doesn't - queries fail.

**Solution:** Test joins between tables (e.g., conversations + messages).

---

## Debugging Failed RLS Tests

### Enable Supabase Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect RLS Policies in SQL Editor

```sql
-- View all policies for a table
SELECT * FROM pg_policies WHERE tablename = 'ai_conversations';

-- Test policy manually with SET ROLE
SET ROLE authenticated;
SET request.jwt.claims.sub = 'test-user-id';
SELECT * FROM ai_conversations;
```

### Check auth.uid() Function

```sql
-- Verify auth.uid() returns expected user ID
SELECT auth.uid();
```

### Test Policy in Isolation

```python
# Disable other policies temporarily (in test DB only!)
ALTER TABLE ai_conversations DROP POLICY "other_policy";

# Re-run test to isolate which policy is failing
pytest tests/test_rls_ai_conversations.py -k test_user_isolation -v
```

---

## Related Standards

- [database-rls-policies.md](database-rls-policies.md) - RLS policy templates and naming conventions
- [testing-tdd.md](testing-tdd.md) - General testing requirements (85% coverage)
- [db-isolation-migrations.md](db-isolation-migrations.md) - Database per service architecture
- [security/api-gateway-networking.md](security/api-gateway-networking.md) - API-level security (defense in depth)

---

## Appendix: Complete Test Suite Example

**File:** `Dave/tests/test_rls_complete.py`

```python
"""
Complete RLS test suite for Dave service.
Tests all 5 tables with user isolation, service role bypass, and admin policies.
"""

import pytest
from supabase import Client

# ============================================================================
# AI Conversations Tests
# ============================================================================

def test_conversations_user_select_own(
    authenticated_client_a: Client,
    supabase_service: Client,
    test_user_a: dict
):
    """User can SELECT their own conversations."""
    conv = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_a["id"],
        "title": "Test",
        "status": "active"
    }).execute()

    result = authenticated_client_a.table("ai_conversations").select("*").eq(
        "id", conv.data[0]["id"]
    ).execute()

    assert len(result.data) == 1
    supabase_service.table("ai_conversations").delete().eq("id", conv.data[0]["id"]).execute()

def test_conversations_user_insert_own(
    authenticated_client_a: Client,
    supabase_service: Client,
    test_user_a: dict
):
    """User can INSERT their own conversations."""
    result = authenticated_client_a.table("ai_conversations").insert({
        "user_id": test_user_a["id"],
        "title": "New Conversation",
        "status": "active"
    }).execute()

    assert len(result.data) == 1
    supabase_service.table("ai_conversations").delete().eq("id", result.data[0]["id"]).execute()

def test_conversations_user_cannot_read_others(
    authenticated_client_a: Client,
    supabase_service: Client,
    test_user_b: dict
):
    """User cannot SELECT other users' conversations."""
    conv = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_b["id"],
        "title": "User B's Conversation",
        "status": "active"
    }).execute()

    result = authenticated_client_a.table("ai_conversations").select("*").eq(
        "id", conv.data[0]["id"]
    ).execute()

    assert len(result.data) == 0
    supabase_service.table("ai_conversations").delete().eq("id", conv.data[0]["id"]).execute()

def test_conversations_service_role_bypass(
    supabase_service: Client,
    test_user_a: dict,
    test_user_b: dict
):
    """Service role bypasses RLS and sees all conversations."""
    conv_a = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_a["id"],
        "title": "Conv A",
        "status": "active"
    }).execute()

    conv_b = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_b["id"],
        "title": "Conv B",
        "status": "active"
    }).execute()

    result = supabase_service.table("ai_conversations").select("*").in_(
        "id", [conv_a.data[0]["id"], conv_b.data[0]["id"]]
    ).execute()

    assert len(result.data) == 2

    supabase_service.table("ai_conversations").delete().in_(
        "id", [conv_a.data[0]["id"], conv_b.data[0]["id"]]
    ).execute()

# ============================================================================
# AI Messages Tests (Child Resource)
# ============================================================================

def test_messages_user_read_own_conversation_messages(
    authenticated_client_a: Client,
    supabase_service: Client,
    test_user_a: dict
):
    """User can read messages in their own conversation."""
    conv = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_a["id"],
        "title": "Test",
        "status": "active"
    }).execute()

    msg = supabase_service.table("ai_messages").insert({
        "conversation_id": conv.data[0]["id"],
        "role": "user",
        "content": "Test message"
    }).execute()

    result = authenticated_client_a.table("ai_messages").select("*").eq(
        "id", msg.data[0]["id"]
    ).execute()

    assert len(result.data) == 1

    supabase_service.table("ai_messages").delete().eq("id", msg.data[0]["id"]).execute()
    supabase_service.table("ai_conversations").delete().eq("id", conv.data[0]["id"]).execute()

def test_messages_user_cannot_read_others_messages(
    authenticated_client_a: Client,
    supabase_service: Client,
    test_user_b: dict
):
    """User cannot read messages in other users' conversations."""
    conv = supabase_service.table("ai_conversations").insert({
        "user_id": test_user_b["id"],
        "title": "User B's Conv",
        "status": "active"
    }).execute()

    msg = supabase_service.table("ai_messages").insert({
        "conversation_id": conv.data[0]["id"],
        "role": "user",
        "content": "User B's message"
    }).execute()

    result = authenticated_client_a.table("ai_messages").select("*").eq(
        "id", msg.data[0]["id"]
    ).execute()

    assert len(result.data) == 0

    supabase_service.table("ai_messages").delete().eq("id", msg.data[0]["id"]).execute()
    supabase_service.table("ai_conversations").delete().eq("id", conv.data[0]["id"]).execute()

# ============================================================================
# Admin Prompts Tests (Public Read, Admin Write)
# ============================================================================

def test_admin_prompts_user_can_read_active_prompts(
    authenticated_client_a: Client,
    supabase_service: Client
):
    """Regular users can read active (non-archived) admin prompts."""
    prompt = supabase_service.table("admin_prompts").insert({
        "category": "test_category",
        "name": "test_prompt",
        "description": "Test description",
        "is_archived": False
    }).execute()

    result = authenticated_client_a.table("admin_prompts").select("*").eq(
        "id", prompt.data[0]["id"]
    ).execute()

    assert len(result.data) == 1

    supabase_service.table("admin_prompts").delete().eq("id", prompt.data[0]["id"]).execute()

def test_admin_prompts_user_cannot_write(
    authenticated_client_a: Client
):
    """Regular users cannot create admin prompts."""
    result = authenticated_client_a.table("admin_prompts").insert({
        "category": "malicious_category",
        "name": "malicious_prompt",
        "description": "Hacked prompt",
        "is_archived": False
    }).execute()

    # Should fail with RLS error
    assert len(result.data) == 0

# Add 20+ more tests for remaining tables...
```

**Total Test Suite Size:** ~300-400 lines of Python test code covering all 5 Dave tables.

---

## Summary

RLS testing is **mandatory** for HIPAA compliance and multi-tenant security. This standard provides:

✅ **Test setup** - pytest fixtures for Supabase clients
✅ **5 core scenarios** - user isolation, child resources, public read, service role, admin-only
✅ **Test data management** - fixtures, cleanup, unique identifiers
✅ **CI/CD integration** - GitHub Actions workflow
✅ **Coverage requirements** - 27 tests for Dave (5 tables)
✅ **Debugging guide** - SQL inspection, logging, policy isolation

**Next Step:** Apply this standard to Dave service (verify 8 RLS policies created in Issue #25).
