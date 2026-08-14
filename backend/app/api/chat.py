from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from app.api.events import (
    Citation,
    DoneData,
    ErrorData,
    EventType,
    TokenData,
    ToolCallStartedData,
    ToolResultData,
    sse,
)
from app.core.config import Settings, SettingsDep

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

_ANSWER = (
    "Based on the retrieved passages, the ingestion pipleine chunks each documet "
    "before embedding, then stores the vectors alongside their source metadata so "
    "answers can point back at specific spans. [1][2]"
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None


# Fake citation for testing purposes
def _fake_citations(n: int, offset: int) -> list[Citation]:
    return [
        Citation(
            chunk_id=f"chunk-{offset + i}",
            document_id=f"doc-{offset}",
            title=f"Stub Document {offset}",
            source=f"seed/stub-{offset}.md",
            position=i,
            score=round(0.91 - i * 0.04, 3),
        )
        for i in range(n)
    ]


# Simulate LLM call loop
async def _stub_stream(
    payload: ChatRequest, request: Request, settings: Settings
) -> AsyncIterator[ServerSentEvent]:
    conversation_id = payload.conversation_id or str(uuid4())
    message_id = str(uuid4())

    try:
        for iteration in range(1, 3):
            if await request.is_disconnected():
                return

            tool_call_id = str(uuid4)
            yield sse(
                EventType.TOOL_CALL_STARTED,
                ToolCallStartedData(
                    tool_call_id=tool_call_id,
                    name="search_documents",
                    arguments={
                        "query": payload.message[:120],
                        "top_k": settings.RETRIEVAL_TOP_K,
                    },
                    iteration=iteration,
                ),
            )
            await asyncio.sleep(0.5)

            if payload.message.strip() == "/error":
                raise RuntimeError("deliberate stub failure")

            yield sse(
                EventType.TOOL_RESULT,
                ToolResultData(
                    tool_call_id=tool_call_id,
                    name="search_documents",
                    ok=True,
                    latency_ms=480,
                    summary=f"{3} chunks above threshold",
                    citations=_fake_citations(3, offset=iteration),
                ),
            )
            await asyncio.sleep(0.2)

        for word in _ANSWER.split(" "):
            if await request.is_disconnected():
                return
            yield sse(EventType.TOKEN, TokenData(text=word + " "))
            await asyncio.sleep(0.04)

        yield sse(
            EventType.DONE,
            DoneData(
                conversation_id=conversation_id,
                message_id=message_id,
                iterations=2,
                finish_reason="complete",
            ),
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("chat stream failed conversation_id=%s", conversation_id)
        yield sse(
            EventType.ERROR,
            ErrorData(
                code="internal_error",
                message="The agent failed while answering. Try again.",
                retryable=True,
            ),
        )


@router.post("/chat")
async def chat(
    payload: ChatRequest, request: Request, settings: SettingsDep
) -> EventSourceResponse:
    return EventSourceResponse(
        _stub_stream(payload, request, settings),
        ping=10,
        headers={
            "Cache-Control": "no-cache, not transform",
            "X-Accel-Buffering": "no",
        },
    )
