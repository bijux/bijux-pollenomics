"""Keep source capture export separate from scientific event approval."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.sead_relations.workflow import (
    source_relation_export,
    write_source_relations,
)


def _inputs() -> tuple[dict[str, object], dict[str, object]]:
    ledger: dict[str, object] = {
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
    admission: dict[str, object] = {
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
def test_inconsistent_source_export_is_refused(field: str, value: object) -> None:
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


def test_failed_summary_write_does_not_expose_partial_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.source_completion.sead_relations import workflow

    ledger, admission = _inputs()
    summary, rows = source_relation_export(ledger, admission)
    monkeypatch.setattr(
        workflow, "reconcile_source_relations", lambda _: (summary, rows)
    )
    original = Path.write_text

    def fail_summary(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path.name == "summary.json":
            raise OSError("summary storage unavailable")
        return original(path, data, encoding=encoding, errors=errors, newline=newline)

    monkeypatch.setattr(Path, "write_text", fail_summary)
    destination = tmp_path / "export"
    with pytest.raises(OSError, match="summary storage unavailable"):
        workflow.write_source_relations(tmp_path, destination)
    assert not destination.exists()


def test_source_replay_cannot_adopt_replaced_output_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.source_completion.sead_relations import workflow

    ledger, admission = _inputs()
    summary, rows = source_relation_export(ledger, admission)
    parent = tmp_path / "reports"
    parent.mkdir()
    displaced = tmp_path / "displaced-reports"

    def replace_parent(_: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
        parent.rename(displaced)
        parent.mkdir()
        (parent / "foreign.txt").write_text("foreign report owner")
        return summary, rows

    monkeypatch.setattr(workflow, "reconcile_source_relations", replace_parent)
    with pytest.raises(ValueError):
        workflow.write_source_relations(tmp_path, parent / "export")
    assert (parent / "foreign.txt").read_text() == "foreign report owner"
    assert not (parent / "export").exists()
    assert not (displaced / "export").exists()


def test_destination_created_after_absence_check_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.source_completion.sead_relations import workflow

    ledger, admission = _inputs()
    summary, rows = source_relation_export(ledger, admission)
    monkeypatch.setattr(
        workflow, "reconcile_source_relations", lambda _: (summary, rows)
    )
    destination = tmp_path / "export"
    original = Path.is_symlink
    occupied = False

    def occupy_after_check(path: Path) -> bool:
        nonlocal occupied
        if path == destination and not occupied:
            occupied = True
            destination.mkdir()
            (destination / "foreign.txt").write_text("foreign completed export")
            return False
        return original(path)

    monkeypatch.setattr(Path, "is_symlink", occupy_after_check)
    with pytest.raises((ValueError, FileExistsError)):
        workflow.write_source_relations(tmp_path, destination)
    assert occupied
    assert (destination / "foreign.txt").read_text() == "foreign completed export"
    assert {path.name for path in destination.iterdir()} == {"foreign.txt"}
