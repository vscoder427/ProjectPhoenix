# AI-Native Development Standards

**Status:** Active
**Scope:** ProjectPhoenix services only
**Last Updated:** 2026-01-10

---

## Overview

This standard defines principles for safe, mindful AI coding assistance in ProjectPhoenix. It establishes decision frameworks, verification requirements, and MCP server safety guidelines that enable AI agents (like Claude Code) to accelerate development without compromising quality or security.

**Key Principle:** AI is a force multiplier, not a replacement for human expertise. This standard clarifies when AI can proceed autonomously, when human review is required, and when human expertise is mandatory.

---

## Decision Framework: When to Use AI vs. Human Expertise

### Green Tier (AI Autonomous)

AI can proceed without human review for:

- **Boilerplate code following established patterns**
  - Example: Adding health endpoints following [golden-service-python](../../services/golden-service-python/) reference
  - Example: Creating CRUD endpoints using [api-conventions.md](api-conventions.md) patterns

- **Test generation based on existing test patterns**
  - Example: Writing pytest tests following [testing-database-strategy.md](testing-database-strategy.md)
  - Example: Creating contract tests per [testing-rls-policies.md](testing-rls-policies.md)

- **Documentation updates**
  - Example: Updating OpenAPI specs per [openapi-documentation.md](openapi-documentation.md)
  - Example: Adding docstrings following [coding-conventions.md](coding-conventions.md)

- **Code formatting and linting fixes**
  - Example: Running black, isort, flake8, mypy per [formatting-linting-typing.md](formatting-linting-typing.md)

- **Dependency updates (minor/patch versions)**
  - Example: Updating `httpx==0.24.0` → `httpx==0.24.1` per [dependency-management.md](dependency-management.md)

**Verification:** Standard [verification-enforcer](../../../.claude/skills/verification-enforcer/SKILL.md) checks apply (no claims without proof).

**When AI Completes Green Tier Tasks:**
- Tests must pass (verified by actual pytest execution)
- Linting must pass (verified by actual command output)
- No breaking changes to existing functionality
- Follows established patterns (checked against golden-service-python or existing code)

---

### Yellow Tier (AI + Human Review Required)

AI can implement, but human must review before merging:

