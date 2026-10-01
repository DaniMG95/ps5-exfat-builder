"""UFS2Tool command construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Ufs2NewfsOptions:
    object_format: str = "2"
    block_size: str = "32768"
    fragment_size: str = "4096"
    sector_size: str = "512"


def newfs_args(
    executable: str | Path,
    source_directory: str | Path,
    output_image: str | Path,
    *,
    options: Ufs2NewfsOptions | None = None,
) -> list[str]:
    opts = options or Ufs2NewfsOptions()
    return [
        str(executable),
        "newfs",
        "-O",
        opts.object_format,
        "-b",
        opts.block_size,
        "-f",
        opts.fragment_size,
        "-S",
        opts.sector_size,
        "-D",
        str(source_directory),
        str(output_image),
    ]


def extract_args(
    executable: str | Path,
    source_image: str | Path,
    output_directory: str | Path,
    *,
    root: str | None = None,
) -> list[str]:
    args = [
        str(executable),
        "extract",
        str(source_image),
        str(output_directory),
    ]
    if root is not None:
        args.append(root)
    return args
