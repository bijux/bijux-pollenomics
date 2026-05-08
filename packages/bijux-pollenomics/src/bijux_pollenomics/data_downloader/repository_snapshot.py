from __future__ import annotations

import json
from pathlib import Path

from ..config import DEFAULT_AADR_VERSION
from .data_layout import AVAILABLE_SOURCES, build_source_output_roots
from .models import DataCollectionSummary
from .pipeline.collection_reports import (
    build_data_collection_summary,
    initialize_source_counts,
)
from .pipeline.contract_surface_writer import write_data_contract_surfaces
from .pipeline.summary_writer import write_collection_summary
from .source_hashes import build_source_hashes
from .source_metadata import build_source_metadata
from .source_provenance import build_source_provenance
from .source_replacement_rules import build_source_replacement_rules
from .source_traceability import build_source_traceability_records

__all__ = [
    "build_repository_collection_summary",
    "build_repository_source_counts",
    "materialize_repository_collection_snapshot",
]


def build_repository_source_counts(output_root: Path) -> dict[str, int]:
    """Infer tracked source counts from an already materialized repository data tree."""
    output_root = Path(output_root)
    counts = initialize_source_counts()
    counts["aadr_file_count"] = sum(
        1
        for path in (output_root / "aadr").rglob("*")
        if path.is_file() and not path.name.startswith(".")
    )
    landclim_summary = output_root / "landclim" / "normalized" / "landclim_summary.json"
    if landclim_summary.is_file():
        payload = json.loads(landclim_summary.read_text(encoding="utf-8"))
        counts["landclim_site_count"] = int(payload.get("site_count", 0))
        counts["landclim_grid_cell_count"] = int(payload.get("grid_cell_count", 0))
    counts["neotoma_point_count"] = _geojson_feature_count(
        output_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson"
    )
    counts["sead_point_count"] = _geojson_feature_count(
        output_root / "sead" / "normalized" / "nordic_environmental_sites.geojson"
    )
    raa_layer = output_root / "raa" / "normalized" / "sweden_archaeology_layer.json"
    if raa_layer.is_file():
        payload = json.loads(raa_layer.read_text(encoding="utf-8"))
        counts_payload = payload.get("counts", {})
        if isinstance(counts_payload, dict):
            counts["raa_total_site_count"] = int(counts_payload.get("all_published_sites", 0))
            counts["raa_heritage_site_count"] = int(counts_payload.get("fornlamning", 0))
    return counts


def build_repository_collection_summary(
    output_root: Path,
    *,
    version: str = DEFAULT_AADR_VERSION,
) -> DataCollectionSummary:
    """Build the checked-in collection summary from the existing repository data tree."""
    output_root = Path(output_root)
    selected_sources = AVAILABLE_SOURCES
    source_output_roots = build_source_output_roots(output_root=output_root, version=version)
    source_metadata = build_source_metadata(
        selected_sources=selected_sources,
        version=version,
    )
    source_hashes = {
        source: {
            "snapshot_sha256": hashes.snapshot_sha256,
            "normalized_sha256": hashes.normalized_sha256,
        }
        for source, hashes in build_source_hashes(
            source_output_roots=source_output_roots,
            selected_sources=selected_sources,
        ).items()
    }
    source_provenance = build_source_provenance(
        selected_sources=selected_sources,
        source_output_roots=source_output_roots,
        source_metadata=source_metadata,
        source_hashes=source_hashes,
    )
    source_replacement_rules = build_source_replacement_rules(
        selected_sources=selected_sources,
        source_output_roots=source_output_roots,
    )
    source_traceability = build_source_traceability_records(
        selected_sources=selected_sources,
        source_metadata=source_metadata,
        source_hashes=source_hashes,
    )
    return build_data_collection_summary(
        output_root=output_root,
        version=version,
        collected_sources=selected_sources,
        source_output_roots=source_output_roots,
        source_metadata=source_metadata,
        source_hashes=source_hashes,
        source_provenance=source_provenance,
        source_replacement_rules=source_replacement_rules,
        source_traceability=source_traceability,
        boundary_source="boundaries" if (output_root / "boundaries").is_dir() else None,
        counts=build_repository_source_counts(output_root),
    )


def materialize_repository_collection_snapshot(
    output_root: Path,
    *,
    version: str = DEFAULT_AADR_VERSION,
) -> DataCollectionSummary:
    """Refresh the checked-in collection summary and contract surfaces in place."""
    summary = build_repository_collection_summary(output_root, version=version)
    write_data_contract_surfaces(summary)
    write_collection_summary(summary)
    return summary


def _geojson_feature_count(path: Path) -> int:
    if not path.is_file():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    return len(features) if isinstance(features, list) else 0
