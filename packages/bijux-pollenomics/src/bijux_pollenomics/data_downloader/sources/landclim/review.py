from __future__ import annotations

from datetime import date
from pathlib import Path

from ....core.files import write_json
from ...models import ContextPointRecord

__all__ = [
    "build_landclim_spatiotemporal_review",
    "render_landclim_spatiotemporal_review_markdown",
    "write_landclim_review_outputs",
]


def build_landclim_spatiotemporal_review(
    records: list[ContextPointRecord],
    temporal_grid_geojson: dict[str, object],
    bibliography: dict[str, object],
) -> dict[str, object]:
    """Review LandClim temporal coverage and bibliography linkage by dataset."""
    features = temporal_grid_geojson.get("features", [])
    if not isinstance(features, list):
        features = []
    datasets = bibliography.get("datasets", [])
    if not isinstance(datasets, list):
        datasets = []

    rows: list[dict[str, object]] = []
    for dataset in datasets:
        if not isinstance(dataset, dict):
            continue
        dataset_id = str(dataset.get("dataset_id", "")).strip()
        dataset_doi = str(dataset.get("doi", "")).strip()
        dataset_records = [
            record for record in records if record.source_url == dataset_doi
        ]
        dataset_features = [
            feature
            for feature in features
            if isinstance(feature, dict)
            and _properties(feature).get("dataset_id") == dataset_id
        ]
        numeric_site_count = sum(
            1
            for record in dataset_records
            if record.time_start_bp is not None and record.time_end_bp is not None
        )
        window_rows = sorted(
            {
                (
                    _integer(_properties(feature).get("time_start_bp")),
                    _integer(_properties(feature).get("time_end_bp")),
                    str(_properties(feature).get("time_label", "")).strip(),
                )
                for feature in dataset_features
            }
        )
        reference_keys = {
            str(key)
            for feature in dataset_features
            for key in _string_list(
                _properties(feature).get("bibliography_reference_keys")
            )
        }
        expected_reference_keys = set(
            _string_list(dataset.get("related_reference_keys"))
        )
        rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_label": str(dataset.get("label", "")).strip(),
                "dataset_doi": dataset_doi,
                "dataset_citation": str(dataset.get("citation", "")).strip(),
                "site_sequence_count": len(dataset_records),
                "numeric_site_interval_count": numeric_site_count,
                "unresolved_site_interval_count": (
                    len(dataset_records) - numeric_site_count
                ),
                "temporal_grid_feature_count": len(dataset_features),
                "temporal_grid_cell_count": len(
                    {
                        str(_properties(feature).get("parent_grid_record_id", ""))
                        for feature in dataset_features
                    }
                    - {""}
                ),
                "temporal_window_count": len(window_rows),
                "temporal_windows": [row[2] for row in window_rows],
                "bibliography_reference_keys": sorted(expected_reference_keys),
                "temporal_grid_reference_keys": sorted(reference_keys),
                "bibliography_linkage_complete": (
                    not dataset_features
                    or bool(expected_reference_keys)
                    and reference_keys.issubset(expected_reference_keys)
                    and bool(reference_keys)
                ),
                "temporal_posture": (
                    "site_intervals_and_modeled_grid_windows"
                    if dataset_features
                    else "site_intervals_without_normalized_grid_windows"
                ),
            }
        )

    numeric_site_count = sum(
        1
        for record in records
        if record.time_start_bp is not None and record.time_end_bp is not None
    )
    numeric_grid_count = sum(
        1
        for feature in features
        if _properties(feature).get("time_start_bp") is not None
        and _properties(feature).get("time_end_bp") is not None
    )
    bibliography_linked_grid_count = sum(
        1
        for feature in features
        if _string_list(_properties(feature).get("bibliography_reference_keys"))
    )
    return {
        "schema_version": "landclim-spatiotemporal-review.v1",
        "generated_on": str(date.today()),
        "source": "LandClim",
        "site_sequence_count": len(records),
        "numeric_site_interval_count": numeric_site_count,
        "unresolved_site_interval_count": len(records) - numeric_site_count,
        "temporal_grid_feature_count": len(features),
        "numeric_temporal_grid_feature_count": numeric_grid_count,
        "bibliography_linked_temporal_grid_feature_count": (
            bibliography_linked_grid_count
        ),
        "dataset_count": len(rows),
        "reference_count": _integer(bibliography.get("reference_count")),
        "all_site_rows_have_explicit_temporal_posture": all(
            bool(record.temporal_semantics) for record in records
        ),
        "all_temporal_grid_rows_have_numeric_bounds": numeric_grid_count == len(features),
        "all_temporal_grid_rows_have_bibliography_links": (
            bibliography_linked_grid_count == len(features)
        ),
        "rows": rows,
        "interpretation_caveats": [
            "REVEALS windows are modeled vegetation estimates, not sample-owned chronologies.",
            "Separate published windows do not imply continuous values between windows.",
            "Upstream-undated site sequences remain explicit spatial context and are not assigned synthetic ages.",
        ],
    }


def write_landclim_review_outputs(
    output_root: Path,
    *,
    records: list[ContextPointRecord],
    temporal_grid_geojson: dict[str, object],
    bibliography: dict[str, object],
) -> Path:
    """Write the governed LandClim temporal and bibliography review."""
    review_root = Path(output_root) / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    payload = build_landclim_spatiotemporal_review(
        records,
        temporal_grid_geojson,
        bibliography,
    )
    review_path = review_root / "spatiotemporal_review.json"
    write_json(review_path, payload)
    (review_root / "spatiotemporal_review.md").write_text(
        render_landclim_spatiotemporal_review_markdown(payload),
        encoding="utf-8",
    )
    return review_path


def render_landclim_spatiotemporal_review_markdown(
    payload: dict[str, object],
) -> str:
    """Render the LandClim review as a reader-facing evidence receipt."""
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    table_rows = "\n".join(
        (
            f"| {row.get('dataset_id', '')} | {row.get('site_sequence_count', 0)} | "
            f"{row.get('numeric_site_interval_count', 0)} | "
            f"{row.get('temporal_grid_cell_count', 0)} | "
            f"{row.get('temporal_window_count', 0)} | "
            f"{row.get('temporal_grid_feature_count', 0)} | "
            f"{row.get('temporal_posture', '')} |"
        )
        for row in rows
        if isinstance(row, dict)
    )
    caveats = payload.get("interpretation_caveats", [])
    caveat_lines = "\n".join(
        f"- {caveat}" for caveat in caveats if isinstance(caveat, str)
    )
    return f"""# LandClim spatiotemporal review

This review joins LandClim site-sequence intervals, modeled REVEALS time windows, and the dataset bibliography without flattening them into one observation type.

- Site sequences: `{payload.get('site_sequence_count', 0)}`
- Site sequences with numeric bounds: `{payload.get('numeric_site_interval_count', 0)}`
- Explicitly unresolved site intervals: `{payload.get('unresolved_site_interval_count', 0)}`
- Time-window grid features: `{payload.get('temporal_grid_feature_count', 0)}`
- Time-window grid features with bibliography links: `{payload.get('bibliography_linked_temporal_grid_feature_count', 0)}`
- Governed dataset citations: `{payload.get('dataset_count', 0)}`
- Governed publication references: `{payload.get('reference_count', 0)}`

| Dataset | Site sequences | Numeric site intervals | Grid cells | Windows | Grid-window features | Temporal posture |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{table_rows}

## Interpretation boundaries

{caveat_lines}
"""


def _properties(feature: object) -> dict[str, object]:
    if not isinstance(feature, dict):
        return {}
    properties = feature.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _integer(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0
