"""Public geodesic and propagation consumers against declared synthetic truth."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics_dev.lra_validation.spatial_eligibility_challenge import (
    build_spatial_eligibility_challenge,
)

JsonObject = dict[str, object]


@pytest.fixture(scope="module")
def report() -> JsonObject:
    return build_spatial_eligibility_challenge()


def _cases(report: JsonObject) -> dict[str, JsonObject]:
    return {
        cast(str, row["case_id"]): row
        for row in cast(list[JsonObject], report["cases"])
    }


def test_all_requested_attempts_and_exclusions_are_retained(report: JsonObject) -> None:
    assert report["denominators"] == {
        "requested_pair_attempts": 18,
        "attempted_pairs": 18,
        "evaluated": 12,
        "pair_refused": 2,
        "ingestion_refused": 3,
        "fixture_refused": 1,
        "contract_passed": 18,
        "regional_requested_neighbors": 3,
        "regional_eligible_neighbors": 3,
    }


def test_full_binary64_threshold_survives_json_persistence(report: JsonObject) -> None:
    cases = _cases(report)
    exact = cast(JsonObject, cases["exact-threshold"]["output"])
    assert exact["distance_km_unrounded"] == 100.0
    assert exact["candidate_status"] == "definite_candidate"
    for name in ("millimetre-outside", "submillimetre-outside"):
        row = cases[name]
        output = cast(JsonObject, row["output"])
        raw = cast(float, output["distance_km_unrounded"])
        assert raw > 100
        assert output["distance_km_display"] == 100
        assert output["candidate_status"] == "excluded_spatial"
        assert output["reason_code"] == "spatial_threshold_exceeded"
        assert row["raw_distance_roundtrip_identical"] is True
        assert json.loads(json.dumps(raw)).hex() == row["raw_distance_hex"]
        assert output["distance_library"] == "pyproj"
        assert output["distance_library_version"]
        assert cast(float, row["distance_error_km"]) <= 1e-11
    assert cases["submillimetre-outside"]["six_decimal_distance_km"] == 100


def test_coordinate_identity_refusals_and_fixture_axes(report: JsonObject) -> None:
    cases = _cases(report)
    shared = cast(JsonObject, cases["distinct-sites-shared-location"]["output"])
    assert shared["distance_km_unrounded"] == 0
    assert shared["shared_location"] is True
    assert shared["source_site_id"] != shared["target_site_id"]
    assert (
        cast(JsonObject, cases["same-governed-site"]["output"])["reason_code"]
        == "same_governed_site"
    )
    missing = cast(JsonObject, cases["missing-coordinate"]["output"])
    assert missing["reason_code"] == "invalid_or_missing_coordinate"
    assert "distance_km_unrounded" not in missing
    assert cases["partial-coordinate"]["status"] == "ingestion_refused"
    assert cases["reversed-nordic-axis"]["silent_axis_swap"] is False


def test_chronology_bounds_never_substitute_midpoints(report: JsonObject) -> None:
    cases = _cases(report)
    overlap = cast(JsonObject, cases["overlap-cross-border"]["output"])
    assert (overlap["minimum_lag_years"], overlap["maximum_lag_years"]) == (-150, 50)
    assert overlap["candidate_status"] == "indeterminate_order"
    assert overlap["directional_arrow_allowed"] is False
    gap = cast(JsonObject, cases["chronology-gap"]["output"])
    assert gap["minimum_lag_years"] is None
    assert gap["maximum_lag_years"] is None
    assert gap["candidate_status"] == "unresolved"
    assert gap["directional_arrow_allowed"] is False
    uncertain = cast(JsonObject, cases["uncertain-lag-threshold"]["output"])
    assert (uncertain["minimum_lag_years"], uncertain["maximum_lag_years"]) == (90, 110)
    assert uncertain["candidate_status"] == "possible_candidate"


def test_country_labels_and_regional_search_preserve_eligibility(
    report: JsonObject,
) -> None:
    cases = _cases(report)
    original = cast(JsonObject, cases["malmo-lund"]["output"])
    swapped = cast(JsonObject, cases["country-label-swap"]["output"])
    assert (original["source_country_code"], original["target_country_code"]) == (
        "NO",
        "SE",
    )
    assert (swapped["source_country_code"], swapped["target_country_code"]) == (
        "SE",
        "NO",
    )
    assert original["cross_border"] is True
    assert report["country_label_invariance_passed"] is True
    regional = cast(JsonObject, report["regional_search"])
    assert regional["contract_status"] == "passed"
    arrows = cast(list[JsonObject], regional["directed_candidates"])
    assert {row["target_country_code"] for row in arrows} == {"NO", "FI", "SE"}
    assert all(row["source_country_code"] == "SE" for row in arrows)
    assert all(row["directional_arrow_allowed"] is True for row in arrows)


def test_retained_report_matches_replay_and_claim_scope(report: JsonObject) -> None:
    root = next(
        parent
        for parent in Path(__file__).parents
        if (parent / "configs/pytest.ini").is_file()
    )
    retained = json.loads(
        (
            root / "docs/report/synthetic-validation/spatial-eligibility/report.json"
        ).read_text()
    )
    assert retained == json.loads(json.dumps(report))
    claims = cast(JsonObject, report["claims"])
    assert claims["synthetic_only"] is True
    assert claims["historical_routes"] is False
    assert claims["country_only_display_context_verified"] is False
