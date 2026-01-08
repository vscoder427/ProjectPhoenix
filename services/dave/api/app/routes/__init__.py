"""
API Router Setup with Versioning
"""
from fastapi import APIRouter

from .chat import router as chat_router
from .health import router as health_router
from .knowledge import router as knowledge_router
from .prompts import router as prompts_router
# from .nudges import router as nudges_router # Uncomment if nudges logic is ready

# Health checks (root level - no versioning)
health = APIRouter()
health.include_router(health_router, tags=["health"])

# API V1 Routes
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v1_router.include_router(chat_router, prefix="/chat", tags=["chat"])
v1_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
v1_router.include_router(prompts_router, prefix="/admin/prompts", tags=["admin"])

# Future: API V2 Routes
# v2_router = APIRouter(prefix="/api/v2", tags=["v2"])
# v2_router.include_router(chat_v2_router, prefix="/chat", tags=["chat"])

# Main router
router = APIRouter()
router.include_router(health)
router.include_router(v1_router)