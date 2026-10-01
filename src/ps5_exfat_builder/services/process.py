"""Subprocess helpers shared by future backends."""

from __future__ import annotations

import subprocess
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ProcessPriority = Literal["normal", "high", "realtime"]


@dataclass(frozen=True, slots=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    output: str


@dataclass(frozen=True, slots=True)
class ProcessPerformance:
    """Runtime hints for long-running conversion tools."""

    priority: ProcessPriority = "normal"
    use_all_cpus: bool = False
    worker_count: int | None = None

    @classmethod
    def maximum(cls) -> "ProcessPerformance":
        return cls(priority="high", use_all_cpus=True, worker_count=os.cpu_count() or 1)

    def env_overrides(self) -> dict[str, str]:
        if not self.worker_count:
            return {}
        value = str(max(1, int(self.worker_count)))
        return {
            "OMP_NUM_THREADS": value,
            "OPENBLAS_NUM_THREADS": value,
            "MKL_NUM_THREADS": value,
            "NUMEXPR_NUM_THREADS": value,
            "UV_THREADPOOL_SIZE": value,
            "PS5_EXFAT_WORKERS": value,
        }


def _apply_performance_hints(
    process: subprocess.Popen[str],
    performance: ProcessPerformance | None,
) -> None:
    if performance is None:
        return
    try:
        import psutil  # type: ignore[import-not-found]
    except Exception:
        return

    try:
        child = psutil.Process(process.pid)
        if performance.use_all_cpus:
            try:
                child.cpu_affinity(list(range(psutil.cpu_count(logical=True) or 1)))
            except Exception:
                pass
        if performance.priority == "high":
            try:
                child.nice(psutil.HIGH_PRIORITY_CLASS if os.name == "nt" else -10)
            except Exception:
                pass
        elif performance.priority == "realtime":
            try:
                child.nice(psutil.REALTIME_PRIORITY_CLASS if os.name == "nt" else -20)
            except Exception:
                pass
    except Exception:
        pass


def run_command(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = None,
    performance: ProcessPerformance | None = None,
) -> CommandResult:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    startupinfo = None
    if hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    env = None
    if performance:
        env = os.environ.copy()
        env.update(performance.env_overrides())

    process = subprocess.Popen(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        startupinfo=startupinfo,
        env=env,
    )
    _apply_performance_hints(process, performance)
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
        raise
    return CommandResult(
        args=tuple(args),
        returncode=process.returncode,
        output=output or "",
    )
