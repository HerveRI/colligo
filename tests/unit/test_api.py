from __future__ import annotations

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["embed_dim"] == 768


async def _collect_event_names(client: AsyncClient, message: str) -> list[str]:
    names: list[str] = []
    async with client.stream("POST", "/chat", json={"message": message}) as res:
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/event-stream")
        async for line in res.aiter_lines():
            if line.startswith("event:"):
                names.append(line.split(":", 1)[1].strip())

    return names


async def test_chat_stream_emits_full_contract(client: AsyncClient) -> None:
    names = await _collect_event_names(client, "how does ingestion work?")
    assert names[0] == "tool_call_started"
    assert names.count("tool_call_started") == 2
    assert "tool_result" in names
    assert "token" in names
    assert names[-1] == "done"


async def test_chat_stream_reports_failure_as_event_not_500(client: AsyncClient) -> None:
    names = await _collect_event_names(client, "/error")
    assert names[-1] == "error"
    assert "done" not in names
