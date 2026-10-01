"""Base interfaces for format transformations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from ps5_exfat_builder.domain import FormatId, TransformRequest, TransformResult
from ps5_exfat_builder.services.progress import ProgressReporter


class FormatConverter(ABC):
    """A converter that transforms one supported format into another."""

    source_format: FormatId
    target_format: FormatId

    @property
    def route(self) -> tuple[FormatId, FormatId]:
        return self.source_format, self.target_format

    @abstractmethod
    def convert(
        self,
        request: TransformRequest,
        progress: ProgressReporter | None = None,
    ) -> TransformResult:
        """Execute the conversion."""


def routes(converters: Iterable[FormatConverter]) -> set[tuple[FormatId, FormatId]]:
    return {converter.route for converter in converters}
