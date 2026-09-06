"""Animal ancient-DNA point evidence for governed boundary review."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.workflow.source_artifacts import (
    resolve_source_artifact_path,
)

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
        source_locator = _required_text(
            row.get("source_locator"), "animal source locator"
        )
        row_source_paths, source_lineage = _animal_source_lineage(
            root,
            source_path_text=source_path_text,
            source_locator=source_locator,
            record_id=record_id,
        )
        source_paths.update(row_source_paths)
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
                    *source_lineage,
                ),
            )
        )
    return (
        "animal_adna",
        points,
        _artifact_records(root, (candidates_path, *sorted(source_paths))),
    )


def _stored_relative_path(root: Path, value: str) -> Path:
    logical_path = _safe_relative_path(value)
    stored_path = resolve_source_artifact_path(root / logical_path)
    try:
        return stored_path.relative_to(root)
    except ValueError as error:
        raise ValueError(
            f"Animal aDNA source artifact escaped the repository: {value}"
        ) from error


def _animal_source_lineage(
    root: Path,
    *,
    source_path_text: str,
    source_locator: str,
    record_id: str,
) -> tuple[tuple[Path, ...], tuple[JsonObject, ...]]:
    source_paths = tuple(
        _stored_relative_path(root, value.strip())
        for value in source_path_text.split(" || ")
    )
    if not source_paths:
        raise ValueError("Animal aDNA source lineage is empty")
    source_locators = tuple(value.strip() for value in source_locator.split(" || "))
    if len(source_paths) == 1:
        return source_paths, (
            _lineage(source_paths[0], source_locator, "source_native_row"),
        )
    if len(source_paths) == len(source_locators):
        return source_paths, tuple(
            _lineage(path, locator, "source_native_row")
            for path, locator in zip(source_paths, source_locators, strict=True)
        )
    raise ValueError(
        f"Animal aDNA source paths and locators cannot be reconciled for {record_id}"
    )
