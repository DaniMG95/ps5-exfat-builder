"""Entrypoints for the desktop application."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    """Run the current Tkinter application without duplicating legacy code."""
    root = project_root()
    legacy_entrypoint = root / "exfat_builder.py"
    if not legacy_entrypoint.exists():
        raise FileNotFoundError(f"Legacy entrypoint not found: {legacy_entrypoint}")

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    runpy.run_path(str(legacy_entrypoint), run_name="__main__")
    return 0
