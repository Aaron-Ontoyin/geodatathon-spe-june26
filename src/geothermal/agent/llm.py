"""Optional LLM layer via LangChain + OpenRouter.

A thin, stateless wrapper: ``build_model`` constructs a LangChain chat model from
``OPENROUTER_API_KEY`` (returning ``None`` when no key or the optional ``llm`` extra
isn't installed), and ``chat`` answers a question **grounded in the deterministic
report** passed as context. Conversation history is supplied by the caller (the
browser holds it) — there is no server-side store. Any model/transport failure
degrades to a plain "unavailable" message, so the core product never depends on it.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

DEFAULT_MODEL = "openai/gpt-4o-mini"
UNAVAILABLE_MESSAGE = (
    "LLM chat is unavailable (set OPENROUTER_API_KEY to enable). "
    "The full deterministic report is available without it."
)


def build_model(*, model: str | None = None, api_key: str | None = None) -> BaseChatModel | None:
    """Build an OpenRouter chat model, or ``None`` if no key / the llm extra is absent."""
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        return None
    os.environ["OPENROUTER_API_KEY"] = key  # init_chat_model reads it from the environment
    model_id = model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
    try:
        return init_chat_model(model_id, model_provider="openrouter")
    except (ImportError, ValueError):
        return None


def invoke_text(model: BaseChatModel, messages: Sequence[tuple[str, str]]) -> str | None:
    """Invoke the model and return its text, or ``None`` on any failure (fail-open)."""
    try:
        response = model.invoke(list(messages))
    except Exception:  # broad by design: any LLM/transport error must degrade gracefully
        return None
    content = response.content
    return content if isinstance(content, str) and content.strip() else None


def chat(
    question: str,
    *,
    context: str,
    history: Sequence[tuple[str, str]] | None = None,
    model: BaseChatModel | None = None,
    api_key: str | None = None,
) -> str:
    """Answer a question grounded in ``context`` (the report); stateless — history is passed in."""
    chat_model = model or build_model(api_key=api_key)
    if chat_model is None:
        return UNAVAILABLE_MESSAGE
    messages: list[tuple[str, str]] = [("system", _system_prompt(context))]
    messages.extend(history or [])
    messages.append(("human", question))
    return invoke_text(chat_model, messages) or UNAVAILABLE_MESSAGE


async def astream_chat(
    question: str,
    *,
    context: str,
    history: Sequence[tuple[str, str]] | None = None,
    model: BaseChatModel | None = None,
    api_key: str | None = None,
) -> AsyncIterator[str]:
    """Stream a grounded answer token-by-token (async); yields text chunks, fail-open."""
    chat_model = model or build_model(api_key=api_key)
    if chat_model is None:
        yield UNAVAILABLE_MESSAGE
        return
    messages: list[tuple[str, str]] = [("system", _system_prompt(context))]
    messages.extend(history or [])
    messages.append(("human", question))
    try:
        async for chunk in chat_model.astream(messages):
            content = chunk.content
            if isinstance(content, str) and content:
                yield content
    except Exception:  # broad by design: a streaming error must not crash the request
        yield "\n[chat interrupted]"


def _system_prompt(context: str) -> str:
    return (
        "You are a geothermal techno-economics analyst. Answer the user's question using ONLY the "
        "report below; if the answer isn't in it, say so plainly. Be concise and precise, and keep "
        "every number consistent with the report.\n\n=== REPORT ===\n" + context
    )
