"""Domain models for source and target formats."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

FormatId = Literal[
    "folder",
    "exfat",
    "ffpkg",
    "ffpfs",
    "ffpfsc",
    "ampr",
    "pkg",
]


@dataclass(frozen=True, slots=True)
class FormatSpec:
    id: FormatId
    label: str
    extensions: tuple[str, ...] = ()
    can_build: bool = False
    can_extract: bool = False
    can_mount: bool = False
    notes: str = ""


@dataclass(frozen=True, slots=True)
class TransformRequest:
    source: Path
    target: Path
    source_format: FormatId
    target_format: FormatId
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TransformResult:
    output: Path
    ok: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
