"""Source-authenticated SEAD LRA prerequisite accounting without admission."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
)

from ..models import canonical_bytes
from .chronology import ChronologyAccounting
from .observations import sead_accounting
from .reading import read_sead_evidence

_COUNTRIES = ("DK", "FI", "NO", "SE", "UNASSIGNED")
_SCIENTIFIC_BLOCKERS = (
    "source_pollen_identity_not_accepted",
    "lra_chronology_decision_not_supplied",
    "parameter_binding_not_supplied",
    "basin_geometry_not_supplied",
    "known_pollen_denominator_not_supplied",
    "site_independence_not_established",
)


@dataclass(frozen=True)
class SeadLraFrontier:
    """Immutable prerequisite projection; never an executable LRA request."""

    canonical_json: bytes
    result_digest: str

    def as_dict(self) -> dict[str, Any]:
        """Return an independent copy of the canonical projection."""
        return cast(dict[str, Any], json.loads(self.canonical_json))


@dataclass(frozen=True)
class _PhysicalSampleAccounting:
    source_links: int
    source_samples: int
    source_multiplicity: dict[str, int]
    selected_links: int
    selected_samples: int
    selected_multiplicity: dict[str, int]
    selected_country_links: dict[str, int]
    selected_country_samples: dict[str, int]
    prerequisite_samples: int
    prerequisite_country_samples: dict[str, int]


def _physical_sample_accounting(
    entities: Sequence[tuple[str, str, int | None]],
    selected: set[str],
    prerequisite_entities: set[str],
) -> _PhysicalSampleAccounting:
    """Reconcile entity links without promoting an entity result to a sample result."""
    source: dict[int, set[str]] = {}
    selected_samples: dict[int, set[str]] = {}
    sample_countries: dict[int, set[str]] = {}
    selected_country_links: Counter[str] = Counter()
    for identity, country, sample_id in entities:
        if country not in _COUNTRIES:
            raise ValueError("SEAD entity country is outside the governed scope")
        if sample_id is None:
            continue
        source.setdefault(sample_id, set()).add(identity)
        sample_countries.setdefault(sample_id, set()).add(country)
        if identity in selected:
            selected_samples.setdefault(sample_id, set()).add(identity)
            selected_country_links[country] += 1
    conflicts = sorted(
        sample_id
        for sample_id, countries in sample_countries.items()
        if len(countries) != 1
    )
    if conflicts:
        raise ValueError(
            "SEAD physical sample has analysis entities in multiple countries: "
            f"{conflicts[0]}"
        )
    selected_country_samples: Counter[str] = Counter()
    prerequisite_country_samples: Counter[str] = Counter()
    prerequisite_samples: set[int] = set()
    for sample_id, identities in selected_samples.items():
        country = next(iter(sample_countries[sample_id]))
        selected_country_samples[country] += 1
        if identities.intersection(prerequisite_entities):
            prerequisite_samples.add(sample_id)
            prerequisite_country_samples[country] += 1

    def multiplicity(rows: dict[int, set[str]]) -> dict[str, int]:
        return dict(
            sorted(
                Counter(str(len(identities)) for identities in rows.values()).items()
            )
        )

    return _PhysicalSampleAccounting(
        source_links=sum(len(identities) for identities in source.values()),
        source_samples=len(source),
        source_multiplicity=multiplicity(source),
        selected_links=sum(len(identities) for identities in selected_samples.values()),
        selected_samples=len(selected_samples),
        selected_multiplicity=multiplicity(selected_samples),
        selected_country_links=dict(selected_country_links),
        selected_country_samples=dict(selected_country_samples),
        prerequisite_samples=len(prerequisite_samples),
        prerequisite_country_samples=dict(prerequisite_country_samples),
    )


def _source_observation_flags(record: dict[str, Any]) -> tuple[bool, bool, bool]:
    """Use observed relations only; a method lookup row is never sufficient."""
    return (
        record["source_count_compatibility"] == "source_absolute_count_candidate",
        record["source_pollen_method_candidate"] is True,
        record["source_taxon_relation"] is not None,
    )


def _selected_entities(
    available: set[str], selected_entity_ids: Sequence[str] | None
) -> tuple[list[str], str]:
    if selected_entity_ids is None:
        return sorted(available), "all_source_entities"
    selected = list(selected_entity_ids)
    if any(
        not isinstance(value, str) or not value or value != value.strip()
        for value in selected
    ):
        raise ValueError(
            "SEAD selected entity identities must be exact nonempty strings"
        )
    if len(selected) != len(set(selected)):
        raise ValueError("SEAD selected entity identities must not be duplicated")
    unknown = sorted(set(selected) - available)
    if unknown:
        raise ValueError(f"Unknown SEAD analysis entity identity: {unknown[0]}")
    return sorted(selected), "explicit_entity_ids"


def assess_sead_lra_frontier(
    *,
    raw_root: Path,
    normalized_root: Path,
    expected_identity: SeadAdmissionExpectedIdentity,
    selected_entity_ids: Sequence[str] | None = None,
) -> SeadLraFrontier:
    """Reconcile source prerequisites while refusing every scientific admission."""
    evidence = read_sead_evidence(
        raw_root, normalized_root, expected_identity=expected_identity
    )
    accounting = sead_accounting(evidence)
    available_entities = set(accounting.entities)
    selection, selection_mode = _selected_entities(
        available_entities, selected_entity_ids
    )
    selected = set(selection)
    entity_counts: dict[str, Counter[str]] = {
        identity: Counter() for identity in selection
    }
    country_counts: dict[str, Counter[str]] = {
        country: Counter() for country in _COUNTRIES
    }
    selected_value_types: Counter[str] = Counter()
    selected_value_presence: Counter[str] = Counter()
    source_observations = 0
    selected_observations = 0

    for source in evidence.rows("source_native_observations.json", "observations"):
        source_observations += 1
        record = accounting.observation(source)
        row = cast(dict[str, Any], record["source_observation"])
        entity_id = str(row["entity_relation_id"])
        if entity_id not in selected:
            continue
        selected_observations += 1
        counts = entity_counts[entity_id]
        counts["observations"] += 1
        count_candidate, observed_pollen_method, taxon_relation = (
            _source_observation_flags(record)
        )
        counts["source_absolute_count_candidate_observations"] += int(count_candidate)
        counts["observed_palynology_method_observations"] += int(observed_pollen_method)
        counts["taxon_related_observations"] += int(taxon_relation)
        counts["count_method_taxon_intersection_observations"] += int(
            count_candidate and observed_pollen_method and taxon_relation
        )
        selected_value_types[type(row["source_value"]).__name__] += 1
        selected_value_presence[str(record["source_value_presence"])] += 1

    chronology = ChronologyAccounting(accounting)
    source_claims = 0
    selected_claims = 0
    for source in evidence.rows("chronology_claims.json", "claims"):
        source_claims += 1
        record = chronology.claim(source)
        claim = cast(dict[str, Any], record["source_claim"])
        entity_id = str(claim["observation_relation_id"])
        if entity_id not in selected:
            continue
        selected_claims += 1
        counts = entity_counts[entity_id]
        counts["chronology_claims"] += 1
        owner_errors = {
            "source_analysis_entity_relation_missing",
            "source_chronology_owner_mismatch",
            "source_chronology_link_missing",
        }.intersection(cast(list[str], record["reason_codes"]))
        counts["owned_comparable_chronology_claims"] += int(
            claim["comparability_status"] == "comparable" and not owner_errors
        )

    entity_sample_rows: list[tuple[str, str, int | None]] = []
    prerequisite_entities: set[str] = set()
    reason_counts: Counter[str] = Counter()
    intersection_fields = (
        "entities_with_absolute_count_candidates",
        "entities_with_observed_palynology_method",
        "entities_with_taxon_relations",
        "entities_with_owned_comparable_chronology",
        "entities_with_count_method_taxon_intersection",
        "entities_with_count_method_taxon_and_owned_comparable_claim",
    )
    intersections: Counter[str] = Counter()
    for identity, source in sorted(accounting.entities.items()):
        chronology.entity(source)
        entity = source.payload()
        physical_sample = entity["physical_sample_id"]
        sample_id = physical_sample if type(physical_sample) is int else None
        country = str(entity["country_code"])
        entity_sample_rows.append((identity, country, sample_id))
        if identity not in selected:
            continue
        counts = entity_counts[identity]
        if country not in country_counts:
            raise ValueError("SEAD entity country is outside the governed scope")
        country_row = country_counts[country]
        country_row["analysis_entities"] += 1
        for field, value in counts.items():
            country_row[field] += value
        predicates = {
            "entities_with_absolute_count_candidates": counts[
                "source_absolute_count_candidate_observations"
            ]
            > 0,
            "entities_with_observed_palynology_method": counts[
                "observed_palynology_method_observations"
            ]
            > 0,
            "entities_with_taxon_relations": counts["taxon_related_observations"] > 0,
            "entities_with_owned_comparable_chronology": counts[
                "owned_comparable_chronology_claims"
            ]
            > 0,
            "entities_with_count_method_taxon_intersection": counts[
                "count_method_taxon_intersection_observations"
            ]
            > 0,
        }
        source_prerequisites = all(predicates.values())
        predicates["entities_with_count_method_taxon_and_owned_comparable_claim"] = (
            source_prerequisites
        )
        for field, present in predicates.items():
            intersections[field] += int(present)
            country_row[field] += int(present)
        if source_prerequisites:
            prerequisite_entities.add(identity)
        if not predicates["entities_with_absolute_count_candidates"]:
            reason_counts["no_source_absolute_count_candidate"] += 1
        if not predicates["entities_with_observed_palynology_method"]:
            reason_counts["no_observed_palynology_method_link"] += 1
        if not predicates["entities_with_taxon_relations"]:
            reason_counts["no_source_taxon_relation"] += 1
        if not predicates["entities_with_owned_comparable_chronology"]:
            reason_counts["no_owned_comparable_chronology_claim"] += 1

    source_document = evidence.document("source_native_observations.json")
    manifest = evidence.manifest()
    expected_observations = int(source_document["observation_count"])
    expected_claims = int(manifest["chronology_claim_count"])
    expected_entities = int(
        evidence.document("observation_relation_index.json")["entity_relation_count"]
    )
    if source_observations != expected_observations:
        raise ValueError("SEAD frontier does not cover the observation denominator")
    if source_claims != expected_claims:
        raise ValueError("SEAD frontier does not cover the chronology denominator")
    if len(accounting.entities) != expected_entities:
        raise ValueError("SEAD frontier does not cover the entity denominator")
    if selected_observations != sum(
        counts["observations"] for counts in entity_counts.values()
    ):
        raise ValueError("SEAD selected observations do not reconcile by entity")
    if selected_claims != sum(
        counts["chronology_claims"] for counts in entity_counts.values()
    ):
        raise ValueError("SEAD selected claims do not reconcile by entity")
    if sum(row["analysis_entities"] for row in country_counts.values()) != len(
        selection
    ):
        raise ValueError("SEAD selected entities do not reconcile by country")
    for field in intersection_fields:
        if sum(row[field] for row in country_counts.values()) != intersections[field]:
            raise ValueError(f"SEAD {field} does not reconcile by country")

    samples = _physical_sample_accounting(
        entity_sample_rows, selected, prerequisite_entities
    )
    for country, count in samples.selected_country_links.items():
        country_counts[country]["analysis_entity_physical_sample_links"] = count
    for country, count in samples.selected_country_samples.items():
        country_counts[country]["entity_linked_physical_samples"] = count
    for country, count in samples.prerequisite_country_samples.items():
        country_counts[country][
            "physical_samples_with_at_least_one_source_prerequisite_entity"
        ] = count
    if sum(samples.selected_country_samples.values()) != samples.selected_samples:
        raise ValueError("SEAD selected physical samples do not reconcile by country")
    if (
        sum(samples.prerequisite_country_samples.values())
        != samples.prerequisite_samples
    ):
        raise ValueError("SEAD prerequisite samples do not reconcile by country")

    source_physical_samples = int(
        source_document["source_table_counts"]["tbl_physical_samples"]
    )
    if samples.source_samples > source_physical_samples:
        raise ValueError("SEAD linked samples exceed the source denominator")
    all_selection_hash = hashlib.sha256(canonical_bytes(selection)).hexdigest()
    payload: dict[str, Any] = {
        "schema_version": "sead-lra-prerequisite-frontier.v1",
        "source_family": "sead",
        "source_run_id": manifest["source_run_id"],
        "normalized_build_id": manifest["build_id"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "selection": {
            "mode": selection_mode,
            "entity_ids": selection if selected_entity_ids is not None else [],
            "selected_entity_ids_sha256": all_selection_hash,
        },
        "source_denominators": {
            "analysis_entities": expected_entities,
            "observations": expected_observations,
            "chronology_claims": expected_claims,
            "source_physical_samples": source_physical_samples,
            "analysis_entity_physical_sample_links": samples.source_links,
            "entity_linked_physical_samples": samples.source_samples,
            "physical_sample_entity_multiplicity_counts": samples.source_multiplicity,
            "physical_samples_without_analysis_entity": (
                source_physical_samples - samples.source_samples
            ),
        },
        "selected_denominators": {
            "analysis_entities": len(selection),
            "observations": selected_observations,
            "chronology_claims": selected_claims,
            "analysis_entity_physical_sample_links": samples.selected_links,
            "entity_linked_physical_samples": samples.selected_samples,
            "physical_sample_entity_multiplicity_counts": samples.selected_multiplicity,
            **{field: intersections[field] for field in intersection_fields},
            "physical_samples_with_at_least_one_source_prerequisite_entity": (
                samples.prerequisite_samples
            ),
            "native_value_type_counts": dict(sorted(selected_value_types.items())),
            "source_value_presence_counts": dict(
                sorted(selected_value_presence.items())
            ),
        },
        "country_denominators": {
            country: {
                key: counts[key]
                for key in (
                    "analysis_entities",
                    "analysis_entity_physical_sample_links",
                    "entity_linked_physical_samples",
                    "physical_samples_with_at_least_one_source_prerequisite_entity",
                    "observations",
                    "chronology_claims",
                    "source_absolute_count_candidate_observations",
                    "observed_palynology_method_observations",
                    "taxon_related_observations",
                    "count_method_taxon_intersection_observations",
                    "owned_comparable_chronology_claims",
                    *intersection_fields,
                )
            }
            for country, counts in sorted(country_counts.items())
        },
        "entity_source_prerequisite_gap_counts": dict(sorted(reason_counts.items())),
        "selected_entity_refusal_reason_counts": {
            **dict(sorted(reason_counts.items())),
            **{reason: len(selection) for reason in _SCIENTIFIC_BLOCKERS},
        },
        "scientific_blockers": [
            {
                "reason_code": reason,
                "status": "not_supplied",
                "selected_analysis_entities": len(selection),
            }
            for reason in _SCIENTIFIC_BLOCKERS
        ],
        "palynology_lookup_present": any(
            row.get("method_id") == 14 for row in accounting.methods.values()
        ),
        "method_scope": "lookup presence does not count as an observed dataset-method relation",
        "frontier_status": "empty_selection" if not selection else "refused",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "claims_not_made": [
            "pollen_taxon_acceptance",
            "chronology_selection",
            "pollen_denominator_acceptance",
            "ppe_or_fall_speed_binding",
            "basin_or_ring_geometry_admission",
            "site_independence",
            "numerical_lra_execution",
            "ecological_accuracy",
            "scientific_acceptance",
        ],
    }
    evidence.assert_unchanged()
    content = canonical_bytes(payload)
    return SeadLraFrontier(content, hashlib.sha256(content).hexdigest())
