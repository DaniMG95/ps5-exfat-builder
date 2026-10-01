"""Declared transformation routes.

Routes describe the product surface separately from converter implementation.
That lets the UI show what is already available through legacy code and what
is planned for new backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ps5_exfat_builder.domain import FormatId
from ps5_exfat_builder.formats.ampr import AMPR_PEER_FORMATS

RouteStatus = Literal["core", "legacy", "planned"]


@dataclass(frozen=True, slots=True)
class TransformationRoute:
    source: FormatId
    target: FormatId
    status: RouteStatus
    label: str
    notes: str = ""

    @property
    def key(self) -> tuple[FormatId, FormatId]:
        return self.source, self.target


def default_routes() -> tuple[TransformationRoute, ...]:
    routes = [
        TransformationRoute(
            source="folder",
            target="exfat",
            status="legacy",
            label="Game folder to exFAT",
            notes="Current build queue in exfat_builder.py.",
        ),
        TransformationRoute(
            source="folder",
            target="ffpkg",
            status="legacy",
            label="Game folder to FFPKG",
            notes="Current FFPKG queue in exfat_builder.py.",
        ),
        TransformationRoute(
            source="exfat",
            target="ffpkg",
            status="legacy",
            label="exFAT to FFPKG",
            notes="Convert tab; now uses shared command builders.",
        ),
        TransformationRoute(
            source="ffpkg",
            target="exfat",
            status="legacy",
            label="FFPKG to exFAT",
            notes="Convert tab; now uses shared command builders.",
        ),
        TransformationRoute(
            source="exfat",
            target="ffpfsc",
            status="legacy",
            label="exFAT to compressed PFS",
            notes="mkpfs path currently owned by the PFS/convert UI.",
        ),
        TransformationRoute(
            source="exfat",
            target="pkg",
            status="planned",
            label="exFAT to PS5 PKG",
            notes="Mount, stage, build PKG, verify.",
        ),
        TransformationRoute(
            source="ffpfsc",
            target="pkg",
            status="planned",
            label="Compressed PFS to PS5 PKG",
            notes="Requires decompression/extract stage before PKG build.",
        ),
    ]
    for source in AMPR_PEER_FORMATS:
        routes.append(
            TransformationRoute(
                source=source,
                target="ampr",
                status="planned",
                label=f"{source.upper()} to AMPR",
                notes="Lazy_AMPR profile-backed pack route.",
            )
        )
    for target in AMPR_PEER_FORMATS:
        routes.append(
            TransformationRoute(
                source="ampr",
                target=target,
                status="planned",
                label=f"AMPR to {target.upper()}",
                notes="Lazy_AMPR profile-backed unpack route.",
            )
        )
    return tuple(routes)


def route_map() -> dict[tuple[FormatId, FormatId], TransformationRoute]:
    return {route.key: route for route in default_routes()}