- **Database schema changes**
  - Migrations, RLS policies, data backfill scripts
  - Why review required: RLS misconfiguration can expose PHI
  - Verification: [Database Schema Changes](#database-schema-changes) checklist

- **Security-sensitive code**
  - Authentication, authorization, encryption, PHI handling
  - Why review required: Security vulnerabilities can violate HIPAA
  - Verification: [Security-Sensitive Code](#security-sensitive-code) checklist

- **External API integrations**
  - New third-party services, webhook handlers
  - Why review required: Data leakage, vendor compliance risks
  - Verification: [External API Integrations](#external-api-integrations) checklist

- **Performance-critical code**
  - Caching, query optimization, rate limiting
  - Why review required: Performance regressions impact user experience
  - Verification: Load testing, profiling results

- **Major refactoring**
  - Architectural changes, design pattern migrations
  - Why review required: Ripple effects across codebase
  - Verification: Comprehensive test coverage (85%+), no behavior changes

**Verification:**
- AI [verification-enforcer](../../../.claude/skills/verification-enforcer/SKILL.md) checks (test results, deployment status) **PLUS**
- Human code review (PR approval required)
- Security scan results reviewed by human (Trivy, Semgrep, Bandit)

**When AI Completes Yellow Tier Tasks:**
- PR created with detailed description
- All automated verification passed (tests, linting, security scans)
- Reviewer checklist provided (see [Verification Checkpoints](#verification-checkpoints-for-high-risk-operations))
- Rollback plan documented (if database migration or deployment)

---

### Red Tier (Human Required)

Human expertise required, AI assists only:

- **HIPAA compliance attestations**
  - Business Associate Agreement (BAA) reviews
  - Risk analysis documentation
  - Why human required: Legal liability, regulatory compliance

- **Production incident response**
  - Debugging live outages, emergency patches
  - Why human required: High-stakes decision-making, context-dependent troubleshooting

- **Threat model creation/updates**
  - STRIDE analysis for new features
  - Attack surface assessments
  - Why human required: Adversarial thinking, domain expertise

- **Architecture Decision Records (ADRs)**
  - Significant architectural choices (database selection, framework adoption)
  - Why human required: Long-term implications, tradeoff analysis

- **Major dependency upgrades**
  - Example: Python 3.11 → 3.13, FastAPI 0.100 → 0.110
  - Why human required: Breaking changes, migration complexity

**Verification:**
- Human-led process
- AI can generate drafts for human review
- Final approval by human expert (architect, security engineer, compliance officer)

**When AI Assists Red Tier Tasks:**
- Provide research summaries (exploration of existing patterns)
- Generate draft documentation (human edits and approves)
- Suggest implementation approaches (human selects final approach)
- Never claim completion without human sign-off

---

## MCP Server Safety Guidelines

### What Are MCP Servers?

**Model Context Protocol (MCP)** servers extend Claude Code's capabilities by providing:
- External service access (GitHub, Supabase, Stripe, etc.)
- Centralized tools for common operations (search repositories, query databases)
- Context efficiency (single tool vs. multiple API calls)

**Current Active MCP Servers (Workspace-Level):**
- **GitHub** (135+ tools) - Repository search, issue management, PR operations
- **Supabase** (37 tools) - Database queries, RLS policy inspection, table management

**See:** [CLAUDE.md](../../../CLAUDE.md#mcp-server-configuration-vscode-extension) for full MCP configuration.

---

### When to Add New MCP Servers

**Add MCP server when:**

✅ **Feature requires >5 API calls to external service** (efficiency threshold)
- Example: Adding Stripe billing requires 10+ API calls (customers, subscriptions, invoices, payments, etc.)
- MCP server reduces this to single-tool invocations

✅ **External service has official MCP server available** (prefer official implementations)
- Example: GitHub MCP server is officially maintained by Anthropic
- Reduces security risk, maintenance burden

✅ **Context efficiency: MCP reduces token usage vs. direct API calls**
- Example: MCP tool uses 50 tokens, equivalent API calls use 200 tokens
- Saves 75% context budget

✅ **Team will use MCP server across multiple projects**
- Example: Supabase MCP server used by Dave, UserOnboarding, Outreach, CareerIntelligence
- Justifies upfront integration effort

**Do NOT add MCP server when:**

❌ **Feature needs 1-2 API calls** (use direct HTTP requests)
- Example: Single webhook POST to n8n workflow
- Direct `curl` or `httpx` call is simpler

❌ **External service lacks official MCP server and custom server effort >2 hours**
- Example: Building custom MCP server for niche API
- Cost exceeds benefit for low-frequency use

❌ **Security risk: MCP server requires broad credentials** (e.g., admin access)
- Example: MCP server needs `repo:admin` scope for single read operation
- Violates least privilege principle

❌ **Context cost: MCP server tools add >2k tokens to every session**
- Example: MCP server with 50 rarely-used tools
- Bloats context window, triggers compaction

---

### MCP Server Configuration Standards

**Store credentials in `.env.workspace` (never hardcode in config):**

```json
// .vscode/settings.json (workspace-level MCP config)
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "--env-file", ".env.workspace", "mcp/github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

**`.env.workspace` (gitignored, never committed):**
```bash
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxxx
SUPABASE_ACCESS_TOKEN=sbp_xxxxxxxxxxxxx
```

**✅ Do:**
- Use `${VARIABLE_NAME}` pattern in `.mcp.json` or VSCode settings
- Document MCP server purpose in config file comments
- Disable unused MCP servers to save context (example: Notion, Stripe disabled in 2026-01-10 consolidation)
- Test MCP server locally before committing config

**❌ Don't:**
- Hardcode credentials in MCP config files (security violation)
- Commit `.env.workspace` to git (add to `.gitignore`)
- Add project-specific MCP servers to workspace config (use `{project}/.mcp.json` instead)
- Enable all MCP servers by default (context bloat)

---

### MCP Usage in Multi-Agent Workflows

MCP servers integrate seamlessly with agent-based execution:

**Exploration agent can use MCP to research external repos:**
```python
Task(
  subagent_type="Explore",
  description="Research FastAPI health endpoint patterns",
  prompt="""Use mcp__github__search_repositories to find similar implementations:

  Search: "topic:fastapi health endpoint"
  Use mcp__github__get_file_contents to read reference code

  Report: Patterns discovered, file paths, code snippets"""
)
```

**Testing agent can use MCP to query database state:**
```python
Task(
  subagent_type="general-purpose",
  description="Verify RLS policies",
  prompt="""Use mcp__supabase__execute_sql to test RLS:

  1. Query as anonymous user (should fail)
  2. Query as authenticated user (should succeed)
  3. Query as admin (should bypass RLS)

  Report: RLS behavior verified"""
)
```

**Verification agent can use MCP to validate deployments:**
```python
# Future: MCP server for GCP Cloud Run
# mcp__cloudrun__get_service_status to verify deployment
```

**Key Principle:** MCP servers reduce context bloat when used correctly (centralized tools vs. duplicated code).

---

## Verification Checkpoints for High-Risk Operations

**Standard Verification (All Operations):**
- [verification-enforcer](../../../.claude/skills/verification-enforcer/SKILL.md) principles apply (no claims without proof)
- Test verification: Actual pytest output required (not assertions)
- Deployment verification: Health check confirmation required

**Additional Verification for Yellow Tier (AI + Human Review):**

---

### Database Schema Changes

**Required Verification:**

✅ **Migration script tested in local Supabase instance**
```bash
cd {project}/api
supabase migration new {migration_name}      # Create migration
supabase db reset                            # Test in local database
```

✅ **RLS policies tested with test users (different roles)**
```bash
pytest tests/test_rls_policies.py -v        # Verify RLS policies
# See: testing-rls-policies.md for comprehensive RLS testing patterns
```

✅ **Data backfill script tested (if data migration required)**
```bash
# Test on local Supabase instance first, NEVER production
python scripts/backfill_{feature}.py --dry-run
python scripts/backfill_{feature}.py --limit 10  # Test with small batch
```

✅ **Rollback plan documented (how to undo migration)**
```markdown
## Rollback Plan

**If migration fails:**
1. Revert to previous migration: `supabase db reset --to {previous_migration_version}`
2. Restore data from backup: `supabase db dump --data-only > rollback.sql`
3. Verify service health: `curl https://{service-url}/health`

**Expected downtime:** < 5 minutes
**Data loss risk:** None (migration is reversible)
```

**Reference Standards:**
- [Database RLS Policies](database-rls-policies.md)
- [DB Isolation and Migrations](db-isolation-migrations.md)
- [Testing RLS Policies](testing-rls-policies.md)
- [Testing Database Strategy](testing-database-strategy.md)

---

### Security-Sensitive Code

**Required Verification:**

✅ **SAST scan completed (Semgrep/Bandit)**
```bash
semgrep --config=auto {file_path}           # SAST scan
bandit -r {project}/api/app/                # Python security scan
```

✅ **Dependency vulnerability scan (Safety)**
```bash
safety check --file requirements.txt        # Dependency vulnerabilities
```

✅ **Threat model updated (STRIDE method)**
```markdown
## Threat Model Update

**Feature:** User authentication with JWT

**STRIDE Analysis:**
- **Spoofing:** JWT signature verification prevents token forgery
- **Tampering:** Token expiry limits replay attack window
- **Repudiation:** Audit logs track all authentication attempts
- **Information Disclosure:** Tokens stored in httpOnly cookies (not localStorage)
- **Denial of Service:** Rate limiting on /auth endpoints (10 req/min per IP)
- **Elevation of Privilege:** Role-based access control (RBAC) enforced via RLS

See: [Threat Modeling](compliance/threat-modeling.md)
```

✅ **Secrets not hardcoded (GCP Secret Manager only)**
```bash
# Verify no secrets in code
git grep -i "password\|secret\|api_key" -- "*.py" "*.js" "*.ts"
# Should return 0 results (or only references to environment variables)
```

**Reference Standards:**
- [Security and Secrets](security/security-secrets.md)
- [Auth and JWT](security/auth-jwt.md)
- [Threat Modeling](compliance/threat-modeling.md)
- [Security Review Checklist](compliance/security-review-checklist.md)

**See Also:** [security-engineer skill](../../../.claude/skills/security-engineer/SKILL.md) for comprehensive security guidance

---

### External API Integrations

**Required Verification:**

✅ **API contract documented (OpenAPI spec or vendor docs)**
```yaml
# Document external API in OpenAPI spec
/integrations/{vendor}/webhook:
  post:
    summary: Handle webhook from {vendor}
    externalDocs:
      description: Vendor webhook documentation
      url: https://docs.vendor.com/webhooks
```

✅ **Error handling tested (network failures, rate limits, invalid responses)**
```bash
pytest tests/test_{service}_integration.py -v  # Integration tests
# Test cases:
# - Network timeout (mocked connection error)
# - Rate limit exceeded (429 response)
# - Invalid JSON response (malformed payload)
# - Authentication failure (401/403 response)
```

✅ **Credentials stored in GCP Secret Manager (not .env)**
```bash
# Verify secret exists in GCP Secret Manager
gcloud secrets describe {vendor}-api-key --format json

# Verify service account has access
gcloud secrets get-iam-policy {vendor}-api-key
```

✅ **Integration tested in Cloud Run environment (not just local)**
```bash
gcloud run services describe {service}         # Verify secrets mounted
curl https://{service-url}/integrations/{vendor}/test  # Test endpoint
```

**Reference Standards:**
- [API Conventions](api-conventions.md)
- [Config and Secrets Implementation](config-secrets-implementation.md)
- [Vendor Management](compliance/vendor-management.md)

**See Also:** [api-integration-engineer skill](../../../.claude/skills/api-integration-engineer/SKILL.md)

---

## Standards Inheritance

**Scope:** This standard applies to **ProjectPhoenix services only**.

**Other Employa projects:**
- Warp, Dave, CareerIntelligence, UserOnboarding, Outreach, AAMeetings, CareerTools, SocialMedia, ContentCreation, Marketing
- These projects MAY adopt AI-native standards if beneficial (not required)

**Future expansion:**
- If AI-native standards prove valuable in ProjectPhoenix, consider promoting to workspace-wide standard (document in [CLAUDE.md](../../../CLAUDE.md))
- Recovery-focused AI principles (for Dave chatbot) may be added as separate standard in `Dave/RECOVERY-FOCUSED-AI-GUIDE.md`
- Refactoring patterns may be added as expansion to [refactoring-specialist skill](../../../.claude/skills/refactoring-specialist/SKILL.md)

**Relationship to existing standards:**
- **Complements** [verification-enforcer skill](../../../.claude/skills/verification-enforcer/SKILL.md) (no duplication)
- **References** existing skills:
  - [security-engineer](../../../.claude/skills/security-engineer/SKILL.md) for security review guidance
  - [testing-engineer](../../../.claude/skills/testing-engineer/SKILL.md) for test verification patterns
  - [deployment-engineer](../../../.claude/skills/deployment-engineer/SKILL.md) for deployment verification
- **Extends** multi-agent orchestration patterns documented in [CLAUDE.md](../../../CLAUDE.md#multi-agent-workflows-new---2026-01-10)

---

## Integration with Service Development Workflow

This standard integrates with the existing 8-phase Service Development Workflow (see [ProjectPhoenix/CLAUDE.md](../../CLAUDE.md)):

**Phase 1: Issue Selection & Understanding** → **Apply Decision Framework (Green/Yellow/Red)**
- Green tier: Proceed autonomously (standard verification applies)
- Yellow tier: Plan for human review checkpoint before merge
- Red tier: Escalate to human expert, AI assists only

**Phase 3: Implementation (TDD)** → **Apply Verification Checkpoints**
- Database migrations: Follow [Database Schema Changes](#database-schema-changes) checklist
- Security code: Follow [Security-Sensitive Code](#security-sensitive-code) checklist
- API integrations: Follow [External API Integrations](#external-api-integrations) checklist

**Phase 6: Pull Request** → **Yellow Tier Requires Reviewer Checklist**
- PR description includes verification checklist
- All automated checks passed (tests, linting, security scans)
- Rollback plan documented (if applicable)

**Phase 7: Code Review** → **Human Review for Yellow/Red Tier**
- Code reviewer verifies AI verification claims (test results, security scans)
- Reviews rollback plan adequacy
- Approves architectural decisions for Red tier

---

## Key Principles

1. **Minimal Viable Standards** - Document what's essential, expand based on usage
2. **No Development Slowdown** - Framework clarifies when to proceed vs. ask (saves time)
3. **Leverage Existing Verification** - Reference skills, don't duplicate
4. **ProjectPhoenix-Specific** - Other projects may adopt later (not forced)
5. **Foundation for Future Expansion** - Recovery-focused AI, refactoring patterns can be added incrementally

---

## Appendix: Example Workflows

### Example 1: Green Tier - Adding Health Endpoint

**Task:** "Add /health endpoint to UserOnboarding service following golden-service-python pattern"

**Decision:** Green Tier (AI Autonomous)
- Reason: Boilerplate code following established pattern
- Verification: Standard verification-enforcer (tests pass, linting passes)

**AI Workflow:**
1. **Exploration:** Read `golden-service-python/app/api/v1/endpoints/health.py`
2. **Implementation:** Create `UserOnboarding/api/app/api/v1/endpoints/health.py` following pattern
3. **Testing:** Write test in `tests/test_health.py`, verify with pytest
4. **Verification:** Run `pytest tests/test_health.py -v` (must pass)
5. **Completion:** PR created, no human review required (Green tier)

**Time saved:** ~20 minutes (no waiting for human review)

---

### Example 2: Yellow Tier - Database Migration for New Feature

**Task:** "Add `user_preferences` table with RLS policies for multi-tenant isolation"

**Decision:** Yellow Tier (AI + Human Review)
- Reason: Database schema change with RLS policies (PHI protection risk)
- Verification: [Database Schema Changes](#database-schema-changes) checklist + human review

**AI Workflow:**
1. **Exploration:** Research existing RLS patterns in `testing-rls-policies.md`
2. **Implementation:** Create migration script, RLS policies, test cases
3. **Verification:**
   - ✅ Test migration in local Supabase: `supabase db reset`
   - ✅ Test RLS policies: `pytest tests/test_rls_policies.py -v`
   - ✅ Document rollback plan: "Revert to migration version X"
4. **PR Creation:** Include verification checklist in PR description
5. **Human Review:** Security engineer reviews RLS policies, approves merge

**Time saved:** ~1 hour (AI handles implementation, human reviews only critical parts)

---

### Example 3: Red Tier - HIPAA Risk Analysis

**Task:** "Conduct HIPAA risk analysis for new Dave chatbot feature (conversation history storage)"

**Decision:** Red Tier (Human Required)
- Reason: HIPAA compliance attestation (legal liability)
- AI Role: Assist only (research, draft, defer to human)

**AI Workflow:**
1. **Research:** Read `compliance/hipaa-risk-analysis.md` for template
2. **Draft Generation:** Create draft risk analysis with AI-generated threat scenarios
3. **Human Review:** Compliance officer reviews, edits, approves
4. **AI Finalization:** Format approved content per documentation standards

**Time saved:** ~30 minutes (AI generates draft, human focuses on expert review)

---

## FAQ

**Q: Why are AI-native standards needed? Aren't existing skills enough?**

A: Existing skills define *how* to perform tasks (testing, security, deployment). AI-native standards define *when* AI should perform tasks autonomously vs. when human expertise is required. This prevents AI from overstepping boundaries (e.g., auto-merging database migrations without review).

**Q: Will this slow down development?**

A: No. Green tier (80% of work) proceeds autonomously. Yellow tier gets clearer checkpoints (saves debugging time). Red tier was already requiring human input (no change). The framework makes decisions faster, not slower.

**Q: How do I know if my task is Green/Yellow/Red?**

A: Use this decision tree:
1. Is it boilerplate code following established patterns? → **Green**
2. Does it involve database, security, or external APIs? → **Yellow**
3. Does it involve legal compliance, architecture decisions, or production incidents? → **Red**

**Q: Can I override the tier decision?**

A: Yes, with justification. Example: "This database migration is trivial (single column addition), treating as Green tier despite being database change." Document reasoning in PR.

**Q: Where can I find examples of verification checkpoints in practice?**

A: See existing skills:
- [verification-enforcer](../../../.claude/skills/verification-enforcer/SKILL.md) - Verification format examples
- [testing-engineer](../../../.claude/skills/testing-engineer/SKILL.md) - Test verification examples
- [deployment-engineer](../../../.claude/skills/deployment-engineer/SKILL.md) - Deployment verification examples

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-10 | Initial release - Decision framework, MCP safety, verification checkpoints |

---

**Owned by:** Engineering Team
**Review Cycle:** Quarterly (March, June, September, December)
**Next Review:** 2026-03-10
