"""Narration for the agentic workflow.

``narrate_deterministic`` produces a fixed, reproducible decision-log narration with
no external calls. ``narrate`` returns that by default; with ``use_llm=True`` and an
available model (OpenRouter key + the ``llm`` extra) it rewrites the log
conversationally, falling back to the deterministic text on any failure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from geothermal.agent.llm import build_model, invoke_text
from geothermal.agent.workflow import WorkflowResult

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

_NARRATE_SYSTEM = (
    "Rewrite the decision log below as a clear, plain-language narrative for a smart "
    "non-specialist, preserving every number and decision. Be concise; invent nothing."
)


def narrate(
    result: WorkflowResult,
    *,
    use_llm: bool = False,
    model: BaseChatModel | None = None,
    api_key: str | None = None,
) -> str:
    """Narrate the workflow; uses the LLM only if requested and available, else deterministic."""
    deterministic = narrate_deterministic(result)
    if not use_llm:
        return deterministic
    chat_model = model or build_model(api_key=api_key)
    if chat_model is None:
        return deterministic
    narrated = invoke_text(chat_model, [("system", _NARRATE_SYSTEM), ("human", deterministic)])
    return narrated or deterministic


def narrate_deterministic(result: WorkflowResult) -> str:
    """A fixed, reproducible narration of the decision log (no external calls)."""
    lines = [
        "# Agentic workflow — decision log",
        "",
        "The workflow ran the full geothermal pipeline and made these decisions:",
        "",
    ]
    for index, step in enumerate(result.steps, start=1):
        lines.append(f"## Step {index}: {step.name}")
        lines.append(f"- **Action:** {step.action}")
        lines.append(f"- **Decision:** {step.decision}")
        if step.metrics:
            metrics = ", ".join(f"{k} = {v:.2f}" for k, v in step.metrics.items())
            lines.append(f"- **Key metrics:** {metrics}")
        lines.append("")
    lines.append(
        f"**Headline:** a staged {result.n_doublets}-doublet system delivering heat and cooling "
        f"at an LCoE of {result.lcoe_eur_per_gj:.1f} €/GJ."
    )
    return "\n".join(lines)
