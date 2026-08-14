from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field
from sse_starlette.sse import ServerSentEvent


class EventType(StrEnum):
    TOKEN = "token"
    TOOL_CALL_STARTED = "tools_call_started"
    TOOL_RESULT = "tool_result"
    DONE = "done"
    ERROR = "error"


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    source: str
    position: int
    score: float


class TokenData(BaseModel):
    text: str


class ToolCallStartedData(BaseModel):
    tool_call_id: str
    name: str
    arguments: dict[str, Any]
    iteration: int


class ToolResultData(BaseModel):
    tool_call_id: str
    name: str
    ok: bool
    latency_ms: int
    summary: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    error: str | None = None


class DoneData(BaseModel):
    conversation_id: str
    message_id: str
    iterations: int
    finish_reason: Literal["complete", "max_iterations", "cancelled"]


class ErrorData(BaseModel):
    code: str
    message: str
    retryable: bool = False


# Json-encode the payload and make it a ServerSentEvent
def sse(event: EventType, data: BaseModel) -> ServerSentEvent:
    return ServerSentEvent(event=event.value, data=data.model_dump_json())
