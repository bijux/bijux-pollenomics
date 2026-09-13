"""Source domains, counts and raw scalar/geometry counterexamples."""

import json
from pathlib import Path
import sqlite3

import pytest

from bijux_pollenomics.collection.sources.raa.materialization.ownership import (
    canonical_bytes,
    geometry_descriptor,
    iter_audit_documents,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    read_only_database,
)

from .conftest import A, blob, identity


def test_complete_source_domains_preserve_missing_zero_and_nested(
    database: Path,
) -> None:
    digest, size = identity(database)
    with read_only_database(
        database, expected_sha256=digest, expected_byte_count=size
    ) as con:
        docs = json.loads(canonical_bytes(list(iter_audit_documents(con))))
    rows = {
        (row["table"], row["fid"]): row for row in docs if row["kind"] == "source_row"
    }
    assert len(rows) == 16
    assert rows["lamning", 1]["source_values"]["lamningsnamn"] == "Å"
    assert rows["lamning", 2]["source_values"]["lamningsnamn"] == ""
    assert rows["ingaendelamning", 1]["source_values"]["antal"] == 0
    assert rows["ingaendelamning", 2]["source_values"]["antal"] == 2
    assert rows["egenskap", 2]["source_values"]["lamning_uuid"] is None
    owner = rows["egenskap", 2]["owner_relation"]
    assert owner["domain"] == "ingaendelamning" and owner["status"] == "linked"
    assert owner["lamning_lineage_via_nested_row"]["native_lamning_uuid"] == A
    assert rows["egenskap", 3]["owner_relation"]["status"] == "orphan_nested_owner"
    assert rows["egenskap", 4]["source_values"]["varde"] == "0"
    assert (
        rows["egenskap", 5]["owner_relation"]["status"] == "both_owner_domains_declared"
    )
    assert rows["linestring", 1]["owner_relation"]["status"] == "orphan_owner"
    assert (
        rows["lämningar_sverige_lägesosäkerhet", 2]["geometry_header_status"]
        == "source_null"
    )
    assert rows["point", 3]["geometry_header_status"] == "declared_crs_mismatch"
    assert rows["lamning", 1]["geometry_row_membership"] == {
        "point": 1,
        "polygon": 1,
        "lämningar_sverige_lägesosäkerhet": 1,
    }
    summary = docs[-1]
    assert summary["unique_valid_native_uuid_values"] == 3
    assert summary["tables"]["egenskap"]["source_rows"] == 5
    assert summary["tables"]["lämningar_sverige_lägesosäkerhet"]["source_cells"][
        "lagesosakerhet_i_meter"
    ] == {
        "non_null": 1,
        "numeric_zero": 1,
        "null": 1,
    }
    assert summary["boundary"]["geometry_validation"] == "not_evaluated"
    assert summary["boundary"]["scientific_admission"] is False


@pytest.mark.parametrize(
    "payload,status",
    [
        (b"", "unsupported_header"),
        (b"not geometry", "unsupported_header"),
        (b"GP\x00\x0f" + b"\x00" * 30, "unsupported_header"),
        (blob()[:9], "truncated_geometry_payload"),
        (blob(4326), "declared_crs_mismatch"),
        (blob(), "supported_header_only"),
        (b"GP\x00\x11" + blob()[4:], "supported_header_only"),
    ],
)
def test_header_is_separate_from_unperformed_wkb_validation(
    payload: bytes, status: str
) -> None:
    descriptor = geometry_descriptor(payload)
    assert descriptor["header_status"] == status
    assert descriptor["byte_count"] == len(payload)
    assert descriptor["geometry_validation"] == "not_evaluated"


@pytest.mark.parametrize(
    "statement",
    [
        "PRAGMA user_version=10300",
        "CREATE TABLE unknown_source (id INTEGER)",
        "ALTER TABLE lamning ADD COLUMN extra TEXT",
        "UPDATE gpkg_geometry_columns SET srs_id=4326 WHERE table_name='point'",
        "DELETE FROM gpkg_contents WHERE table_name='egenskap'",
    ],
)
def test_uninspected_profile_refuses(database: Path, statement: str) -> None:
    with sqlite3.connect(database) as con:
        con.execute(statement)
    digest, size = identity(database)
    with (
        read_only_database(
            database, expected_sha256=digest, expected_byte_count=size
        ) as con,
        pytest.raises(ValueError),
    ):
        list(iter_audit_documents(con))


def test_duplicate_owners_do_not_select_first(database: Path) -> None:
    with sqlite3.connect(database) as con:
        con.execute("UPDATE lamning SET uuid=? WHERE fid=2", (A,))
        con.execute("UPDATE ingaendelamning SET id=10 WHERE fid=2")
    digest, size = identity(database)
    with read_only_database(
        database, expected_sha256=digest, expected_byte_count=size
    ) as con:
        docs = json.loads(canonical_bytes(list(iter_audit_documents(con))))
    rows = {
        (row["table"], row["fid"]): row for row in docs if row["kind"] == "source_row"
    }
    assert rows["point", 1]["owner_relation"]["status"] == "ambiguous_owner"
    assert rows["egenskap", 2]["owner_relation"]["status"] == "ambiguous_nested_owner"
    assert docs[-1]["duplicate_native_uuid_values"] == 1
