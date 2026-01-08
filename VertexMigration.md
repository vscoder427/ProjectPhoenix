# Vertex AI Migration & Maximization Plan

**Author:** Consultant CTO (Claude)
**Date:** January 7, 2026
**Target System:** Google Cloud Vertex AI (Enterprise)
**Current State:** Google Generative AI API (Prototyping)

## 1. Executive Summary

We are currently utilizing Google's AI models via the standard `google-generativeai` SDK and API keys. While functional, this is a "consumer-grade" implementation. To support enterprise growth, HIPAA compliance, and robust security, we must migrate to **Vertex AI**.

This migration changes **how** we access the models, not necessarily **which** models we use (Gemini remains the engine). This pivot lays the foundation for advanced features like Grounding (connecting AI to real-time data), Vector Search, and the ability to swap Gemini for Claude 3.5 Sonnet via the Model Garden without rewriting code.

---

## 2. Current State vs. Vertex AI Future

| Feature | Current State (Legacy) | Future State (Vertex AI) | Why it Matters |
| :--- | :--- | :--- | :--- |
| **SDK** | `google.generativeai` (GenAI) | `vertexai` / `google-cloud-aiplatform` | The Vertex SDK supports enterprise features (logging, private endpoints). |
| **Auth** | API Keys (`GEMINI_API_KEY`) | IAM (Service Accounts / Workload Identity) | **Security.** No static keys to leak. Auth is tied to the running service identity. |
| **Data Privacy** | Public API Endpoint | VPC Service Controls | **Compliance.** Traffic stays within Google's trusted perimeter (crucial for HIPAA). |
| **Rate Limits** | Variable / User-tier | Quota-based / Provisioned Throughput | **Reliability.** Guaranteed capacity for scaling. |
| **Prompts** | Hardcoded Strings | Vertex AI Prompt Management | **Agility.** Non-engineers can edit prompts in the UI without deployments. |
| **Context** | Static RAG (Supabase) | Vertex Vector Search / Grounding | **Intelligence.** Connects AI to Google Search or massive datasets automatically. |

---

## 3. Migration Roadmap

### Phase 1: Infrastructure & Security (Day 1-2)

Before touching code, we must prepare the Google Cloud environment.

1.  **Enable APIs:**
    *   `aiplatform.googleapis.com` (Vertex AI API)
    *   `cloudaicompanion.googleapis.com` (If using Duet AI features)
2.  **IAM Setup:**
    *   Create a Service Account: `sa-dave-ai@<project-id>.iam.gserviceaccount.com`.
    *   Grant Role: `Vertex AI User` (allows model inference).
    *   **Crucial:** Configure **Workload Identity** for Cloud Run. This maps the Cloud Run service to this Service Account, removing the need to download JSON key files.
3.  **Region Selection:**
    *   Standardize on **`us-east4` (Virginia)** to minimize latency for East Coast users and ensure maximum model availability.

### Phase 2: Code Migration - The "Dave" Pilot (Day 3-5)

We will refactor the `Dave` service in `ProjectPhoenix` to use the Vertex SDK.

**Action Items:**
1.  **Dependency Swap:**
    *   Remove `google-generativeai`.
    *   Add `google-cloud-aiplatform`.
2.  **Client Refactor:**
    *   Rewrite `app/clients/gemini.py` to initialize `vertexai.init(project=..., location=...)`.
    *   Replace `genai.GenerativeModel` with `vertexai.generative_models.GenerativeModel`.
3.  **Config Update:**
    *   Remove `GEMINI_API_KEY` from `.env` and `config.py`.
    *   Add `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`.

### Phase 3: n8n Workflow Migration (OUT OF SCOPE)

**Decision:** `n8n` is being deprecated across the Employa ecosystem. No migration of n8n workflows to Vertex AI is required. Existing logic in n8n will be ported directly into the new Python microservices using the `Golden Service` standard.

### Phase 4: Maximizing Vertex (The "Value Add")

Once migrated, we enable features that were previously impossible.

#### 4.1. Grounding with Google Search
*   **The Upgrade:** Currently, Dave might hallucinate facts.
*   **Vertex Feature:** We can enable "Grounding" in the API call.
*   **Benefit:** Dave can answer "What are the latest recovery job fairs in NYC?" with real-time data.

#### 4.2. Vertex AI Prompt Management
*   **The Upgrade:** Move prompts from `prompts.py` or Supabase to the Vertex Console.
*   **Benefit:** The Product Team can tweak the "Dave Persona" prompt in the Google Cloud UI, version it, and test it, without asking devs to push code.

---

## 4. Strategic Decisions Made

1.  **n8n Deprecation:** We will not invest in Vertex integration for n8n. All automation is moving to microservices.
2.  **Regional Focus:** `us-east4` (Virginia) is the primary region for AI workloads to serve our East Coast user base.
3.  **Claude Timeline:** We will continue using **Gemini** as the primary runtime engine. Claude in Model Garden will be evaluated only after the Vertex migration is stabilized.

---

## 5. Immediate Next Step

**Approve the Refactor of `Dave` to Vertex AI SDK.**
I will begin rewriting `services/dave/api/app/clients/gemini.py` to use `vertexai` and strip out the API key logic.
