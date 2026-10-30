"""Scenario-qualified propagation claims and exploratory aggregate limits."""

from __future__ import annotations

import pytest

from .test_scientific_edges import edge_row, render_edges


@pytest.mark.parametrize("status", ["definite_candidate", "possible_candidate"])
@pytest.mark.parametrize(
    "scenario", ["rectangular_100km_100yr_v1", "rectangular_50km_50yr_v1"]
)
def test_native_candidate_claim_names_scenario_and_limits(
    status: str, scenario: str
) -> None:
    row = edge_row(status, native=True)
    row["scenario_id"] = scenario
    rendered = render_edges([row])["rows"][0]
    expected = (
        f"Under scenario {scenario}, these governed observations form a candidate "
        "propagation link. This relation is consistent with spatiotemporal succession; "
        "it does not demonstrate a migration route, transport mechanism, local "
        "establishment, cultivation, or causation."
    )
    assert expected in rendered["popup"]
    relation = rendered["focus"]["detailTabs"]["relation"]
    assert rendered["focus"]["detailTabs"]["overview"]["interpretation"] == expected
    assert relation["candidate_status"] == status
    assert relation["scenario_id"] == scenario
    assert relation["directional_arrow_allowed"] is True


@pytest.mark.parametrize("native", [False, True])
def test_legacy_or_missing_scenario_does_not_invent_a_governed_claim(
    native: bool,
) -> None:
    row = edge_row("definite_candidate", native=native)
    if not native:
        row["scenario_id"] = "rectangular_100km_100yr_v1"
    rendered = render_edges([row])["rows"][0]
    interpretation = rendered["focus"]["detailTabs"]["overview"]["interpretation"]
    assert (
        interpretation
        == "Candidate succession under the governed rule; not proof of migration or causation."
    )
    assert "Under scenario" not in rendered["popup"]


@pytest.mark.parametrize(
    ("native", "resolution", "warning"),
    [
        (True, "whole_pollen", True),
        (False, "whole_pollen", False),
        (True, "taxon", False),
        (True, "ecological_group", False),
    ],
    ids=["MATCH-005", "legacy-whole", "taxon", "ecological-group"],
)
def test_whole_pollen_qualification_is_visible_without_relabelling_other_edges(
    native: bool, resolution: str, warning: bool
) -> None:
    row = edge_row("definite_candidate", native=native)
    row.update(resolution=resolution, scenario_id="rectangular_100km_100yr_v1")
    rendered = render_edges([row])["rows"][0]
    interpretation = rendered["focus"]["detailTabs"]["overview"]["interpretation"]
    limit = (
        "Whole-pollen comparison is an exploratory aggregate of heterogeneous taxa; "
        "it does not establish taxon-level equivalence."
    )
    assert isinstance(interpretation, str)
    assert (limit in interpretation) is warning
    assert (limit in rendered["popup"]) is warning
    assert ("Under scenario rectangular_100km_100yr_v1" in interpretation) is native
    assert rendered["focus"]["detailTabs"]["overview"]["resolution"] == resolution
