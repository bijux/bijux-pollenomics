"""Strict repository interchange parser; the native HYDE 3.5 format is unverified."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from ..quarantine import IntakeRefusal
from .grid import GridSpec, finite_number
from .models import DeclaredGridLayer, VariableSpec
from .time import CalendarYear, TimeSupport


def _object(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise IntakeRefusal("hyde_interchange_fields_invalid", label)
    return value


def _optional_text(value: object, field: str) -> str | None:
    if value is None or (isinstance(value, str) and value.strip()):
        return value
    raise IntakeRefusal("hyde_metadata_text_invalid", field)


def _calendar(value: object) -> CalendarYear:
    payload = _object(value, {"year", "era"}, "calendar_year")
    return CalendarYear(**payload)


def load_declared_grid(
    path: Path, *, expected_sha256: str, maximum_bytes: int = 16_000_000
) -> DeclaredGridLayer:
    """Inspect an explicitly declared small interchange bound to an external digest.

    Native provider raster/NetCDF/ASCII conventions are deliberately not inferred.
    Neither local digest agreement nor a 3.5 release label confers source approval.
    """
    if (
        not isinstance(expected_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
    ):
        raise IntakeRefusal("hyde_expected_digest_invalid", repr(expected_sha256))
    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise IntakeRefusal("hyde_intake_limit_invalid", repr(maximum_bytes))
    if path.is_symlink() or not path.is_file():
        raise IntakeRefusal("hyde_local_asset_missing_or_symlink", str(path))
    with path.open("rb") as handle:
        content = handle.read(maximum_bytes + 1)
    if len(content) > maximum_bytes:
        raise IntakeRefusal("hyde_interchange_size_limit", str(len(content)))
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected_sha256:
        raise IntakeRefusal("hyde_interchange_digest_mismatch", str(path))
    try:
        payload = json.loads(content, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeDecodeError) as exc:
        raise IntakeRefusal("hyde_native_format_unverified", str(path)) from exc
    document = _object(
        payload,
        {
            "schema_version",
            "source",
            "grid",
            "time",
            "variable",
            "values",
            "land_fractions",
            "nodata_value",
        },
        "document",
    )
    if document["schema_version"] != "hyde-declared-grid.v1":
        raise IntakeRefusal(
            "hyde_native_format_unverified", str(document["schema_version"])
        )
    source = _object(
        document["source"],
        {"kind", "release_claim", "url", "citation", "license_claim"},
        "source",
    )
    grid = GridSpec(
        **_object(
            document["grid"],
            {
                "columns",
                "rows",
                "west",
                "south",
                "longitude_step",
                "latitude_step",
                "row_order",
                "crs",
            },
            "grid",
        )
    )
    time = _object(document["time"], {"start", "end", "kind", "convention"}, "time")
    variable = VariableSpec(
        **_object(
            document["variable"],
            {"source_label", "category_key", "scenario", "quantity", "units"},
            "variable",
        )
    )
    nodata = document["nodata_value"]
    if nodata is not None:
        nodata = finite_number(nodata, "nodata_value")
        if nodata >= 0:
            raise IntakeRefusal("hyde_nodata_overlaps_valid_domain", str(nodata))
    raw_values = _matrix(document["values"], grid, "values", allow_null=True)
    if variable.quantity == "population":
        for value in raw_values:
            if type(value) is int and float(value) != value:
                raise IntakeRefusal("hyde_population_precision_loss", str(value))
    land = _matrix(document["land_fractions"], grid, "land_fractions", allow_null=False)
    return DeclaredGridLayer(
        interchange_sha256=actual,
        source_kind=source["kind"],
        release_claim=source["release_claim"],
        source_url=_optional_text(source["url"], "source.url"),
        citation=_optional_text(source["citation"], "citation"),
        license_claim=_optional_text(source["license_claim"], "license_claim"),
        grid=grid,
        time=TimeSupport(
            _calendar(time["start"]),
            _calendar(time["end"]),
            time["kind"],
            time["convention"],
        ),
        variable=variable,
        values=tuple(
            None if value is None or value == nodata else float(value)
            for value in raw_values
        ),
        land_fractions=tuple(float(value) for value in land if value is not None),
        source_values=raw_values,
        nodata_value=nodata,
    )


def _matrix(
    value: object, grid: GridSpec, label: str, *, allow_null: bool
) -> tuple[int | float | None, ...]:
    if not isinstance(value, list) or len(value) != grid.rows:
        raise IntakeRefusal("hyde_grid_row_count_mismatch", label)
    result: list[int | float | None] = []
    for row in value:
        if not isinstance(row, list) or len(row) != grid.columns:
            raise IntakeRefusal("hyde_grid_column_count_mismatch", label)
        for item in row:
            if item is None and allow_null:
                result.append(None)
            else:
                finite_number(item, label)
                result.append(item)
    return tuple(result)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result
