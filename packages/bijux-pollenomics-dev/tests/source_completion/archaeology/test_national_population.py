"""National source-accounting controls with duplicates, missingness and orphan rows."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sqlite3
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    GEOMETRY_TYPES,
    SOURCE_COLUMNS,
)
from bijux_pollenomics.collection.sources.raa.materialization.ownership import (
    iter_audit_documents,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    quote_identifier,
)
from bijux_pollenomics_dev.source_completion.archaeology.national_population import (
    historical_comparison,
    summarize,
    verify_sql,
)

UUID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def connection(tmp_path: Path) -> Any:
    c = sqlite3.connect(tmp_path / "native.gpkg")
    c.row_factory = sqlite3.Row
    for table, columns in SOURCE_COLUMNS.items():
        fields = []
        for name in columns:
            kind = (
                "INTEGER PRIMARY KEY"
                if name == "fid"
                else "BLOB"
                if name == "geometri"
                else "INTEGER"
                if name in {"id", "ingaendelamning_id", "antal"}
                else "TEXT"
            )
            fields.append(quote_identifier(name) + " " + kind)
        c.execute(f"CREATE TABLE {quote_identifier(table)}({','.join(fields)})")
    c.execute("PRAGMA application_id=1196444487")
    c.execute("PRAGMA user_version=10400")
    c.execute(
        "CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER)"
    )
    c.execute(
        "CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER,z INTEGER,m INTEGER)"
    )
    c.execute(
        "CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER,organization TEXT,organization_coordsys_id INTEGER)"
    )
    c.execute("INSERT INTO gpkg_spatial_ref_sys VALUES(3006,'EPSG',3006)")
    for table in SOURCE_COLUMNS:
        c.execute(
            "INSERT INTO gpkg_contents VALUES(?,?,?)",
            (
                table,
                "features" if table in GEOMETRY_TYPES else "attributes",
                3006 if table in GEOMETRY_TYPES else 0,
            ),
        )
    for table, kind in GEOMETRY_TYPES.items():
        c.execute(
            "INSERT INTO gpkg_geometry_columns VALUES(?,'geometri',?,3006,0,0)",
            (table, kind),
        )
    c.executemany(
        "INSERT INTO lamning(fid,uuid,antikvariskbedomning,skadestatus) VALUES(?,?,?,?)",
        [
            (1, UUID, "Fornlämning", None),
            (2, UUID, "Möjlig fornlämning", ""),
            (3, None, None, ""),
        ],
    )
    c.executemany(
        "INSERT INTO ingaendelamning(fid,id,lamning_uuid,antal) VALUES(?,?,?,?)",
        [(1, 9, UUID, 0), (2, 9, UUID, None)],
    )
    c.execute(
        "INSERT INTO egenskap(fid,ingaendelamning_id,typ,varde) VALUES(1,9,'Datering','Järnålder')"
    )
    c.executemany(
        "INSERT INTO point(fid,lamning_uuid) VALUES(?,?)",
        [(1, UUID), (2, "00000000-0000-0000-0000-000000000002")],
    )
    yield c
    c.close()


def test_national_native_populations_preserve_duplicates_orphans_and_nulls(
    connection: sqlite3.Connection,
) -> None:
    report = summarize(iter_audit_documents(connection))
    verify_sql(connection, report)
    summary = report["native_ownership_summary"]
    assert isinstance(summary, dict)
    assert summary["duplicate_native_uuid_values"] == 1
    assert summary["unique_valid_native_uuid_values"] == 1
    assert summary["duplicate_native_nested_ids"] == 1
    tables = summary["tables"]
    assert isinstance(tables, dict)
    assert tables["point"]["owner_status_counts"] == {
        "ambiguous_owner": 1,
        "orphan_owner": 1,
    }
    assert tables["lamning"]["owner_status_counts"] == {
        "ambiguous_owner": 2,
        "invalid_or_missing_native_uuid": 1,
    }
    assert tables["egenskap"]["owner_status_counts"] == {"ambiguous_nested_owner": 1}
    assert tables["lamning"]["source_cells"]["skadestatus"] == {
        "null": 1,
        "non_null": 2,
        "empty_text": 2,
    }
    assert tables["ingaendelamning"]["source_cells"]["antal"]["numeric_zero"] == 1
    assert summary["geometry_header_status_counts"] == {"source_null": 2}
    assert summary["boundary"]["chronology_admission"] is False


def test_sql_oracle_detects_changed_population_and_category(
    connection: sqlite3.Connection,
) -> None:
    report = summarize(iter_audit_documents(connection))
    connection.execute(
        "UPDATE lamning SET antikvariskbedomning='different' WHERE fid=1"
    )
    with pytest.raises(ValueError, match="categories differ"):
        verify_sql(connection, report)
    connection.execute("INSERT INTO point(fid) VALUES(3)")
    with pytest.raises(ValueError, match="population differs"):
        verify_sql(connection, report)


def test_sql_oracle_detects_missing_to_empty_conversion(
    connection: sqlite3.Connection,
) -> None:
    report = summarize(iter_audit_documents(connection))
    connection.execute("UPDATE lamning SET skadestatus='' WHERE fid=1")
    with pytest.raises(ValueError, match="null/zero/empty counts differ"):
        verify_sql(connection, report)


def test_historical_aggregate_difference_never_becomes_record_equivalence(
    connection: sqlite3.Connection,
) -> None:
    report = summarize(iter_audit_documents(connection))
    historical = {
        "counts": {
            "all_published_sites": 3,
            "fornlamning": 0,
            "fornlamning_or_possible": 4,
        }
    }
    compared = historical_comparison(report, historical)
    assert compared["aggregate_counts"] == {
        "all_published_sites": {
            "native_source_rows": 3,
            "historical_wfs_declared_hits": 3,
            "difference_native_minus_historical": 0,
        },
        "fornlamning": {
            "native_source_rows": 1,
            "historical_wfs_declared_hits": 0,
            "difference_native_minus_historical": 1,
        },
        "fornlamning_or_possible": {
            "native_source_rows": 2,
            "historical_wfs_declared_hits": 4,
            "difference_native_minus_historical": -2,
        },
    }
    assert compared["population_equivalence"] is False
    assert compared["geometry_equivalence"] is False
    assert compared["individual_additions_or_removals"] is None
    bad = deepcopy(historical)
    bad["counts"]["all_published_sites"] = True
    with pytest.raises(ValueError, match="declared nonnegative integer"):
        historical_comparison(report, bad)


def test_missing_terminal_summary_refuses() -> None:
    with pytest.raises(ValueError, match="summary absent"):
        summarize([])
