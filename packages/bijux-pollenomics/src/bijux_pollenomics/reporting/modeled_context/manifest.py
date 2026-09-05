"""Build a fail-closed browser manifest from admitted LandClim polygons."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import math

from ...core.geospatial.geojson import as_mapping, feature_list
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
    PANGAEA_WINDOWS_PRESENT_TO_OLDEST,
)


class ModeledContextContractError(ValueError):
    """Raised when purported PANGAEA model rows violate the display contract."""


def _unavailable(reason_code: str) -> dict[str, object]:
    return {
        "schema_version": "modeled-context-manifest.v1",
        "status": "unavailable",
        "reason_code": reason_code,
        "evidence_role": "context_only",
        "propagation_use_allowed": False,
        "windows_oldest_to_present": [],
    }


def _finite_number(value: object, *, locator: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModeledContextContractError(f"{locator} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ModeledContextContractError(f"{locator} must be a finite number")
    return number


def _model_properties(
    polygon_layers: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    rows: list[Mapping[str, object]] = []
    for layer in polygon_layers:
        if layer.get("key") != LANDCLIM_TEMPORAL_LAYER_KEY:
            continue
        geojson = as_mapping(layer.get("geojson"))
        if geojson is None:
            raise ModeledContextContractError("LandClim temporal layer has no GeoJSON")
        for feature in feature_list(geojson):
            properties = as_mapping(feature.get("properties"))
            if (
                properties is not None
                and properties.get("dataset_id") == PANGAEA_DATASET_ID
            ):
                rows.append(properties)
    return rows


def _validate_row(
    row: Mapping[str, object],
    *,
    expected_windows: Mapping[str, tuple[int, int]],
) -> tuple[str, str]:
    record_id = str(row.get("record_id", "")).strip()
    if not record_id:
        raise ModeledContextContractError("PANGAEA modeled row has no record_id")
    label = str(row.get("time_label", ""))
    expected = expected_windows.get(label)
    if (
        expected is None
        or (row.get("time_start_bp"), row.get("time_end_bp")) != expected
    ):
        raise ModeledContextContractError(
            f"{record_id} has an unsupported source window"
        )
    country = str(row.get("country", ""))
    if country not in PANGAEA_COUNTRY_CELL_COUNTS:
        raise ModeledContextContractError(f"{record_id} has an unsupported country")
    if row.get("source_url") != PANGAEA_DATASET_DOI:
        raise ModeledContextContractError(f"{record_id} has the wrong PANGAEA DOI")
    if row.get("value_unit") != OPEN_LAND_VALUE_UNIT:
        raise ModeledContextContractError(f"{record_id} has the wrong value unit")
    if row.get("temporal_comparability_posture") != "numeric_interval_with_caveat":
        raise ModeledContextContractError(f"{record_id} lacks modeled-time caveats")
    bibliography = row.get("bibliography_reference_keys")
    if not isinstance(bibliography, list) or "githumbi-et-al-2022" not in bibliography:
        raise ModeledContextContractError(f"{record_id} lacks Githumbi provenance")
    estimates = as_mapping(row.get("reconstruction_values"))
    errors = as_mapping(row.get("standard_errors"))
    if estimates is None or errors is None:
        raise ModeledContextContractError(f"{record_id} lacks estimates or errors")
    estimate = _finite_number(
        estimates.get(OPEN_LAND_METRIC_KEY), locator=f"{record_id} OL estimate"
    )
    standard_error = _finite_number(
        errors.get(OPEN_LAND_METRIC_KEY), locator=f"{record_id} OL standard error"
    )
    if not 0 <= estimate <= 100 or standard_error < 0:
        raise ModeledContextContractError(f"{record_id} has invalid OL values")
    return label, country


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


def build_modeled_context_manifest(
    polygon_layers: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Describe only a complete, exact PANGAEA 937075 Nordic OL surface."""
    rows = _model_properties(polygon_layers)
    if not rows:
        return _unavailable("pangaea_937075_temporal_grid_not_available")
    expected_windows = {
        label: (start, end) for label, start, end in PANGAEA_WINDOWS_PRESENT_TO_OLDEST
    }
    record_ids = [str(row.get("record_id", "")).strip() for row in rows]
    if len(record_ids) != len(set(record_ids)):
        raise ModeledContextContractError("PANGAEA modeled record_ids are not unique")
    counts = Counter(
        _validate_row(row, expected_windows=expected_windows) for row in rows
    )
    expected_feature_count = len(expected_windows) * sum(
        PANGAEA_COUNTRY_CELL_COUNTS.values()
    )
    if len(rows) != expected_feature_count or any(
        counts[(label, country)] != expected_country_count
        for label in expected_windows
        for country, expected_country_count in PANGAEA_COUNTRY_CELL_COUNTS.items()
    ):
        raise ModeledContextContractError(
            "PANGAEA 937075 Nordic country/window inventory is incomplete"
        )
    windows = [
        {
            "label": label,
            "time_start_bp": start,
            "time_end_bp": end,
            "feature_count": sum(PANGAEA_COUNTRY_CELL_COUNTS.values()),
            "country_counts": dict(PANGAEA_COUNTRY_CELL_COUNTS),
        }
        for label, start, end in reversed(PANGAEA_WINDOWS_PRESENT_TO_OLDEST)
    ]
    return {
        "schema_version": "modeled-context-manifest.v1",
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
        "palette": _palette_contract(),
        "evidence_role": "context_only",
        "propagation_use_allowed": False,
        "interpolation_allowed": False,
        "cell_count": sum(PANGAEA_COUNTRY_CELL_COUNTS.values()),
        "feature_count": len(rows),
        "country_cell_counts": dict(PANGAEA_COUNTRY_CELL_COUNTS),
        "windows_oldest_to_present": windows,
        "download_schema_version": "modeled-context-visible-frame.v1",
    }


__all__ = ["ModeledContextContractError", "build_modeled_context_manifest"]
