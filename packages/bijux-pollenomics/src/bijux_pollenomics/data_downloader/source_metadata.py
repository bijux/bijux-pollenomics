from __future__ import annotations

from datetime import date

from .models import SourceAcquisitionMetadata

__all__ = ["build_source_metadata"]

_SOURCE_LICENSES: dict[str, str] = {
    "aadr": "source-specific terms",
    "boundaries": "public geodata terms",
    "landclim": "source-specific terms",
    "neotoma": "source-specific terms",
    "raa": "open data terms",
    "sead": "source-specific terms",
}


def build_source_metadata(
    *, selected_sources: tuple[str, ...], version: str
) -> dict[str, SourceAcquisitionMetadata]:
    """Build source acquisition metadata for every selected source."""
    retrieved_on = str(date.today())
    metadata: dict[str, SourceAcquisitionMetadata] = {}
    for source in selected_sources:
        metadata[source] = SourceAcquisitionMetadata(
            source=source,
            version=version,
            license=_SOURCE_LICENSES.get(source, "source-specific terms"),
            retrieved_on=retrieved_on,
            acquisition_method="collector_pipeline",
        )
    return metadata
