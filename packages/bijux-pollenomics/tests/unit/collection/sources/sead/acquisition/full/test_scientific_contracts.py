from __future__ import annotations

from datetime import datetime

import pytest
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    NORDIC_COUNTRY_CODES,
    reconcile_sead_countries,
    reconcile_sead_join,
)
from bijux_pollenomics.collection.sources.sead.acquisition.full.serialization import (
    utc_text,
)


def test_country_reconciliation_has_fixed_four_country_denominator() -> None:
    result = reconcile_sead_countries(
        [{"site_id": code} for code in ("1", "2", "3", "4", "5")],
        country_by_site_id={"1": "SE", "2": "DK", "3": "NO", "4": "FI"},
    )
    assert NORDIC_COUNTRY_CODES == ("SE", "DK", "NO", "FI", "UNASSIGNED")
    assert result["counts"] == {"SE": 1, "DK": 1, "NO": 1, "FI": 1, "UNASSIGNED": 1}
    assert result["assigned_count"] == 4
    assert result["unassigned_count"] == 1
    assert result["reconciles"] is True


def test_null_join_keys_are_counted_as_loss() -> None:
    result = reconcile_sead_join(
        edge="sites_to_samples",
        parent_rows=[{"site_id": 1}],
        child_rows=[{"sample_id": 2, "site_id": None}],
        parent_key="site_id",
        child_key="sample_id",
        child_foreign_key="site_id",
    )
    assert result["matched_child_count"] == 0
    assert result["unexplained_loss_count"] == 1
    assert result["status"] == "failed"


def test_naive_acquisition_timestamps_are_refused() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        utc_text(datetime(2026, 9, 5, 12, 0))
