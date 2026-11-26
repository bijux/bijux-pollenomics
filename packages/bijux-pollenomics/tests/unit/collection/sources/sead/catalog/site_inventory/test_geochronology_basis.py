"""Unspecified radiometric ages do not supply calendar-BP site envelopes."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
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


def _inventory(route: str, *, mixed: bool, dendro: bool = False) -> dict[str, Any]:
    tables = _tables()
    for table in ("tbl_relative_dates", "tbl_analysis_entity_ages"):
        tables[table] = []
    tables["tbl_geochronology"][0].update(
        age=1200, error_younger=20, error_older=10, dating_uncertainty_id=None
    )
    if dendro:
        tables["tbl_dendro_dates"][0].update(
            age_older=1754, age_younger=None, dating_uncertainty_id=None
        )
    else:
        tables["tbl_dendro_dates"] = []
    if mixed:
        tables["tbl_age_types"][0]["age_type"] = "cal bp"
        tables["tbl_analysis_dating_ranges"][0].update(low_value=300, high_value=400)
    else:
        tables["tbl_analysis_dating_ranges"] = []
    sites = deepcopy(tables["tbl_sites"])
    before = deepcopy(tables)
    if route == "mapping":
        populate_sead_site_inventory_from_reader(
            sites, reader=MappingSeadTableReader(tables)
        )
    else:

        def fetch(
            url: str, *, params: object, headers: dict[str, str], timeout: float
        ) -> object:
            del params, timeout
            return (
                deepcopy(tables.get(url.rsplit("/", 1)[-1], []))
                if int(headers["Range"].split("-", 1)[0]) == 0
                else []
            )

        populate_sead_site_inventory_fields(sites, fetch_json_fn=fetch)
    assert tables == before
    return sites[0]


@pytest.mark.parametrize("route", ["api", "mapping"])
@pytest.mark.parametrize("mixed", [False, True])
def test_unknown_geochronology_does_not_contribute_to_bp_envelope(
    route: str, mixed: bool
) -> None:
    site = _inventory(route, mixed=mixed)
    row = site["geochronology_rows"][0]
    assert (row["age"], row["error_younger"], row["error_older"]) == (1200, 20, 10)
    assert (row["time_start_bp"], row["time_end_bp"]) == (1180, 1210)
    assert site["geochronology_count"] == 1
    claims = normalize_sead_chronology_claims(
        [site], provenance_record_id="fixture", build_id="fixture"
    )
    claim = next(item for item in claims if item["claim_type"] == "geochronology")
    assert (
        claim["comparability_status"],
        claim["chronology_eligibility"],
        claim["younger_bp"],
        claim["older_bp"],
    ) == ("context_only", "refused", None, None)
    assert (
        sead_claim_age_policy("geochronology", row)["comparability_status"]
        == "context_only"
    )
    expected = (300, 400) if mixed else (None, None)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == expected
    refresh_sead_repository_rows([site])
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == expected
    assert (row["time_start_bp"], row["time_end_bp"]) == (1180, 1210)


def test_retained_site_4237_keeps_context_fallback_without_geochron_bp() -> None:
    relative = Path("data/sead/raw/nordic_sites.json")
    source = next(
        (
            parent / relative
            for parent in Path(__file__).resolve().parents
            if (parent / relative).is_file()
        ),
        None,
    )
    if source is None:
        pytest.skip("retained historical SEAD inventory is unavailable")
    raw = source.read_bytes()
    if (
        hashlib.sha256(raw).hexdigest()
        != "d864d2636763c76c8ffe51983a9e5c6f8d517a0aae33ea640635bd911f7960a6"
    ):
        pytest.skip("exact retained historical SEAD inventory is unavailable")
    site = deepcopy(
        next(row for row in json.loads(raw)["rows"] if row["site_id"] == 4237)
    )
    geo = deepcopy(site["geochronology_rows"])
    refresh_sead_repository_rows([site])
    assert site["geochronology_count"] == 3
    assert [(row["geochron_id"], row["age"]) for row in site["geochronology_rows"]] == [
        (row["geochron_id"], row["age"]) for row in geo
    ]
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (None, None)
    assert (site["contextual_time_start_bp"], site["contextual_time_end_bp"]) == (
        7000,
        10000,
    )
    assert (site["time_start_bp"], site["time_end_bp"]) == (7000, 10000)


@pytest.mark.parametrize("route", ["api", "mapping"])
def test_calendar_dendro_still_supplies_site_interval(route: str) -> None:
    site = _inventory(route, mixed=False, dendro=True)
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (196, 196)
    assert site["geochronology_count"] == 1 and site["dendro_date_count"] == 1
    refresh_sead_repository_rows([site])
    assert (site["numeric_time_start_bp"], site["numeric_time_end_bp"]) == (196, 196)
