"""One-sided source dates cannot establish a closed site interval."""

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
from bijux_pollenomics.collection.sources.sead.evidence.normalization.chronology_claims import (
    normalize_sead_chronology_claims,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization.chronology_policy import (
    sead_claim_age_policy,
)
from tests.unit.collection.sources.sead.evidence.test_native_rows import _tables


def _inventory(
    label: str | None, route: str, *, mixed: bool = False, error: int | None = None
) -> dict[str, Any]:
    tables = _tables()
    for table in (
        "tbl_relative_dates",
        "tbl_analysis_entity_ages",
        "tbl_analysis_dating_ranges",
        "tbl_dendro_dates",
    ):
        tables[table] = []
    first = tables["tbl_geochronology"][0]
    first.update(
        age=1200, error_older=error, error_younger=error, dating_uncertainty_id=3
    )
    tables["tbl_dating_uncertainty"] = [
        {"dating_uncertainty_id": 3, "uncertainty": label, "description": "fixture"}
    ]
    if mixed:
        second = deepcopy(first)
        second.update(
            geochron_id=98,
            age=1400,
            error_younger=20,
            error_older=10,
            dating_uncertainty_id=None,
        )
        tables["tbl_geochronology"].append(second)
    sites = deepcopy(tables["tbl_sites"])
    before = deepcopy(tables)
    if route == "api":

        def fetch(
            url: str, *, params: object, headers: dict[str, str], timeout: float
        ) -> object:
            del params, timeout
            table = url.rsplit("/", 1)[-1]
            return (
                deepcopy(tables.get(table, []))
                if int(headers["Range"].split("-", 1)[0]) == 0
                else []
            )

        populate_sead_site_inventory_fields(sites, fetch_json_fn=fetch)
    else:
        populate_sead_site_inventory_from_reader(
            sites, reader=MappingSeadTableReader(tables)
        )
    assert tables == before
    return sites[0]


@pytest.mark.parametrize("route", ["api", "mapping"])
@pytest.mark.parametrize("label", [">", " > "])
def test_open_ended_geochronology_stays_context_without_numeric_bounds(
    route: str, label: str
) -> None:
    site = _inventory(label, route)
    row = site["geochronology_rows"][0]
    assert row["age"] == 1200 and row["uncertainty_label"] == ">"
    assert row["error_older"] is None and row["error_younger"] is None
    assert site["geochronology_count"] == 1
    assert (row["time_start_bp"], row["time_end_bp"]) == (None, None)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (None, None)
    assert (
        sead_claim_age_policy("geochronology", row)["comparability_status"]
        == "context_only"
    )
    claim = normalize_sead_chronology_claims(
        [site], provenance_record_id="fixture", build_id="fixture"
    )[0]
    assert claim["comparability_status"] == "context_only"
    assert claim["chronology_eligibility"] == "refused"
    assert claim["younger_bp"] is None and claim["older_bp"] is None
    assert claim["source_age_value"]["uncertainty_label"] == ">"
    row.pop("dating_uncertainty_id", None)
    refresh_sead_repository_rows([site])
    assert (row["time_start_bp"], row["time_end_bp"]) == (None, None)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (None, None)


@pytest.mark.parametrize("route", ["api", "mapping"])
def test_mixed_site_retains_other_finite_interval(route: str) -> None:
    site = _inventory(">", route, mixed=True)
    assert site["geochronology_count"] == 2
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (1380, 1410)
    refresh_sead_repository_rows([site])
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (1380, 1410)


@pytest.mark.parametrize("route", ["api", "mapping"])
@pytest.mark.parametrize("error", [None, 0])
def test_unqualified_finite_point_remains_a_point(
    route: str, error: int | None
) -> None:
    site = _inventory(None, route, error=error)
    row = site["geochronology_rows"][0]
    assert (row["time_start_bp"], row["time_end_bp"]) == (1200, 1200)
    row["error_older"] = 0
    row["error_younger"] = 0
    refresh_sead_repository_rows([site])
    assert (row["time_start_bp"], row["time_end_bp"]) == (1200, 1200)


def test_open_qualifier_remains_open_even_with_recorded_errors() -> None:
    site = _inventory(">", "mapping", error=50)
    row = site["geochronology_rows"][0]
    assert (row["error_younger"], row["error_older"]) == (50, 50)
    assert (row["time_start_bp"], row["time_end_bp"]) == (None, None)
