from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import dispose_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info(
        "colligo up | env=%s llm=%s embed=%s(%s) dim=%d max_iter=%d",
        settings.ENVIRONMENT,
        settings.LLM_PROVIDER.value,
        settings.EMBED_PROVIDER.value,
        settings.embed_model,
        settings.EMBED_DIM,
        settings.AGENT_MAX_ITERATIONS,
    )
    yield
    await dispose_engine()
    logger.info("colligo down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="colligo", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    return app


app = create_app()
