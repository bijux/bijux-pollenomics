"""Open-ended source dates stay contextual through both catalogue readers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.sead import (
    populate_sead_site_inventory_fields,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.refresh import (
    refresh_sead_repository_rows,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.service import (
    populate_sead_site_inventory_from_reader,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.table_readers import (
    MappingSeadTableReader,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization.chronology_policy import (
    sead_claim_age_policy,
)
from tests.unit.collection.sources.sead.evidence.test_native_rows import _tables


def source_tables(
    label: str | None, *, dated: bool
) -> dict[str, list[dict[str, object]]]:
    tables = _tables()
    for name in (
        "tbl_relative_dates",
        "tbl_geochronology",
        "tbl_analysis_entity_ages",
        "tbl_analysis_dating_ranges",
    ):
        tables[name] = []
    tables["tbl_dating_uncertainty"] = [
        {
            "dating_uncertainty_id": 2,
            "uncertainty": label,
            "description": "Generated source qualifier",
        }
    ]
    tables["tbl_dendro_dates"][0].update(
        age_older=1754 if dated else None,
        age_younger=None,
        dating_uncertainty_id=2,
    )
    return tables


def enrich(
    tables: dict[str, list[dict[str, object]]], route: str
) -> tuple[dict[str, Any], dict[str, int | str]]:
    sites = deepcopy(tables["tbl_sites"])
    before = deepcopy(tables)
    calls: list[str] = []
    if route == "api":

        def fetch(
            url: str, *, params: object, headers: dict[str, str], timeout: float
        ) -> object:
            del params, timeout
            table = url.rsplit("/", 1)[-1]
            calls.append(table)
            start = int(headers["Range"].split("-", 1)[0])
            return deepcopy(tables.get(table, [])) if start == 0 else []

        summary = populate_sead_site_inventory_fields(sites, fetch_json_fn=fetch)
        assert "tbl_dating_uncertainty" in calls and "tbl_dendro_dates" in calls
    else:
        summary = populate_sead_site_inventory_from_reader(
            sites, reader=MappingSeadTableReader(tables)
        )
    assert tables == before
    site: dict[str, Any] = sites[0]
    row = site["dendro_date_rows"][0]
    assert (
        site["site_id"],
        row["sample_group_id"],
        row["physical_sample_id"],
        row["analysis_entity_id"],
        row["dataset_id"],
    ) == (1, 2, 3, 4, 5)
    assert row["age_older"] == tables["tbl_dendro_dates"][0]["age_older"]
    assert row["age_younger"] is None
    assert site["dendro_date_count"] == 1
    return site, summary


@pytest.mark.parametrize("route", ["api", "mapping"])
@pytest.mark.parametrize("label", ["From", "from"])
def test_open_ended_dendro_does_not_create_closed_numeric_envelope(
    route: str, label: str
) -> None:
    site, summary = enrich(source_tables(label, dated=True), route)
    row = site["dendro_date_rows"][0]
    assert row["uncertainty_label"] == label
    policy = sead_claim_age_policy("dendrochronology", row)
    assert policy["comparability_status"] == "context_only"
    assert policy["reason_codes"] == ("open_ended_dendro_from_uncertainty",)
    assert site["numeric_time_start_bp"] is None
    assert site["numeric_time_end_bp"] is None
    assert summary["numeric_interval_row_count"] == 0


@pytest.mark.parametrize("route", ["api", "mapping"])
@pytest.mark.parametrize("label", [None, "?", "Ca."])
def test_other_retained_qualifiers_keep_existing_finite_date_behavior(
    route: str, label: str | None
) -> None:
    site, summary = enrich(source_tables(label, dated=True), route)
    assert site["numeric_time_start_bp"] == site["numeric_time_end_bp"] == 196
    assert site["dendro_date_rows"][0]["uncertainty_label"] == (label or "")
    assert summary["numeric_interval_row_count"] == 1


@pytest.mark.parametrize("route", ["api", "mapping"])
@pytest.mark.parametrize("label", [None, "From"])
def test_missing_dates_stay_unavailable_with_source_record_retained(
    route: str, label: str | None
) -> None:
    site, summary = enrich(source_tables(label, dated=False), route)
    assert site["numeric_time_start_bp"] is None
    assert site["numeric_time_end_bp"] is None
    assert site["time_start_bp"] is None and site["time_end_bp"] is None
    assert summary["numeric_interval_row_count"] == 0


@pytest.mark.parametrize("label", ["From", "from", None, "?", "Ca."])
def test_refresh_preserves_dendro_site_admission_posture(label: str | None) -> None:
    site, _ = enrich(source_tables(label, dated=True), "mapping")
    row = deepcopy(site["dendro_date_rows"][0])
    expected = (None, None) if label in {"From", "from"} else (196, 196)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == expected
    refresh_sead_repository_rows([site])
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == expected
    assert site["dendro_date_rows"][0] == row


def test_refresh_retains_other_finite_dendro_interval() -> None:
    tables = source_tables("From", dated=True)
    finite = deepcopy(tables["tbl_dendro_dates"][0])
    finite.update(dendro_date_id=98, age_older=1700, dating_uncertainty_id=None)
    tables["tbl_dendro_dates"].append(finite)
    sites = deepcopy(tables["tbl_sites"])
    populate_sead_site_inventory_from_reader(
        sites, reader=MappingSeadTableReader(tables)
    )
    site = sites[0]
    assert site["dendro_date_count"] == 2
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (250, 250)
    refresh_sead_repository_rows(sites)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (250, 250)
