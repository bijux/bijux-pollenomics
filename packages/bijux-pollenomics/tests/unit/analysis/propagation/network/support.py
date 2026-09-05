"""Shared builders for propagation-network tests."""

from __future__ import annotations

from bijux_pollenomics.analysis.propagation.network import (
    PhenomenonEvent,
    PropagationNetworkResult,
    PropagationScenarioResult,
)


def event(
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
    """Build one valid source-native event with explicit override points."""
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


def scenario(
    result: PropagationNetworkResult, scenario_id: str
) -> PropagationScenarioResult:
    """Select a scenario result by its governed identity."""
    return next(
        row
        for row in result.scenario_results
        if row.scenario.scenario_id == scenario_id
    )
