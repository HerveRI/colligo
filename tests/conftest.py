from __future__ import annotations

import os
from collections.abc import AsyncIterator

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://app:changeme@localhost:5432/colligo_test"
)
os.environ.setdefault("EMBED_DIM", "768")
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("EMBED_PROVIDER", "ollama")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
