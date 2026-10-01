"""mkpfs integration boundary."""

from __future__ import annotations

from pathlib import Path


def pack_ffpfsc_args(source_exfat: Path, output_ffpfsc: Path) -> list[str]:
    return ["-i", str(source_exfat), "-o", str(output_ffpfsc)]
