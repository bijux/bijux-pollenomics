"""Animal ancient-DNA point evidence for governed boundary review."""

from __future__ import annotations

from pathlib import Path

from ..models import JsonObject, PointEvidence
from ..serialization import (
    _object_rows,
    _optional_text,
    _read_json_object,
    _required_number,
    _required_text,
)
from .records import _artifact_records, _lineage, _safe_relative_path


def _load_animal_adna_points(
    root: Path,
) -> tuple[str, list[PointEvidence], list[JsonObject]]:
    candidates_path = Path("data/adna/final/atlas/animal_atlas_point_candidates.json")
    payload = _read_json_object(root / candidates_path)
    rows = _object_rows(payload, "rows", candidates_path)
    points: list[PointEvidence] = []
    source_paths: set[Path] = set()
    for index, row in enumerate(rows):
        record_id = _required_text(row.get("site_record_id"), "animal aDNA site ID")
        source_path_text = _required_text(
            row.get("source_artifact_path"), "animal aDNA source path"
        )
        source_path = _safe_relative_path(source_path_text)
        source_paths.add(source_path)
        points.append(
            PointEvidence(
                source_family="animal_adna",
                source_scope="global_with_four_country_filter",
                source_record_id=record_id,
                longitude=_required_number(
                    row.get("longitude"), "animal aDNA longitude"
                ),
                latitude=_required_number(row.get("latitude"), "animal aDNA latitude"),
                raw_country=_optional_text(row.get("political_entity")),
                published_country=_optional_text(row.get("political_entity")),
                lineage=(
                    _lineage(candidates_path, f"rows[{index}]", "point_record"),
                    _lineage(
                        source_path,
                        _required_text(
                            row.get("source_locator"), "animal source locator"
                        ),
                        "source_native_row",
                    ),
                ),
            )
        )
    return (
        "animal_adna",
        points,
        _artifact_records(root, (candidates_path, *sorted(source_paths))),
    )
