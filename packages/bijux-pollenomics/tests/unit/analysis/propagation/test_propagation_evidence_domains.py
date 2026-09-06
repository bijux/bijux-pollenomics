from __future__ import annotations

from dataclasses import replace

import pytest
from bijux_pollenomics.analysis.propagation.network import (
    EVIDENCE_DOMAINS,
    EventValidationError,
    PhenomenonEvent,
    PropagationPairRefusal,
    evaluate_propagation_pair,
    generate_propagation_network,
    generate_propagation_network_exhaustive,
)


def _event(
    name: str,
    *,
    evidence_domain: str = "pollen_context",
    age_bp: int = 5600,
    longitude: float = 13.0038,
) -> PhenomenonEvent:
    return PhenomenonEvent(
        source_family="source-native-fixture",
        evidence_domain=evidence_domain,
        source_snapshot_id="snapshot-1",
        source_record_id=f"record-{name}",
        site_id=f"site-{name}",
        observation_ids=(f"observation-{name}",),
        country_code="SE",
        latitude=55.605,
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
        method_compatibility_key="presence-method.v1",
        accepted_taxon_concept_id="accepted-taxon-1",
        taxonomic_qualifier="accepted",
    )


def test_evidence_domain_is_required_and_governed() -> None:
    pollen = _event("pollen")

    assert EVIDENCE_DOMAINS == (
        "pollen_context",
        "human_ancient_dna",
        "animal_ancient_dna",
    )
    assert pollen.as_dict()["evidence_domain"] == "pollen_context"
    with pytest.raises(EventValidationError) as unsupported:
        replace(pollen, evidence_domain="sedimentary_dna", event_id="")
    assert unsupported.value.reason_code == "unsupported_evidence_domain"
    with pytest.raises(EventValidationError) as missing:
        replace(pollen, evidence_domain="", event_id="")
    assert missing.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize("evidence_domain", ("human_ancient_dna", "animal_ancient_dna"))
def test_non_pollen_domains_cannot_use_pollen_aggregate_resolutions(
    evidence_domain: str,
) -> None:
    event = _event("adna", evidence_domain=evidence_domain)

    with pytest.raises(EventValidationError) as error:
        replace(
            event,
            resolution="whole_pollen",
            feature_key="whole:all_pollen",
            accepted_taxon_concept_id=None,
            taxonomic_qualifier=None,
            event_id="",
        )
    assert error.value.reason_code == "incompatible_evidence_domain_resolution"


def test_domain_is_part_of_identity_and_pair_compatibility() -> None:
    pollen = _event("shared")
    human = replace(pollen, evidence_domain="human_ancient_dna", event_id="")
    animal = replace(pollen, evidence_domain="animal_ancient_dna", event_id="")

    assert len({pollen.event_id, human.event_id, animal.event_id}) == 3
    mixed = evaluate_propagation_pair(pollen, human)
    non_pollen = evaluate_propagation_pair(human, animal)
    same_non_pollen = evaluate_propagation_pair(
        human,
        replace(human, source_record_id="other", site_id="other", event_id=""),
    )
    assert isinstance(mixed, PropagationPairRefusal)
    assert mixed.reason_code == "incompatible_evidence_domain"
    assert isinstance(non_pollen, PropagationPairRefusal)
    assert non_pollen.reason_code == "incompatible_evidence_domain"
    assert isinstance(same_non_pollen, PropagationPairRefusal)
    assert (
        same_non_pollen.reason_code == "evidence_domain_not_pollen_propagation_eligible"
    )


def test_network_partitions_domains_before_pollen_pair_accounting() -> None:
    pollen_source = _event("pollen-source", age_bp=5600)
    pollen_target = _event("pollen-target", age_bp=5500, longitude=13.01)
    human = _event("human", evidence_domain="human_ancient_dna", age_bp=5600)
    animal = _event(
        "animal",
        evidence_domain="animal_ancient_dna",
        age_bp=5500,
        longitude=13.01,
    )
    events = (human, pollen_target, animal, pollen_source)

    indexed = generate_propagation_network(events)
    exhaustive = generate_propagation_network_exhaustive(tuple(reversed(events)))
    pollen_only = generate_propagation_network((pollen_source, pollen_target))
    assert indexed.as_dict() == exhaustive.as_dict()
    assert indexed.event_manifest_digest == pollen_only.event_manifest_digest
    assert (
        indexed.scenario_results[0].evaluated_pairs
        == pollen_only.scenario_results[0].evaluated_pairs
    )
    assert indexed.scenario_results[0].refusals == ()
    assert {event.event_id for event in indexed.events} == {
        pollen_source.event_id,
        pollen_target.event_id,
    }
    assert {event.evidence_domain for event in indexed.excluded_non_pollen_events} == {
        "human_ancient_dna",
        "animal_ancient_dna",
    }

    scenario = indexed.scenario_results[0]
    reconciliation = scenario.reconciliation
    assert reconciliation.input_event_count == 4
    assert reconciliation.eligible_event_count == 2
    assert reconciliation.excluded_non_pollen_event_count == 2
    assert dict(reconciliation.evidence_domain_event_counts) == {
        "pollen_context": 2,
        "human_ancient_dna": 1,
        "animal_ancient_dna": 1,
    }
    assert reconciliation.evaluated_pair_count == 2
    assert reconciliation.refused_pair_count == 0
    pollen_ids = {pollen_source.event_id, pollen_target.event_id}
    assert {
        event_id
        for row in scenario.evaluated_pairs
        for event_id in (row.source_event_id, row.target_event_id)
    } == pollen_ids


def test_non_pollen_only_network_has_exact_zero_pollen_denominators() -> None:
    network = generate_propagation_network(
        (
            _event("human", evidence_domain="human_ancient_dna"),
            _event("animal", evidence_domain="animal_ancient_dna"),
        )
    )
    scenario = network.scenario_results[0]

    assert network.events == ()
    assert len(network.excluded_non_pollen_events) == 2
    assert scenario.evaluated_pairs == ()
    assert scenario.refusals == ()
    assert scenario.reconciliation.input_event_count == 2
    assert scenario.reconciliation.eligible_event_count == 0
    assert scenario.reconciliation.excluded_non_pollen_event_count == 2
    assert dict(scenario.reconciliation.evidence_domain_event_counts) == {
        "pollen_context": 0,
        "human_ancient_dna": 1,
        "animal_ancient_dna": 1,
    }
