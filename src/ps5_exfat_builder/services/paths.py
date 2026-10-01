"""Path helpers for project and runtime data."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def asset_path(*parts: str) -> Path:
    return repo_root().joinpath("assets", *parts)
