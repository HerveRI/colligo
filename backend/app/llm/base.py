from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant", "tool"]
FinishReason = Literal["stop", "tool_calls", "length"]


class ProviderError(RuntimeError):
    """Transport or API-level failure."""


class MalformedToolCall(ProviderError):
    """Model emitted something tool-call-shaped that could not be normalized"""

    def __init__(self, reason: str, raw: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.raw = raw


@dataclass(frozen=True)
class TextBlock:
    text: str


@dataclass(frozen=True)
class ToolUseBlock:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResultBlock:
    tool_call_id: str
    name: str
    content: str
    ok: bool = True


ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock


@dataclass(frozen=True)
class Message:
    role: Role
    content: list[ContentBlock]

    @classmethod
    def system(cls, text: str) -> Message:
        return cls("system", [TextBlock(text)])

    @classmethod
    def user(cls, text: str) -> Message:
        return cls("user", [TextBlock(text)])

    @classmethod
    def assistant(cls, blocks: list[ContentBlock]) -> Message:
        return cls("assistant", list(blocks))

    @property
    def text(self) -> str:
        return "".join(b.text for b in self.content if isinstance(b, TextBlock))


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class StreamEnd:
    finish_reason: FinishReason


StreamEvent = TextDelta | ToolCall | StreamEnd


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@runtime_checkable
class ChatProvider(Protocol):
    model: str

    def chat_stream(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> AsyncIterator[StreamEvent]: ...

    async def aclose(self) -> None: ...


@runtime_checkable
class EmbedProvider(Protocol):
    model: str

    @property
    def dim(self) -> int: ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...

    async def aclose(self) -> None: ...


def parse_arguments(raw: Any) -> dict[str, Any]:
    """Make an LLM provider's arguments payload into a dict, or raise."""
    if isinstance(raw, dict):
        return raw
    if raw in (None, ""):
        return {}
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MalformedToolCall("args_not_json", raw) from exc
        if not isinstance(parsed, dict):
            raise MalformedToolCall("args_not_object", raw)
        return parsed
    raise MalformedToolCall("args_unexpected_type", repr(raw))
