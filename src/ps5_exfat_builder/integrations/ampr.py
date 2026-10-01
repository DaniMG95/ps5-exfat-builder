"""Lazy_AMPR/ampr_emu integration boundary."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

AmprCommandStyle = Literal["generic", "route-flags", "positional"]

AMPR_TOOL_NAMES = (
    "lazy_ampr.exe",
    "Lazy_AMPR.exe",
    "lazy_ampr.bat",
    "run_lazy_ampr.bat",
    "run_ampr.bat",
    "run.bat",
    "lazy_ampr.py",
    "main.py",
)


@dataclass(frozen=True, slots=True)
class AmprProfile:
    path: Path
    name: str
    data: dict


@dataclass(frozen=True, slots=True)
class AmprTool:
    executable: Path
    default_args: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AmprBuildInput:
    source: Path
    output: Path
    mode: str = "pack"
    source_format: str = ""
    target_format: str = ""
    profile: AmprProfile | None = None
    extra_args: tuple[str, ...] = ()


def profile_candidates(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.glob("*.toml")))


def tool_candidates(root: str | Path) -> tuple[Path, ...]:
    root_path = Path(root)
    found = []
    for name in AMPR_TOOL_NAMES:
        candidate = root_path / name
        if candidate.is_file():
            found.append(candidate)
    return tuple(found)


def find_tool(path: str | Path) -> Path | None:
    candidate = Path(path)
    if candidate.is_file():
        return candidate
    if candidate.is_dir():
        candidates = tool_candidates(candidate)
        if candidates:
            return candidates[0]
    return None


def load_profile(path: str | Path) -> AmprProfile:
    profile_path = Path(path)
    with profile_path.open("rb") as file:
        data = tomllib.load(file)
    name = (
        str(data.get("name", "")).strip()
        or str(data.get("profile", "")).strip()
        or profile_path.stem
    )
    return AmprProfile(path=profile_path, name=name, data=data)


def discover_profiles(root: str | Path) -> tuple[AmprProfile, ...]:
    return tuple(load_profile(path) for path in profile_candidates(Path(root)))


def build_ampr_args(
    tool: AmprTool,
    build_input: AmprBuildInput,
    *,
    style: AmprCommandStyle = "generic",
) -> list[str]:
    """Build a generic Lazy_AMPR-style command line.

    This adapter is intentionally generic until the exact embedded backend is
    selected. Tool-specific argument changes should stay in this module.
    """
    args = [str(tool.executable), *tool.default_args]
    if style == "generic":
        args.extend(["--input", str(build_input.source)])
        args.extend(["--output", str(build_input.output)])
        if build_input.profile:
            args.extend(["--profile", str(build_input.profile.path)])
    elif style == "route-flags":
        args.extend(["--mode", build_input.mode])
        args.extend(["--source-format", build_input.source_format])
        args.extend(["--target-format", build_input.target_format])
        args.extend(["--input", str(build_input.source)])
        args.extend(["--output", str(build_input.output)])
        if build_input.profile:
            args.extend(["--profile", str(build_input.profile.path)])
    elif style == "positional":
        args.extend([build_input.mode, str(build_input.source), str(build_input.output)])
        if build_input.profile:
            args.append(str(build_input.profile.path))
    else:
        raise ValueError(f"unsupported AMPR command style: {style!r}")
    args.extend(build_input.extra_args)
    return args
