"""PKG builder integration boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PkgBuildInput:
    staged_game_dir: Path
    output_pkg: Path
    sdk: str = ""
    verify_sha256: bool = False


@dataclass(frozen=True, slots=True)
class PkgBuilderTool:
    executable: Path
    default_args: tuple[str, ...] = ()


def generic_pkg_builder_args(
    tool: PkgBuilderTool,
    build_input: PkgBuildInput,
) -> list[str]:
    """Build a conservative generic CLI invocation.

    Real tool-specific adapters can replace this once the exact PKG backend is
    selected. Keeping this function simple makes the integration point explicit
    without assuming one third-party CLI's argument names throughout the app.
    """
    args = [str(tool.executable), *tool.default_args]
    args.extend(["--input", str(build_input.staged_game_dir)])
    args.extend(["--output", str(build_input.output_pkg)])
    if build_input.sdk:
        args.extend(["--sdk", build_input.sdk])
    if build_input.verify_sha256:
        args.append("--verify-sha256")
    return args
