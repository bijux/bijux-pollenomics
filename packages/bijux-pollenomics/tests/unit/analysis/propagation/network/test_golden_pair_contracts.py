"""Propagation refusal accounting and synthetic cross-border contract fixtures."""

from __future__ import annotations

from dataclasses import replace
import json
from typing import TypedDict

from pyproj import Geod
import pytest

from bijux_pollenomics.analysis.propagation.network import (
    PropagationCandidate,
    PropagationPairRefusal,
    evaluate_propagation_pair,
    generate_propagation_network,
)

from .support import event


class _EventOverrides(TypedDict, total=False):
    feature_key: str
    observation_ids: tuple[str, ...]
    preaggregation_valid: bool
    site_id: str
    method_compatibility_key: str
    latitude: float | None
    longitude: float | None


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        pytest.param(
            {"feature_key": "taxon:secale_cereale"},
            "incompatible_feature",
            id="PROP-008",
        ),
        pytest.param(
            {"observation_ids": ("observation-source",)},
            "duplicate_underlying_observation",
            id="PROP-009",
        ),
        pytest.param(
            {"preaggregation_valid": False},
            "invalid_preaggregation",
            id="PROP-010",
        ),
        pytest.param({"site_id": "site-source"}, "same_governed_site", id="PROP-012"),
        pytest.param(
            {"method_compatibility_key": "different-method.v1"},
            "incompatible_evidence_method",
            id="PROP-014",
        ),
        pytest.param(
            {"latitude": None, "longitude": None},
            "invalid_or_missing_coordinate",
            id="SOURCE-009",
        ),
    ),
)
def test_refused_pairs_preserve_identity_and_reconcile_outside_candidate_statuses(
    overrides: _EventOverrides, reason: str
) -> None:
    source = event("source")
    target = event(
        "target", latitude=55.7047, longitude=13.191, younger_bp=5500, older_bp=5500
    )
    target = replace(target, event_id="", **overrides)
    refusal = evaluate_propagation_pair(source, target)

    assert isinstance(refusal, PropagationPairRefusal)
    assert refusal.reason_code == reason
    assert refusal.source_event_id == source.event_id
    assert refusal.target_event_id == target.event_id
    repeated = evaluate_propagation_pair(source, target)
    assert isinstance(repeated, PropagationPairRefusal)
    assert refusal.pair_id == repeated.pair_id
    assert refusal.config_digest and refusal.producer_version
    assert json.loads(json.dumps(refusal.as_dict())) == refusal.as_dict()
    network = generate_propagation_network((source, target))
    result = network.scenario_results[0]
    assert result.evaluated_pairs == ()
    assert result.directed_candidates == ()
    reverse = evaluate_propagation_pair(target, source)
    assert isinstance(reverse, PropagationPairRefusal)
    requested_refusals = (refusal, reverse)
    assert len({row.pair_id for row in requested_refusals}) == 2
    assert {row.reason_code for row in requested_refusals} == {reason}
    assert sum(dict(result.reconciliation.status_counts).values()) == 0
    if reason in {"incompatible_feature", "incompatible_evidence_method"}:
        # Compatibility universes define automatic attempts; explicit requests
        # keep their own refusal ledger and denominator.
        assert result.refusals == ()
        assert result.reconciliation.refused_pair_count == 0
    else:
        assert len(result.refusals) == result.reconciliation.refused_pair_count == 2
        assert {row.reason_code for row in result.refusals} == {reason}
        assert {row.pair_id for row in result.refusals} == {
            row.pair_id for row in requested_refusals
        }


@pytest.mark.parametrize(
    "site_is_shared",
    (pytest.param(False, id="PROP-011"), pytest.param(True, id="SPACE-008")),
)
def test_colocation_keeps_distinct_sites_eligible_and_same_site_refused(
    site_is_shared: bool,
) -> None:
    source = event("source")
    target = event(
        "target",
        site_id=source.site_id if site_is_shared else "distinct-site",
        younger_bp=5500,
        older_bp=5500,
    )
    result = evaluate_propagation_pair(source, target)
    if site_is_shared:
        assert isinstance(result, PropagationPairRefusal)
        assert result.reason_code == "same_governed_site"
    else:
        assert isinstance(result, PropagationCandidate)
        assert result.distance_km_unrounded == 0
        assert result.shared_location is True
        assert result.candidate_status == "definite_candidate"
        assert result.directional_arrow_allowed is True
        assert result.route_interpretation_allowed is False


