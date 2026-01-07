from fastapi import APIRouter
from .chat import router as chat_router
from .health import router as health_router
from .knowledge import router as knowledge_router
from .prompts import router as prompts_router
# from .nudges import router as nudges_router # Uncomment if nudges logic is ready

router = APIRouter()

# Health checks (root level)
router.include_router(health_router, tags=["health"])

# API V1 Routes
router.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
router.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["knowledge"])
router.include_router(prompts_router, prefix="/api/v1/admin/prompts", tags=["admin"])