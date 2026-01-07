"""
Health Check Endpoints

Provides health, readiness, and liveness checks for Cloud Run.
"""

from fastapi import APIRouter, Depends

from app.clients.supabase import get_supabase_client
from app.clients.gemini import GeminiClient
from app.services.prompt_manager import get_prompt_manager

router = APIRouter()


@router.get("")
async def health():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/live")
async def liveness():
    """Liveness probe - is the service running?"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness():
    """
    Readiness probe - are dependencies available?

    Checks:
    - Supabase connectivity
    - Gemini API availability
    """
    checks = {}
    overall_status = "ready"

    # Check Supabase
    try:
        client = get_supabase_client()
        # Simple query to verify connection
        result = client.table("admin_prompts").select("id").limit(1).execute()
        checks["supabase"] = "ok"
    except Exception as e:
        checks["supabase"] = f"error: {str(e)}"
        overall_status = "not_ready"

    # Check Gemini
    try:
        gemini = GeminiClient()
        # Health check doesn't make API call, just verifies config
        if gemini.is_configured:
            checks["gemini"] = "ok"
        else:
            checks["gemini"] = "not configured"
            overall_status = "not_ready"
    except Exception as e:
        checks["gemini"] = f"error: {str(e)}"
        overall_status = "not_ready"

    return {
        "status": overall_status,
        "checks": checks,
    }


@router.get("/debug/prompts")
async def debug_prompts():
    """
    Debug endpoint to verify prompt loading.

    Shows what prompts Dave is actually loading from the database.
    """
    prompt_manager = get_prompt_manager()
    results = {}

    # Test fetching each prompt Dave needs
    prompt_checks = [
        ("dave_system", "base_personality"),
        ("dave_system", "job_seeker_mode"),
        ("dave_system", "employer_mode"),
        ("dave_system", "treatment_center_mode"),
        ("dave_system", "off_topic_redirect"),
        ("dave_system", "welcome_message"),
        ("recovery_language", "guidelines"),
    ]

    for category, name in prompt_checks:
        try:
            content = await prompt_manager.get_prompt(category, name, use_cache=False)
            if content:
                results[f"{category}/{name}"] = {
                    "status": "found",
                    "preview": content[:100] + "..." if len(content) > 100 else content,
                    "length": len(content),
                }
            else:
                results[f"{category}/{name}"] = {
                    "status": "not_found",
                    "using_fallback": True,
                }
        except Exception as e:
            results[f"{category}/{name}"] = {
                "status": "error",
                "error": str(e),
            }

    # Also get the full system prompt
    try:
        full_prompt = await prompt_manager.get_dave_system_prompt(user_type="job_seeker")
        results["full_system_prompt"] = {
            "status": "built",
            "length": len(full_prompt),
            "preview": full_prompt[:200] + "..." if len(full_prompt) > 200 else full_prompt,
        }
    except Exception as e:
        results["full_system_prompt"] = {
            "status": "error",
            "error": str(e),
        }

    return results
