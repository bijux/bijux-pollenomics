"""Native geometry decoding refuses ambiguous owners and lossy numeric tokens."""

from __future__ import annotations

import pytest

from bijux_pollenomics.collection.sources.neotoma.country.decisions import (
    build_neotoma_context_country_decisions,
)
from bijux_pollenomics.collection.sources.neotoma.country.site_geometry import (
    classify_neotoma_site_country,
    neotoma_site_representative_point,
)


@pytest.mark.parametrize(
    "geography",
    [
        '{"type":"Point","coordinates":[99,99],"coordinates":[2,2]}',
        '{"type":"Point","coordinates":[1e-9999,2]}',
        '{"type":"Point","coordinates":[2,2],"source":{"id":1,"id":2}}',
    ],
)
def test_ambiguous_or_lossy_geography_cannot_select_a_point_or_country(
    geography: str,
) -> None:
    site: dict[str, object] = {"siteid": 1, "geography": geography}
    assert neotoma_site_representative_point(site) is None
    assert classify_neotoma_site_country(site, (-10, -10, 10, 10), {}) == ""
    assert site["geography"] == geography
    boundaries: dict[str, dict[str, object]] = {
        "Sweden": {
            "features": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [3, 0], [3, 3], [0, 3], [0, 0]]],
                    }
                }
            ]
        }
    }
    decision = build_neotoma_context_country_decisions([site], boundaries)["1"]
    assert decision.derived_country is None
    assert decision.decision_status == "refused"
    assert decision.refusal_reason == "invalid_site_geometry"


@pytest.mark.parametrize("geography", [None, "", "broken", "[]", "null", "true"])
def test_missing_or_invalid_geometry_keeps_existing_unavailable_posture(
    geography: object,
) -> None:
    assert neotoma_site_representative_point({"geography": geography}) is None


def test_native_zero_and_regular_point_keep_their_values() -> None:
    assert neotoma_site_representative_point(
        {"geography": '{"type":"Point","coordinates":[0,2]}'}
    ) == (0.0, 2.0, "Point")
