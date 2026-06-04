"""Tests for the optional LangChain/OpenRouter LLM layer (Phase 5g).

Uses LangChain's fake chat model so no network/API key is needed; skips entirely if
the optional ``llm`` extra isn't installed.
"""

from __future__ import annotations

import pytest

pytest.importorskip("langchain_core")

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from geothermal.agent import chat, narrate, run_workflow
from geothermal.agent.llm import UNAVAILABLE_MESSAGE, invoke_text


def test_chat_answers_via_injected_model() -> None:
    model = FakeListChatModel(responses=["One well plus storage is the cheapest option."])
    answer = chat("Why one well?", context="REPORT", model=model)
    assert answer == "One well plus storage is the cheapest option."


def test_chat_is_unavailable_without_model_or_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert chat("hi", context="ctx", model=None, api_key=None) == UNAVAILABLE_MESSAGE


def test_narrate_uses_injected_model() -> None:
    result = run_workflow(mc_samples=200)
    model = FakeListChatModel(responses=["A friendly plain-language narration."])
    assert narrate(result, use_llm=True, model=model) == "A friendly plain-language narration."


def test_invoke_text_returns_none_on_blank_response() -> None:
    assert invoke_text(FakeListChatModel(responses=[""]), [("human", "hi")]) is None
