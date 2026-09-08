"""Scoped row, identity, country, and coverage validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import math

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    NORDIC_COUNTRY_CODES,
)

from .models import SeadDependency, SeadScopedTablePlan


def _dependency_ids(
    dependencies: Sequence[SeadDependency],
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
) -> tuple[int, ...]:
    values: set[int] = set()
    for dependency in dependencies:
        if dependency.table not in rows_by_table:
            raise ValueError(
                f"SEAD acquisition dependency is not available: {dependency.table}"
            )
        for row in rows_by_table[dependency.table]:
            value = row.get(dependency.field)
            if value is not None:
                values.add(_required_source_id(row, dependency.field))
    return tuple(sorted(values))


def _validated_rows(
    table: str,
    rows: Iterable[Mapping[str, object]],
    primary_key: str,
    projection: str,
) -> tuple[dict[str, object], ...]:
    projected_fields = set(projection.split(","))
    materialized: list[dict[str, object]] = []
    identities: list[int] = []
    for index, row in enumerate(rows):
        missing = sorted(projected_fields - set(row))
        if missing:
            raise ValueError(
                f"SEAD {table} row {index} is missing projected fields: {missing}"
            )
        identities.append(_required_source_id(row, primary_key))
        materialized.append(dict(row))
    duplicates = sorted(
        identity for identity, count in Counter(identities).items() if count > 1
    )
    if duplicates:
        raise ValueError(f"SEAD {table} contains duplicate source keys: {duplicates}")
    materialized.sort(key=lambda row: _required_source_id(row, primary_key))
    return tuple(materialized)


def _required_source_id(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(
            f"SEAD source key must be a positive integer: {field}={value!r}"
        )
    return value


def _validate_site_uuids(rows: Sequence[Mapping[str, object]]) -> None:
    uuids: list[str] = []
    for row in rows:
        value = row.get("site_uuid")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"SEAD site_uuid is required for site_id={row.get('site_id')!r}"
            )
        uuids.append(value)
    duplicates = sorted(value for value, count in Counter(uuids).items() if count > 1)
    if duplicates:
        raise ValueError(f"SEAD site_uuid values are not unique: {duplicates}")


def _normalize_country_assignments(
    values: Mapping[object, str],
) -> dict[int, str]:
    normalized: dict[int, str] = {}
    for raw_site_id, raw_code in values.items():
        site_id = _mapping_site_id(raw_site_id)
        if site_id in normalized:
            raise ValueError(f"Duplicate normalized SEAD country site ID: {site_id}")
        if not isinstance(raw_code, str):
            raise ValueError(f"Invalid governed SEAD country code: {raw_code!r}")
        code = raw_code.strip().upper()
        if code not in NORDIC_COUNTRY_CODES:
            raise ValueError(f"Invalid governed SEAD country code: {raw_code!r}")
        normalized[site_id] = code
    return normalized


def _mapping_site_id(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Invalid governed SEAD site ID: {value!r}")
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        if parsed > 0:
            return parsed
    raise ValueError(f"Invalid governed SEAD site ID: {value!r}")


def _validate_declared_table_coverage(
    table_plans: Sequence[SeadScopedTablePlan],
    required_tables: Sequence[str],
    relation_scope: str,
) -> None:
    planned = ("tbl_sites", *(plan.table for plan in table_plans))
    if len(planned) != len(set(planned)) or set(planned) != set(required_tables):
        raise RuntimeError(
            f"SEAD {relation_scope} acquisition plans do not exactly cover "
            "declared source tables"
        )


def _validate_bbox(bbox: tuple[float, float, float, float]) -> None:
    if len(bbox) != 4 or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        for value in bbox
    ):
        raise ValueError("SEAD bbox must contain four finite numeric values")
    minimum_longitude, minimum_latitude, maximum_longitude, maximum_latitude = bbox
    if not (
        -180 <= minimum_longitude < maximum_longitude <= 180
        and -90 <= minimum_latitude < maximum_latitude <= 90
    ):
        raise ValueError("SEAD bbox is outside valid longitude/latitude bounds")


def _bbox_filters(
    bbox: tuple[float, float, float, float],
) -> tuple[tuple[str, str], ...]:
    minimum_longitude, minimum_latitude, maximum_longitude, maximum_latitude = bbox
    return (
        ("latitude_dd", f"gte.{minimum_latitude}"),
        ("latitude_dd", f"lte.{maximum_latitude}"),
        ("longitude_dd", f"gte.{minimum_longitude}"),
        ("longitude_dd", f"lte.{maximum_longitude}"),
    )
