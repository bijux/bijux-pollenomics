from __future__ import annotations

from dataclasses import replace
import json

from hypothesis import given, settings
from hypothesis import strategies as st
from pyproj import Geod
import pytest

from bijux_pollenomics.analysis.propagation.network import (
    COUNTRY_CODES,
    PROPAGATION_SENSITIVITY_SCENARIOS,
    EventValidationError,
    PhenomenonEvent,
    PropagationCandidate,
    PropagationNetworkResult,
    PropagationPairRefusal,
    PropagationScenarioResult,
    evaluate_propagation_pair,
    generate_propagation_network,
    generate_propagation_network_exhaustive,
    run_propagation_sensitivity,
)
from bijux_pollenomics.analysis.propagation.network.codec import (
    _event_manifest_digest,
)
from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
    CandidatePropagationScenario,
)
from bijux_pollenomics.core.geo_distance import wgs84_inverse_geodesic


def _event(
    name: str,
    *,
    site_id: str | None = None,
    country_code: str = "SE",
    latitude: float | None = 55.605,
    longitude: float | None = 13.0038,
    younger_bp: int | None = 5600,
    older_bp: int | None = 5600,
    comparability_status: str = "comparable",
    resolution: str = "taxon",
    feature_key: str = "taxon:triticum_aestivum",
    classification_contract_version: str | None = "classification.v1",
    observation_ids: tuple[str, ...] | None = None,
    threshold_profile_id: str = "reported_positive_v1",
    measurement_semantics_id: str = "presence.v1",
    method_compatibility_key: str = "pollen-presence.v1",
    subject_granularity: str = "sample",
    preaggregation_valid: bool = True,
    accepted_taxon_concept_id: str = "accepted-taxon-1",
) -> PhenomenonEvent:
    return PhenomenonEvent(
        source_family="source-native-fixture",
        evidence_domain="pollen_context",
        source_snapshot_id="snapshot-1",
        source_record_id=f"record-{name}",
        site_id=site_id or f"site-{name}",
        observation_ids=observation_ids or (f"observation-{name}",),
        country_code=country_code,
        latitude=latitude,
        longitude=longitude,
        coordinate_quality="source-reported",
        event_type="reported_positive_observation",
        resolution=resolution,
        feature_key=feature_key,
        chronology_claim_id=f"chronology-{name}",
        younger_bp=younger_bp,
        older_bp=older_bp,
        comparability_status=comparability_status,
        threshold_profile_id=threshold_profile_id,
        classification_contract_version=classification_contract_version,
        provenance_record_id=f"provenance-{name}",
        input_digest=f"input-{name}",
        config_digest="event-config-v1",
        producer_version="fixture-producer.v1",
        build_id="build-1",
        measurement_semantics_id=measurement_semantics_id,
        evidence_method_id="source-native-method",
        method_compatibility_key=method_compatibility_key,
        subject_granularity=subject_granularity,
        preaggregation_valid=preaggregation_valid,
        role_membership_explicit=resolution == "ecological_role",
        accepted_taxon_concept_id=(
            accepted_taxon_concept_id if resolution == "taxon" else None
        ),
        taxonomic_qualifier="accepted" if resolution == "taxon" else None,
    )


def _scenario(
    result: PropagationNetworkResult, scenario_id: str
) -> PropagationScenarioResult:
    return next(
        row
        for row in result.scenario_results
        if row.scenario.scenario_id == scenario_id
    )


def test_source_native_event_id_is_stable_and_preserves_zero() -> None:
    first = _event("zero", younger_bp=0, older_bp=0)
    second = _event("zero", younger_bp=0, older_bp=0)

    assert first.event_id == second.event_id
    assert first.interval is not None
    assert first.interval.younger_bp == 0
    assert first.as_dict()["observation_ids"] == ["observation-zero"]


def test_publication_schema_excludes_internal_identity_fields() -> None:
    baseline = _event("identity")
    changed = replace(baseline, measurement_semantics_id="abundance.v1")

    assert baseline.as_dict() == changed.as_dict()
    assert _event_manifest_digest((baseline,)) != _event_manifest_digest((changed,))


