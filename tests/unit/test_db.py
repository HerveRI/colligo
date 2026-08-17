from __future__ import annotations

from app.core.config import get_settings
from app.db import models
from app.db.base import RAG_SCHEMA
from app.db.session import get_session
from app.main import app

MODELS = (models.Document, models.Chunk, models.Conversation, models.Message, models.ToolCall)


def test_models_land_in_rag_schema() -> None:
    for model in MODELS:
        assert model.__table__.schema == RAG_SCHEMA


def test_embedding_columns_matches_configured_dim() -> None:
    assert models.Chunk.__table__.c.embedding.type.dim == get_settings().EMBED_DIM


async def test_ready_ok_with_stub_session(client) -> None:
    class _StubSession:
        async def execute(self, *_a, **_kw):
            return None

    async def _override():
        yield _StubSession()

    app.dependency_overrides[get_session] = _override
    try:
        r = await client.get("/health/ready")
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()


async def test_ready_503_when_database_down(client) -> None:
    class _BrokenSession:
        async def execute(self, *_a, **_kw):
            raise ConnectionError("down")

    async def _override():
        yield _BrokenSession()

    app.dependency_overrides[get_session] = _override
    try:
        r = await client.get("/health/ready")
        assert r.status_code == 503
    finally:
        app.dependency_overrides.clear()
