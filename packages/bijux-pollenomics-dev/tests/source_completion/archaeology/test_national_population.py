"""National source-accounting controls with duplicates, missingness and orphan rows."""

from __future__ import annotations

from copy import deepcopy
import sqlite3

import pytest

from bijux_pollenomics.collection.sources.raa.materialization.ownership import (
    iter_audit_documents,
)
from bijux_pollenomics_dev.source_completion.archaeology.national_population import (
    historical_comparison,
    summarize,
    verify_sql,
)


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
