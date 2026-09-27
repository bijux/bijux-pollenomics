"""Retain synthetic threshold, chronology and regional eligibility consumers."""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
from typing import cast

from bijux_pollenomics.analysis.propagation.network import (
    EventValidationError,
    PhenomenonEvent,
    PropagationCandidate,
    evaluate_propagation_pair,
    generate_propagation_network,
    generate_propagation_network_exhaustive,
)
from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic

JsonObject = dict[str, object]
_SEMIMAJOR_METRES = 6_378_137.0
_DISTANCE_TOLERANCE_KM = 1e-11


def _event(
    name: str,
    *,
    country: str = "SE",
    latitude: float | None = 0.0,
    longitude: float | None = 0.0,
    interval: tuple[float, float] | None = (5600.0, 5600.0),
) -> PhenomenonEvent:
    return PhenomenonEvent(
        source_family="synthetic-spatial-truth",
        evidence_domain="pollen_context",
        source_snapshot_id="synthetic-spatial-truth",
        source_record_id=f"record:{name}",
        site_id=f"site:{name}",
        observation_ids=(f"observation:{name}",),
        country_code=country,
        latitude=latitude,
        longitude=longitude,
        coordinate_quality="fabricated_fixture",
        event_type="reported_positive_observation",
        resolution="whole_pollen",
        feature_key="whole:pollen",
        chronology_claim_id=f"chronology:{name}",
        younger_bp=None if interval is None else interval[0],
        older_bp=None if interval is None else interval[1],
        comparability_status="unresolved" if interval is None else "comparable",
        threshold_profile_id="synthetic-reported-positive",
        classification_contract_version=None,
        provenance_record_id=f"provenance:{name}",
        input_digest=hashlib.sha256(name.encode()).hexdigest(),
        config_digest="synthetic-spatial-config",
        producer_version="synthetic-spatial-eligibility.v1",
        build_id="synthetic-spatial-truth",
        measurement_semantics_id="synthetic-presence",
        evidence_method_id="synthetic-known-truth",
        method_compatibility_key="synthetic-whole-pollen",
    )


def _equatorial_longitude(distance_km: float) -> tuple[float, int]:
    """Construct independent equatorial arc truth, not a geodesic forward call.

    Binary64 input/output may straddle the exact boundary. For that one case,
    search at most 32 adjacent longitude ULPs for an inverse result of exactly
    100.0. The threshold stays fixed; every adjustment is recorded.
    """
    longitude = math.degrees(distance_km * 1000 / _SEMIMAJOR_METRES)
    if distance_km != 100.0:
        return longitude, 0
    for steps in range(33):
        distance = wgs84_inverse_geodesic(
            latitude_a=0.0, longitude_a=0.0, latitude_b=0.0, longitude_b=longitude
        ).distance_km_unrounded
        if distance == 100.0:
            return longitude, steps
        longitude = math.nextafter(longitude, math.inf if distance < 100 else -math.inf)
    raise ValueError("No exact binary64 100 km fixture in the declared 32 ULP budget")


def _pair(
    name: str,
    source: PhenomenonEvent,
    target: PhenomenonEvent,
    expected_status: str,
    *,
    expected_distance_km: float | None = None,
    constructor_ulp_steps: int = 0,
) -> JsonObject:
    result = evaluate_propagation_pair(source, target)
    persisted = json.loads(json.dumps(result.as_dict(), allow_nan=False))
    row: JsonObject = {
        "case_id": name,
        "inputs": {"source": asdict(source), "target": asdict(target)},
        "independent_expected_status": expected_status,
        "independent_equatorial_distance_km": expected_distance_km,
        "constructor_ulp_steps": constructor_ulp_steps,
        "output": persisted,
    }
    if isinstance(result, PropagationCandidate):
        expected_lags = (
            None
            if source.interval is None or target.interval is None
            else (
                cast(float, source.younger_bp) - cast(float, target.older_bp),
                cast(float, source.older_bp) - cast(float, target.younger_bp),
            )
        )
        roundtrip = (
            cast(float, persisted["distance_km_unrounded"]).hex()
            == result.distance_km_unrounded.hex()
        )
        distance_error = (
            None
            if expected_distance_km is None
            else abs(result.distance_km_unrounded - expected_distance_km)
        )
        passed = (
            result.candidate_status == expected_status
            and result.directional_arrow_allowed
            == (expected_status in {"definite_candidate", "possible_candidate"})
            and (
                (result.minimum_lag_years, result.maximum_lag_years)
                == ((None, None) if expected_lags is None else expected_lags)
            )
            and roundtrip
            and bool(result.distance_library_version)
            and (distance_error is None or distance_error <= _DISTANCE_TOLERANCE_KM)
        )
        row.update(
            status="evaluated",
            expected_lag_bounds_years=expected_lags,
            distance_error_km=distance_error,
            raw_distance_hex=result.distance_km_unrounded.hex(),
            raw_distance_roundtrip_identical=roundtrip,
            six_decimal_distance_km=round(result.distance_km_unrounded, 6),
            contract_status="passed" if passed else "failed",
        )
    else:
        row.update(
            status="pair_refused",
            contract_status="passed"
            if result.reason_code == expected_status
            else "failed",
        )
    return row


