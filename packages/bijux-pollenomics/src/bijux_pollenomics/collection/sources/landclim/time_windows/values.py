"""Numeric, uncertainty, geometry, and grouped-value contracts."""

from __future__ import annotations

from collections.abc import Mapping


def _numeric_values(
    headers: list[str], row: list[str], *, start_index: int
) -> dict[str, float]:
    from . import clean_optional_text, parse_float

    return {
        clean_optional_text(headers[index]): parsed
        for index in range(start_index, min(len(headers), len(row)))
        for parsed in [parse_float(row[index])]
        if clean_optional_text(headers[index]) and parsed is not None
    }


def _numeric_mapping(
    row: Mapping[str, object], *, excluded: set[str]
) -> dict[str, float]:
    from . import clean_optional_text, parse_float

    return {
        str(key): parsed
        for key, value in row.items()
        if key not in excluded
        for parsed in [parse_float(clean_optional_text(value))]
        if parsed is not None
    }


def _require_uncertainty_pair(
    estimates: Mapping[str, float],
    standard_errors: Mapping[str, float],
    *,
    dataset_id: str,
    record_id: str,
) -> None:
    """Require exact, finite uncertainty coverage for every emitted model estimate."""
    from . import math

    estimate_variables = set(estimates)
    uncertainty_variables = set(standard_errors)
    if estimate_variables != uncertainty_variables:
        missing = sorted(estimate_variables - uncertainty_variables)
        unexpected = sorted(uncertainty_variables - estimate_variables)
        raise ValueError(
            "LandClim estimate/standard-error variables differ for "
            f"dataset {dataset_id} record {record_id}: "
            f"missing={missing}, unexpected={unexpected}"
        )
    invalid_estimates = sorted(
        variable for variable, value in estimates.items() if not math.isfinite(value)
    )
    invalid_uncertainties = sorted(
        variable
        for variable, value in standard_errors.items()
        if not math.isfinite(value) or value < 0
    )
    if invalid_estimates or invalid_uncertainties:
        raise ValueError(
            "LandClim estimate/standard-error values are invalid for "
            f"dataset {dataset_id} record {record_id}: "
            f"estimates={invalid_estimates}, standard_errors={invalid_uncertainties}"
        )


def _polygon_center(geometry: Mapping[str, object]) -> tuple[float, float]:
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("LandClim polygon has no coordinate ring")
    ring = coordinates[0]
    if not isinstance(ring, list) or len(ring) < 4:
        raise ValueError("LandClim polygon has an invalid coordinate ring")
    points = [
        point for point in ring[:4] if isinstance(point, list) and len(point) >= 2
    ]
    if len(points) != 4:
        raise ValueError("LandClim polygon has an invalid coordinate ring")
    return (
        sum(float(point[0]) for point in points) / 4,
        sum(float(point[1]) for point in points) / 4,
    )


def _properties(feature: dict[str, object]) -> dict[str, object]:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("LandClim temporal feature is missing properties")
    return properties


def _grouped_values(
    properties: dict[str, object], key: str
) -> dict[str, dict[str, float]]:
    value = properties.get(key)
    if isinstance(value, dict):
        return value
    grouped: dict[str, dict[str, float]] = {}
    properties[key] = grouped
    return grouped
