"""Unqualified entity ages stay source context in both inventory paths."""

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
from bijux_pollenomics.collection.sources.sead.evidence.normalization.site_temporal_semantics import (
    build_sead_temporal_semantics,
)
from tests.unit.collection.sources.sead.evidence.test_native_rows import _tables


def _inventory(
    route: str, *, mixed: bool = False, zero: bool = False
) -> dict[str, Any]:
    tables = _tables()
    for table in ("tbl_relative_dates", "tbl_geochronology", "tbl_dendro_dates"):
        tables[table] = []
    tables["tbl_analysis_entity_ages"][0].update(
        age=0 if zero else None,
        age_younger=None if zero else 5000,
        age_older=None if zero else 7000,
        age_range="[0,1)" if zero else "[5000,7001)",
        dating_specifier="Chosen_Period",
        chronology_id=777,
    )
    if mixed:
        tables["tbl_age_types"][0]["age_type"] = "cal bp"
        tables["tbl_analysis_dating_ranges"][0].update(low_value=300, high_value=400)
    else:
        tables["tbl_analysis_dating_ranges"] = []
    sites = deepcopy(tables["tbl_sites"])
    before = deepcopy(tables)
    if route == "api":

        def fetch(
            url: str, *, params: object, headers: dict[str, str], timeout: float
        ) -> object:
            del params, timeout
            table = url.rsplit("/", 1)[-1]
            start = int(headers["Range"].split("-", 1)[0])
            return deepcopy(tables.get(table, [])) if start == 0 else []

        populate_sead_site_inventory_fields(sites, fetch_json_fn=fetch)
    else:
        populate_sead_site_inventory_from_reader(
            sites, reader=MappingSeadTableReader(tables)
        )
    assert tables == before
    return sites[0]


@pytest.mark.parametrize("route", ["api", "mapping"])
@pytest.mark.parametrize("zero", [False, True])
def test_unspecified_entity_age_never_becomes_bp_interval(
    route: str, zero: bool
) -> None:
    site = _inventory(route, zero=zero)
    row = site["analysis_entity_age_rows"][0]
    assert site["analysis_entity_age_count"] == 1
    assert row["chronology_id"] == 777 and row["dating_specifier"] == "Chosen_Period"
    assert row["age"] == (0 if zero else None)
    assert row["age_younger"] == (None if zero else 5000)
    assert row["age_older"] == (None if zero else 7000)
    assert row["age_range"] == ("[0,1)" if zero else "[5000,7001)")
    assert (row["time_start_bp"], row["time_end_bp"]) == (None, None)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (None, None)
    assert (
        build_sead_temporal_semantics(site, time_interval=None)["comparability_posture"]
        == "unresolved"
    )
    claim = normalize_sead_chronology_claims(
        [site], provenance_record_id="fixture", build_id="fixture"
    )[0]
    assert (
        claim["comparability_status"] == "unresolved"
        and claim["chronology_eligibility"] == "refused"
    )
    assert (claim["younger_bp"], claim["older_bp"]) == (None, None)
    row["age_type"] = "cal bp"
    assert (
        sead_claim_age_policy("analysis_entity_age", row)["comparability_status"]
        == "unresolved"
    )
    row["time_start_bp"], row["time_end_bp"] = 5000, 7000
    refresh_sead_repository_rows([site])
    assert (row["time_start_bp"], row["time_end_bp"]) == (None, None)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (None, None)
    refresh_sead_repository_rows([site])
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (None, None)


@pytest.mark.parametrize("route", ["api", "mapping"])
def test_comparable_dating_range_remains_when_entity_age_is_unresolved(
    route: str,
) -> None:
    site = _inventory(route, mixed=True)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (300, 400)
    claims = normalize_sead_chronology_claims(
        [site], provenance_record_id="fixture", build_id="fixture"
    )
    by_kind = {claim["claim_type"]: claim for claim in claims}
    assert by_kind["analysis_entity_age"]["comparability_status"] == "unresolved"
    assert by_kind["dating_range"]["comparability_status"] == "comparable"
    assert (
        by_kind["dating_range"]["younger_bp"],
        by_kind["dating_range"]["older_bp"],
    ) == (300, 400)
    refresh_sead_repository_rows([site])
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (300, 400)
