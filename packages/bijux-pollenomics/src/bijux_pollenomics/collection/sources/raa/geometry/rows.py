"""Stream every base geometry occurrence with explicit source-owned status."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from hashlib import sha256
import math
import sqlite3
from typing import Any, cast

from ..materialization.contracts import GEOMETRY_TYPES
from ..materialization.reading import quote_identifier, source_profile
from .binary import describe_geometry
from .crs import inspect_crs
from .models import BOUNDARY


def _native(value: object) -> object:
    if isinstance(value, bytes):
        return {
            "sqlite_storage_type": "blob",
            "sha256": sha256(value).hexdigest(),
            "byte_count": len(value),
        }
    if isinstance(value, float) and not math.isfinite(value):
        return {"sqlite_storage_type": "real", "float_hex": value.hex()}
    return value


def iter_geometry_documents(
    connection: sqlite3.Connection,
) -> Iterator[dict[str, object]]:
    """Decode base tables only; joined views never multiply the denominator."""
    profile = cast(dict[str, Any], source_profile(connection))
    crs = inspect_crs(profile)
    yield {
        "kind": "source_profile",
        "profile": profile,
        "crs": crs,
        "boundary": BOUNDARY,
    }
    totals: dict[str, object] = {}
    all_statuses: Counter[str] = Counter()
    total = 0
    for table, geometry_type in GEOMETRY_TYPES.items():
        count = 0
        statuses: Counter[str] = Counter()
        reasons: Counter[str] = Counter()
        for row in connection.execute(
            f"SELECT * FROM {quote_identifier(table)} ORDER BY fid"
        ):
            source = dict(row)
            fid = source["fid"]
            if type(fid) is not int:
                raise ValueError("RAÄ geometry occurrence requires native integer fid")
            description = describe_geometry(
                source.pop("geometri"), geometry_type=geometry_type
            )
            status = str(description["status"])
            statuses[status] += 1
            reasons.update(cast(list[str], description["reason_codes"]))
            count += 1
            yield {
                "kind": "geometry_occurrence",
                "table": table,
                "geometry_column": "geometri",
                "fid": fid,
                "source_fields": {
                    name: _native(value) for name, value in source.items()
                },
                "geometry": description,
                "crs_status": crs["status"],
                "crs_reason_codes": crs["reason_codes"],
                "scientific_admission": False,
            }
        if count != profile["tables"][table]["row_count"]:
            raise ValueError("RAÄ geometry table row denominator changed")
        totals[table] = {
            "source_rows": count,
            "status_counts": dict(sorted(statuses.items())),
            "reason_counts": dict(sorted(reasons.items())),
        }
        total += count
        all_statuses.update(statuses)
    yield {
        "kind": "summary",
        "geometry_occurrences": total,
        "tables": totals,
        "status_counts": dict(sorted(all_statuses.items())),
        "crs_status": crs["status"],
        "crs_reason_codes": crs["reason_codes"],
        "boundary": BOUNDARY,
    }
