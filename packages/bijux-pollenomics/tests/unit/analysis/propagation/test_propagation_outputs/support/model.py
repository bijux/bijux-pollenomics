"""Normative propagation contract fixture used by output tests."""

from __future__ import annotations

import hashlib
import json

PROPAGATION_CONTRACT_VERSION = "1.0.0"

MODEL = {
    "schema_version": "1.0.0",
    "contract_id": "bijux-pollenomics.propagation-model",
    "contract_version": PROPAGATION_CONTRACT_VERSION,
    "status": "normative",
    "scientific_claim": {
        "output_class": "candidate_propagation",
        "preferred_label": "candidate propagation link",
        "alternate_label": "spatiotemporal succession consistent with spread",
        "establishes_route": False,
        "establishes_causation": False,
        "establishes_human_migration": False,
        "establishes_plant_migration": False,
        "establishes_local_cultivation": False,
        "note": (
            "An edge is a versioned exploratory relation between evidence events, "
            "not a physical route or proof of a mechanism."
        ),
    },
    "geographic_scope": {
        "countries": ["SE", "NO", "FI", "DK"],
        "country_boundaries_partition_candidate_generation": False,
        "domestic_and_cross_border_rules_identical": True,
        "required_ordered_country_pair_reporting": [
            f"{source}-{target}"
            for source in ("SE", "NO", "FI", "DK")
            for target in ("SE", "NO", "FI", "DK")
        ],
    },
    "default_scenario": {
        "scenario_id": "rectangular_100km_100yr_v1",
        "spatial": {
            "maximum_distance_km": 100.0,
            "maximum_is_inclusive": True,
            "is_diameter": False,
        },
        "temporal": {
            "minimum_positive_lag_years": 0.0,
            "minimum_is_exclusive": True,
            "maximum_lag_years": 100.0,
            "maximum_is_inclusive": True,
            "direction": "older_event_to_younger_event",
        },
        "geometry": "rectangular_threshold",
        "rate_or_velocity_model": False,
        "biological_law": False,
    },
    "spatial_calculation": {
        "coordinate_reference_system": "EPSG:4326",
        "algorithm": "WGS84 inverse geodesic",
        "ellipsoid": "WGS84",
        "eligibility_distance_field": "distance_km_unrounded",
        "eligibility_value_rounding_allowed": False,
        "eligibility_uses_unrounded_value": True,
        "silent_algorithm_fallback_allowed": False,
    },
    "event_contract": {
        "allowed_evidence_domains": [
            "pollen_context",
            "human_ancient_dna",
            "animal_ancient_dna",
        ],
        "pollen_candidate_domain": "pollen_context",
        "non_pollen_domain_posture": (
            "retain as accounted input evidence but exclude from pollen candidate "
            "generation"
        ),
    },
    "candidate_logic": {
        "no_midpoint_shortcut": True,
        "same_point_age_directional": False,
    },
    "output_edge_contract": {
        "map_geometry": (
            "straight geodesic endpoint connection for visualization only"
        ),
        "route_interpretation_allowed": False,
    },
    "sensitivity_analysis": {
        "distance_km_values": [25.0, 50.0, 100.0, 200.0],
        "lag_year_values": [50.0, 100.0, 200.0, 500.0],
        "required_metrics": [
            "eligible_event_count",
            "evaluated_pair_count",
            "definite_candidate_count",
            "possible_candidate_count",
            "indeterminate_order_count",
            "unresolved_pair_count",
            "excluded_spatial_count",
            "excluded_temporal_count",
            "connected_component_count",
            "country_pair_counts",
            "feature_stability_across_scenarios",
        ],
    },
    "map_contract": {
        "merge_selected_features": False,
        "color_alone_is_sufficient": False,
    },
    "denominators": {
        "statuses_are_mutually_exclusive": True,
        "all_evaluated_pairs_must_be_accounted_for": True,
        "required_partitions": [
            "country_code",
            "ordered_country_pair",
            "source_family",
            "evidence_domain",
            "resolution",
            "feature_key",
            "candidate_status",
            "scenario_id",
            "threshold_profile_id",
        ],
    },
}

MODEL_BYTES = json.dumps(MODEL, sort_keys=True).encode()
PROPAGATION_CONTRACT_DIGEST = hashlib.sha256(MODEL_BYTES).hexdigest()
