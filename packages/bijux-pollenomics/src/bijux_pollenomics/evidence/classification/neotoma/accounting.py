"""Classification-accounting orchestration over admitted source rows."""

from __future__ import annotations

from collections.abc import Mapping


def _build_neotoma_classification_accounting(
    relational_snapshot: Mapping[str, object],
) -> dict[str, object]:
    from . import (
        _RELEASE_REASON_CODES,
        _blocker,
        _build_partitions,
        _concept_id,
        _country_release_blockers,
        _deduplicate_observations,
        _finalize_concept,
        _governed_country_code,
        _index_rows,
        _integer_count,
        _mapping_posture,
        _mapping_rows,
        _partition_value,
        _qualifier_markers,
        _required_text,
        _set_member,
        _source_concept_identity,
        _source_country_code,
        _source_evidence_universe,
        _variable_identity_matches,
        copy,
    )

    if relational_snapshot.get("source_family") != "neotoma":
        raise ValueError("classification accounting requires a Neotoma snapshot")

    observations = _mapping_rows(relational_snapshot.get("observations"))
    variables = _index_rows(
        _mapping_rows(relational_snapshot.get("variables")), "variable_id"
    )
    sites = _index_rows(_mapping_rows(relational_snapshot.get("sites")), "site_id")
    unique_observations, duplicate_blockers = _deduplicate_observations(observations)

    concept_accumulators: dict[str, dict[str, object]] = {}
    observation_memberships: list[dict[str, object]] = []
    integrity_blockers: list[dict[str, object]] = list(duplicate_blockers)
    for observation in unique_observations:
        observation_id = _required_text(observation, "observation_id")
        variable_id = _required_text(observation, "variable_id")
        site_id = _required_text(observation, "site_id")
        variable = variables.get(variable_id)
        site = sites.get(site_id)
        if variable is None:
            integrity_blockers.append(
                _blocker("orphan_variable_reference", observation_id, variable_id)
            )
        elif not _variable_identity_matches(variable, observation):
            integrity_blockers.append(
                _blocker("variable_identity_conflict", observation_id, variable_id)
            )
        if site is None:
            integrity_blockers.append(
                _blocker("orphan_site_reference", observation_id, site_id)
            )

        source_country = _source_country_code(site)
        governed_country = _governed_country_code(observation.get("country_code"))
        identity = _source_concept_identity(observation)
        concept_id = _concept_id(identity)
        mapping_status, mapping_reason = _mapping_posture(identity)
        accumulator = concept_accumulators.get(concept_id)
        if accumulator is None:
            accumulator = {
                "classification_concept_id": concept_id,
                **copy.deepcopy(identity),
                "source_element_type_partition": _partition_value(
                    identity["source_element_type"]
                ),
                "source_label_qualifier_markers": _qualifier_markers(
                    identity["source_reported_name"]
                ),
                "mapping_status": mapping_status,
                "mapping_reason_code": mapping_reason,
                "source_evidence_universe": _source_evidence_universe(
                    identity, mapping_status
                ),
                "aggregation_posture": "exact_source_unit_only",
                "cross_unit_aggregation_allowed": False,
                "accepted_taxon_concept_id": None,
                "accepted_taxon_name": None,
                "primary_group_id": None,
                "primary_subgroup_id": None,
                "role_ids": [],
                "evidence_reference_ids": [],
                "reviewer_id": None,
                "decision_date": None,
                "crosswalk_version": None,
                "release_eligible": False,
                "release_blocker_reason_codes": list(_RELEASE_REASON_CODES)
                if mapping_status == "unmapped"
                else [],
                "source_country_codes": set(),
                "governed_country_codes": set(),
                "observation_ids": set(),
            }
            concept_accumulators[concept_id] = accumulator
        _set_member(accumulator, "source_country_codes", source_country)
        _set_member(accumulator, "governed_country_codes", governed_country)
        _set_member(accumulator, "observation_ids", observation_id)
        observation_memberships.append(
            {
                "observation_id": observation_id,
                "classification_concept_id": concept_id,
                "mapping_status": mapping_status,
                "source_country_code": source_country,
                "governed_country_code": governed_country,
            }
        )

    concepts = [_finalize_concept(row) for row in concept_accumulators.values()]
    concepts.sort(key=lambda row: str(row["classification_concept_id"]))
    observation_memberships.sort(key=lambda row: str(row["observation_id"]))
    integrity_blockers.sort(
        key=lambda row: (
            str(row["reason_code"]),
            str(row["subject_id"]),
            str(row.get("detail", "")),
        )
    )
    partitions = _build_partitions(concepts, observation_memberships)
    unresolved_concept_ids = [
        str(row["classification_concept_id"])
        for row in concepts
        if row["mapping_status"] == "unmapped"
    ]
    country_release_blockers = _country_release_blockers(
        concepts, observation_memberships
    )
    observation_count = len(observation_memberships)
    return {
        "schema_version": "neotoma-classification-accounting.v1",
        "source_family": "neotoma",
        "source_snapshot_id": copy.deepcopy(
            relational_snapshot.get("source_snapshot_id")
        ),
        "build_id": copy.deepcopy(relational_snapshot.get("build_id")),
        "classification_posture": "source_accounting_only",
        "release_status": "refused",
        "release_reason_codes": list(_RELEASE_REASON_CODES),
        "concepts": concepts,
        "observation_memberships": observation_memberships,
        "partitions": partitions,
        "review": {
            "unresolved_concept_ids": unresolved_concept_ids,
            "country_release_blockers": country_release_blockers,
            "integrity_blockers": integrity_blockers,
        },
        "reconciliation": {
            "input_observation_row_count": len(observations),
            "unique_observation_count": observation_count,
            "duplicate_observation_row_count": len(observations) - observation_count,
            "observation_membership_count": observation_count,
            "concept_count": len(concepts),
            "concept_observation_count_sum": sum(
                _integer_count(row, "observation_count") for row in concepts
            ),
            "mapping_status_concept_count_sum": sum(
                _integer_count(row, "concept_count")
                for row in partitions["mapping_status"]
            ),
            "mapping_status_observation_count_sum": sum(
                _integer_count(row, "observation_count")
                for row in partitions["mapping_status"]
            ),
            "accepted_concept_count": 0,
            "release_eligible_concept_count": 0,
            "integrity_blocker_count": len(integrity_blockers),
        },
    }
