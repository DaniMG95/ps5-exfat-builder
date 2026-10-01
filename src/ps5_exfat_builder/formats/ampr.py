"""AMPR format converters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ps5_exfat_builder.domain import FormatId, TransformRequest, TransformResult
from ps5_exfat_builder.formats.base import FormatConverter
from ps5_exfat_builder.integrations.ampr import (
    AmprBuildInput,
    AmprCommandStyle,
    AmprTool,
    build_ampr_args,
    find_tool,
    load_profile,
)
from ps5_exfat_builder.services.process import ProcessPerformance, run_command
from ps5_exfat_builder.services.progress import ProgressEvent
from ps5_exfat_builder.services.progress import ProgressReporter


class AmprConversionError(ValueError):
    pass


AMPR_PEER_FORMATS: tuple[FormatId, ...] = (
    "folder",
    "exfat",
    "ffpkg",
    "ffpfs",
    "ffpfsc",
    "pkg",
)

AMPR_ROUTES: tuple[tuple[FormatId, FormatId], ...] = tuple(
    [*(("ampr", target) for target in AMPR_PEER_FORMATS)]
    + [*((source, "ampr") for source in AMPR_PEER_FORMATS)]
)


@dataclass(frozen=True, slots=True)
class AmprExecutionPlan:
    tool: Path
    profile_path: Path | None
    args: list[str]
    timeout: float | None
    cwd: Path | None
    dry_run: bool
    route: tuple[FormatId, FormatId]
    mode: str
    command_style: AmprCommandStyle
    performance: ProcessPerformance | None

    def details(self) -> dict[str, object]:
        source, target = self.route
        return {
            "args": self.args,
            "tool": str(self.tool),
            "profile": str(self.profile_path) if self.profile_path else None,
            "route": f"{source}->{target}",
            "mode": self.mode,
            "command_style": self.command_style,
            "cwd": str(self.cwd) if self.cwd else None,
            "timeout": self.timeout,
            "performance": {
                "priority": self.performance.priority,
                "use_all_cpus": self.performance.use_all_cpus,
                "worker_count": self.performance.worker_count,
            }
            if self.performance
            else None,
        }


def _option_args(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    try:
        return tuple(str(arg) for arg in value)  # type: ignore[operator]
    except TypeError:
        return (str(value),)


def _option_timeout(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        timeout = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise AmprConversionError(f"invalid AMPR timeout: {value!r}") from exc
    if timeout <= 0:
        raise AmprConversionError(f"invalid AMPR timeout: {value!r}")
    return timeout


def _option_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _option_path(value: object, *, name: str) -> Path:
    if value is None or value == "":
        raise AmprConversionError(f"AMPR {name} option is required")
    try:
        return Path(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise AmprConversionError(f"invalid AMPR {name}: {value!r}") from exc


def _option_command_style(value: object) -> AmprCommandStyle:
    if value is None or value == "":
        return "generic"
    if not isinstance(value, str):
        raise AmprConversionError(f"invalid AMPR command_style: {value!r}")
    style = value.strip().lower()
    if style in {"generic", "route-flags", "positional"}:
        return style  # type: ignore[return-value]
    raise AmprConversionError(f"unsupported AMPR command_style: {value!r}")


def _option_int(value: object, *, name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise AmprConversionError(f"invalid AMPR {name}: {value!r}") from exc
    if number <= 0:
        raise AmprConversionError(f"invalid AMPR {name}: {value!r}")
    return number


def _option_performance(options: dict[str, object]) -> ProcessPerformance | None:
    preset = str(options.get("performance_preset", "") or "").strip().lower()
    high_performance = _option_bool(options.get("high_performance", False))
    use_all_cpus = _option_bool(options.get("use_all_cpus", False))
    worker_count = _option_int(options.get("worker_count"), name="worker_count")
    priority = str(options.get("priority", "") or "").strip().lower()

    if preset in {"", "normal"} and not high_performance and not use_all_cpus:
        if worker_count is None and priority == "":
            return None
    if preset in {"max", "maximum"} or high_performance:
        default = ProcessPerformance.maximum()
        return ProcessPerformance(
            priority="high" if priority == "" else _option_priority(priority),
            use_all_cpus=True,
            worker_count=worker_count or default.worker_count,
        )
    if preset not in {"", "normal", "balanced"}:
        raise AmprConversionError(f"unsupported AMPR performance_preset: {preset!r}")
    return ProcessPerformance(
        priority="normal" if priority == "" else _option_priority(priority),
        use_all_cpus=use_all_cpus,
        worker_count=worker_count,
    )


def _option_priority(value: object) -> str:
    priority = str(value or "").strip().lower()
    if priority in {"normal", "high", "realtime"}:
        return priority
    raise AmprConversionError(f"unsupported AMPR priority: {value!r}")


@dataclass(frozen=True, slots=True)
class AmprConverter(FormatConverter):
    """Generic Lazy_AMPR/ampr_emu converter for any declared AMPR route."""

    source_format: FormatId
    target_format: FormatId

    def __post_init__(self) -> None:
        if self.source_format == self.target_format:
            raise AmprConversionError("AMPR route source and target must differ")
        if (self.source_format, self.target_format) not in AMPR_ROUTES:
            raise AmprConversionError(
                f"unsupported AMPR route: "
                f"{self.source_format!r}->{self.target_format!r}"
            )

    @property
    def mode(self) -> str:
        if self.target_format == "ampr":
            return "pack"
        if self.source_format == "ampr":
            return "unpack"
        return "transform"

    def _prepare_plan(self, request: TransformRequest) -> AmprExecutionPlan:
        dry_run = _option_bool(request.options.get("dry_run", False))
        tool_path = _option_path(request.options.get("tool_path"), name="tool_path")
        tool = find_tool(tool_path)
        if not tool and dry_run:
            tool = tool_path
        if not tool:
            raise AmprConversionError(f"AMPR tool not found: {tool_path}")

        profile = None
        profile_path = request.options.get("profile_path")
        if profile_path:
            try:
                profile = load_profile(profile_path)
            except (OSError, ValueError) as exc:
                raise AmprConversionError(
                    f"AMPR profile could not be loaded: {exc}"
                ) from exc

        timeout = None if dry_run else _option_timeout(request.options.get("timeout"))
        command_style = _option_command_style(request.options.get("command_style"))
        performance = _option_performance(request.options)
        args = build_ampr_args(
            AmprTool(
                executable=tool,
                default_args=_option_args(request.options.get("default_args")),
            ),
            AmprBuildInput(
                source=request.source,
                output=request.target,
                mode=self.mode,
                source_format=self.source_format,
                target_format=self.target_format,
                profile=profile,
                extra_args=_option_args(request.options.get("extra_args")),
            ),
            style=command_style,
        )
        return AmprExecutionPlan(
            tool=tool,
            profile_path=profile.path if profile else None,
            args=args,
            timeout=timeout,
            cwd=request.source if request.source.is_dir() else None,
            dry_run=dry_run,
            route=self.route,
            mode=self.mode,
            command_style=command_style,
            performance=performance,
        )

    def convert(
        self,
        request: TransformRequest,
        progress: ProgressReporter | None = None,
    ) -> TransformResult:
        if request.source_format != self.source_format:
            raise AmprConversionError(
                f"expected source format {self.source_format!r}, "
                f"got {request.source_format!r}"
            )
        if request.target_format != self.target_format:
            raise AmprConversionError(
                f"expected target format {self.target_format!r}, "
                f"got {request.target_format!r}"
            )

        try:
            plan = self._prepare_plan(request)
        except AmprConversionError as exc:
            return TransformResult(
                output=request.target,
                ok=False,
                message=str(exc),
            )

        if progress:
            progress(
                ProgressEvent(
                    step="ampr",
                    percent=0.0,
                    message=f"Prepared AMPR {self.mode} command",
                )
            )

        details = plan.details()

        if plan.dry_run:
            return TransformResult(
                output=request.target,
                ok=True,
                message="AMPR dry run prepared",
                details=details,
            )

        if not request.source.exists():
            return TransformResult(
                output=request.target,
                ok=False,
                message=f"AMPR source not found: {request.source}",
                details=details,
            )
        try:
            request.target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return TransformResult(
                output=request.target,
                ok=False,
                message=f"AMPR output directory could not be created: {exc}",
                details=details,
            )

        try:
            result = run_command(
                plan.args,
                cwd=plan.cwd,
                timeout=plan.timeout,
                performance=plan.performance,
            )
        except Exception as exc:
            return TransformResult(
                output=request.target,
                ok=False,
                message=f"AMPR conversion failed to start: {exc}",
                details=details,
            )
        ok = result.returncode == 0
        if progress:
            progress(
                ProgressEvent(
                    step="ampr",
                    percent=100.0,
                    message="AMPR conversion complete" if ok else "AMPR conversion failed",
                )
            )
        return TransformResult(
            output=request.target,
            ok=ok,
            message="AMPR conversion complete" if ok else "AMPR conversion failed",
            details={
                "args": list(result.args),
                "returncode": result.returncode,
                "output": result.output,
                **{key: value for key, value in details.items() if key != "args"},
            },
        )


def ampr_converters() -> tuple[AmprConverter, ...]:
    return tuple(
        AmprConverter(source_format=source, target_format=target)
        for source, target in AMPR_ROUTES
    )


class FolderToAmprConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="folder", target_format="ampr")


class ExfatToAmprConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="exfat", target_format="ampr")


class FfpkgToAmprConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ffpkg", target_format="ampr")


class FfpfsToAmprConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ffpfs", target_format="ampr")


class FfpfscToAmprConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ffpfsc", target_format="ampr")


class PkgToAmprConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="pkg", target_format="ampr")


class AmprToFolderConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ampr", target_format="folder")


class AmprToExfatConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ampr", target_format="exfat")


class AmprToFfpkgConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ampr", target_format="ffpkg")


class AmprToFfpfsConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ampr", target_format="ffpfs")


class AmprToFfpfscConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ampr", target_format="ffpfsc")


class AmprToPkgConverter(AmprConverter):
    def __init__(self) -> None:
        super().__init__(source_format="ampr", target_format="pkg")