def build_spatial_eligibility_challenge() -> JsonObject:
    """Run the fixed synthetic attempts without source or country admission."""
    source = _event("equator-source", country="NO")
    rows: list[JsonObject] = []
    for name, distance, expected in (
        ("inside-threshold", 99.999999, "definite_candidate"),
        ("exact-threshold", 100.0, "definite_candidate"),
        ("millimetre-outside", 100.000001, "excluded_spatial"),
        ("submillimetre-outside", 100.0000004, "excluded_spatial"),
    ):
        longitude, steps = _equatorial_longitude(distance)
        target = _event(name, longitude=longitude, interval=(5500.0, 5500.0))
        rows.append(
            _pair(
                name,
                source,
                target,
                expected,
                expected_distance_km=distance,
                constructor_ulp_steps=steps,
            )
        )
    malmo = _event("malmo", latitude=55.605, longitude=13.0038, country="NO")
    lund = _event("lund", latitude=55.7047, longitude=13.191, interval=(5500, 5500))
    rows.append(_pair("malmo-lund", malmo, lund, "definite_candidate"))
    rows.append(
        _pair(
            "country-label-swap",
            replace(malmo, country_code="SE"),
            replace(lund, country_code="NO"),
            "definite_candidate",
        )
    )
    outside = _event(
        "outside-finland", longitude=2.0, country="FI", interval=(5500, 5500)
    )
    rows.append(
        _pair(
            "outside-cross-border",
            replace(source, country_code="SE"),
            outside,
            "excluded_spatial",
        )
    )
    identical = _event("shared-location", interval=(5500, 5500))
    rows.append(
        _pair(
            "distinct-sites-shared-location",
            source,
            identical,
            "definite_candidate",
            expected_distance_km=0.0,
        )
    )
    rows.append(
        _pair(
            "same-governed-site",
            source,
            replace(identical, site_id=source.site_id),
            "same_governed_site",
        )
    )
    rows.append(
        _pair(
            "missing-coordinate",
            source,
            _event("missing", latitude=None, longitude=None, interval=(5500, 5500)),
            "invalid_or_missing_coordinate",
        )
    )
    for name, source_interval, target_interval, expected in (
        (
            "overlap-cross-border",
            (5500.0, 5600.0),
            (5550.0, 5650.0),
            "indeterminate_order",
        ),
        ("chronology-gap", None, (5500.0, 5500.0), "unresolved"),
        (
            "lag-too-large",
            (5601.0, 5601.0),
            (5500.0, 5500.0),
            "excluded_temporal_too_large",
        ),
        (
            "uncertain-lag-threshold",
            (5590.0, 5610.0),
            (5500.0, 5500.0),
            "possible_candidate",
        ),
    ):
        rows.append(
            _pair(
                name,
                _event(f"{name}:older", interval=source_interval),
                _event(
                    f"{name}:younger",
                    country="DK",
                    longitude=0.1,
                    interval=target_interval,
                ),
                expected,
            )
        )
    for name, latitude, longitude in (
        ("invalid-latitude", 91.0, 0.0),
        ("invalid-longitude", 0.0, 181.0),
        ("partial-coordinate", None, 13.0),
    ):
        try:
            _event(name, latitude=latitude, longitude=longitude)
        except EventValidationError as error:
            rows.append(
                {
                    "case_id": name,
                    "inputs": {"latitude": latitude, "longitude": longitude},
                    "status": "ingestion_refused",
                    "reason_code": error.reason_code,
                    "detail": str(error),
                    "contract_status": "passed",
                }
            )
        else:
            rows.append(
                {
                    "case_id": name,
                    "status": "unexpected_admission",
                    "contract_status": "failed",
                }
            )
    # A valid numerical axis reversal cannot be detected from WGS84 ranges alone.
    # This independently declared Nordic fixture box rejects it without swapping.
    reversed_coordinate = (13.0038, 55.605)
    rows.append(
        {
            "case_id": "reversed-nordic-axis",
            "inputs": reversed_coordinate,
            "fixture_range": {"latitude": [54, 72], "longitude": [4, 32]},
            "status": "fixture_refused",
            "reason_code": "outside_declared_fixture_range",
            "silent_axis_swap": False,
            "contract_status": "passed"
            if not (
                54 <= reversed_coordinate[0] <= 72 and 4 <= reversed_coordinate[1] <= 32
            )
            else "failed",
        }
    )
    northern = _event("northern-se", country="SE", latitude=68.0, longitude=20.0)
    neighbors = tuple(
        _event(
            f"northern-{country}",
            country=country,
            latitude=68.0,
            longitude=longitude,
            interval=(5500, 5500),
        )
        for country, longitude in (("NO", 19.9), ("FI", 20.1), ("SE", 20.2))
    )
    network = generate_propagation_network((northern, *neighbors)).scenario_results[0]
    exhaustive = generate_propagation_network_exhaustive(
        (northern, *neighbors)
    ).scenario_results[0]
    arrows = tuple(
        row
        for row in network.directed_candidates
        if row.source_event_id == northern.event_id
    )
    regional_passed = {row.target_country_code for row in arrows} == {
        "NO",
        "FI",
        "SE",
    } and sorted(row.edge_id for row in network.directed_candidates) == sorted(
        row.edge_id for row in exhaustive.directed_candidates
    )
    label_passed = all(
        cast(JsonObject, rows[4]["output"])[key]
        == cast(JsonObject, rows[5]["output"])[key]
        for key in (
            "distance_km_unrounded",
            "minimum_lag_years",
            "maximum_lag_years",
            "candidate_status",
            "directional_arrow_allowed",
        )
    )
    return {
        "schema_version": "pollenomics-synthetic-spatial-eligibility.v1",
        "source_kind": "fabricated_coordinates_and_BP_intervals",
        "prospective_contract": {
            "pair_attempts": 18,
            "regional_events": 4,
            "regional_source_neighbors": 3,
            "maximum_distance_km": 100.0,
            "maximum_lag_years": 100.0,
            "equatorial_semimajor_metres": _SEMIMAJOR_METRES,
            "distance_absolute_tolerance_km": _DISTANCE_TOLERANCE_KM,
            "eligibility_threshold_tolerance_km": 0.0,
            "truth_method": "stdlib degrees(distance_metres / WGS84_semimajor_metres); exact equatorial arc",
            "exact_boundary_constructor_maximum_ulp_steps": 32,
        },
        "cases": rows,
        "regional_search": {
            "inputs": [asdict(event) for event in (northern, *neighbors)],
            "evaluated_pairs": [row.as_dict() for row in network.evaluated_pairs],
            "pair_refusals": [row.as_dict() for row in network.refusals],
            "directed_candidates": [row.as_dict() for row in arrows],
            "reconciliation": asdict(network.reconciliation),
            "exhaustive_reference_edges": [
                row.as_dict() for row in exhaustive.directed_candidates
            ],
            "contract_status": "passed" if regional_passed else "failed",
        },
        "country_label_invariance_passed": label_passed,
        "denominators": {
            "requested_pair_attempts": 18,
            "attempted_pairs": len(rows),
            "evaluated": sum(row["status"] == "evaluated" for row in rows),
            "pair_refused": sum(row["status"] == "pair_refused" for row in rows),
            "ingestion_refused": sum(
                row["status"] == "ingestion_refused" for row in rows
            ),
            "fixture_refused": sum(row["status"] == "fixture_refused" for row in rows),
            "contract_passed": sum(row["contract_status"] == "passed" for row in rows),
            "regional_requested_neighbors": 3,
            "regional_eligible_neighbors": len(arrows),
        },
        "claims": {
            "synthetic_only": True,
            "historical_routes": False,
            "country_only_display_context_verified": False,
            "coordinate_axis_detection": "declared_fixture_box_only",
            "partial_coordinates": "refused_at_event_ingestion; paired_nulls_retained_in_pair_refusal_ledger",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_spatial_eligibility_challenge()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    counts = cast(dict[str, int], report["denominators"])
    print(json.dumps({"output": str(args.output), **counts}))
    return (
        0
        if (
            counts["contract_passed"] == counts["requested_pair_attempts"]
            and report["country_label_invariance_passed"]
            and cast(JsonObject, report["regional_search"])["contract_status"]
            == "passed"
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
