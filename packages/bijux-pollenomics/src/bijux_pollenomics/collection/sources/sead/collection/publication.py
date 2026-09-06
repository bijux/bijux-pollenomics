from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.contracts.artifacts import (
    SEAD_POINT_CSV,
    SEAD_POINT_GEOJSON,
    SEAD_TEMPORAL_EVIDENCE_CSV,
    SEAD_TEMPORAL_EVIDENCE_GEOJSON,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.exports.context_points import (
    write_context_points_csv,
    write_context_points_geojson,
)
from bijux_pollenomics.collection.sources.sead.catalog.discovery import (
    build_sweden_archaeology_site_discovery,
    write_sweden_archaeology_site_discovery,
)
from bijux_pollenomics.collection.sources.sead.review import write_sead_review_outputs
from bijux_pollenomics.collection.sources.sead.review.publication import (
    review_lineage_from_admission,
)


def write_source_surfaces(
    output_root: Path,
    *,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
    temporal_records: list[ContextPointRecord],
) -> tuple[Path, Path]:
    normalized_csv_path = SEAD_POINT_CSV.source_path_under(output_root)
    normalized_geojson_path = SEAD_POINT_GEOJSON.source_path_under(output_root)
    _write_context_surfaces(
        normalized_csv_path,
        normalized_geojson_path,
        SEAD_TEMPORAL_EVIDENCE_CSV.source_path_under(output_root),
        SEAD_TEMPORAL_EVIDENCE_GEOJSON.source_path_under(output_root),
        records,
        temporal_records,
    )
    _write_reviews_and_discovery(output_root, rows, records, temporal_records)
    return normalized_csv_path, normalized_geojson_path


def write_repository_surfaces(
    data_root: Path,
    *,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
    temporal_records: list[ContextPointRecord],
    admission: dict[str, object],
) -> tuple[Path, Path]:
    output_root = data_root / "sead"
    normalized_csv_path = SEAD_POINT_CSV.path_under(data_root)
    normalized_geojson_path = SEAD_POINT_GEOJSON.path_under(data_root)
    normalized_csv_path.parent.mkdir(parents=True, exist_ok=True)
    _write_context_surfaces(
        normalized_csv_path,
        normalized_geojson_path,
        SEAD_TEMPORAL_EVIDENCE_CSV.path_under(data_root),
        SEAD_TEMPORAL_EVIDENCE_GEOJSON.path_under(data_root),
        records,
        temporal_records,
    )
    _write_reviews_and_discovery(
        output_root,
        rows,
        records,
        temporal_records,
        review_lineage=review_lineage_from_admission(admission),
    )
    return normalized_csv_path, normalized_geojson_path


def _write_context_surfaces(
    point_csv_path: Path,
    point_geojson_path: Path,
    temporal_csv_path: Path,
    temporal_geojson_path: Path,
    records: list[ContextPointRecord],
    temporal_records: list[ContextPointRecord],
) -> None:
    write_context_points_csv(point_csv_path, records)
    write_context_points_geojson(point_geojson_path, records)
    write_context_points_csv(temporal_csv_path, temporal_records)
    write_context_points_geojson(temporal_geojson_path, temporal_records)


def _write_reviews_and_discovery(
    output_root: Path,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
    temporal_records: list[ContextPointRecord],
    *,
    review_lineage: dict[str, str] | None = None,
) -> None:
    write_sead_review_outputs(
        output_root,
        rows=rows,
        records=records,
        lineage=review_lineage,
    )
    write_archaeology_site_discovery(
        output_root=output_root,
        rows=rows,
        records=records,
        temporal_records=temporal_records,
    )


def write_archaeology_site_discovery(
    *,
    output_root: Path,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
    temporal_records: list[ContextPointRecord],
) -> None:
    raa_path = (
        output_root.parent / "raa" / "normalized" / "sweden_archaeology_density.geojson"
    )
    raa_density: dict[str, object] | None = None
    if raa_path.is_file():
        payload = json.loads(raa_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            raa_density = payload
    discovery = build_sweden_archaeology_site_discovery(
        site_records=records,
        temporal_records=temporal_records,
        raw_rows=rows,
        raa_density_geojson=raa_density,
    )
    write_sweden_archaeology_site_discovery(output_root, discovery)
