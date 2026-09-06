"""Fail-closed validation of PANGAEA 937075 modeled-context rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ModeledContextFeature:
    """One governed model row paired with the geometry it describes."""

    properties: Mapping[str, object]
    geometry: Mapping[str, object]


@dataclass(frozen=True)
class ValidatedModelRow:
    """Identity dimensions required to reconcile the temporal grid."""

    record_id: str
    parent_grid_record_id: str
    time_label: str
    country: str
    quality_class: str
    geometry_identity: tuple[tuple[tuple[float, float], ...], ...]


# Counts transcribed from the source workbook's GC_quality_by_TW sheet after the
# governed Nordic spatial filter. Keeping the country/window intersection makes a
# label swap visible even when the 1,875-row global totals remain unchanged.
_QUALITY_COUNTS_BY_WINDOW_COUNTRY: Mapping[str, Mapping[str, tuple[int, int, int]]] = {
    "0-100 BP": {
        "Denmark": (4, 1, 1),
        "Finland": (2, 14, 3),
        "Norway": (7, 13, 4),
        "Sweden": (11, 13, 2),
    },
    "100-350 BP": {
        "Denmark": (5, 1, 0),
        "Finland": (4, 10, 5),
        "Norway": (7, 13, 4),
        "Sweden": (12, 14, 0),
    },
    "350-700 BP": {
        "Denmark": (2, 2, 2),
        "Finland": (3, 14, 2),
        "Norway": (7, 16, 1),
        "Sweden": (12, 14, 0),
    },
    "700-1200 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (5, 12, 2),
        "Norway": (8, 14, 2),
        "Sweden": (12, 13, 1),
    },
    "1200-1700 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 14, 1),
        "Norway": (10, 13, 1),
        "Sweden": (11, 15, 0),
    },
    "1700-2200 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (5, 12, 2),
        "Norway": (10, 13, 1),
        "Sweden": (12, 14, 0),
    },
    "2200-2700 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 15, 0),
        "Norway": (10, 12, 2),
        "Sweden": (11, 15, 0),
    },
    "2700-3200 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 14, 1),
        "Norway": (10, 14, 0),
        "Sweden": (12, 13, 1),
    },
    "3200-3700 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 15, 0),
        "Norway": (10, 14, 0),
        "Sweden": (12, 14, 0),
    },
    "3700-4200 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (3, 15, 1),
        "Norway": (9, 15, 0),
        "Sweden": (12, 13, 1),
    },
    "4200-4700 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 13, 2),
        "Norway": (10, 13, 1),
        "Sweden": (12, 12, 2),
    },
    "4700-5200 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 13, 2),
        "Norway": (10, 14, 0),
        "Sweden": (12, 13, 1),
    },
    "5200-5700 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 12, 3),
        "Norway": (10, 14, 0),
        "Sweden": (11, 14, 1),
    },
    "5700-6200 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (3, 12, 4),
        "Norway": (10, 14, 0),
        "Sweden": (12, 12, 2),
    },
    "6200-6700 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 12, 3),
        "Norway": (10, 14, 0),
        "Sweden": (12, 12, 2),
    },
    "6700-7200 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 11, 4),
        "Norway": (10, 14, 0),
        "Sweden": (11, 13, 2),
    },
    "7200-7700 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (4, 11, 4),
        "Norway": (10, 14, 0),
        "Sweden": (11, 13, 2),
    },
    "7700-8200 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (3, 12, 4),
        "Norway": (10, 14, 0),
        "Sweden": (11, 12, 3),
    },
    "8200-8700 BP": {
        "Denmark": (2, 1, 3),
        "Finland": (3, 12, 4),
        "Norway": (10, 14, 0),
        "Sweden": (11, 10, 5),
    },
    "8700-9200 BP": {
        "Denmark": (2, 0, 4),
        "Finland": (3, 12, 4),
        "Norway": (10, 12, 2),
        "Sweden": (11, 9, 6),
    },
    "9200-9700 BP": {
        "Denmark": (2, 0, 4),
        "Finland": (3, 12, 4),
        "Norway": (10, 12, 2),
        "Sweden": (11, 9, 6),
    },
    "9700-10200 BP": {
        "Denmark": (2, 0, 4),
        "Finland": (3, 9, 7),
        "Norway": (9, 12, 3),
        "Sweden": (8, 10, 8),
    },
    "10200-10700 BP": {
        "Denmark": (1, 1, 4),
        "Finland": (2, 7, 10),
        "Norway": (8, 11, 5),
        "Sweden": (7, 9, 10),
    },
    "10700-11200 BP": {
        "Denmark": (0, 2, 4),
        "Finland": (1, 6, 12),
        "Norway": (6, 9, 9),
        "Sweden": (7, 7, 12),
    },
    "11200-11700 BP": {
        "Denmark": (0, 1, 5),
        "Finland": (1, 2, 16),
        "Norway": (5, 7, 12),
        "Sweden": (4, 7, 15),
    },
}


def expected_quality_inventory() -> Counter[tuple[str, str, str]]:
    """Return the governed quality totals at country/window granularity."""
    inventory: Counter[tuple[str, str, str]] = Counter()
    for time_label, countries in _QUALITY_COUNTS_BY_WINDOW_COUNTRY.items():
        for country, counts in countries.items():
            for quality_class, count in zip(
                PANGAEA_QUALITY_CLASSES, counts, strict=True
            ):
                inventory[(time_label, country, quality_class)] = count
    return inventory


def model_features(
    polygon_layers: Sequence[Mapping[str, object]],
) -> list[ModeledContextFeature]:
    """Select PANGAEA 937075 properties with their governed geometries."""
    features: list[ModeledContextFeature] = []
    for layer in polygon_layers:
        if layer.get("key") != LANDCLIM_TEMPORAL_LAYER_KEY:
            continue
        geojson = as_mapping(layer.get("geojson"))
        if geojson is None:
            raise ModeledContextContractError("LandClim temporal layer has no GeoJSON")
        for feature in feature_list(geojson):
            properties = as_mapping(feature.get("properties"))
            if properties is None or properties.get("dataset_id") != PANGAEA_DATASET_ID:
                continue
            geometry = as_mapping(feature.get("geometry"))
            if geometry is None:
                record_id = str(properties.get("record_id", "")).strip()
                raise ModeledContextContractError(
                    f"{record_id or 'PANGAEA modeled row'} has no geometry"
                )
            features.append(
                ModeledContextFeature(properties=properties, geometry=geometry)
            )
    return features


def model_properties(
    polygon_layers: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    """Select only PANGAEA 937075 rows from the governed temporal layer."""
    return [feature.properties for feature in model_features(polygon_layers)]


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


def _geometry_identity(
    geometry: Mapping[str, object], *, record_id: str
) -> tuple[tuple[tuple[float, float], ...], ...]:
    if geometry.get("type") != "Polygon":
        raise ModeledContextContractError(f"{record_id} has unsupported geometry")
    raw_rings = geometry.get("coordinates")
    if not isinstance(raw_rings, Sequence) or isinstance(
        raw_rings, (str, bytes, bytearray)
    ):
        raise ModeledContextContractError(f"{record_id} has invalid geometry")
    rings: list[tuple[tuple[float, float], ...]] = []
    for raw_ring in raw_rings:
        if not isinstance(raw_ring, Sequence) or isinstance(
            raw_ring, (str, bytes, bytearray)
        ):
            raise ModeledContextContractError(f"{record_id} has invalid geometry")
        ring: list[tuple[float, float]] = []
        for raw_position in raw_ring:
            if (
                not isinstance(raw_position, Sequence)
                or isinstance(raw_position, (str, bytes, bytearray))
                or len(raw_position) != 2
            ):
                raise ModeledContextContractError(f"{record_id} has invalid geometry")
            longitude = _finite_number(
                raw_position[0], locator=f"{record_id} geometry longitude"
            )
            latitude = _finite_number(
                raw_position[1], locator=f"{record_id} geometry latitude"
            )
            if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
                raise ModeledContextContractError(
                    f"{record_id} has out-of-range geometry"
                )
            ring.append((longitude, latitude))
        if len(ring) < 4 or ring[0] != ring[-1]:
            raise ModeledContextContractError(f"{record_id} has invalid geometry")
        rings.append(tuple(ring))
    if not rings:
        raise ModeledContextContractError(f"{record_id} has invalid geometry")
    return tuple(rings)


def validate_model_row(
    row: Mapping[str, object],
    *,
    expected_windows: Mapping[str, tuple[int, int]],
    geometry: Mapping[str, object],
) -> ValidatedModelRow:
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
    parent_grid_record_id = str(row.get("parent_grid_record_id", "")).strip()
    if not parent_grid_record_id:
        raise ModeledContextContractError(f"{record_id} has no parent grid identity")
    if not record_id.startswith(f"{PANGAEA_DATASET_ID}:{parent_grid_record_id}:"):
        raise ModeledContextContractError(
            f"{record_id} disagrees with its parent grid identity"
        )
    _validate_metric_pairs(row, record_id=record_id)
    return ValidatedModelRow(
        record_id=record_id,
        parent_grid_record_id=parent_grid_record_id,
        time_label=label,
        country=country,
        quality_class=quality_class,
        geometry_identity=_geometry_identity(geometry, record_id=record_id),
    )


__all__ = [
    "ModeledContextFeature",
    "ModeledContextContractError",
    "ValidatedModelRow",
    "expected_quality_inventory",
    "model_features",
    "model_properties",
    "validate_model_row",
]
