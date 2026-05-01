from __future__ import annotations

from pathlib import Path

from .models import SourceAcquisitionMetadata

__all__ = ["validate_source_snapshot"]


def validate_source_snapshot(
    *,
    output_root: Path,
    selected_sources: tuple[str, ...],
    source_output_roots: dict[str, str],
    source_metadata: dict[str, SourceAcquisitionMetadata],
    boundary_source: str | None,
) -> None:
    """Validate source snapshot completeness and consistency before publish."""
    for source in selected_sources:
        if source not in source_output_roots:
            raise ValueError(
                f"incomplete source snapshot: missing output root for {source}"
            )
        if source not in source_metadata:
            raise ValueError(
                f"incomplete source snapshot: missing metadata for {source}"
            )

        source_root = Path(source_output_roots[source])
        if not source_root.exists() or not source_root.is_dir():
            raise ValueError(
                f"malformed source snapshot: missing directory {source_root}"
            )

        metadata = source_metadata[source]
        if not metadata.version or not metadata.retrieved_on:
            raise ValueError(f"malformed source snapshot metadata for {source}")
        if not metadata.license or not metadata.acquisition_method:
            raise ValueError(f"incomplete source snapshot metadata for {source}")

    requires_boundaries = any(
        source in selected_sources
        for source in ("boundaries", "landclim", "neotoma", "sead", "raa")
    )
    if requires_boundaries and boundary_source is None:
        raise ValueError(
            "contradictory source snapshot: boundary-dependent sources selected without boundary source"
        )

    if not output_root.exists() or not output_root.is_dir():
        raise ValueError(f"malformed source snapshot root: {output_root}")
