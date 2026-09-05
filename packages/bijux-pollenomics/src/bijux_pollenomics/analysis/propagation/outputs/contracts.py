"""Normative propagation contract and scientific-claim validation."""

from __future__ import annotations
from pathlib import Path
from bijux_pollenomics.analysis.propagation.network import (
    COUNTRY_CODES,
    EVIDENCE_DOMAINS,
)
from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
)

from .codec import _refuse, _sha256
from .inputs import _path_has_symlink_component, _read_identity_file
from .models import PropagationOutputRefusalError, _SCIENTIFIC_CLAIM_BOOLEAN_FIELDS
from .producer import _required_contract_section


def _validate_propagation_contract_identity(
    contract_path: Path,
    *,
    schema_root: Path,
    propagation_contract_version: str,
    propagation_contract_digest: str,
) -> None:
    governed_contract = schema_root / "propagation-model.v1.yaml"
    if (
        not schema_root.is_absolute()
        or _path_has_symlink_component(schema_root)
        or not schema_root.is_dir()
        or not contract_path.is_absolute()
        or contract_path.name != "propagation-model.v1.yaml"
        or contract_path != governed_contract
        or _path_has_symlink_component(contract_path)
        or not contract_path.is_file()
        or contract_path.resolve(strict=True) != governed_contract.resolve(strict=True)
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract must be the governed file in schema_root",
        )
    contract_bytes = _read_identity_file(
        contract_path,
        parent=schema_root,
        reason_code="invalid_propagation_identity",
    )
    if _sha256(contract_bytes) != propagation_contract_digest:
        _refuse(
            "invalid_propagation_identity",
            "propagation_contract_digest does not match contract bytes",
        )
    try:
        import yaml
    except ImportError as error:
        raise PropagationOutputRefusalError(
            "invalid_propagation_identity",
            "PyYAML is required to verify the propagation contract",
        ) from error
    try:
        contract = yaml.safe_load(contract_bytes)
    except (ValueError, yaml.YAMLError) as error:
        raise PropagationOutputRefusalError(
            "invalid_propagation_identity",
            "propagation contract cannot be parsed",
        ) from error
    if not isinstance(contract, dict):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract must be a mapping",
        )
    sensitivity = contract.get("sensitivity_analysis")
    event_contract = contract.get("event_contract")
    geography = contract.get("geographic_scope")
    default = contract.get("default_scenario")
    scientific_claim = contract.get("scientific_claim")
    spatial_calculation = contract.get("spatial_calculation")
    candidate_logic = contract.get("candidate_logic")
    output_edge_contract = contract.get("output_edge_contract")
    map_contract = contract.get("map_contract")
    denominators = contract.get("denominators")
    sensitivity = _required_contract_section(sensitivity)
    event_contract = _required_contract_section(event_contract)
    geography = _required_contract_section(geography)
    default = _required_contract_section(default)
    scientific_claim_section = _required_contract_section(scientific_claim)
    spatial_calculation = _required_contract_section(spatial_calculation)
    candidate_logic = _required_contract_section(candidate_logic)
    output_edge_contract = _required_contract_section(output_edge_contract)
    map_contract = _required_contract_section(map_contract)
    denominators = _required_contract_section(denominators)
    spatial = default.get("spatial")
    temporal = default.get("temporal")
    required_metrics = sensitivity.get("required_metrics")
    governed_metrics = {
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
    }
    expected_country_pairs = [
        f"{source}-{target}" for source in COUNTRY_CODES for target in COUNTRY_CODES
    ]
    scientific_boolean_fields = {
        key
        for key, value in scientific_claim_section.items()
        if isinstance(value, bool)
    }
    if contract.get("contract_id") != "bijux-pollenomics.propagation-model":
        _refuse(
            "invalid_propagation_identity",
            "propagation contract does not match governed scientific semantics",
        )
    if contract.get("contract_version") != propagation_contract_version:
        _refuse(
            "invalid_propagation_identity",
            "propagation contract does not match governed scientific semantics",
        )
    if contract.get("status") != "normative":
        _refuse(
            "invalid_propagation_identity",
            "propagation contract does not match governed scientific semantics",
        )
    if scientific_claim_section.get("output_class") != "candidate_propagation":
        _refuse(
            "invalid_propagation_identity",
            "propagation contract semantics do not match the implementation",
        )
    if scientific_claim_section.get("preferred_label") != "candidate propagation link":
        _refuse(
            "invalid_propagation_identity",
            "propagation contract semantics do not match the implementation",
        )
    if (
        scientific_claim_section.get("alternate_label")
        != "spatiotemporal succession consistent with spread"
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract semantics do not match the implementation",
        )
    if scientific_claim_section.get("note") != (
        "An edge is a versioned exploratory relation between evidence events, "
        "not a physical route or proof of a mechanism."
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract semantics do not match the implementation",
        )
    if (
        scientific_boolean_fields != set(_SCIENTIFIC_CLAIM_BOOLEAN_FIELDS)
        or any(
            scientific_claim_section[field] is not False
            for field in scientific_boolean_fields
        )
        or event_contract.get("allowed_evidence_domains") != list(EVIDENCE_DOMAINS)
        or event_contract.get("pollen_candidate_domain") != "pollen_context"
        or event_contract.get("non_pollen_domain_posture")
        != "retain as accounted input evidence but exclude from pollen candidate generation"
        or geography.get("countries") != list(COUNTRY_CODES)
        or geography.get("country_boundaries_partition_candidate_generation")
        is not False
        or geography.get("domestic_and_cross_border_rules_identical") is not True
        or geography.get("required_ordered_country_pair_reporting")
        != expected_country_pairs
        or default.get("scenario_id") != DEFAULT_PROPAGATION_SCENARIO.scenario_id
        or not isinstance(spatial, dict)
        or spatial.get("maximum_distance_km")
        != DEFAULT_PROPAGATION_SCENARIO.maximum_distance_km
        or spatial.get("maximum_is_inclusive") is not True
        or spatial.get("is_diameter") is not False
        or not isinstance(temporal, dict)
        or temporal.get("minimum_positive_lag_years") != 0.0
        or temporal.get("minimum_is_exclusive") is not True
        or temporal.get("maximum_lag_years")
        != DEFAULT_PROPAGATION_SCENARIO.maximum_lag_years
        or temporal.get("maximum_is_inclusive") is not True
        or temporal.get("direction") != "older_event_to_younger_event"
        or default.get("geometry") != "rectangular_threshold"
        or default.get("rate_or_velocity_model") is not False
        or default.get("biological_law") is not False
        or spatial_calculation.get("coordinate_reference_system") != "EPSG:4326"
        or spatial_calculation.get("algorithm") != "WGS84 inverse geodesic"
        or spatial_calculation.get("ellipsoid") != "WGS84"
        or spatial_calculation.get("eligibility_distance_field")
        != "distance_km_unrounded"
        or spatial_calculation.get("eligibility_value_rounding_allowed") is not False
        or spatial_calculation.get("eligibility_uses_unrounded_value") is not True
        or spatial_calculation.get("silent_algorithm_fallback_allowed") is not False
        or candidate_logic.get("no_midpoint_shortcut") is not True
        or candidate_logic.get("same_point_age_directional") is not False
        or output_edge_contract.get("route_interpretation_allowed") is not False
        or output_edge_contract.get("map_geometry")
        != "straight geodesic endpoint connection for visualization only"
        or map_contract.get("merge_selected_features") is not False
        or map_contract.get("color_alone_is_sufficient") is not False
        or denominators.get("statuses_are_mutually_exclusive") is not True
        or denominators.get("all_evaluated_pairs_must_be_accounted_for") is not True
        or denominators.get("required_partitions")
        != [
            "country_code",
            "ordered_country_pair",
            "source_family",
            "evidence_domain",
            "resolution",
            "feature_key",
            "candidate_status",
            "scenario_id",
            "threshold_profile_id",
        ]
        or sensitivity.get("distance_km_values") != [25.0, 50.0, 100.0, 200.0]
        or sensitivity.get("lag_year_values") != [50.0, 100.0, 200.0, 500.0]
        or not isinstance(required_metrics, list)
        or not all(isinstance(metric, str) for metric in required_metrics)
        or set(required_metrics) != governed_metrics
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract semantics do not match the implementation",
        )
