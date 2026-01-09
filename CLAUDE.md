# ProjectPhoenix - Enterprise Service Modernization Initiative

## Mission
Transform 8 legacy Employa microservices into a unified, enterprise-grade platform following the "Golden Service" reference implementation, strict governance gates, and HIPAA compliance standards.

## Architecture Overview

### Golden Service Template
**Location:** `/services/golden-service-python/`
**Purpose:** Canonical FastAPI microservice reference implementation with all required patterns

**Key Features:**
- FastAPI with Pydantic v2 validation
- mTLS and JWT authentication
- Structured JSON logging (OpenTelemetry)
- Health, metrics, and readiness endpoints
- Redis caching layer
- Supabase integration with RLS policies
- Automated CI/CD with GitHub Actions
- 85%+ test coverage (pytest)

### Modernization Roadmap (8 Services)

**Phase 1 - Pathfinder (Weeks 1-2):** **CURRENTLY IN PROGRESS**
- **Dave** (`/services/dave/`) - User-facing AI career coach gateway
- **Status:** Active development, migrating from legacy to Golden Service pattern

**Phase 2 - Core Business Logic (Weeks 3-6):**
- **CareerIntelligence** - Resume analysis, career path recommendations
- **UserOnboarding** - Registration, profile creation, onboarding flows
- **AAMeetings** - Recovery meeting locator and scheduler

**Phase 3 - Supporting Services (Weeks 7-10):**
- **CareerTools** - Job search utilities, application tracking
- **Marketing** - Campaign management, email templates
- **Outreach** - External integrations, partner APIs
- **ContentCreation** - AI-powered content generation

### Parallel Initiative: Vertex AI Migration
**Goal:** Migrate all AI-powered services from Google Gemini to Vertex AI for HIPAA compliance
**Affected Services:** Dave, CareerIntelligence, ContentCreation
**Timeline:** Parallel to service modernization

## Technology Stack

### Backend & APIs
- **Language:** Python 3.12+
- **Framework:** FastAPI
- **Validation:** Pydantic v2
- **API Spec:** OpenAPI 3.1.0
- **Async:** asyncio, httpx

### Infrastructure
- **Platform:** Google Cloud Run (serverless containers)
- **Secrets:** GCP Secret Manager
- **Observability:** Cloud Logging, Cloud Monitoring
- **Metrics:** OpenTelemetry

### Data & Caching
- **Primary Database:** Supabase (PostgreSQL 15+)
- **Caching:** Redis
- **Security:** Row-Level Security (RLS) policies

### AI/ML
- **Current:** Google Gemini API
- **Target:** Vertex AI (HIPAA-compliant)
- **Use Cases:** Career coaching, resume analysis, content generation

### Security
- **Authentication:** JWT tokens
- **Service-to-Service:** mTLS
- **Secrets:** Never in code, always GCP Secret Manager
- **Scanning:** SAST (Bandit), SCA (Safety), Trivy container scans

### CI/CD
- **VCS:** GitHub (GitHub Flow branching)
- **Pipelines:** GitHub Actions
- **Build:** Cloud Build
- **Deployment:** Automated to Cloud Run

## Compliance & Standards

### HIPAA Compliance
- PHI/recovery data encrypted at rest and in transit
- Business Associate Agreement (BAA) with GCP
- Audit logging for all PHI access
- Data retention and deletion policies

### GDPR/CCPA
- Data privacy by design
- Right to erasure
- Consent management
- Data portability

### Governance Gates ("Definition of Done")
Every service must pass **5 gates** before production:
1. **Code Quality:** 85%+ test coverage, linting, type hints
2. **Documentation:** OpenAPI spec, runbooks, ADRs
3. **Compliance:** HIPAA checklist, threat model, security scan
4. **Observability:** Structured logging, metrics, health endpoints
5. **Cleanup:** No TODOs, secrets removed, dead code eliminated

