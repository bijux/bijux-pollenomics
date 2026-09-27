"""Consume derived synthetic sample events through all propagation scenarios."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from typing import cast

from bijux_pollenomics.analysis.propagation.event_estimation import (
    GovernedSample,
    estimate_first_observed,
)
from bijux_pollenomics.analysis.propagation.network import (
    PhenomenonEvent,
    PropagationCandidate,
    evaluate_propagation_pair,
    run_propagation_sensitivity,
)

JsonObject = dict[str, object]
# name, native site, country annotation, equatorial arc km, [younger,older],
# underlying observation owner. Aliases are explicit evidence dependencies.
_EVENTS = (
    ("older-no", "older-site", "NO", 0.0, 5600.0, 5600.0, "older-no"),
    ("younger-se", "younger-site", "SE", 25.0, 5500.0, 5500.0, "younger-se"),
    ("boundary-fi", "boundary-site", "FI", 100.0, 5480.0, 5520.0, "boundary-fi"),
    ("outside-dk", "outside-site", "DK", 100.000001, 5550.0, 5650.0, "outside-dk"),
    ("distant-se", "distant-site", "SE", 200.0, 5000.0, 5000.0, "distant-se"),
    ("lag-boundary-no", "lag-site", "NO", 50.0, 5550.0, 5550.0, "lag-boundary-no"),
    ("same-site-alias", "older-site", "NO", 0.0, 5590.0, 5590.0, "same-site-alias"),
    ("dependent-alias", "dependent-site", "SE", 25.0, 5500.0, 5500.0, "younger-se"),
)
_DISTANCES = (25.0, 50.0, 100.0, 200.0)
_LAGS = (50.0, 100.0, 200.0, 500.0)
_GEODESIC_TOLERANCE_KM = 1e-11


def _inputs(
    spec: tuple[str, str, str, float, float, float, str],
) -> tuple[PhenomenonEvent, tuple[GovernedSample, ...]]:
    name, site, country, arc_km, younger, older, observation_owner = spec
    template = PhenomenonEvent(
        source_family="synthetic-propagation-truth",
        evidence_domain="pollen_context",
        source_snapshot_id="synthetic-sample-topology",
        source_record_id=f"template:{name}",
        site_id=site,
        observation_ids=(f"template:{name}",),
        country_code=country,
        latitude=0,
        longitude=math.degrees(arc_km * 1000 / 6378137),
        coordinate_quality="fabricated_fixture",
        event_type="reported_positive_observation",
        resolution="whole_pollen",
        feature_key="whole:pollen",
        chronology_claim_id=f"template-age:{name}",
        younger_bp=0,
        older_bp=0,
        comparability_status="comparable",
        threshold_profile_id="reported_positive_v1",
        classification_contract_version=None,
        provenance_record_id=f"fixture:{name}",
        input_digest="synthetic-topology",
        config_digest="synthetic-topology",
        producer_version="synthetic-propagation.v1",
        build_id="synthetic-propagation-truth",
        measurement_semantics_id="synthetic-count.v1",
        evidence_method_id="synthetic-native-count",
        method_compatibility_key="synthetic-native-count.v1",
    )
    samples = tuple(
        GovernedSample(
            observation_id=f"{observation_owner}:{index}",
            source_record_id=f"record:{name}:{index}",
            source_family=template.source_family,
            source_snapshot_id=template.source_snapshot_id,
            feature_key=template.feature_key,
            site_id=site,
            collection_unit_id=f"core:{name}",
            sequence_position=index,
            value=0 if index == 0 else 5,
            measure_kind="count",
            source_unit="grains",
            measurement_semantics_id=template.measurement_semantics_id,
            chronology_claim_id=f"age:{name}:{index}",
            comparability_status="comparable",
            younger_bp=interval[0],
            older_bp=interval[1],
            source_age_value=interval[0] if interval[0] == interval[1] else None,
            source_age_unit="synthetic_cal_bp_1950",
        )
        for index, interval in enumerate(
            (
                (older + 100, older + 100),
                (younger, older),
                (younger - 100, younger - 100),
            )
        )
    )
    return template, samples


def _expected(
    source: tuple[str, str, str, float, float, float, str],
    target: tuple[str, str, str, float, float, float, str],
    distance_max: float,
    lag_max: float,
) -> JsonObject:
    """Independent declared geometry and interval arithmetic; no production calls."""
    distance = abs(source[3] - target[3])
    minimum, maximum = source[4] - target[5], source[5] - target[4]
    if source[1] == target[1]:
        return {"status": "refused", "reason_code": "same_governed_site"}
    if source[6] == target[6]:
        return {"status": "refused", "reason_code": "duplicate_underlying_observation"}
    if distance > distance_max:
        status = "excluded_spatial"
    elif maximum <= 0:
        status = "excluded_temporal_nonpositive"
    elif minimum <= 0:
        status = "indeterminate_order"
    elif minimum > lag_max:
        status = "excluded_temporal_too_large"
    elif maximum <= lag_max:
        status = "definite_candidate"
    else:
        status = "possible_candidate"
    return {
        "status": status,
        "distance_km": distance,
        "minimum_lag_years": minimum,
        "maximum_lag_years": maximum,
        "arrow_allowed": status in {"definite_candidate", "possible_candidate"},
        "cross_border": source[2] != target[2],
    }


def build_propagation_challenge() -> JsonObject:
    events: list[PhenomenonEvent] = []
    derivations: list[JsonObject] = []
    for spec in _EVENTS:
        template, samples = _inputs(spec)
        result = estimate_first_observed(samples, event_template=template)
        passed = (
            result.event is not None
            and result.event.younger_bp == spec[4]
            and result.event.older_bp == spec[5]
            and result.supporting_observation_ids == (f"{spec[6]}:1",)
        )
        derivations.append(
            {
                "case_id": spec[0],
                "event_template": template.as_dict(),
                "native_samples": [asdict(row) for row in samples],
                "output": result.as_dict(),
                "contract_status": "passed" if passed else "failed",
            }
        )
        if result.event is not None:
            events.append(result.event)
    # A missing chronology is retained as a derivation refusal, not fabricated
    # into a dated propagation event or silently removed from the denominator.
    from dataclasses import replace

    template, samples = _inputs(_EVENTS[0])
    gap_samples = tuple(
        replace(
            row,
            younger_bp=None,
            older_bp=None,
            comparability_status="unresolved",
            source_age_value=None,
        )
        if index == 1
        else row
        for index, row in enumerate(samples)
    )
    gap = estimate_first_observed(gap_samples, event_template=template)
    derivations.append(
        {
            "case_id": "chronology-gap",
            "event_template": template.as_dict(),
            "native_samples": [asdict(row) for row in gap_samples],
            "output": gap.as_dict(),
            "contract_status": "passed"
            if gap.event is None and gap.reason_code == "chronology_unresolved"
            else "failed",
        }
    )
    if len(events) != len(_EVENTS):
        raise ValueError(
            "Synthetic sample derivation failed; no smaller favorable graph is allowed"
        )
    network = run_propagation_sensitivity(events)
    scenarios: list[JsonObject] = []
    stability: Counter[tuple[str, str]] = Counter()
    for scenario_result in network.scenario_results:
        scenario = scenario_result.scenario
        network_rows = {
            (row.source_event_id, row.target_event_id): row
            for row in scenario_result.evaluated_pairs
        }
        network_refusals = {
            (row.source_event_id, row.target_event_id): row
            for row in scenario_result.refusals
        }
        complete: list[JsonObject] = []
        expected_edges: set[tuple[str, str]] = set()
        for source_index, source in enumerate(events):
            for target_index, target in enumerate(events):
                if source_index == target_index:
                    continue
                expected = _expected(
                    _EVENTS[source_index],
                    _EVENTS[target_index],
                    scenario.maximum_distance_km,
                    scenario.maximum_lag_years,
                )
                actual = evaluate_propagation_pair(source, target, scenario=scenario)
                key = (source.event_id, target.event_id)
                error: float | None = None
                if isinstance(actual, PropagationCandidate):
                    error = abs(
                        actual.distance_km_unrounded
                        - cast(float, expected.get("distance_km", math.inf))
                    )
                    passed = (
                        actual.candidate_status == expected["status"]
                        and error <= _GEODESIC_TOLERANCE_KM
                        and actual.minimum_lag_years
                        == expected.get("minimum_lag_years")
                        and actual.maximum_lag_years
                        == expected.get("maximum_lag_years")
                        and actual.directional_arrow_allowed
                        == expected.get("arrow_allowed")
                        and actual.cross_border == expected.get("cross_border")
                    )
                    if actual.directional_arrow_allowed:
                        expected_edges.add(key)
                        stability[
                            (_EVENTS[source_index][0], _EVENTS[target_index][0])
                        ] += 1
                    membership = (
                        "evaluated"
                        if key in network_rows
                        else "outside_search_envelope"
                    )
                    if key in network_rows:
                        retained = network_rows[key]
                        passed = passed and all(
                            retained.as_dict()[field] == actual.as_dict()[field]
                            for field in (
                                "distance_km_unrounded",
                                "minimum_lag_years",
                                "maximum_lag_years",
                                "candidate_status",
                                "directional_arrow_allowed",
                            )
                        )
                    else:
                        passed = (
                            passed and actual.candidate_status == "excluded_spatial"
                        )
                else:
                    passed = actual.reason_code == expected.get("reason_code")
                    membership = (
                        "refused" if key in network_refusals else "missing_refusal"
                    )
                    passed = (
                        passed
                        and key in network_refusals
                        and network_refusals[key].reason_code == actual.reason_code
                    )
                complete.append(
                    {
                        "source_case_id": _EVENTS[source_index][0],
                        "target_case_id": _EVENTS[target_index][0],
                        "independent_expectation": expected,
                        "output": actual.as_dict(),
                        "distance_error_km": error,
                        "network_membership": membership,
                        "contract_status": "passed" if passed else "failed",
                    }
                )
        network_edges = {
            (row.source_event_id, row.target_event_id)
            for row in scenario_result.directed_candidates
        }
        expected_count = sum(
            row["independent_expectation"] is not None
            and cast(JsonObject, row["independent_expectation"]).get(
                "arrow_allowed", False
            )
            is True
            for row in complete
        )
        scenario_passed = (
            all(row["contract_status"] == "passed" for row in complete)
            and expected_edges == network_edges
            and len(network_edges) == expected_count
        )
        scenarios.append(
            {
                "scenario": asdict(scenario),
                "complete_pair_ledger": complete,
                "network_reconciliation": scenario_result.reconciliation.as_dict(),
                "network_evaluated_edge_ids": sorted(
                    row.edge_id for row in network_rows.values()
                ),
                "network_refusal_pair_ids": sorted(
                    row.pair_id for row in network_refusals.values()
                ),
                "directed_candidates": [
                    row.as_dict() for row in scenario_result.directed_candidates
                ],
                "contract_status": "passed" if scenario_passed else "failed",
                "denominators": {
                    "complete_ordered_pairs": len(complete),
                    "network_evaluated": len(network_rows),
                    "network_refused": len(network_refusals),
                    "outside_search_envelope": sum(
                        row["network_membership"] == "outside_search_envelope"
                        for row in complete
                    ),
                    "directed_candidates": len(network_edges),
                    "pair_contract_passed": sum(
                        row["contract_status"] == "passed" for row in complete
                    ),
                },
            }
        )
    truth = {"events": _EVENTS, "distances_km": _DISTANCES, "lags_years": _LAGS}
    return {
        "schema_version": "pollenomics-synthetic-propagation.v1",
        "prospective_contract": {
            **truth,
            "derivation_attempts": 9,
            "graph_events": 8,
            "scenarios": 16,
            "ordered_pairs_per_scenario": 56,
            "requested_pair_attempts": 896,
            "distance_absolute_tolerance_km": _GEODESIC_TOLERANCE_KM,
            "eligibility_tolerance": 0.0,
            "threshold_profile_id": "reported_positive_v1",
            "truth_geometry": "independent_stdlib_equatorial_WGS84_semimajor_arc_6378137_metres",
            "country_labels": "fixture_annotations_never_search_partitions",
        },
        "truth_sha256": hashlib.sha256(
            json.dumps(truth, sort_keys=True).encode()
        ).hexdigest(),
        "derivations": derivations,
        "scenarios": scenarios,
        "edge_stability": [
            {
                "source_case_id": source,
                "target_case_id": target,
                "eligible_scenarios": count,
                "requested_scenarios": 16,
            }
            for (source, target), count in sorted(stability.items())
        ],
        "denominators": {
            "derivation_requested": 9,
            "derived": len(events),
            "derivation_refused": 1,
            "derivation_contract_passed": sum(
                row["contract_status"] == "passed" for row in derivations
            ),
            "scenarios_requested": 16,
            "scenarios_attempted": len(scenarios),
            "scenario_contract_passed": sum(
                row["contract_status"] == "passed" for row in scenarios
            ),
            "pair_attempts": sum(
                cast(dict[str, int], row["denominators"])["complete_ordered_pairs"]
                for row in scenarios
            ),
            "pair_contract_passed": sum(
                cast(dict[str, int], row["denominators"])["pair_contract_passed"]
                for row in scenarios
            ),
        },
        "claims": {
            "synthetic_only": True,
            "real_source_admission": False,
            "historical_routes": False,
            "empirical_threshold_validation": False,
            "all_threshold_profiles_challenged": False,
            "taxon_and_ecological_hierarchy_challenged": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_propagation_challenge()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    counts = cast(dict[str, int], report["denominators"])
    print(json.dumps({"output": str(args.output), **counts}))
    return (
        0
        if counts["derivation_contract_passed"] == 9
        and counts["scenario_contract_passed"] == 16
        and counts["pair_contract_passed"] == 896
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
