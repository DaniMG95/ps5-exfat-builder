"""Temporary workspace helpers for conversion backends."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Workspace:
    root: Path
    keep: bool = False

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def mkdir(self, *parts: str) -> Path:
        path = self.path(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def cleanup(self) -> None:
        if not self.keep:
            shutil.rmtree(self.root, ignore_errors=True)

    def __enter__(self) -> "Workspace":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()


def create_workspace(
    prefix: str,
    *,
    base_dir: str | Path | None = None,
    keep: bool = False,
) -> Workspace:
    root = Path(tempfile.mkdtemp(prefix=prefix, dir=str(base_dir) if base_dir else None))
    return Workspace(root=root, keep=keep)
