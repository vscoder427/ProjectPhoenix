# Modernization Scope & Execution Plan

**Project:** Employa Enterprise Service Migration
**Date:** 2026-01-07
**Status:** DRAFT

## 1. Executive Summary

This document defines the scope and execution strategy for migrating the current batch of 8 microservices to the new Employa Enterprise Standards. The goal is to transition from independent, ad-hoc implementations to a unified, scalable, and compliant microservice architecture.

## 2. In-Scope Services (The "Batch of 8")

The following services are targeted for migration. They must be refactored to match the `Golden Service` reference and `Tier 1` standards.

1.  **Dave (Unified AI Gateway)** - *PATHFINDER PILOT*
    *   *Role:* AI Career Coach & Gateway.
    *   *Priority:* Critical (User Facing).
2.  **AAMeetings**
    *   *Role:* Meeting finder and schedule management.
3.  **CareerIntelligence**
    *   *Role:* Market analysis and job matching logic.
4.  **CareerTools**
    *   *Role:* Resume builder, assessment tools.
5.  **ContentCreation**
    *   *Role:* Generative content for marketing/blogs.
6.  **Marketing**
    *   *Role:* User acquisition and public site data.
7.  **Outreach**
    *   *Role:* Email/messaging campaigns.
8.  **UserOnboarding**
    *   *Role:* Signup flows and initial profile setup.

*Note: `ProjectPhoenix` is now the repository for this modernization effort and the home of the Golden Service reference.*

## 3. Migration Strategy: "Strangler Fig"

We will **not** perform a "Big Bang" rewrite. We will use the [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html).

1.  **Phase 1: The Pathfinder (Weeks 1-2)**
    *   **Target:** `Dave`
    *   **Goal:** Prove the `Golden Service` template works in production.
    *   **Actions:**
        *   Re-implement `Dave` using the new FastAPI template.
        *   Implement full Observability (Logging, Tracing, SLOs).
        *   Deploy to Cloud Run alongside the old version.
        *   Cut over traffic via API Gateway.
    *   **Exit Gate:** `Dave` runs in production with <0.1% error rate and full compliance.

2.  **Phase 2: Core Business Logic (Weeks 3-6)**
    *   **Targets:** `CareerIntelligence`, `UserOnboarding`, `AAMeetings`.
    *   **Goal:** Migrating high-value, high-risk services while the team is fresh.
    *   **Actions:** Strict TDD, Security Reviews, and Data Migration testing.

3.  **Phase 4: Supporting Services (Weeks 7-10)**
    *   **Targets:** `CareerTools`, `Marketing`, `Outreach`, `ContentCreation`.
    *   *Note: Section renumbered to Phase 4 to allow for validation phase.*
    *   **Goal:** Velocity. These are lower risk (Tier 2 potential) and should move fast using the lessons from Phase 1 & 2.

## 4. Definition of Done (Per Service)

A service is considered "Migrated" only when it meets the **Strict Governance Gate**:

1.  **Code:** Re-implemented in the `Golden Service` structure.
2.  **Docs:** `docs/spec.md`, `docs/runbook.md`, and `README.md` are complete.
3.  **Compliance:**
    *   CI/CD pipeline passes (Lint, Type Check, Tests).
    *   Security Scans (SAST/SCA) are green.
    *   SBOM is generated.
4.  **Observability:**
    *   /health and /ready endpoints active.
    *   SLOs defined and alerting.
    *   Logs flowing to centralized logging.
5.  **Cleanup:** Old repository/folder archived.

## 5. Success Metrics

*   **Standardization:** 100% of services share the same build pipeline and project structure.
*   **Security:** 0 Critical/High vulnerabilities across the entire fleet.
*   **Reliability:** All Tier 0/1 services have defined SLOs and automated burn-rate alerting.
*   **Velocity:** Onboarding a new developer takes <1 day (vs current ~1 week).
