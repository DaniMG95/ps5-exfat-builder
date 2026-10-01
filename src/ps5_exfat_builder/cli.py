"""Small developer CLI for inspecting the package core."""

from __future__ import annotations

import argparse
from pathlib import Path

from ps5_exfat_builder.domain import FormatId, TransformRequest
from ps5_exfat_builder.formats.ampr import AMPR_PEER_FORMATS
from ps5_exfat_builder.formats.pkg import ExfatToPkgConverter, FfpfscToPkgConverter
from ps5_exfat_builder.formats import default_registry, default_routes


def _add_ampr_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument(
        "--source-format",
        choices=("ampr", *AMPR_PEER_FORMATS),
        default="folder",
    )
    parser.add_argument(
        "--target-format",
        choices=("ampr", *AMPR_PEER_FORMATS),
        default="ampr",
    )
    parser.add_argument("--profile")
    parser.add_argument(
        "--command-style",
        choices=("generic", "route-flags", "positional"),
        default="generic",
    )
    parser.add_argument(
        "--performance-preset",
        choices=("normal", "balanced", "max", "maximum"),
        default="normal",
    )
    parser.add_argument("--worker-count", type=int)
    parser.add_argument("--high-performance", action="store_true")
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--default-arg", action="append", default=[])
    parser.add_argument("--extra-arg", action="append", default=[])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ps5-exfat-builder-core")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("formats", help="List known formats")
    subparsers.add_parser("routes", help="List declared transformation routes")
    ampr = subparsers.add_parser("ampr-dry-run", help="Build an AMPR command")
    _add_ampr_arguments(ampr)
    ampr_run = subparsers.add_parser("ampr-convert", help="Run an AMPR conversion")
    _add_ampr_arguments(ampr_run)
    pkg = subparsers.add_parser("pkg-dry-run", help="Build a PKG command")
    pkg.add_argument("--source", required=True)
    pkg.add_argument("--target", required=True)
    pkg.add_argument("--tool", required=True)
    pkg.add_argument("--source-format", choices=("exfat", "ffpfsc"), default="exfat")
    pkg.add_argument("--sdk", default="")
    pkg.add_argument("--verify-sha256", action="store_true")
    pkg.add_argument("--default-arg", action="append", default=[])
    pkg.add_argument("--extra-arg", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "formats":
        registry = default_registry(include_experimental=True)
        for spec in registry.formats.values():
            extensions = ", ".join(spec.extensions) or "(directory)"
            print(f"{spec.id}\t{extensions}\t{spec.label}")
        return 0
    if args.command == "routes":
        for route in default_routes():
            print(f"{route.source}->{route.target}\t{route.status}\t{route.label}")
        return 0
    if args.command in {"ampr-dry-run", "ampr-convert"}:
        registry = default_registry(include_experimental=True)
        source_format: FormatId = args.source_format
        target_format: FormatId = args.target_format
        if not registry.can_convert(source_format, target_format):
            print(f"Unsupported AMPR route: {source_format}->{target_format}")
            return 2
        converter = registry.get_converter(source_format, target_format)
        result = converter.convert(
            TransformRequest(
                source=Path(args.source),
                target=Path(args.target),
                source_format=source_format,
                target_format=target_format,
                options={
                    "tool_path": args.tool,
                    "profile_path": args.profile,
                    "command_style": args.command_style,
                    "performance_preset": args.performance_preset,
                    "worker_count": args.worker_count,
                    "high_performance": args.high_performance,
                    "timeout": args.timeout,
                    "default_args": args.default_arg,
                    "extra_args": args.extra_arg,
                    "dry_run": args.command == "ampr-dry-run",
                },
            )
        )
        if not result.ok:
            print(result.message)
            return 2
        if args.command == "ampr-dry-run":
            print(" ".join(result.details["args"]))
        else:
            print(result.message)
            if result.details.get("output"):
                print(result.details["output"])
        return 0
    if args.command == "pkg-dry-run":
        converter = (
            ExfatToPkgConverter()
            if args.source_format == "exfat"
            else FfpfscToPkgConverter()
        )
        result = converter.convert(
            TransformRequest(
                source=Path(args.source),
                target=Path(args.target),
                source_format=args.source_format,
                target_format="pkg",
                options={
                    "tool_path": args.tool,
                    "sdk": args.sdk,
                    "verify_sha256": args.verify_sha256,
                    "default_args": args.default_arg,
                    "extra_args": args.extra_arg,
                    "dry_run": True,
                },
            )
        )
        if not result.ok:
            print(result.message)
            return 2
        print(" ".join(result.details["args"]))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
