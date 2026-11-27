"""Conservatively withhold closed intervals for trailing calendar markers."""

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.chronology_records import (
    _build_relative_period_row,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.refresh import (
    refresh_sead_repository_rows,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.temporal import (
    _interval_from_relative_age_label,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization.chronology_policy import (
    sead_claim_age_policy,
)


def _row(label: str, younger: int | None, older: int | None) -> dict[str, Any]:
    return _build_relative_period_row(
        {"relative_date_id": 47981, "relative_age_id": 1027},
        site_id=4570,
        relative_age={
            "label": label,
            "cal_age_younger": younger,
            "cal_age_older": older,
        },
        method={},
        uncertainty={"label": "From"},
        relation_identity={},
    )


def test_retained_source_shaped_open_relative_period_keeps_context_without_closed_point() -> (
    None
):
    source = {"label": "CAL_1175_AD-", "cal_age_younger": None, "cal_age_older": 775}
    before = deepcopy(source)
    row = _build_relative_period_row(
        {"relative_date_id": 47981, "relative_age_id": 1027},
        site_id=4570,
        relative_age=source,
        method={},
        uncertainty={"label": "From"},
        relation_identity={},
    )
    assert source == before
    assert (
        row["relative_age_label"] == "CAL_1175_AD-"
        and row["uncertainty_label"] == "From"
    )
    assert (row["time_start_bp"], row["time_end_bp"]) == (None, None)
    assert row["interval_source"] == "unresolved"
    assert (
        sead_claim_age_policy("relative_period", row)["comparability_status"]
        == "context_only"
    )


@pytest.mark.parametrize("label", ["CAL_1175_AD-", "CAL_500_BC-"])
def test_open_label_does_not_fabricate_finite_fallback(label: str) -> None:
    assert _interval_from_relative_age_label(label) is None


def test_refresh_does_not_revive_persisted_open_point_or_fallback() -> None:
    original = _row("CAL_1175_AD-", None, 775)
    original["time_start_bp"] = 775
    original["time_end_bp"] = 775
    site = {
        "site_id": 4570,
        "relative_period_rows": [original],
        "dating_range_rows": [],
        "bibliography_rows": [],
    }
    refresh_sead_repository_rows([site])
    assert (original["time_start_bp"], original["time_end_bp"]) == (None, None)
    assert (
        site["contextual_time_start_bp"] is None
        and site["contextual_time_end_bp"] is None
    )
    assert (
        original["relative_age_label"] == "CAL_1175_AD-"
        and original["uncertainty_label"] == "From"
    )
    assert original["interval_source"] == "unresolved"
    refresh_sead_repository_rows([site])
    assert (original["time_start_bp"], original["time_end_bp"]) == (None, None)


def test_closed_or_ambiguous_labels_and_other_numeric_rows_keep_existing_semantics() -> (
    None
):
    assert (
        _row("CAL_1200-1250_AD", 700, 750)["time_start_bp"],
        _row("CAL_1200-1250_AD", 700, 750)["time_end_bp"],
    ) == (700, 750)
    assert (
        _row("CAL_1950_AD", 0, 0)["time_start_bp"],
        _row("CAL_1950_AD", 0, 0)["time_end_bp"],
    ) == (0, 0)
    assert (
        _row("CAL_-1225_AD", 725, None)["time_start_bp"],
        _row("CAL_-1225_AD", 725, None)["time_end_bp"],
    ) == (725, 725)
    open_row = _row("CAL_1175_AD-", None, 775)
    site = {
        "site_id": 4570,
        "relative_period_rows": [open_row],
        "dating_range_rows": [
            {"low_value": 500, "high_value": 600, "age_type": "cal BP"}
        ],
        "bibliography_rows": [],
    }
    refresh_sead_repository_rows([site])
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (500, 600)


def test_overlay_refuses_unversioned_interval_source_change() -> None:
    from bijux_pollenomics.collection.sources.sead.evidence.chronology_overlay import (
        reconcile_chronology_rows,
    )

    old: dict[str, Any] = {
        "chronology_claim_id": "fixture:relative",
        "source_age_value": {
            "relative_age_label": "CAL_1175_AD-",
            "interval_source": "relative_age_bounds",
            "time_start_bp": 775,
            "time_end_bp": 775,
        },
        "original_interval_orientation": "point",
    }
    corrected = deepcopy(old)
    corrected["source_age_value"].update(
        interval_source="unresolved", time_start_bp=None, time_end_bp=None
    )
    corrected["original_interval_orientation"] = "unavailable"
    with pytest.raises(ValueError, match="nonderived fields differ"):
        reconcile_chronology_rows([old], [corrected], expected_count=1)


def test_conflicting_closed_bounds_with_trailing_marker_are_withheld() -> None:
    row = _row("CAL_1175-1200_AD-", 750, 775)
    assert (row["time_start_bp"], row["time_end_bp"]) == (None, None)
    assert row["interval_source"] == "unresolved"
    assert row["relative_age_label"] == "CAL_1175-1200_AD-"


def test_retained_relative_age_witness_remains_open_context() -> None:
    import hashlib
    import json

    from bijux_pollenomics.core.repository import repository_data_root

    root = (
        repository_data_root(__file__)
        / "sead/raw/acquisitions/sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac/payloads"
    )
    pins = {
        "tbl_relative_ages": "c5346bc1b091d2a738458e5df6d131a52306e55749034a673b6d1ecc4a6bf327",
        "tbl_relative_dates": "d0f404fee3b0e125c1b7584a901ce4be74d2f4137dc4ac1ec8a3baff29d857eb",
        "tbl_dating_uncertainty": "c26d76957028ac747fa26b77c0af6d038cbda10ed08599430f1f0f1a97d33503",
    }
    tables = {}
    for name, pin in pins.items():
        raw = (root / f"{name}.json").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == pin
        tables[name] = json.loads(raw)["rows"]
    age = next(r for r in tables["tbl_relative_ages"] if r["relative_age_id"] == 1027)
    date = next(
        r for r in tables["tbl_relative_dates"] if r["relative_date_id"] == 47981
    )
    uncertainty = next(
        r for r in tables["tbl_dating_uncertainty"] if r["dating_uncertainty_id"] == 4
    )
    assert date["relative_age_id"] == 1027 and date["dating_uncertainty_id"] == 4
    assert age["relative_age_name"] == "CAL_1175_AD-"
    assert (age["cal_age_younger"], age["cal_age_older"]) == (None, 775.0)
    row = _build_relative_period_row(
        date,
        site_id=4570,
        relative_age={
            "label": age["relative_age_name"],
            "cal_age_younger": age["cal_age_younger"],
            "cal_age_older": age["cal_age_older"],
        },
        method={},
        uncertainty={
            "label": uncertainty["uncertainty"],
            "description": uncertainty["description"],
        },
        relation_identity={},
    )
    assert row["uncertainty_label"] == "From"
    assert row["interval_source"] == "unresolved"
    assert (row["time_start_bp"], row["time_end_bp"]) == (None, None)
    assert (
        sead_claim_age_policy("relative_period", row)["comparability_status"]
        == "context_only"
    )


def test_retained_site_inventory_links_relative_date_to_site() -> None:
    import hashlib
    import json

    from bijux_pollenomics.core.repository import repository_data_root

    path = repository_data_root(__file__) / "sead/raw/nordic_sites.json"
    body = path.read_bytes()
    assert (
        hashlib.sha256(body).hexdigest()
        == "d864d2636763c76c8ffe51983a9e5c6f8d517a0aae33ea640635bd911f7960a6"
    )
    site = next(row for row in json.loads(body)["rows"] if row["site_id"] == 4570)
    period = next(
        row for row in site["relative_period_rows"] if row["relative_date_id"] == 47981
    )
    assert period["relative_age_label"] == "CAL_1175_AD-"
    assert period["uncertainty_label"] == "From"
