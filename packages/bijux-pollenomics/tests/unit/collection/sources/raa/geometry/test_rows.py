"""Native occurrence denominators retain malformed rows and source attributes."""

import json
from pathlib import Path
import sqlite3
from typing import cast

from bijux_pollenomics.collection.sources.raa.geometry.rows import (
    iter_geometry_documents,
)
from bijux_pollenomics.collection.sources.raa.materialization.ownership import (
    canonical_bytes,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    read_only_database,
)

from .support import A, add_geometry, database, gpkg, identity, point, polygon


def test_real_sqlite_null_infinity_and_zero_accounting(tmp_path: Path) -> None:
    source = database(tmp_path)
    for fid, value in enumerate(
        (None, float("inf"), float("nan"), gpkg(point()), "0"), start=1
    ):
        add_geometry(source, "point", value, fid=fid)
    add_geometry(source, "polygon", gpkg(polygon([]), empty=True))
    pin, size = identity(source)
    with read_only_database(
        source, expected_sha256=pin, expected_byte_count=size
    ) as con:
        records = list(iter_geometry_documents(con))
    assert all(json.loads(canonical_bytes(row)) == row for row in records)
    summary = records[-1]
    assert summary["geometry_occurrences"] == 6
    assert summary["status_counts"] == {
        "source_null": 2,
        "invalid": 2,
        "structurally_valid_nonempty": 1,
        "structurally_valid_empty": 1,
    }
    occurrences = [r for r in records if r["kind"] == "geometry_occurrence"]
    assert all(
        cast(dict[str, object], r["source_fields"])["lamning_uuid"] == A
        for r in occurrences
    )
    assert cast(dict[str, object], occurrences[1]["geometry"])["source_value"] == {
        "float_hex": "inf"
    }
    assert all(r["scientific_admission"] is False for r in occurrences)


def test_crs_refusal_does_not_erase_valid_structures(tmp_path: Path) -> None:
    source = database(tmp_path)
    add_geometry(source, "point", gpkg(point()))
    with sqlite3.connect(source) as con:
        con.execute("UPDATE gpkg_spatial_ref_sys SET definition='not WKT'")
    pin, size = identity(source)
    with read_only_database(
        source, expected_sha256=pin, expected_byte_count=size
    ) as con:
        records = list(iter_geometry_documents(con))
    assert records[-1]["crs_status"] == "refused"
    assert records[-1]["status_counts"] == {"structurally_valid_nonempty": 1}
