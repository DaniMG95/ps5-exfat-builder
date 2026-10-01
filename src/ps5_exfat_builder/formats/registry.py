"""Registry for current and future format backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ps5_exfat_builder.domain import FormatId, FormatSpec

from .ampr import ampr_converters
from .base import FormatConverter
from .pkg import ExfatToPkgConverter, FfpfscToPkgConverter


@dataclass(slots=True)
class FormatRegistry:
    formats: dict[FormatId, FormatSpec] = field(default_factory=dict)
    converters: dict[tuple[FormatId, FormatId], FormatConverter] = field(
        default_factory=dict
    )

    def register_format(self, spec: FormatSpec) -> None:
        self.formats[spec.id] = spec

    def register_converter(self, converter: FormatConverter) -> None:
        self.converters[converter.route] = converter

    def get_format(self, format_id: FormatId) -> FormatSpec:
        return self.formats[format_id]

    def get_converter(
        self,
        source_format: FormatId,
        target_format: FormatId,
    ) -> FormatConverter:
        return self.converters[(source_format, target_format)]

    def can_convert(self, source_format: FormatId, target_format: FormatId) -> bool:
        return (source_format, target_format) in self.converters

    def detect_path_format(self, path: str | Path) -> FormatId | None:
        path = Path(path)
        if path.is_dir():
            return "folder"
        suffix = path.suffix.lower()
        for spec in self.formats.values():
            if suffix in spec.extensions:
                return spec.id
        return None


def default_registry(*, include_experimental: bool = False) -> FormatRegistry:
    registry = FormatRegistry()
    for spec in _default_specs():
        registry.register_format(spec)
    if include_experimental:
        for converter in ampr_converters():
            registry.register_converter(converter)
        registry.register_converter(ExfatToPkgConverter())
        registry.register_converter(FfpfscToPkgConverter())
    return registry


def _default_specs() -> tuple[FormatSpec, ...]:
    return (
        FormatSpec(
            id="folder",
            label="Game folder",
            can_build=True,
            can_extract=True,
            notes="Unpacked PS5 game dump folder.",
        ),
        FormatSpec(
            id="exfat",
            label="exFAT image",
            extensions=(".exfat",),
            can_build=True,
            can_extract=True,
            can_mount=True,
        ),
        FormatSpec(
            id="ffpkg",
            label="FFPKG UFS2 image",
            extensions=(".ffpkg",),
            can_build=True,
            can_extract=True,
            can_mount=True,
        ),
        FormatSpec(
            id="ffpfs",
            label="PFS image",
            extensions=(".ffpfs",),
            can_build=True,
            can_extract=True,
        ),
        FormatSpec(
            id="ffpfsc",
            label="Compressed PFS image",
            extensions=(".ffpfsc",),
            can_build=True,
            can_extract=True,
        ),
        FormatSpec(
            id="ampr",
            label="AMPR LZ4 pack",
            extensions=(".ampr",),
            can_build=True,
            can_extract=True,
            notes="Planned Lazy_AMPR/ampr_emu integration point.",
        ),
        FormatSpec(
            id="pkg",
            label="PS5 PKG",
            extensions=(".pkg",),
            can_build=True,
            notes="Planned LibProsperoPKG/fpkg backend integration point.",
        ),
    )