@pytest.mark.parametrize(
    "overrides",
    (
        {"younger_bp": 100, "older_bp": 50},
        {"younger_bp": 100, "older_bp": None},
        {"younger_bp": -1, "older_bp": 50},
        {"subject_granularity": "site_midpoint"},
        {"feature_key": "taxon:"},
    ),
)
def test_invalid_or_presentation_level_events_are_refused(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(EventValidationError) as refusal:
        _event("invalid", **overrides)  # type: ignore[arg-type]

    assert refusal.value.reason_code == "invalid_event_schema"


def test_malmo_5600_to_lund_5500_is_exact_temporal_boundary_candidate() -> None:
    malmo = _event("malmo", site_id="malmo", younger_bp=5600, older_bp=5600)
    lund = _event(
        "lund",
        site_id="lund",
        latitude=55.7047,
        longitude=13.191,
        younger_bp=5500,
        older_bp=5500,
    )

    scenario = _scenario(
        generate_propagation_network((lund, malmo)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    candidate = next(
        row
        for row in scenario.directed_candidates
        if row.source_event_id == malmo.event_id
    )

    assert candidate.target_event_id == lund.event_id
    assert candidate.minimum_lag_years == 100
    assert candidate.maximum_lag_years == 100
    assert candidate.distance_km_unrounded < 100
    assert candidate.directional_arrow_allowed is True
    assert candidate.route_interpretation_allowed is False
    assert scenario.reconciliation.status_counts == (
        ("definite_candidate", 1),
        ("possible_candidate", 0),
        ("indeterminate_order", 0),
        ("unresolved", 0),
        ("excluded_spatial", 0),
        ("excluded_temporal_nonpositive", 1),
        ("excluded_temporal_too_large", 0),
    )


def test_same_time_and_overlapping_intervals_never_emit_ambiguous_arrows() -> None:
    same_a = _event("same-a", younger_bp=5500, older_bp=5500)
    same_b = _event(
        "same-b", latitude=55.61, longitude=13.01, younger_bp=5500, older_bp=5500
    )
    overlap_a = _event("overlap-a", younger_bp=5500, older_bp=5600)
    overlap_b = _event(
        "overlap-b",
        latitude=55.62,
        longitude=13.02,
        younger_bp=5550,
        older_bp=5650,
    )

    same = _scenario(
        generate_propagation_network((same_a, same_b)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    overlap = _scenario(
        generate_propagation_network((overlap_a, overlap_b)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert {row.candidate_status for row in same.evaluated_pairs} == {
        "excluded_temporal_nonpositive"
    }
    assert {row.candidate_status for row in overlap.evaluated_pairs} == {
        "indeterminate_order"
    }
    assert all(not row.directional_arrow_allowed for row in same.evaluated_pairs)
    assert all(not row.directional_arrow_allowed for row in overlap.evaluated_pairs)
    assert not overlap.directed_candidates


def test_null_chronology_is_unresolved_while_zero_remains_numeric() -> None:
    undated = _event(
        "undated",
        younger_bp=None,
        older_bp=None,
        comparability_status="unresolved",
    )
    zero = _event(
        "zero-target",
        latitude=55.61,
        longitude=13.01,
        younger_bp=0,
        older_bp=0,
    )

    scenario = _scenario(
        generate_propagation_network((undated, zero)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert {row.candidate_status for row in scenario.evaluated_pairs} == {"unresolved"}
    assert all(row.minimum_lag_years is None for row in scenario.evaluated_pairs)
    assert all(row.maximum_lag_years is None for row in scenario.evaluated_pairs)
    assert all(not row.directional_arrow_allowed for row in scenario.evaluated_pairs)


def test_unrounded_distance_controls_exact_boundary_and_epsilon_outside() -> None:
    geod = Geod(ellps="WGS84")
    longitude, latitude, _ = geod.fwd(15.0, 60.0, 90.0, 100_000.0)
    boundary_distance = wgs84_inverse_geodesic(
        latitude_a=60.0,
        longitude_a=15.0,
        latitude_b=latitude,
        longitude_b=longitude,
    ).distance_km_unrounded
    source = _event(
        "distance-source",
        latitude=60.0,
        longitude=15.0,
        younger_bp=5600,
        older_bp=5600,
    )
    boundary = _event(
        "distance-boundary",
        latitude=latitude,
        longitude=longitude,
        younger_bp=5500,
        older_bp=5500,
    )
    exact_scenario = CandidatePropagationScenario(
        scenario_id="measured_100km_boundary_v1",
        maximum_distance_km=boundary_distance,
        maximum_lag_years=100,
    )

    exact = evaluate_propagation_pair(source, boundary, scenario=exact_scenario)
    assert isinstance(exact, PropagationCandidate)
    assert exact.distance_km_unrounded == exact_scenario.maximum_distance_km
    assert exact.candidate_status == "definite_candidate"

    outside_longitude, outside_latitude, _ = geod.fwd(15.0, 60.0, 90.0, 100_001.0)
    outside = _event(
        "distance-outside",
        latitude=outside_latitude,
        longitude=outside_longitude,
        younger_bp=5500,
        older_bp=5500,
    )
    excluded = evaluate_propagation_pair(source, outside)
    assert isinstance(excluded, PropagationCandidate)
    assert excluded.distance_km_unrounded > 100
    assert excluded.distance_km_display == 100.001
    assert excluded.candidate_status == "excluded_spatial"


def test_cross_border_metadata_does_not_change_scientific_decision() -> None:
    source = _event("source", country_code="SE", younger_bp=5600, older_bp=5600)
    domestic_target = _event(
        "target",
        country_code="SE",
        latitude=55.7,
        longitude=13.19,
        younger_bp=5500,
        older_bp=5500,
    )
    cross_border_target = replace(domestic_target, country_code="DK")

    domestic = evaluate_propagation_pair(source, domestic_target)
    cross_border = evaluate_propagation_pair(source, cross_border_target)

    assert isinstance(domestic, PropagationCandidate)
    assert isinstance(cross_border, PropagationCandidate)
    assert domestic.candidate_status == cross_border.candidate_status
    assert domestic.distance_km_unrounded == cross_border.distance_km_unrounded
    assert domestic.cross_border is False
    assert cross_border.cross_border is True
    assert cross_border.source_country_code == "SE"
    assert cross_border.target_country_code == "DK"


def test_signal_resolution_and_role_universes_remain_separate() -> None:
    taxon_a = _event("taxon-a")
    taxon_b = _event(
        "taxon-b", latitude=55.7, longitude=13.19, younger_bp=5500, older_bp=5500
    )
    role_a = _event(
        "role-a",
        resolution="ecological_role",
        feature_key="role:cereal_indicator",
    )
    role_b = _event(
        "role-b",
        resolution="ecological_role",
        feature_key="role:cereal_indicator",
        latitude=55.7,
        longitude=13.19,
        younger_bp=5500,
        older_bp=5500,
    )

    scenario = _scenario(
        generate_propagation_network((taxon_a, role_b, taxon_b, role_a)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert {row.feature_key for row in scenario.evaluated_pairs} == {
        "taxon:triticum_aestivum",
        "role:cereal_indicator",
    }
    assert all(
        (
            row.source_event_id.startswith("event:")
            and row.target_event_id.startswith("event:")
        )
        for row in scenario.evaluated_pairs
    )
    assert len(scenario.evaluated_pairs) == 4


def test_taxon_universe_requires_the_same_accepted_concept() -> None:
    accepted_a = _event("accepted-a")
    accepted_b = _event(
        "accepted-b",
        latitude=55.7,
        longitude=13.19,
        younger_bp=5500,
        older_bp=5500,
        accepted_taxon_concept_id="accepted-taxon-2",
    )

    scenario = _scenario(
        generate_propagation_network((accepted_a, accepted_b)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    direct = evaluate_propagation_pair(accepted_a, accepted_b)

    assert not scenario.evaluated_pairs
    assert isinstance(direct, PropagationPairRefusal)
    assert direct.reason_code == "incompatible_feature"


def test_refusal_ledger_accounts_same_site_duplicate_and_missing_coordinates() -> None:
    same_a = _event("same-site-a", site_id="governed-site")
    same_b = _event(
        "same-site-b",
        site_id="governed-site",
        younger_bp=5500,
        older_bp=5500,
    )
    duplicate = _event(
        "duplicate",
        latitude=55.7,
        longitude=13.19,
        observation_ids=same_a.observation_ids,
        younger_bp=5500,
        older_bp=5500,
    )
    missing = _event(
        "missing",
        latitude=None,
        longitude=None,
        younger_bp=5500,
        older_bp=5500,
    )

    scenario = _scenario(
        generate_propagation_network((same_a, same_b, duplicate, missing)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    reasons = {row.reason_code for row in scenario.refusals}

    assert {
        "same_governed_site",
        "duplicate_underlying_observation",
        "invalid_or_missing_coordinate",
    } <= reasons
    assert scenario.reconciliation.refused_pair_count == len(scenario.refusals)
    assert not (
        {row.pair_id for row in scenario.refusals}
        & {row.edge_id for row in scenario.evaluated_pairs}
    )


def test_direct_incompatible_pair_is_refused_before_candidate_assignment() -> None:
    taxon = _event("taxon")
    role = _event(
        "role",
        resolution="ecological_role",
        feature_key="role:cereal_indicator",
    )

    refusal = evaluate_propagation_pair(taxon, role)

    assert isinstance(refusal, PropagationPairRefusal)
    assert refusal.reason_code == "incompatible_feature"


def test_sensitivity_runs_declared_scenarios_and_all_country_pair_bins() -> None:
    malmo = _event("sensitivity-source", country_code="SE")
    lund = _event(
        "sensitivity-target",
        country_code="DK",
        latitude=55.7047,
        longitude=13.191,
        younger_bp=5500,
        older_bp=5500,
    )

    result = run_propagation_sensitivity((malmo, lund))
    scenario_ids = {row.scenario.scenario_id for row in result.scenario_results}

    assert len(PROPAGATION_SENSITIVITY_SCENARIOS) == 16
    assert len(result.scenario_results) == 16
    assert DEFAULT_PROPAGATION_SCENARIO.scenario_id in scenario_ids
    for scenario in result.scenario_results:
        country_counts = dict(scenario.reconciliation.ordered_country_pair_counts)
        assert tuple(country_counts) == tuple(
            f"{source}-{target}" for source in COUNTRY_CODES for target in COUNTRY_CODES
        )
        assert sum(dict(scenario.reconciliation.status_counts).values()) == len(
            scenario.evaluated_pairs
        )
        assert all(
            sum(dict(counts).values()) >= 0 for counts in country_counts.values()
        )
    lag_50 = _scenario(result, "rectangular_100km_50yr_v1")
    lag_100 = _scenario(result, "rectangular_100km_100yr_v1")
    assert not lag_50.directed_candidates
    assert len(lag_100.directed_candidates) == 1
    assert lag_100.directed_candidates[0].cross_border is True


def test_duplicate_input_and_shuffled_input_are_content_deterministic() -> None:
    events = (
        _event("det-a"),
        _event("det-b", latitude=55.7, longitude=13.19, younger_bp=5500, older_bp=5500),
        _event("det-c", latitude=56.0, longitude=13.3, younger_bp=5450, older_bp=5450),
    )

    forward = generate_propagation_network((*events, events[0]))
    shuffled = generate_propagation_network(
        (events[2], events[0], events[0], events[1])
    )

    assert forward.duplicate_input_event_count == 1
    assert json.dumps(forward.as_dict(), sort_keys=True) == json.dumps(
        shuffled.as_dict(), sort_keys=True
    )


@settings(max_examples=30, deadline=None)
@given(
    points=st.lists(
        st.tuples(
            st.floats(54, 71, allow_nan=False, allow_infinity=False),
            st.floats(5, 32, allow_nan=False, allow_infinity=False),
            st.integers(0, 10_000),
        ),
        min_size=2,
        max_size=8,
    )
)
def test_latitude_index_matches_exhaustive_reference(
    points: list[tuple[float, float, int]],
) -> None:
    events = tuple(
        _event(
            f"property-{index}",
            latitude=latitude,
            longitude=longitude,
            younger_bp=age,
            older_bp=age,
        )
        for index, (latitude, longitude, age) in enumerate(points)
    )
    scenario = CandidatePropagationScenario(
        scenario_id="property_200km_500yr_v1",
        maximum_distance_km=200,
        maximum_lag_years=500,
    )

    indexed = generate_propagation_network(events, scenarios=(scenario,))
    exhaustive = generate_propagation_network_exhaustive(events, scenarios=(scenario,))

    assert indexed.as_dict() == exhaustive.as_dict()
