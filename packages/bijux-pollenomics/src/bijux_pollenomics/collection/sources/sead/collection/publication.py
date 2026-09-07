from __future__ import annotations

from datetime import date
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
    _write_reviews_and_discovery(
        output_root,
        rows,
        records,
        temporal_records,
        context_data_root=output_root.parent,
    )
    return normalized_csv_path, normalized_geojson_path


def write_repository_surfaces(
    output_data_root: Path,
    *,
    context_data_root: Path,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
    temporal_records: list[ContextPointRecord],
    admission: dict[str, object],
    generated_on: date,
) -> tuple[Path, Path]:
    output_root = output_data_root / "sead"
    normalized_csv_path = SEAD_POINT_CSV.path_under(output_data_root)
    normalized_geojson_path = SEAD_POINT_GEOJSON.path_under(output_data_root)
    normalized_csv_path.parent.mkdir(parents=True, exist_ok=True)
    _write_context_surfaces(
        normalized_csv_path,
        normalized_geojson_path,
        SEAD_TEMPORAL_EVIDENCE_CSV.path_under(output_data_root),
        SEAD_TEMPORAL_EVIDENCE_GEOJSON.path_under(output_data_root),
        records,
        temporal_records,
    )
    _write_reviews_and_discovery(
        output_root,
        rows,
        records,
        temporal_records,
        context_data_root=context_data_root,
        review_lineage=review_lineage_from_admission(admission),
        generated_on=generated_on,
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
    context_data_root: Path,
    review_lineage: dict[str, str] | None = None,
    generated_on: date | None = None,
) -> None:
    write_sead_review_outputs(
        output_root,
        rows=rows,
        records=records,
        lineage=review_lineage,
        generated_on=generated_on,
    )
    write_archaeology_site_discovery(
        output_root=output_root,
        rows=rows,
        records=records,
        temporal_records=temporal_records,
        context_data_root=context_data_root,
        generated_on=generated_on,
    )


def write_archaeology_site_discovery(
    *,
    output_root: Path,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
    temporal_records: list[ContextPointRecord],
    context_data_root: Path,
    generated_on: date | None = None,
) -> None:
    raa_path = (
        context_data_root / "raa" / "normalized" / "sweden_archaeology_density.geojson"
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
        generated_on=generated_on,
    )
    write_sweden_archaeology_site_discovery(output_root, discovery)
