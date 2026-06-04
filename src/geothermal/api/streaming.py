"""SSE streaming helpers.

``stream_with_progress`` bridges the synchronous core to async SSE: it runs the work
in a worker thread and forwards its progress callback to the client. ``chat_events``
streams grounded chat tokens. Both yield sse-starlette event dicts.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable

from geothermal.agent.llm import astream_chat
from geothermal.api.schemas import ChatRequest
from geothermal.progress import Progress


async def stream_with_progress(
    run: Callable[[Callable[[Progress], None]], dict[str, object]],
) -> AsyncIterator[dict[str, str]]:
    """Run ``run`` (sync, in a thread), streaming its progress events then its result."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

    def on_progress(progress: Progress) -> None:
        loop.call_soon_threadsafe(
            queue.put_nowait,
            (
                "progress",
                {
                    "stage": progress.stage,
                    "done": progress.done,
                    "total": progress.total,
                    "fraction": progress.fraction,
                    "message": progress.message,
                },
            ),
        )

    async def worker() -> None:
        result = await asyncio.to_thread(run, on_progress)
        loop.call_soon_threadsafe(queue.put_nowait, ("result", result))

    task = asyncio.ensure_future(worker())
    try:
        while True:
            kind, payload = await queue.get()
            yield {"event": kind, "data": json.dumps(payload)}
            if kind == "result":
                break
    finally:
        await task


async def chat_events(request: ChatRequest) -> AsyncIterator[dict[str, str]]:
    """Stream grounded chat tokens as SSE events, ending with a 'done' event."""
    async for token in astream_chat(
        request.question,
        context=request.context,
        history=request.history,
        api_key=request.api_key,
    ):
        yield {"event": "token", "data": token}
    yield {"event": "done", "data": ""}
