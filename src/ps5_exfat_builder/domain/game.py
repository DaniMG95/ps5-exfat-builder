"""Game metadata shared by builders, converters, and UI surfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameMetadata:
    title: str = ""
    title_id: str = ""
    version: str = ""
    sdk_version: str = ""
    content_id: str = ""
