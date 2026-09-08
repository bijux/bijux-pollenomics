"""Source spatiotemporal posture registry assembly."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .archaeology_sources import _build_raa_row, _build_sead_row
from .pollen_sources import _build_landclim_row, _build_neotoma_row
from .reference_sources import _build_boundaries_row, _build_svar_row

__all__ = []


def build_source_spatiotemporal_posture_payload(
    output_root: Path,
) -> dict[str, object]:
    """Build one reader-facing registry of source spatiotemporal posture."""
    output_root = Path(output_root)
    rows = (
        _build_landclim_row(output_root),
        _build_neotoma_row(output_root),
        _build_sead_row(output_root),
        _build_raa_row(output_root),
        _build_svar_row(output_root),
        _build_boundaries_row(output_root),
    )
    return {
        "schema_version": "source-spatiotemporal-posture-registry.v2",
        "row_count": len(rows),
        "rows": [asdict(row) for row in rows],
    }
