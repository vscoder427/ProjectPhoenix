"""
Integration test configuration.

This conftest.py provides integration test specific fixtures.
Integration tests use the real local database (Docker PostgreSQL).

IMPORTANT: Docker Compose database must be running.

Start database:
    docker-compose -f docker-compose.local-db.yml up -d

Stop database:
    docker-compose -f docker-compose.local-db.yml down -v
"""
import pytest

# Import database fixtures from fixtures/database.py
# These are used by integration tests marked with @pytest.mark.integration

# Integration tests should:
# 1. Use real local database (Docker PostgreSQL)
# 2. Mock only external services (Gemini API, external HTTP)
# 3. Test full business logic flows
# 4. Clean up test data after completion
