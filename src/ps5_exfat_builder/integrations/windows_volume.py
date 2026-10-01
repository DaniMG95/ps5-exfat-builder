"""Windows volume and copy command construction."""

from __future__ import annotations

from pathlib import Path


def format_exfat_args(mount_point: str, *, label: str = "") -> list[str]:
    return [
        "cmd.exe",
        "/c",
        "format",
        mount_point,
        "/FS:exFAT",
        "/Q",
        "/Y",
        "/V:" + label,
    ]


def robocopy_tree_args(
    source: str | Path,
    destination: str | Path,
    *,
    retries: int = 1,
    wait_seconds: int = 1,
    show_eta: bool = True,
) -> list[str]:
    args = [
        "robocopy.exe",
        str(source),
        str(destination),
        "/E",
        "/COPY:DAT",
        "/DCOPY:DAT",
        f"/R:{retries}",
        f"/W:{wait_seconds}",
        "/NP",
    ]
    if show_eta:
        args.append("/ETA")
    return args
