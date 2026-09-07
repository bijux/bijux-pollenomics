"""Field validation for source-bounded aurochs reconciliation."""

from __future__ import annotations


def _required_coordinate(value: str, *, label: str, axis: str) -> str:
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError(f"PRJEB75467 {label} {axis} is invalid") from error
    bound = 90 if axis == "latitude" else 180
    if not -bound <= number <= bound:
        raise ValueError(f"PRJEB75467 {label} {axis} is out of range")
    return value


def _source_coordinate_pair(
    latitude: str, longitude: str, *, label: str
) -> tuple[str, str]:
    """Preserve a paired source ``Unknown`` marker without treating it as a point."""
    if latitude == longitude == "Unknown":
        return latitude, longitude
    if "Unknown" in {latitude, longitude}:
        raise ValueError(f"PRJEB75467 {label} coordinate pair is incomplete")
    return (
        _required_coordinate(latitude, label=label, axis="latitude"),
        _required_coordinate(longitude, label=label, axis="longitude"),
    )


def _required(value: str, label: str, field: str) -> str:
    if not value:
        raise ValueError(f"PRJEB75467 {label} {field} is missing")
    return value


def _cell(row: tuple[str, ...], index: int) -> str:
    return row[index].strip() if index < len(row) else ""
