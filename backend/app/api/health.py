from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import SettingsDep

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