### Standards Library
**Location:** `/docs/standards/`
**60+ Standards Documents covering:**
- **Architecture:** API conventions, microservice patterns, event-driven design
- **Security:** Secrets management, mTLS, threat modeling, SAST/SCA
- **Compliance:** HIPAA checklist, PHI handling, audit logging
- **Testing:** TDD workflows, pytest patterns, coverage enforcement
- **Operations:** Runbooks, incident response, release readiness
- **Documentation:** ADR templates, OpenAPI conventions, recovery-focused language

## Workspace Skills - When to Use Which

### Backend Development
**Primary Skills:**
- **backend-developer** - FastAPI microservices, Cloud Run deployment, async patterns
- **api-integration-engineer** - Supabase integration, external APIs, OpenAPI specs
- **security-engineer** - mTLS, JWT auth, secrets management, HIPAA compliance

**Use Cases:**
- Building new endpoints in Dave or other services
- Integrating with Supabase database
- Implementing authentication/authorization
- Writing FastAPI middleware or dependencies

### AI/ML Integration
**Primary Skills:**
- **ai-ml-engineer** - Gemini/Vertex AI integration, recovery-focused prompts, HIPAA-compliant AI
- **performance-engineer** - AI response optimization, caching strategies

**Use Cases:**
- Migrating Dave from Gemini to Vertex AI
- Writing recovery-focused career coaching prompts
- Implementing AI response caching
- Optimizing token usage and latency

### Database & Data Migration
**Primary Skills:**
- **sql-pro** - Supabase/PostgreSQL queries, RLS policies, indexing
- **data-migration-engineer** - Schema migrations, zero-downtime deployments, data backfills

**Use Cases:**
- Writing RLS policies for PHI data
- Creating database migrations for service modernization
- Optimizing queries for performance
- Backfilling data from legacy services

### Infrastructure & DevOps
**Primary Skills:**
- **devops-engineer** - GCP infrastructure, Terraform, Cloud Run, Secret Manager
- **deployment-engineer** - CI/CD pipelines, semantic versioning, release readiness
- **monitoring-observability-engineer** - OpenTelemetry, structured logging, SLI/SLO

**Use Cases:**
- Setting up Cloud Run services
- Writing GitHub Actions workflows
- Implementing structured logging
- Creating health and metrics endpoints
- Defining SLOs for service availability

### Security & Compliance
**Primary Skills:**
- **security-engineer** - HIPAA compliance, threat modeling, SAST/SCA, mTLS
- **sql-pro** - RLS policies, secure query patterns

**Use Cases:**
- HIPAA compliance checklist for new services
- Threat modeling for Dave AI gateway
- Implementing mTLS between services
- Writing secure API endpoints
- Scanning for vulnerabilities (Bandit, Safety, Trivy)

### Testing & Quality
**Primary Skills:**
- **testing-engineer** - TDD, pytest, 85% coverage enforcement, integration tests
- **performance-engineer** - Load testing, API optimization, autoscaling

**Use Cases:**
- Writing pytest fixtures for FastAPI
- Achieving 85%+ test coverage
- Integration tests for Supabase
- Load testing Dave service
- Optimizing slow endpoints

### Documentation
**Primary Skills:**
- **documentation-engineer** - Technical writing, OpenAPI specs, ADRs, runbooks
- **git-workflow-manager** - Semantic versioning, conventional commits

**Use Cases:**
- Writing OpenAPI specs for new endpoints
- Creating ADRs for architectural decisions
- Documenting runbooks for service operations
- Updating standards in `/docs/standards/`
- Writing migration guides for legacy-to-Golden Service transitions

### Code Quality & Refactoring
**Primary Skills:**
- **refactoring-specialist** - Code smell detection, safe refactoring, pattern extraction
- **git-workflow-manager** - Semantic commits, branching strategy

**Use Cases:**
- Refactoring legacy Dave code to Golden Service patterns
- Extracting shared utilities from services
- Removing code smells and technical debt
- Safe refactoring with test coverage

### Frontend (Warp Integration)
**Primary Skills:**
- **ui-designer** - Recovery-focused UI, shadcn/ui, accessibility, Tailwind CSS
- **ux-researcher** - Trauma-informed research, recovery-focused personas

