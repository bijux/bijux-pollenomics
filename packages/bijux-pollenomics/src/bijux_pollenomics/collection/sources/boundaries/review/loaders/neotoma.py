"""Neotoma point evidence for governed boundary review."""

from __future__ import annotations

from pathlib import Path

from ......core.geospatial.geojson import feature_list
from ..models import JsonObject, PointEvidence
from ..serialization import (
    _object_rows,
    _optional_text,
    _read_json_object,
    _required_int,
    _required_text,
)
from .records import _artifact_records, _lineage, _point_feature


def _load_neotoma_points(
    root: Path,
) -> tuple[str, list[PointEvidence], list[JsonObject]]:
    normalized_path = Path("data/neotoma/normalized/nordic_pollen_sites.geojson")
    relational_path = Path("data/neotoma/relational/surfaces/sites/part-00001.json")
    raw_path = Path("data/neotoma/raw/neotoma_pollen_sites.json")
    normalized = _read_json_object(root / normalized_path)
    relational = _read_json_object(root / relational_path)
    relational_rows = _object_rows(relational, "rows", relational_path)
    upstream_by_source_id = {
        str(_required_int(row.get("source_site_id"), "Neotoma source site ID")): row
        for row in relational_rows
    }
    points: list[PointEvidence] = []
    for index, feature in enumerate(feature_list(normalized)):
        properties, longitude, latitude = _point_feature(feature, "Neotoma")
        source_id = _required_text(properties.get("record_id"), "Neotoma record ID")
        upstream = upstream_by_source_id.get(source_id)
        if upstream is None:
            raise ValueError(f"Neotoma relational point is missing: {source_id}")
        points.append(
            PointEvidence(
                source_family="neotoma",
                source_scope="four_country_expected",
                source_record_id=f"neotoma:site:{source_id}",
                longitude=longitude,
                latitude=latitude,
                raw_country=_optional_text(upstream.get("raw_country")),
                published_country=_optional_text(properties.get("country")),
                lineage=(
                    _lineage(
                        raw_path, f"rows[siteid={source_id}]", "source_native_row"
                    ),
                    _lineage(normalized_path, f"features[{index}]", "point_geometry"),
                    _lineage(
                        relational_path,
                        f"rows[source_site_id={source_id}]",
                        "source_native_country_and_prior_decision",
                    ),
                ),
                prior_decision={
                    "decision_status": upstream.get("country_decision_status"),
                    "decision_method": upstream.get("country_decision_method"),
                    "derived_country": upstream.get("derived_country"),
                    "boundary_artifact_digest": upstream.get(
                        "boundary_artifact_digest"
                    ),
                },
            )
        )
    return (
        "neotoma",
        points,
        _artifact_records(root, (raw_path, normalized_path, relational_path)),
    )
