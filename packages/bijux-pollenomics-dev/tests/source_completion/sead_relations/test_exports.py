"""Keep source capture export separate from scientific event approval."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead_relations.workflow import (
    source_relation_export,
    write_source_relations,
)


def _inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    ledger: dict[str, Any] = {
        "source_run_id": "capture",
        "build_id": "build",
        "scope_id": "scope",
        "acquisition_manifest_sha256": "a" * 64,
        "acquisition_bundle_sha256": "bundle",
        "source_key_set_sha256": "keys",
        "site_identity_sha256": "identities",
        "site_country_binding_sha256": "bindings",
        "table_count": 1,
        "source_row_count": 0,
        "distinct_primary_key_count": 0,
        "empty_table_count": 1,
        "country_binding_accountability": {"assigned_site_count": 0},
        "tables": [
            {
                "table": "tbl_empty",
                "primary_key": "id",
                "row_count": 0,
                "distinct_primary_key_count": 0,
                "duplicate_primary_key_count": 0,
                "minimum_primary_key": None,
                "maximum_primary_key": None,
                "key_range_count": 0,
                "payload": {"sha256": "p"},
                "receipt": {"sha256": "r", "status": "complete"},
            }
        ],
    }
    admission = {
        "acquisition_bundle_sha256": "bundle",
        "release_status": "refused",
        "downstream_statuses": {"propagation": "refused"},
    }
    return ledger, admission


def test_capture_export_retains_empty_tables_and_refused_science() -> None:
    ledger, admission = _inputs()
    before = deepcopy(ledger)
    summary, rows = source_relation_export(ledger, admission)
    assert ledger == before
    assert summary["receipt_status_counts"] == {"complete": 1}
    assert summary["empty_table_count"] == 1
    assert summary["admission_release_status"] == "refused"
    assert summary["downstream_statuses"] == {"propagation": "refused"}
    assert rows[0]["minimum_primary_key"] is None
    assert rows[0]["maximum_primary_key"] is None
    assert rows[0]["row_count"] == 0
    assert rows[0]["receipt_sha256"] == "r"


@pytest.mark.parametrize(
    "field,value",
    [
        ("table_count", 2),
        ("source_row_count", 1),
        ("acquisition_bundle_sha256", "other"),
    ],
)
def test_inconsistent_source_export_is_refused(field: str, value: int | str) -> None:
    ledger, admission = _inputs()
    ledger[field] = value
    with pytest.raises(ValueError, match="(reconcile|diverge)"):
        source_relation_export(ledger, admission)


def test_existing_destination_is_not_overwritten(tmp_path: Path) -> None:
    retained = tmp_path / "retained"
    retained.mkdir()
    (retained / "summary.json").write_text("original source result")
    with pytest.raises(ValueError, match="already exists"):
        write_source_relations(tmp_path / "absent-data", retained)
    assert (retained / "summary.json").read_text() == "original source result"


def test_writer_uses_lf_and_retains_export_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import hashlib
    import json

    from bijux_pollenomics_dev.source_completion.sead_relations import workflow

    ledger, admission = _inputs()
    summary, rows = source_relation_export(ledger, admission)
    monkeypatch.setattr(
        workflow, "reconcile_source_relations", lambda _: (summary, rows)
    )
    destination = tmp_path / "export"
    workflow.write_source_relations(tmp_path, destination)
    raw = (destination / "tables.csv").read_bytes()
    assert b"\r" not in raw
    assert len(raw.splitlines()) == 2
    assert (
        json.loads((destination / "summary.json").read_text())["tables_csv_sha256"]
        == hashlib.sha256(raw).hexdigest()
    )
