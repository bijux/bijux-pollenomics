from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.sead.collection.archive import (
    write_sead_site_archive,
)
from bijux_pollenomics.collection.sources.sead.collection.repository import (
    attach_sead_country_decisions,
    build_repository_inventory_summary,
)
from bijux_pollenomics.collection.sources.sead.collection.validation import (
    validate_sead_rows,
)


def test_null_and_zero_identifiers_are_not_admitted() -> None:
    for site_id in (None, 0):
        with pytest.raises(ValueError, match="Invalid required SEAD tbl_sites.site_id"):
            validate_sead_rows("tbl_sites", [{"site_id": site_id}])


def test_country_assignment_requires_governed_nordic_identity() -> None:
    copied_files = {
        "country-decisions.json": json.dumps(
            {
                "decisions": [
                    {
                        "site_id": 1,
                        "governed_country_code": "UNASSIGNED",
                        "decision": {"decision_method": "boundary"},
                    }
                ]
            }
        ).encode()
    }
    with pytest.raises(ValueError, match="SEAD admitted site is not assigned"):
        attach_sead_country_decisions(copied_files, [{"site_id": 1}])


def test_temporal_inventory_keeps_unresolved_sites_explicit() -> None:
    summary = build_repository_inventory_summary(
        [{"site_id": 1, "time_start_bp": None, "time_end_bp": None}]
    )
    assert summary["numeric_interval_row_count"] == 0
    assert summary["unresolved_site_count"] == 1
    assert summary["site_inventory_only_row_count"] == 1
    assert summary["temporal_capture_posture"] == "site_inventory_only"


def test_archive_bytes_are_order_independent(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    rows: list[dict[str, object]] = [{"site_id": 2}, {"site_id": 1}]
    first_bytes = write_sead_site_archive(
        first,
        bbox=(4.0, 54.0, 35.0, 72.0),
        rows=rows,
        inventory_summary={"site_row_count": 2},
    ).read_bytes()
    second_bytes = write_sead_site_archive(
        second,
        bbox=(4.0, 54.0, 35.0, 72.0),
        rows=list(reversed(rows)),
        inventory_summary={"site_row_count": 2},
    ).read_bytes()
    assert first_bytes == second_bytes
