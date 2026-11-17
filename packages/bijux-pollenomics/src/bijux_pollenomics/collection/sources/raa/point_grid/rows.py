"""Conserve native UUIDs and raw POINT cardinality before conditional cell counts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from hashlib import sha256
import sqlite3
from typing import Any, cast

from ..geometry.binary import describe_geometry
from ..geometry.crs import inspect_crs
from ..geometry.rows import _native
from ..materialization.contracts import GEOMETRY_TYPES
from ..materialization.ownership import _uuid, canonical_bytes
from ..materialization.reading import quote_identifier, source_profile
from .contracts import DISPOSITIONS, NativePointGridLimits
from .projection import NativePointProjection, grid_cell


@dataclass(slots=True)
class _Owner:
    fid: int
    native_class: object
    raw: int = 0
    valid: int = 0
    uncertainty: int = 0
    xy: tuple[float, float] | None = None
    reasons: tuple[str, ...] = ()


def iter_point_grid_documents(
    connection: sqlite3.Connection,
    limits: NativePointGridLimits,
    projection: NativePointProjection,
) -> Iterator[dict[str, object]]:
    """Decode primary POINT only; separately authenticate all geometry ownership."""
    profile = cast(dict[str, Any], source_profile(connection))
    crs = inspect_crs(profile)
    if crs["status"] != "declared_crs_verified":
        raise ValueError(
            "Native POINT source CRS declarations conflict or are unsupported"
        )
    if profile["tables"]["lamning"]["row_count"] > limits.max_uuid_records:
        raise ValueError("Native UUID row budget exceeded")
    roles = {name: profile["tables"][name]["row_count"] for name in GEOMETRY_TYPES}
    if sum(roles.values()) > limits.max_geometry_rows:
        raise ValueError("Native geometry row budget exceeded")
    owners: dict[str, _Owner] = {}
    for row in connection.execute(
        "SELECT fid,uuid,antikvariskbedomning FROM lamning ORDER BY fid"
    ):
        key = _uuid(row[1])
        if key is None or type(row[0]) is not int:
            raise ValueError("Native UUID owner is invalid or missing")
        if key in owners:
            raise ValueError("Native UUID owner is duplicate")
        owners[key] = _Owner(row[0], row[2])
    if len(owners) != profile["tables"]["lamning"]["row_count"]:
        raise ValueError("Native UUID source denominator changed")
    for table in GEOMETRY_TYPES:
        observed = 0
        for row in connection.execute(
            f"SELECT fid,lamning_uuid FROM {quote_identifier(table)} ORDER BY fid"
        ):
            key = _uuid(row[1])
            if key is None or key not in owners or type(row[0]) is not int:
                raise ValueError("Native geometry owner is invalid or orphaned")
            observed += 1
            if table == "point":
                owners[key].raw += 1
            elif table == "lämningar_sverige_lägesosäkerhet":
                owners[key].uncertainty += 1
        if observed != roles[table]:
            raise ValueError("Native geometry owner denominator changed")
    # Refuse oversize blobs before projecting any point payload from SQLite.
    for row in connection.execute(
        "SELECT length(geometri) FROM point WHERE typeof(geometri)='blob'"
    ):
        if row[0] > limits.max_point_bytes:
            raise ValueError("Native point blob byte budget exceeded")
    observed = valid = 0
    for row in connection.execute(
        "SELECT fid,lamning_uuid,typeof(geometri),"
        "CASE WHEN typeof(geometri)='blob' THEN geometri ELSE NULL END "
        "FROM point ORDER BY fid"
    ):
        owner = owners[row[1]]
        # Non-BLOB storage is accounted from its native type without exposing
        # arbitrary TEXT payloads through SQLite's Python decoder.
        description = (
            describe_geometry(row[3], geometry_type="POINT")
            if row[2] in {"blob", "null"}
            else {"status": "invalid", "reason_codes": ["non_blob_geometry"]}
        )
        if description.get("header_srs_id", 3006) != 3006:
            raise ValueError(
                "Native point header CRS conflicts with source declaration"
            )
        observed += 1
        if (
            description["status"] == "structurally_valid_nonempty"
            and description["coordinate_count"] == 1
        ):
            bounds = cast(list[float], description["coordinate_extrema_xy"])
            owner.valid += 1
            valid += 1
            owner.xy = bounds[0], bounds[2]
        else:
            owner.reasons = tuple(cast(list[str], description["reason_codes"])) or (
                str(description["status"]),
            )
    if observed != roles["point"]:
        raise ValueError("Native point payload denominator changed")
    yield {
        "kind": "profile",
        "native_profile_sha256": sha256(canonical_bytes(profile)).hexdigest(),
        "crs": crs,
        "geometry_role_rows": roles,
    }
    dispositions = Counter(dict.fromkeys(DISPOSITIONS, 0))
    cells: Counter[tuple[int, int]] = Counter()
    total = len(owners)
    selected = sum(owner.native_class == "Fornlämning" for owner in owners.values())
    for key in sorted(owners):
        owner = owners.pop(key)
        xy = owner.xy if owner.raw == owner.valid == 1 else None
        geographic = None
        cell = None
        if owner.native_class != "Fornlämning":
            disposition = "unselected_native_class"
        elif owner.raw == 0:
            disposition = "no_primary_point_occurrence"
        elif owner.raw > 1:
            disposition = "multiple_primary_point_occurrences"
        elif owner.valid != 1 or xy is None:
            disposition = "unsupported_sole_point"
        elif (geographic := projection.inverse_point(*xy)) is None:
            disposition = "unsupported_projection_or_location"
        else:
            disposition = "included"
            cell = grid_cell(*geographic)
            cells[cell] += 1
        dispositions[disposition] += 1
        yield {
            "kind": "uuid_disposition",
            "source_fid": owner.fid,
            "native_lamning_uuid": key,
            "native_class": _native(owner.native_class),
            "raw_point_occurrences": owner.raw,
            "valid_point_occurrences": owner.valid,
            "uncertainty_occurrences": owner.uncertainty,
            "point_refusal_reasons": list(owner.reasons),
            "disposition": disposition,
            "source_xy_metres": list(xy) if xy else None,
            "geographic_longitude_latitude": list(geographic) if geographic else None,
            "grid_cell": list(cell) if cell else None,
        }
    if (
        sum(dispositions.values()) != total
        or sum(cells.values()) != dispositions["included"]
    ):
        raise ValueError("Native UUID point-grid conservation failed")
    yield {
        "kind": "summary",
        "counts": {
            "source_uuids": total,
            "selected_class_uuids": selected,
            "included_uuids": dispositions["included"],
            "raw_point_occurrences": observed,
            "valid_point_occurrences": valid,
        },
        "dispositions": dict(dispositions),
        "geometry_role_rows": roles,
        "cell_count_total": sum(cells.values()),
        "cells": [
            {"west_longitude": west, "south_latitude": south, "uuid_count": count}
            for (west, south), count in sorted(
                cells.items(), key=lambda item: (item[0][1], item[0][0])
            )
        ],
    }