**Use Cases:**
- Designing UI for Dave chatbot in Warp
- Ensuring accessibility for recovery-focused users
- Writing recovery-focused microcopy
- User research for career coaching features

## Key Standards to Follow

### API Conventions
- **Endpoints:** RESTful naming, versioning (`/v1/...`)
- **Request/Response:** JSON with Pydantic validation
- **Errors:** RFC 7807 Problem Details format
- **OpenAPI:** 3.1.0 spec with examples

### Testing Standards
- **Coverage:** 85%+ (enforced in CI)
- **Framework:** pytest with async support
- **Fixtures:** Shared fixtures in `conftest.py`
- **Integration:** Test against real Supabase (test project)

### Security Standards
- **Secrets:** GCP Secret Manager only, never in code or `.env`
- **Authentication:** JWT for users, mTLS for services
- **HIPAA:** Encrypt PHI, audit all access, enforce RLS
- **Scanning:** Bandit (SAST), Safety (SCA), Trivy (containers)

### Observability Standards
- **Logging:** Structured JSON (OpenTelemetry format)
- **Metrics:** Health (`/health`), readiness (`/ready`), metrics (`/metrics`)
- **Tracing:** OpenTelemetry trace IDs in all logs
- **SLOs:** Define availability, latency, error rate targets

### Git Workflow
- **Branching:** GitHub Flow (feature branches, PR to main)
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Versioning:** Semantic versioning (SemVer 2.0.0)
- **PRs:** Require approval, passing tests, no merge commits

## Project-Specific Patterns

### Golden Service Structure
```
services/golden-service-python/
├── app/
│   ├── api/         # FastAPI routes
│   ├── core/        # Config, logging, dependencies
│   ├── models/      # Pydantic schemas
│   ├── services/    # Business logic
│   └── main.py      # FastAPI app
├── tests/           # pytest tests
├── Dockerfile       # Cloud Run container
├── requirements.txt
└── README.md
```

### Service Specifications
**Location:** `/docs/services/<service>/spec.md`
**Contains:** Endpoints, data models, dependencies, migration notes

### Release Artifacts
**Location:** `/docs/releases/<service>/<date>-<tag>/`
**Contains:** Release notes, readiness checklist, rollback plan, performance baselines

## Common Commands

### Local Development
```bash
# Start Dave service locally
cd services/dave
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Run tests
pytest --cov=app --cov-report=term-missing

# Lint and type check
ruff check app/
mypy app/
```

### Cloud Run Deployment
```bash
# Deploy Dave to Cloud Run
gcloud run deploy dave-service \
  --source ./services/dave \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10
```

### Database Migrations
```bash
# Create migration
cd services/dave
alembic revision --autogenerate -m "Add career_goals table"

# Apply migration
alembic upgrade head
```

## GitHub CLI Configuration
**IMPORTANT:** `gh` CLI is NOT in system PATH on Windows. Always use full path:

```bash
"C:\Program Files\GitHub CLI\gh.exe" issue list --repo vscoder427/ProjectPhoenix
"C:\Program Files\GitHub CLI\gh.exe" pr create --title "feat(dave): add career coaching endpoint" --body "..."
```

## Next Steps for Claude Code

When working on ProjectPhoenix:

1. **Understand the phase:** Is this Dave (Phase 1), core services (Phase 2), or supporting services (Phase 3)?
2. **Reference Golden Service:** Always check `/services/golden-service-python/` for patterns
3. **Follow standards:** Consult `/docs/standards/` for architecture, security, testing guidelines
4. **Use appropriate skills:** Reference the "When to Use Which" section above
5. **Enforce governance gates:** Code quality, documentation, compliance, observability, cleanup
6. **Maintain HIPAA compliance:** PHI encryption, audit logging, RLS policies
7. **Write recovery-focused code:** Follow trauma-informed principles (see `documentation-engineer` skill)

All 16 workspace skills are available automatically. Use them explicitly when needed:
- "Use **backend-developer** skill to implement this FastAPI endpoint"
- "Use **security-engineer** skill to review this HIPAA compliance checklist"
- "Use **ai-ml-engineer** skill to migrate this Gemini integration to Vertex AI"
