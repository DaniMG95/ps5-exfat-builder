"""Progress reporting primitives independent of Tkinter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    step: str
    percent: float | None = None
    message: str = ""


ProgressReporter = Callable[[ProgressEvent], None]


def report(
    progress: ProgressReporter | None,
    step: str,
    *,
    percent: float | None = None,
    message: str = "",
) -> None:
    if progress is not None:
        progress(ProgressEvent(step=step, percent=percent, message=message))
