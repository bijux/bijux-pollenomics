"""Derived explanations of governed candidate classification branch order.

These are presentation fields, not recorded execution telemetry. Canonical
candidate records and their source event identities remain authoritative.
"""

from __future__ import annotations

from ..candidates import CandidatePropagationScenario, classify_candidate_propagation
from ..network import PhenomenonEvent, PropagationCandidate
from ..network.pairs import _pair_refusal_reason


def candidate_relation_details(
    row: PropagationCandidate,
    source: PhenomenonEvent,
    target: PhenomenonEvent,
    scenario: CandidatePropagationScenario,
) -> dict[str, object]:
    """Explain the reached checks without assigning outcomes to skipped checks.

    The network projection separately authenticates the complete event manifest.
    Here exact endpoint identities and the stored decision must agree with the
    current pair eligibility and pure classification contracts. No distance or
    scientific eligibility is newly estimated by this presentation.
    """
    if _pair_refusal_reason(source, target) is not None or (
        row.source_event_id,
        row.target_event_id,
        row.source_site_id,
        row.target_site_id,
        row.source_country_code,
        row.target_country_code,
        row.resolution,
        row.feature_key,
        row.scenario_id,
        row.threshold_profile_id,
        row.temporal_contract_version,
        row.classification_contract_version,
        row.build_id,
    ) != (
        source.event_id,
        target.event_id,
        source.site_id,
        target.site_id,
        source.country_code,
        target.country_code,
        source.resolution,
        source.feature_key,
        scenario.scenario_id,
        source.threshold_profile_id,
        source.temporal_contract_version,
        source.classification_contract_version,
        source.build_id,
    ):
        raise ValueError("relation explanation conflicts with governed endpoints")
    decision = classify_candidate_propagation(
        distance_km_unrounded=row.distance_km_unrounded,
        source_interval=source.interval,
        target_interval=target.interval,
        scenario=scenario,
    )
    if any(
        getattr(row, name) != getattr(decision, name)
        for name in (
            "candidate_status",
            "reason_code",
            "minimum_lag_years",
            "maximum_lag_years",
            "directional_arrow_allowed",
        )
    ):
        raise ValueError("relation explanation conflicts with governed decision")

    checks: list[dict[str, object]] = []
    reached = True

    def append(
        predicate_id: str,
        label: str,
        observed: float | None,
        threshold: float | None,
        status: str,
    ) -> None:
        nonlocal reached
        checks.append(
            {
                "predicate_id": predicate_id,
                "label": label,
                "status": status if reached else "not_evaluated",
                "observed": observed if reached else None,
                "threshold": threshold,
            }
        )
        if status != "pass":
            reached = False

    append(
        "spatial_threshold",
        "Distance is within the scenario maximum (km)",
        row.distance_km_unrounded,
        scenario.maximum_distance_km,
        "refuse" if row.candidate_status == "excluded_spatial" else "pass",
    )
    append(
        "chronology_available",
        "Comparable source and target age intervals are available",
        None,
        None,
        "unavailable" if row.minimum_lag_years is None else "pass",
    )
    append(
        "positive_lag_possible",
        "Maximum supported directional lag is greater than zero (years)",
        row.maximum_lag_years,
        0,
        "refuse" if row.candidate_status == "excluded_temporal_nonpositive" else "pass",
    )
    append(
        "positive_lag_certain",
        "Minimum supported directional lag is greater than zero (years)",
        row.minimum_lag_years,
        0,
        "qualify" if row.candidate_status == "indeterminate_order" else "pass",
    )
    append(
        "lag_within_limit_possible",
        "Minimum supported lag is within the scenario maximum (years)",
        row.minimum_lag_years,
        scenario.maximum_lag_years,
        "refuse" if row.candidate_status == "excluded_temporal_too_large" else "pass",
    )
    append(
        "lag_within_limit_certain",
        "Maximum supported lag is within the scenario maximum (years)",
        row.maximum_lag_years,
        scenario.maximum_lag_years,
        "qualify" if row.candidate_status == "possible_candidate" else "pass",
    )
    return {
        "basis": "derived_governed_evaluator_branch_explanation",
        "scenario_id": scenario.scenario_id,
        "maximum_distance_km": scenario.maximum_distance_km,
        "maximum_lag_years": scenario.maximum_lag_years,
        "predicates": checks,
    }
