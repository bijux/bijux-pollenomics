"""Fail-closed validation of PANGAEA 937075 modeled-context rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math

from ...core.geospatial.geojson import as_mapping, feature_list
from .contracts import (
    LANDCLIM_TEMPORAL_LAYER_KEY,
    OPEN_LAND_VALUE_UNIT,
    PANGAEA_COUNTRY_CELL_COUNTS,
    PANGAEA_DATASET_DOI,
    PANGAEA_DATASET_ID,
    PANGAEA_QUALITY_CLASSES,
)
from .metric_families import LAND_COVER_COMPONENT_KEYS, PANGAEA_METRIC_KEYS


class ModeledContextContractError(ValueError):
    """Raised when purported PANGAEA model rows violate the display contract."""


def model_properties(
    polygon_layers: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    """Select only PANGAEA 937075 rows from the governed temporal layer."""
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


def _finite_number(value: object, *, locator: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModeledContextContractError(f"{locator} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ModeledContextContractError(f"{locator} must be a finite number")
    return number


def _validate_metric_pairs(row: Mapping[str, object], *, record_id: str) -> None:
    estimates = as_mapping(row.get("reconstruction_values"))
    errors = as_mapping(row.get("standard_errors"))
    if estimates is None or errors is None:
        raise ModeledContextContractError(f"{record_id} lacks estimates or errors")
    if tuple(estimates) != PANGAEA_METRIC_KEYS:
        raise ModeledContextContractError(
            f"{record_id} estimate metric keys/order differ from the source header"
        )
    if tuple(errors) != PANGAEA_METRIC_KEYS:
        raise ModeledContextContractError(
            f"{record_id} standard-error metric keys/order differ from the source header"
        )
    numeric_estimates: dict[str, float] = {}
    for metric_key in PANGAEA_METRIC_KEYS:
        estimate = _finite_number(
            estimates.get(metric_key),
            locator=f"{record_id} {metric_key} estimate",
        )
        standard_error = _finite_number(
            errors.get(metric_key),
            locator=f"{record_id} {metric_key} standard error",
        )
        if not 0 <= estimate <= 100 or standard_error < 0:
            raise ModeledContextContractError(
                f"{record_id} has invalid {metric_key} values"
            )
        numeric_estimates[metric_key] = estimate
    for land_cover_key, component_keys in LAND_COVER_COMPONENT_KEYS.items():
        component_sum = sum(numeric_estimates[key] for key in component_keys)
        if not math.isclose(
            numeric_estimates[land_cover_key],
            component_sum,
            rel_tol=1e-12,
            abs_tol=1e-9,
        ):
            raise ModeledContextContractError(
                f"{record_id} {land_cover_key} does not reconcile to source PFT codes"
            )


def validate_model_row(
    row: Mapping[str, object],
    *,
    expected_windows: Mapping[str, tuple[int, int]],
) -> tuple[str, str, str]:
    """Validate identity, chronology, provenance, and all metric/error pairs."""
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
    quality_class = str(row.get("quality_class", "")).strip()
    if quality_class not in PANGAEA_QUALITY_CLASSES:
        raise ModeledContextContractError(
            f"{record_id} has an unsupported or missing quality class"
        )
    if row.get("temporal_comparability_posture") != "numeric_interval_with_caveat":
        raise ModeledContextContractError(f"{record_id} lacks modeled-time caveats")
    bibliography = row.get("bibliography_reference_keys")
    if not isinstance(bibliography, list) or "githumbi-et-al-2022" not in bibliography:
        raise ModeledContextContractError(f"{record_id} lacks Githumbi provenance")
    _validate_metric_pairs(row, record_id=record_id)
    return label, country, quality_class


__all__ = [
    "ModeledContextContractError",
    "model_properties",
    "validate_model_row",
]
