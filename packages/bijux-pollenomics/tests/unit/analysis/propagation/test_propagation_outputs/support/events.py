"""Scientific event fixtures for propagation output tests."""

from __future__ import annotations

from bijux_pollenomics.analysis.propagation.network import PhenomenonEvent


def event(
    name: str,
    *,
    country_code: str = "SE",
    latitude: float = 55.605,
    longitude: float = 13.0038,
    age_bp: int = 5600,
) -> PhenomenonEvent:
    """Build one source-traceable pollen-context event."""
    return PhenomenonEvent(
        source_family="source-native-fixture",
        evidence_domain="pollen_context",
        source_snapshot_id="snapshot-1",
        source_record_id=f"record-{name}",
        site_id=f"site-{name}",
        observation_ids=(f"observation-{name}",),
        country_code=country_code,
        latitude=latitude,
        longitude=longitude,
        coordinate_quality="reported",
        event_type="reported_positive_observation",
        resolution="taxon",
        feature_key="taxon:triticum_aestivum",
        chronology_claim_id=f"chronology-{name}",
        younger_bp=age_bp,
        older_bp=age_bp,
        comparability_status="comparable",
        threshold_profile_id="reported_positive_v1",
        classification_contract_version="classification.v1",
        provenance_record_id=f"provenance-{name}",
        input_digest=f"input-{name}",
        config_digest="event-config-v1",
        producer_version="fixture-producer.v1",
        build_id="build-1",
        measurement_semantics_id="presence.v1",
        evidence_method_id="source-native-method",
        method_compatibility_key="pollen-presence.v1",
        accepted_taxon_concept_id="accepted-taxon-1",
        taxonomic_qualifier="accepted",
    )
