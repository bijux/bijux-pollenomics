from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
import json
from threading import Barrier
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.raa import collection
from bijux_pollenomics.collection.sources.raa.page_observation import (
    RaaObservedInventory,
)


def page(name: str, crs: object = None) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "numberMatched": 2,
        "crs": crs,
        "features": [
            {
                "type": "Feature",
                "properties": {"lamningsnummer": name},
                "geometry": None,
            }
        ],
    }


def capture(pages: list[dict[str, object]]) -> RaaObservedInventory:
    with patch.object(
        collection, "fetch_raa_feature_page", side_effect=deepcopy(pages)
    ):
        return collection.capture_raa_feature_inventory()


def test_capture_distinguishes_absent_and_explicit_later_page_without_inventory_change() -> (
    None
):
    first = page("A", {"type": "name", "properties": {"name": "EPSG:4326"}})
    explicit = page("B", {"type": "name", "properties": {"name": "EPSG:4326"}})
    absent = deepcopy(explicit)
    del absent["crs"]
    left = capture([first, explicit])
    right = capture([first, absent])
    assert left.inventory == right.inventory
    assert (
        left.observation.canonical_inventory_sha256
        == right.observation.canonical_inventory_sha256
    )
    assert left.observation.pages[1].crs_state == "declared"
    assert right.observation.pages[1].crs_state == "absent"
    assert (
        left.observation.pages[1].canonical_page_sha256
        != right.observation.pages[1].canonical_page_sha256
    )
    collection.validate_raa_page_observation(left.inventory, left.observation)
    collection.validate_raa_page_observation(right.inventory, right.observation)


def test_observations_refuse_inventory_drift_and_page_reordering() -> None:
    captured = capture([page("A"), page("B")])
    changed = deepcopy(captured.inventory)
    assert isinstance(changed["features"], list)
    changed["features"].reverse()
    with pytest.raises(ValueError):
        collection.validate_raa_page_observation(changed, captured.observation)
    reversed_pages = replace(
        captured.observation, pages=captured.observation.pages[::-1]
    )
    with pytest.raises(ValueError):
        collection.validate_raa_page_observation(captured.inventory, reversed_pages)
    wrong_profile = replace(captured.observation, requested_crs="EPSG:3857")
    with pytest.raises(ValueError):
        collection.validate_raa_page_observation(captured.inventory, wrong_profile)


def test_first_page_claim_must_match_retained_inventory_crs() -> None:
    first = page("A", {"type": "name", "properties": {"name": "EPSG:4326"}})
    captured = capture([first, page("B")])
    forged = replace(captured.observation.pages[0], crs_state="absent", crs_name=None)
    observation = replace(
        captured.observation, pages=(forged, *captured.observation.pages[1:])
    )
    with pytest.raises(ValueError, match="first page CRS"):
        collection.validate_raa_page_observation(captured.inventory, observation)


def test_default_fetch_matches_capture_inventory() -> None:
    pages = [page("A"), page("B")]
    with patch.object(
        collection, "fetch_raa_feature_page", side_effect=deepcopy(pages)
    ):
        ordinary = collection.fetch_raa_feature_inventory()
    observed = capture(pages)
    assert observed.inventory == ordinary
    assert json.dumps(observed.inventory, indent=2, ensure_ascii=False) == json.dumps(
        ordinary, indent=2, ensure_ascii=False
    )


def test_capture_refuses_conflicting_page_before_return() -> None:
    with pytest.raises(ValueError, match="RAÄ.*CRS"):
        capture(
            [
                page("A"),
                page("B", {"type": "name", "properties": {"name": "EPSG:3857"}}),
            ]
        )


def test_empty_population_and_null_declaration() -> None:
    empty = {
        "type": "FeatureCollection",
        "numberMatched": 0,
        "features": [],
        "crs": None,
    }
    result = capture([empty])
    assert result.observation.pages[0].crs_state == "null"
    assert result.observation.pages[0].count == 0
    collection.validate_raa_page_observation(result.inventory, result.observation)


def test_accepted_alias_is_preserved_as_observed() -> None:
    alias = "urn:ogc:def:crs:EPSG::4326"
    result = capture(
        [page("A"), page("B", {"type": "name", "properties": {"name": alias}})]
    )
    assert result.observation.pages[1].crs_state == "declared"
    assert result.observation.pages[1].crs_name == alias
    collection.validate_raa_page_observation(result.inventory, result.observation)


def test_observation_count_budget_refuses_without_altering_prior_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior = capture([page("A"), page("B")])
    monkeypatch.setattr(collection, "MAX_PAGES", 1)
    with pytest.raises(ValueError, match="budget"):
        capture([page("C"), page("D")])
    assert prior.observation.pages[0].start == 0
    assert prior.observation.pages[1].start == 1


def test_observation_page_byte_budget_is_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(collection, "MAX_PAGE_BYTES", 20)
    with pytest.raises(ValueError, match="byte budget"):
        capture([page("A"), page("B")])


def test_page_population_drift_is_refused() -> None:
    second = page("B")
    second["numberMatched"] = 3
    with pytest.raises(ValueError, match="population changed"):
        capture([page("A"), second])


def test_concurrent_captures_keep_request_scopes_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    barrier = Barrier(2, timeout=5)

    def fetch(*, start_index: int, cql_filter: str | None = None) -> dict[str, object]:
        assert cql_filter is not None
        if start_index == 0:
            barrier.wait()
        return page(f"{cql_filter}-{start_index}")

    monkeypatch.setattr(collection, "fetch_raa_feature_page", fetch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = list(
            pool.map(collection.capture_raa_feature_inventory, ["scope_a", "scope_b"])
        )
    assert a.observation.cql_filter == "scope_a"
    assert b.observation.cql_filter == "scope_b"
    assert (
        a.observation.canonical_inventory_sha256
        != b.observation.canonical_inventory_sha256
    )
    collection.validate_raa_page_observation(a.inventory, a.observation)
    collection.validate_raa_page_observation(b.inventory, b.observation)
