# Dave Service - Local Development with Docker

## Overview

This guide shows you how to run Dave completely locally with Docker, including a local PostgreSQL database. This is ideal for:
- **Development** without cloud dependencies
- **Integration testing** with real database
- **Offline work**
- **Faster iteration** (no network latency)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Network                         │
│                                                          │
│  ┌──────────────┐     ┌──────────────┐                 │
│  │ Dave Service │────▶│  PostgREST   │                 │
│  │  (FastAPI)   │     │ (REST API)   │                 │
│  │  Port: 8080  │     │  Port: 3000  │                 │
│  └──────────────┘     └──────────────┘                 │
│         │                     │                          │
│         │                     ▼                          │
│         │            ┌──────────────┐                   │
│         │            │  PostgreSQL  │◀── Migrations     │
│         │            │  (Supabase)  │                   │
│         │            │  Port: 5432  │                   │
│         │            └──────────────┘                   │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                       │
│  │    Redis     │                                       │
│  │ Port: 6379   │                                       │
│  └──────────────┘                                       │
│                                                          │
│  Optional:                                              │
│  ┌──────────────┐                                       │
│  │   pgAdmin    │  (Database Management UI)            │
│  │  Port: 5050  │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Prerequisites

- Docker Desktop installed
- Git (to clone repo)
- A Gemini API key (for AI features)

### 2. Setup Environment

```bash
cd ProjectPhoenix/services/dave

# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
# (Database will be local, so no Supabase keys needed)
```

### 3. Start Everything

```bash
# Start all services (database + Dave + Redis)
docker-compose -f docker-compose.local-db.yml up -d

# Check status
docker-compose -f docker-compose.local-db.yml ps

# Watch logs
docker-compose -f docker-compose.local-db.yml logs -f dave
```

### 4. Verify It's Working

```bash
# Check Dave health
curl http://localhost:8080/health

# Check database connection
curl http://localhost:3000/

# Open pgAdmin (optional)
# http://localhost:5050
# Login: admin@employa.local / admin
```

## What Gets Created

When you start the local stack:

1. **PostgreSQL** with Dave schema automatically migrated:
   - 5 tables (ai_conversations, ai_messages, admin_prompts, etc.)
   - 15 RLS policies
   - 6 system prompts seeded

2. **PostgREST** API layer (Supabase-compatible REST API)

3. **Dave Service** connected to local database

4. **Redis** for rate limiting

5. **pgAdmin** for database management (optional)

## Development Workflow

### Running Tests Against Local DB

```bash
# Run all tests with local database
docker-compose -f docker-compose.local-db.yml exec dave pytest tests/

# Run integration tests specifically
docker-compose -f docker-compose.local-db.yml exec dave pytest tests/integration/ -v

# Watch mode (re-run on file changes)
docker-compose -f docker-compose.local-db.yml exec dave ptw tests/
```

### Making Database Changes

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.local-db.yml exec postgres psql -U postgres

# Run new migration
docker-compose -f docker-compose.local-db.yml exec postgres psql -U postgres -f /path/to/migration.sql

# Reset database (nuclear option)
docker-compose -f docker-compose.local-db.yml down -v
docker-compose -f docker-compose.local-db.yml up -d
```

### Accessing pgAdmin

1. Open http://localhost:5050
2. Login with `admin@employa.local` / `admin`
3. Add server:
   - **Name:** Dave Local
   - **Host:** postgres
   - **Port:** 5432
   - **Username:** postgres
   - **Password:** postgres

### Hot Reload

The Dave service has hot reload enabled:
- Edit files in `api/` directory
- Changes are automatically reflected (no restart needed)

## Stopping Services

```bash
# Stop services (keep data)
docker-compose -f docker-compose.local-db.yml down

# Stop and delete all data (nuclear reset)
docker-compose -f docker-compose.local-db.yml down -v
```

## Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| Dave API | http://localhost:8080 | Main FastAPI service |
| Health Check | http://localhost:8080/health | Service health |
| PostgREST | http://localhost:3000 | Direct database REST API |
| pgAdmin | http://localhost:5050 | Database management UI |
| Redis | localhost:6379 | Rate limiting cache |
| PostgreSQL | localhost:5432 | Direct database connection |

## Database Credentials (Local)

```
Host: localhost
Port: 5432
User: postgres
Password: postgres
Database: postgres
```

## Switching Between Local and Cloud Database

### Local Database (for development)
```bash
docker-compose -f docker-compose.local-db.yml up -d
```

### Cloud Database (for testing against production)
```bash
# Edit .env with cloud Supabase credentials
docker-compose up -d
```

## Troubleshooting

### Database won't start
```bash
# Check logs
docker-compose -f docker-compose.local-db.yml logs postgres

# Reset database
docker-compose -f docker-compose.local-db.yml down -v
docker-compose -f docker-compose.local-db.yml up -d
```

### Migrations not applying
Migrations run automatically on first start. To re-run:
```bash
docker-compose -f docker-compose.local-db.yml down -v
docker-compose -f docker-compose.local-db.yml up -d postgres
```

### Dave can't connect to database
```bash
# Verify PostgREST is running
curl http://localhost:3000/

# Check Dave logs
docker-compose -f docker-compose.local-db.yml logs dave
```

## Benefits of Local Database

✅ **Fast iteration** - No network latency
✅ **Offline development** - Work anywhere
✅ **Integration testing** - Test with real database
✅ **Data isolation** - Won't pollute cloud database
✅ **RLS policy testing** - Test security policies locally
✅ **Cost savings** - No cloud database usage during dev
✅ **Reset anytime** - `docker-compose down -v` for clean slate

## Next Steps

- Run the test suite: `make test`
- Explore the database: http://localhost:5050
- Start developing: Edit files in `api/` and see changes instantly