@pytest.mark.parametrize(
    ("source_country", "target_country", "source_point", "target_point"),
    (
        pytest.param(
            "SE", "DK", (55.6050, 13.0038), (55.6761, 12.5683), id="NORDIC-001"
        ),
        pytest.param(
            "NO", "SE", (68.4381, 17.4274), (68.3491, 18.8294), id="NORDIC-002"
        ),
        pytest.param(
            "FI", "SE", (65.8481, 24.1466), (65.8355, 24.1368), id="NORDIC-003"
        ),
        pytest.param(
            "DK", "DK", (55.6761, 12.5683), (55.6419, 12.0878), id="NORDIC-004"
        ),
    ),
)
def test_synthetic_country_pairs_apply_identical_scientific_thresholds(
    source_country: str,
    target_country: str,
    source_point: tuple[float, float],
    target_point: tuple[float, float],
) -> None:
    source = event(
        "source",
        country_code=source_country,
        latitude=source_point[0],
        longitude=source_point[1],
    )
    target = event(
        "target",
        country_code=target_country,
        latitude=target_point[0],
        longitude=target_point[1],
        younger_bp=5500,
        older_bp=5500,
    )
    result = evaluate_propagation_pair(source, target)
    domestic = evaluate_propagation_pair(
        source, replace(target, country_code=source_country, event_id="")
    )
    assert isinstance(result, PropagationCandidate)
    assert isinstance(domestic, PropagationCandidate)
    assert result.candidate_status == domestic.candidate_status == "definite_candidate"
    assert result.distance_km_unrounded == domestic.distance_km_unrounded < 100
    assert (result.minimum_lag_years, result.maximum_lag_years) == (100, 100)
    assert (result.source_country_code, result.target_country_code) == (
        source_country,
        target_country,
    )
    assert result.cross_border is (source_country != target_country)
    network = generate_propagation_network((source, target)).scenario_results[0]
    assert len(network.directed_candidates) == 1
    assert network.directed_candidates[0].source_event_id == source.event_id
    assert network.directed_candidates[0].target_event_id == target.event_id


@pytest.mark.parametrize(
    "distance_metres", (pytest.param(100_000.0004, id="SPACE-010"),)
)
def test_full_geodesic_result_survives_persistence_and_controls_pair_eligibility(
    distance_metres: float,
) -> None:
    longitude, latitude, _ = Geod(ellps="WGS84").fwd(15, 60, 90, distance_metres)
    source = event("source", latitude=60, longitude=15)
    target = event(
        "target", latitude=latitude, longitude=longitude, younger_bp=5500, older_bp=5500
    )
    result = evaluate_propagation_pair(source, target)
    assert isinstance(result, PropagationCandidate)
    assert result.distance_km_unrounded == pytest.approx(
        distance_metres / 1000, abs=1e-10, rel=0
    )
    assert result.distance_km_unrounded > 100
    assert result.distance_km_display == 100
    assert result.candidate_status == "excluded_spatial"
    assert result.directional_arrow_allowed is False
    reopened = json.loads(json.dumps(result.as_dict()))
    assert reopened["distance_km_unrounded"] == result.distance_km_unrounded
    assert reopened["distance_km_display"] == 100
    assert reopened["distance_library"] == "pyproj"
    assert reopened["distance_library_version"]


def test_refusal_configuration_digest_tracks_both_event_configurations() -> None:
    source = event("source")
    target = event("target", site_id=source.site_id)
    original = evaluate_propagation_pair(source, target)
    source_changed = evaluate_propagation_pair(
        replace(source, config_digest="source-configuration", event_id=""), target
    )
    target_changed = evaluate_propagation_pair(
        source, replace(target, config_digest="target-configuration", event_id="")
    )
    assert isinstance(original, PropagationPairRefusal)
    assert isinstance(source_changed, PropagationPairRefusal)
    assert isinstance(target_changed, PropagationPairRefusal)
    assert (
        len({row.config_digest for row in (original, source_changed, target_changed)})
        == 3
    )
    assert original.propagation_contract_version == "1.0.0"
    assert original.producer_version == "propagation-network.v1"
