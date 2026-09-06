"""Tests for exact cattle archive-to-supplement reconciliation."""

from __future__ import annotations

from collections import Counter

import pytest
from bijux_pollenomics.adna.projects.sample_master.tables.fertile_crescent_cattle import (
    FERTILE_CRESCENT_CATTLE_SUPPLEMENT_SHA256,
    _reconcile_fertile_crescent_cattle_panel,
)

from .support import governed_inputs

pytestmark = pytest.mark.generated_artifacts


def test_reconciliation_closes_all_archive_and_supplement_identities() -> None:
    archive_text, supplement_digest = governed_inputs()
    rows = _reconcile_fertile_crescent_cattle_panel(
        archive_text=archive_text,
        supplement_sha256=supplement_digest,
    )

    assert len(rows) == 78
    assert Counter(row.reconciliation_status for row in rows) == {
        "archive_supplement_literal_join": 60,
        "archive_supplement_explicit_alias_join": 5,
        "archive_only": 12,
        "supplement_only": 1,
    }
    assert len({row.locality_text for row in rows if row.sample_id}) == 40
    assert Counter(row.source_native_scientific_name for row in rows) == {
        "Bos taurus": 68,
        "Bos primigenius": 5,
        "Bos indicus": 3,
        "Bos gaurus": 1,
        "": 1,
    }


def test_aliases_and_coordinate_refusals_are_explicit() -> None:
    archive_text, supplement_digest = governed_inputs()
    rows = _reconcile_fertile_crescent_cattle_panel(
        archive_text=archive_text,
        supplement_sha256=supplement_digest,
    )
    by_sample = {row.sample_id: row for row in rows if row.sample_id}

    assert {
        sample_id: by_sample[sample_id].archive_native_sample_id
        for sample_id in ("Bes1", "Bes2", "Gyu2", "Men2", "Sub1")
    } == {
        "Bes1": "SAMEA5577351",
        "Bes2": "SAMEA5577352",
        "Gyu2": "SAMEA5577362",
        "Men2": "SAMEA5577377",
        "Sub1": "SAMEA5577393",
    }
    dariali = [row for row in rows if row.sample_id.startswith("Kaz")]
    assert len(dariali) == 5
    assert all(
        row.coordinate_admission_status == "withheld_utm_datum_unspecified"
        and row.source_coordinate_text == "UTM 38N 469400, 4731800; datum not stated"
        for row in dariali
    )


def test_source_digest_drift_fails_closed() -> None:
    archive_text, _ = governed_inputs()

    with pytest.raises(ValueError, match="archive sha256 drift"):
        _reconcile_fertile_crescent_cattle_panel(
            archive_text=f"{archive_text}\n",
            supplement_sha256=FERTILE_CRESCENT_CATTLE_SUPPLEMENT_SHA256,
        )
    with pytest.raises(ValueError, match="supplement sha256 drift"):
        _reconcile_fertile_crescent_cattle_panel(
            archive_text=archive_text,
            supplement_sha256="0" * 64,
        )
