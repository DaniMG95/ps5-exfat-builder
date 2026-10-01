"""PKG format converters."""

from __future__ import annotations

from pathlib import Path

from ps5_exfat_builder.domain import TransformRequest, TransformResult
from ps5_exfat_builder.formats.base import FormatConverter
from ps5_exfat_builder.integrations.pkg import (
    PkgBuilderTool,
    PkgBuildInput,
    generic_pkg_builder_args,
)
from ps5_exfat_builder.services.process import run_command
from ps5_exfat_builder.services.progress import ProgressEvent
from ps5_exfat_builder.services.progress import ProgressReporter


class PkgConversionError(ValueError):
    pass


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
        raise PkgConversionError(f"invalid PKG timeout: {value!r}") from exc
    if timeout <= 0:
        raise PkgConversionError(f"invalid PKG timeout: {value!r}")
    return timeout


def _find_tool(path: object) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    if candidate.is_file():
        return candidate
    return None


class _BasePkgConverter(FormatConverter):
    target_format = "pkg"

    def convert(
        self,
        request: TransformRequest,
        progress: ProgressReporter | None = None,
    ) -> TransformResult:
        if request.source_format != self.source_format:
            raise PkgConversionError(
                f"expected source format {self.source_format!r}, "
                f"got {request.source_format!r}"
            )
        if request.target_format != self.target_format:
            raise PkgConversionError(
                f"expected target format {self.target_format!r}, "
                f"got {request.target_format!r}"
            )

        tool_path = request.options.get("tool_path")
        if not tool_path:
            return TransformResult(
                output=request.target,
                ok=False,
                message="PKG tool_path option is required",
            )

        dry_run = bool(request.options.get("dry_run", False))
        tool = _find_tool(tool_path)
        if not tool and dry_run:
            tool = Path(tool_path)
        if not tool:
            return TransformResult(
                output=request.target,
                ok=False,
                message=f"PKG tool not found: {tool_path}",
            )

        build_input = PkgBuildInput(
            staged_game_dir=request.source,
            output_pkg=request.target,
            sdk=str(request.options.get("sdk", "") or ""),
            verify_sha256=bool(request.options.get("verify_sha256", False)),
        )
        args = generic_pkg_builder_args(
            PkgBuilderTool(
                executable=tool,
                default_args=_option_args(request.options.get("default_args")),
            ),
            build_input,
        )
        args.extend(_option_args(request.options.get("extra_args")))

        if progress:
            progress(ProgressEvent(step="pkg", percent=0.0, message="Prepared PKG command"))

        details = {"args": args, "tool": str(tool)}
        if dry_run:
            return TransformResult(
                output=request.target,
                ok=True,
                message="PKG dry run prepared",
                details=details,
            )

        if not request.source.exists():
            return TransformResult(
                output=request.target,
                ok=False,
                message=f"PKG source not found: {request.source}",
                details=details,
            )
        try:
            timeout = _option_timeout(request.options.get("timeout"))
        except PkgConversionError as exc:
            return TransformResult(
                output=request.target,
                ok=False,
                message=str(exc),
                details=details,
            )
        try:
            request.target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return TransformResult(
                output=request.target,
                ok=False,
                message=f"PKG output directory could not be created: {exc}",
                details=details,
            )

        try:
            result = run_command(args, timeout=timeout)
        except Exception as exc:
            return TransformResult(
                output=request.target,
                ok=False,
                message=f"PKG conversion failed to start: {exc}",
                details=details,
            )

        ok = result.returncode == 0
        if progress:
            progress(
                ProgressEvent(
                    step="pkg",
                    percent=100.0,
                    message="PKG conversion complete" if ok else "PKG conversion failed",
                )
            )
        return TransformResult(
            output=request.target,
            ok=ok,
            message="PKG conversion complete" if ok else "PKG conversion failed",
            details={
                "args": list(result.args),
                "returncode": result.returncode,
                "output": result.output,
                "tool": str(tool),
            },
        )


class ExfatToPkgConverter(_BasePkgConverter):
    source_format = "exfat"


class FfpfscToPkgConverter(_BasePkgConverter):
    source_format = "ffpfsc"
