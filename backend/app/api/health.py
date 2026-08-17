from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import SettingsDep
from app.db.session import SessionDep

router = APIRouter(tags=["ops"])


class HealthResponse(BaseModel):
    status: str
    environment: str
    llm_provider: str
    embed_provider: str
    embed_dim: int
    agent_max_iterations: int


@router.get("/health", response_model=HealthResponse)
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        llm_provider=settings.LLM_PROVIDER.value,
        embed_provider=settings.EMBED_PROVIDER.value,
        embed_dim=settings.EMBED_DIM,
        agent_max_iterations=settings.AGENT_MAX_ITERATIONS,
    )


@router.get("/health/ready")
async def ready(session: SessionDep) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database unvailable: {type(exc).__name__}",
        ) from exc
    return {"status": "ready", "database": "ok"}
