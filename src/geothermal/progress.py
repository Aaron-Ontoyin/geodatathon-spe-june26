"""Lightweight progress reporting for long-running operations.

The pipeline stays synchronous; long operations simply accept an optional
``on_progress`` callback and call it as they advance. The web layer forwards those
calls over Server-Sent Events so the UI can show a live progress bar, while the CLI
and tests can pass a callback that records or ignores them. This is the one seam
between the sync core and the streaming UI.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Progress:
    """A single progress update emitted by a long-running operation."""

    stage: str  # e.g. "optimize", "workflow"
    done: int
    total: int
    message: str

    @property
    def fraction(self) -> float:
        return self.done / self.total if self.total > 0 else 1.0


ProgressCallback = Callable[[Progress], None]


def report(callback: ProgressCallback | None, progress: Progress) -> None:
    """Invoke ``callback`` if present (a no-op otherwise)."""
    if callback is not None:
        callback(progress)
