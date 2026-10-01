"""File inventory and image sizing helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileInventory:
    file_count: int
    total_bytes: int


def scan_file_inventory(root: str | Path) -> FileInventory:
    file_count = 0
    total_bytes = 0
    for current_root, _dirs, files in os.walk(root):
        for filename in files:
            try:
                total_bytes += os.path.getsize(Path(current_root) / filename)
                file_count += 1
            except Exception:
                pass
    return FileInventory(file_count=file_count, total_bytes=total_bytes)


def align_up(value: int, alignment: int) -> int:
    if alignment <= 0:
        raise ValueError("alignment must be positive")
    return ((value + alignment - 1) // alignment) * alignment


def estimate_exfat_image_size(
    payload_bytes: int,
    *,
    overhead_ratio: float = 1.10,
    alignment: int = 64 * 1024 * 1024,
) -> int:
    target_size = int(payload_bytes * overhead_ratio)
    target_size = align_up(target_size, alignment)
    return max(target_size, alignment)
