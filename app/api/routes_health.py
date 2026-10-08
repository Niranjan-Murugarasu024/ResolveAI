from fastapi import APIRouter
from app.core.config import settings
from app.services.rag_engine import rag_engine

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "indexed_knowledge_chunks": len(rag_engine.chunks),
        "thresholds": {
            "resolve": settings.RESOLVE_THRESHOLD,
            "review": settings.REVIEW_THRESHOLD
        }
    }
