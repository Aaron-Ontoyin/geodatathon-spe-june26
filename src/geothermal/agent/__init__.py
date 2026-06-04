"""Phase 5g — the agentic workflow (bonus).

Orchestrates the full pipeline (clean → assess → site → design → optimise → risk →
report), recording the decision made at each stage, and narrates it. Fully
deterministic and key-free so judges can reproduce it; an optional LLM layer
(``narrate(..., use_llm=True)``) rewrites the decision log conversationally when an
API key is present, and falls back to the deterministic narration otherwise.
"""

from geothermal.agent.llm import astream_chat, build_model, chat
from geothermal.agent.narrate import narrate, narrate_deterministic
from geothermal.agent.workflow import WorkflowResult, WorkflowStep, run_workflow

__all__ = [
    "WorkflowResult",
    "WorkflowStep",
    "astream_chat",
    "build_model",
    "chat",
    "narrate",
    "narrate_deterministic",
    "run_workflow",
]
