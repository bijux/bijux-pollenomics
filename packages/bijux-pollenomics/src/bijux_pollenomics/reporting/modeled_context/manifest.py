"""Build a fail-closed browser manifest from admitted LandClim polygons."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence

from .contracts import (
    GITHUMBI_CITATION,
    GITHUMBI_METHOD_DOI,
    LANDCLIM_TEMPORAL_LAYER_KEY,
    OPEN_LAND_METRIC_KEY,
    OPEN_LAND_METRIC_LABEL,
    OPEN_LAND_PALETTE,
    OPEN_LAND_VALUE_UNIT,
    PANGAEA_COUNTRY_CELL_COUNTS,
    PANGAEA_DATASET_DOI,
    PANGAEA_DATASET_ID,
    PANGAEA_QUALITY_CLASS_COUNTS,
    PANGAEA_QUALITY_CLASSES,
    PANGAEA_WINDOWS_PRESENT_TO_OLDEST,
)
from .metric_families import METRIC_FAMILIES, PANGAEA_METRIC_KEYS
from .validation import (
    ModeledContextContractError,
    ValidatedModelRow,
    expected_quality_inventory,
    model_features,
    validate_model_row,
)


def _unavailable(reason_code: str) -> dict[str, object]:
    return {
        "schema_version": "modeled-context-manifest.v3",
        "status": "unavailable",
        "reason_code": reason_code,
        "evidence_role": "context_only",
        "propagation_use_allowed": False,
        "metric_families": [],
        "windows_oldest_to_present": [],
    }


def _palette_contract() -> list[dict[str, object]]:
    palette: list[dict[str, object]] = []
    previous_maximum = 0
    for index, (maximum, color) in enumerate(OPEN_LAND_PALETTE):
        lower_label = "0" if index == 0 else f">{previous_maximum}"
        palette.append(
            {
                "maximum": maximum,
                "color": color,
                "label": f"{lower_label}–{maximum}%",
            }
        )
        previous_maximum = maximum
    return palette


def _validate_parent_topology(
    rows: Sequence[ValidatedModelRow], *, expected_windows: Mapping[str, object]
) -> None:
    expected_parent_count = sum(PANGAEA_COUNTRY_CELL_COUNTS.values())
    parent_window_counts = Counter(
        (row.parent_grid_record_id, row.time_label) for row in rows
    )
    parent_countries: dict[str, set[str]] = defaultdict(set)
    parent_geometries: dict[str, set[tuple[tuple[tuple[float, float], ...], ...]]] = (
        defaultdict(set)
    )
    for row in rows:
        parent_countries[row.parent_grid_record_id].add(row.country)
        parent_geometries[row.parent_grid_record_id].add(row.geometry_identity)
    parents = set(parent_countries)
    if len(parents) != expected_parent_count or any(
        parent_window_counts[(parent, time_label)] != 1
        for parent in parents
        for time_label in expected_windows
    ):
        raise ModeledContextContractError(
            "PANGAEA 937075 parent-grid/window topology is incomplete or duplicated"
        )
    if any(len(countries) != 1 for countries in parent_countries.values()):
        raise ModeledContextContractError(
            "PANGAEA 937075 parent-grid country assignment drifts across windows"
        )
    if any(len(geometries) != 1 for geometries in parent_geometries.values()):
        raise ModeledContextContractError(
            "PANGAEA 937075 parent-grid geometry drifts across windows"
        )
    parent_country_counts = Counter(
        next(iter(countries)) for countries in parent_countries.values()
    )
    if parent_country_counts != Counter(PANGAEA_COUNTRY_CELL_COUNTS):
        raise ModeledContextContractError(
            "PANGAEA 937075 parent-grid country inventory is incomplete"
        )


def build_modeled_context_manifest(
    polygon_layers: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Describe a complete PANGAEA 937075 Nordic metric surface."""
    features = model_features(polygon_layers)
    if not features:
        return _unavailable("pangaea_937075_temporal_grid_not_available")
    expected_windows = {
        label: (start, end) for label, start, end in PANGAEA_WINDOWS_PRESENT_TO_OLDEST
    }
    record_ids = [
        str(feature.properties.get("record_id", "")).strip() for feature in features
    ]
    if len(record_ids) != len(set(record_ids)):
        raise ModeledContextContractError("PANGAEA modeled record_ids are not unique")
    admitted_rows = [
        validate_model_row(
            feature.properties,
            expected_windows=expected_windows,
            geometry=feature.geometry,
        )
        for feature in features
    ]
    _validate_parent_topology(admitted_rows, expected_windows=expected_windows)
    inventory_counts = Counter((row.time_label, row.country) for row in admitted_rows)
    quality_counts = Counter(row.quality_class for row in admitted_rows)
    window_quality_counts = Counter(
        (row.time_label, row.quality_class) for row in admitted_rows
    )
    country_quality_counts = Counter(
        (row.country, row.quality_class) for row in admitted_rows
    )
    quality_inventory = Counter(
        (row.time_label, row.country, row.quality_class) for row in admitted_rows
    )
    expected_feature_count = len(expected_windows) * sum(
        PANGAEA_COUNTRY_CELL_COUNTS.values()
    )
    if len(features) != expected_feature_count or any(
        inventory_counts[(label, country)] != expected_country_count
        for label in expected_windows
        for country, expected_country_count in PANGAEA_COUNTRY_CELL_COUNTS.items()
    ):
        raise ModeledContextContractError(
            "PANGAEA 937075 Nordic country/window inventory is incomplete"
        )
    if any(
        quality_counts[quality_class] != expected_count
        for quality_class, expected_count in PANGAEA_QUALITY_CLASS_COUNTS.items()
    ):
        raise ModeledContextContractError(
            "PANGAEA 937075 quality-class inventory differs from the source workbook"
        )
    if quality_inventory != expected_quality_inventory():
        raise ModeledContextContractError(
            "PANGAEA 937075 country/window quality inventory differs from the "
            "source workbook"
        )
    windows = [
        {
            "label": label,
            "time_start_bp": start,
            "time_end_bp": end,
            "feature_count": sum(PANGAEA_COUNTRY_CELL_COUNTS.values()),
            "no_pollen_data_count": window_quality_counts[(label, "no_pollen_data")],
            "quality_class_counts": {
                quality_class: window_quality_counts[(label, quality_class)]
                for quality_class in PANGAEA_QUALITY_CLASSES
            },
            "country_counts": dict(PANGAEA_COUNTRY_CELL_COUNTS),
            "country_quality_class_counts": {
                country: {
                    quality_class: quality_inventory[(label, country, quality_class)]
                    for quality_class in PANGAEA_QUALITY_CLASSES
                }
                for country in PANGAEA_COUNTRY_CELL_COUNTS
            },
        }
        for label, start, end in reversed(PANGAEA_WINDOWS_PRESENT_TO_OLDEST)
    ]
    return {
        "schema_version": "modeled-context-manifest.v3",
        "status": "available",
        "reason_code": None,
        "layer_key": LANDCLIM_TEMPORAL_LAYER_KEY,
        "dataset_id": PANGAEA_DATASET_ID,
        "dataset_doi": PANGAEA_DATASET_DOI,
        "method_citation": GITHUMBI_CITATION,
        "method_doi": GITHUMBI_METHOD_DOI,
        "metric_key": OPEN_LAND_METRIC_KEY,
        "metric_label": OPEN_LAND_METRIC_LABEL,
        "value_unit": OPEN_LAND_VALUE_UNIT,
        "default_metric_family_key": "source_land_cover_types",
        "metric_family_count": len(METRIC_FAMILIES),
        "metric_count": len(PANGAEA_METRIC_KEYS),
        "estimate_standard_error_pair_count": len(features) * len(PANGAEA_METRIC_KEYS),
        "land_cover_pft_reconciliation_count": len(features) * 3,
        "metric_families": [family.as_dict() for family in METRIC_FAMILIES],
        "palette": _palette_contract(),
        "evidence_role": "context_only",
        "propagation_use_allowed": False,
        "interpolation_allowed": False,
        "cell_count": sum(PANGAEA_COUNTRY_CELL_COUNTS.values()),
        "feature_count": len(features),
        "quality_classes": list(PANGAEA_QUALITY_CLASSES),
        "quality_class_counts": {
            quality_class: quality_counts[quality_class]
            for quality_class in PANGAEA_QUALITY_CLASSES
        },
        "no_pollen_data_display_posture": "null_not_zero",
        "country_cell_counts": dict(PANGAEA_COUNTRY_CELL_COUNTS),
        "country_quality_class_counts": {
            country: {
                quality_class: country_quality_counts[(country, quality_class)]
                for quality_class in PANGAEA_QUALITY_CLASSES
            }
            for country in PANGAEA_COUNTRY_CELL_COUNTS
        },
        "windows_oldest_to_present": windows,
        "download_schema_version": "modeled-context-visible-frame.v3",
    }


__all__ = ["ModeledContextContractError", "build_modeled_context_manifest"]
