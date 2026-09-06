from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
    validate_materialized_sead_full_evidence_admission,
)
from bijux_pollenomics.collection.sources.sead.evidence.claims import (
    build_sead_chronology_claim_bundle,
)

from .admission import _country_by_site, _load_full_admission
from .constants import (
    _ABUNDANCE_COMPONENTS,
    _ANALYSIS_VALUE_COMPONENTS,
    _DIMENSION_RELATION_TABLES,
    _OBSERVATION_TABLES,
    EVENT_BUNDLE_SCHEMA_VERSION,
    EVIDENCE_BUNDLE_SCHEMA_VERSION,
    OBSERVATION_SCHEMA_VERSION,
    RELATION_INDEX_SCHEMA_VERSION,
)
from .relations import (
    _assert_observation_reconciliation,
    _component_indices,
    _dataset_semantics_index,
    _dimension_relation_index,
    _entity_relations,
    _four_country_counts,
    _observation_components,
    _observation_dimension_relation_ids,
    _observation_semantics,
    _taxonomy_index,
    _unique_index,
    _value_semantics_index,
)
from .serialization import (
    _copied_file_sha256,
    _positive_int,
    _required_sha256,
    _required_text,
    _stable_id,
)


def build_sead_source_native_evidence_bundle(
    acquisition_root: Path,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> dict[str, dict[str, object]]:
    """Build complete observation, relation, chronology, and refusal surfaces."""
    admission = validate_materialized_sead_full_evidence_admission(
        acquisition_root, expected_identity=expected_identity
    )
    root, tables, table_sha256 = _load_full_admission(
        acquisition_root, validated_admission=admission
    )
    manifest_sha256 = _required_sha256(admission, "acquisition_manifest_sha256")
    build_id = _required_text(admission, "build_id")
    run_id = _required_text(admission, "run_id")
    claim_bundle = build_sead_chronology_claim_bundle(root)
    claim_bundle["propagation_reason_code"] = "source_classification_not_accepted"

    country_by_site = _country_by_site(root)
    relation_rows, entity_relations = _entity_relations(
        tables, country_by_site=country_by_site
    )
    claim_ids_by_entity: dict[int, list[str]] = defaultdict(list)
    eligible_claim_ids_by_entity: dict[int, list[str]] = defaultdict(list)
    claims = claim_bundle.get("claims")
    if not isinstance(claims, list):
        raise TypeError("SEAD chronology bundle claims must be a list")
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise TypeError("SEAD chronology claim must be an object")
        entity_id = _positive_int(claim.get("analysis_entity_id"), "claim entity")
        claim_id = _required_text(claim, "chronology_claim_id")
        claim_ids_by_entity[entity_id].append(claim_id)
        if (
            claim.get("chronology_eligibility") == "eligible"
            and claim.get("comparability_status") == "comparable"
        ):
            eligible_claim_ids_by_entity[entity_id].append(claim_id)
    for relation_row in relation_rows:
        entity_id = cast(int, relation_row["analysis_entity_id"])
        claim_ids = sorted(claim_ids_by_entity.get(entity_id, []))
        eligible_ids = sorted(eligible_claim_ids_by_entity.get(entity_id, []))
        relation_row["chronology_link"] = {
            "selection_rule": "same_analysis_entity_only",
            "claim_ids": claim_ids,
            "eligible_claim_ids": eligible_ids,
        }

    components = _component_indices(tables)
    taxonomy = _taxonomy_index(tables)
    value_semantics = _value_semantics_index(tables)
    dataset_semantics = _dataset_semantics_index(tables)
    dimension_semantics, dimension_relations, dimensions_by_owner = (
        _dimension_relation_index(tables, manifest_sha256=manifest_sha256)
    )
    analysis_values = _unique_index(tables["tbl_analysis_values"], "analysis_value_id")
    observations: list[dict[str, object]] = []
    dispositions: list[dict[str, object]] = []
    country_counts: Counter[str] = Counter()
    table_counts: Counter[str] = Counter()
    chronology_status_counts: Counter[str] = Counter()
    unit_status_counts: Counter[str] = Counter()
    taxon_status_counts: Counter[str] = Counter()
    refusal_counts: Counter[str] = Counter()
    observation_ids_by_entity: dict[int, list[str]] = defaultdict(list)

    for table, primary_key, value_field in _OBSERVATION_TABLES:
        for source_row in tables[table]:
            source_id = _positive_int(source_row.get(primary_key), f"{table} key")
            semantic_source_row = source_row
            analysis_value_id: int | None = None
            if table == "tbl_analysis_taxon_counts":
                analysis_value_id = _positive_int(
                    source_row.get("analysis_value_id"),
                    "tbl_analysis_taxon_counts analysis_value_id",
                )
                parent_value = analysis_values.get(analysis_value_id)
                if parent_value is None:
                    raise ValueError(
                        f"SEAD analysis taxon count lacks analysis value: {source_id}"
                    )
                semantic_source_row = parent_value
            entity_id = _positive_int(
                semantic_source_row.get("analysis_entity_id"),
                f"{table} analysis_entity_id",
            )
            relation = entity_relations.get(entity_id)
            if relation is None:
                raise ValueError(
                    f"SEAD observation lacks entity relation: {table}:{source_id}"
                )
            observation_id = _stable_id(
                "sead-observation", manifest_sha256, table, str(source_id)
            )
            all_claim_ids = sorted(claim_ids_by_entity.get(entity_id, []))
            eligible_claim_ids = sorted(eligible_claim_ids_by_entity.get(entity_id, []))
            chronology_status = (
                "direct_analysis_entity_eligible_claim"
                if eligible_claim_ids
                else (
                    "direct_analysis_entity_context_only"
                    if all_claim_ids
                    else "unavailable_at_analysis_entity"
                )
            )
            dataset_value = relation["dataset_id"]
            dataset_id = dataset_value if isinstance(dataset_value, int) else None
            source_components = _observation_components(
                table, source_id=source_id, components=components
            )
            taxon_relation = (
                taxonomy.get(cast(int, source_row.get("taxon_id")))
                if table in {"tbl_abundances", "tbl_analysis_taxon_counts"}
                else None
            )
            taxon_status = (
                "source_native_linked"
                if taxon_relation is not None
                else (
                    "source_taxon_unavailable"
                    if table in {"tbl_abundances", "tbl_analysis_taxon_counts"}
                    else "not_exposed_for_observation_type"
                )
            )
            semantics = _observation_semantics(
                table,
                source_row=semantic_source_row,
                dataset_id=dataset_id,
                dataset_semantics=dataset_semantics,
                value_semantics=value_semantics,
            )
            dimension_relation_ids = _observation_dimension_relation_ids(
                table,
                source_id=source_id,
                analysis_value_id=analysis_value_id,
                entity_relation=relation,
                dimensions_by_owner=dimensions_by_owner,
            )
            unit_status = cast(str, semantics["unit_status"])
            reasons = ["source_classification_not_accepted"]
            if not eligible_claim_ids:
                reasons.append(
                    "eligible_chronology_claim_unavailable_at_analysis_entity"
                )
            if unit_status != "source_native_linked":
                reasons.append("source_unit_unavailable")
            if taxon_relation is None:
                reasons.append("source_taxon_unavailable")
            reasons = sorted(reasons)
            observations.append(
                {
                    "schema_version": OBSERVATION_SCHEMA_VERSION,
                    "observation_id": observation_id,
                    "source_family": "sead",
                    "source_table": table,
                    "source_record_id": str(source_id),
                    "source_row": dict(source_row),
                    "source_value_field": value_field,
                    "source_value": source_row.get(value_field),
                    "source_value_state": (
                        "source_null"
                        if source_row.get(value_field) is None
                        else "reported"
                    ),
                    "entity_relation_id": relation["entity_relation_id"],
                    "country_code": relation["country_code"],
                    "source_components": source_components,
                    "source_semantics": semantics,
                    "dimension_relation_ids": dimension_relation_ids,
                    "dimension_status": (
                        "source_native_linked"
                        if dimension_relation_ids
                        else "unavailable_in_admitted_relations"
                    ),
                    "taxon_relation_id": (
                        taxon_relation["taxon_relation_id"]
                        if taxon_relation is not None
                        else None
                    ),
                    "taxon_status": taxon_status,
                    "chronology_link": {
                        "status": chronology_status,
                        "selection_rule": "same_analysis_entity_only",
                        "entity_relation_id": relation["entity_relation_id"],
                        "claim_count": len(all_claim_ids),
                        "eligible_claim_count": len(eligible_claim_ids),
                    },
                    "event_eligibility": "refused",
                    "event_refusal_reason_codes": reasons,
                    "acquisition_manifest_sha256": manifest_sha256,
                    "source_payload_sha256": table_sha256[table],
                    "build_id": build_id,
                }
            )
            observation_ids_by_entity[entity_id].append(observation_id)
            dispositions.append(
                {
                    "observation_id": observation_id,
                    "status": "refused",
                    "reason_codes": reasons,
                    "eligible_chronology_claim_count": len(eligible_claim_ids),
                }
            )
            country_counts[cast(str, relation["country_code"])] += 1
            table_counts[table] += 1
            chronology_status_counts[chronology_status] += 1
            unit_status_counts[unit_status] += 1
            taxon_status_counts[taxon_status] += 1
            refusal_counts.update(reasons)

    _assert_observation_reconciliation(
        tables, observations, dispositions, component_indices=components
    )
    for claim in claims:
        if not isinstance(claim, dict):
            raise TypeError("SEAD chronology claim must be a mutable object")
        entity_id = _positive_int(claim.get("analysis_entity_id"), "claim entity")
        linked_count = len(observation_ids_by_entity.get(entity_id, []))
        claim["observation_relation_id"] = f"sead-analysis-entity:{entity_id}"
        claim["linked_source_native_observation_count"] = linked_count
        claim["observation_link_status"] = (
            "linked_at_analysis_entity"
            if linked_count
            else "unavailable_at_analysis_entity"
        )
        claim["propagation_eligibility"] = "refused"
        claim["propagation_reason_codes"] = [
            (
                "source_classification_not_accepted"
                if linked_count
                else "source_native_observation_unavailable_at_analysis_entity"
            )
        ]
    relation_index = {
        "schema_version": RELATION_INDEX_SCHEMA_VERSION,
        "source_family": "sead",
        "source_run_id": run_id,
        "build_id": build_id,
        "acquisition_manifest_sha256": manifest_sha256,
        "source_table_counts": {table: len(tables[table]) for table in sorted(tables)},
        "source_table_sha256": dict(sorted(table_sha256.items())),
        "entity_relation_count": len(relation_rows),
        "entity_relations": relation_rows,
        "dataset_semantic_count": len(dataset_semantics),
        "dataset_semantics": [
            dataset_semantics[key] for key in sorted(dataset_semantics)
        ],
        "value_semantic_count": len(value_semantics),
        "value_semantics": [value_semantics[key] for key in sorted(value_semantics)],
        "taxon_relation_count": len(taxonomy),
        "taxon_relations": [taxonomy[key] for key in sorted(taxonomy)],
        "dimension_semantic_count": len(dimension_semantics),
        "dimension_semantics": [
            dimension_semantics[key] for key in sorted(dimension_semantics)
        ],
        "dimension_relation_count": len(dimension_relations),
        "dimension_relation_table_counts": {
            table: len(tables[table]) for table, *_ in _DIMENSION_RELATION_TABLES
        },
        "dimension_relations": dimension_relations,
        "unavailable_dimensions": {
            "abundance_properties": len(tables["tbl_abundance_properties"]),
            "value_qualifiers": len(tables["tbl_value_qualifiers"]),
        },
    }
    observation_bundle = {
        "schema_version": EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "source_family": "sead",
        "source_run_id": run_id,
        "source_scope_id": _required_text(admission, "scope_id"),
        "build_id": build_id,
        "acquisition_manifest_sha256": manifest_sha256,
        "acquisition_bundle_sha256": _required_text(
            admission, "acquisition_bundle_sha256"
        ),
        "parent_admission_sha256": _required_sha256(
            admission, "parent_admission_sha256"
        ),
        "country_decisions_sha256": _copied_file_sha256(
            admission, "country-decisions.json"
        ),
        "source_table_counts": {table: len(tables[table]) for table in sorted(tables)},
        "source_table_sha256": dict(sorted(table_sha256.items())),
        "observation_count": len(observations),
        "observation_table_counts": {
            table: table_counts.get(table, 0) for table, _, _ in _OBSERVATION_TABLES
        },
        "country_counts": _four_country_counts(country_counts),
        "chronology_link_status_counts": dict(sorted(chronology_status_counts.items())),
        "unit_status_counts": dict(sorted(unit_status_counts.items())),
        "taxon_status_counts": dict(sorted(taxon_status_counts.items())),
        "component_table_counts": {
            table: len(tables[table])
            for table in (*_ANALYSIS_VALUE_COMPONENTS, *_ABUNDANCE_COMPONENTS)
        },
        "observations": observations,
    }
    event_bundle = {
        "schema_version": EVENT_BUNDLE_SCHEMA_VERSION,
        "source_family": "sead",
        "source_run_id": run_id,
        "build_id": build_id,
        "acquisition_manifest_sha256": manifest_sha256,
        "observation_denominator": len(observations),
        "eligible_event_count": 0,
        "refused_event_count": len(dispositions),
        "refusal_reason_counts": dict(sorted(refusal_counts.items())),
        "country_observation_counts": _four_country_counts(country_counts),
        "country_eligible_event_counts": _four_country_counts(Counter()),
        "events": [],
        "refusals": dispositions,
        "scientific_posture": {
            "classification": "no_accepted_derived_classification",
            "chronology_selection": "same_analysis_entity_only",
            "claim_alternatives": "all_retained",
            "site_envelopes": "forbidden",
            "propagation": "refused",
        },
    }
    return {
        "chronology_claims.json": claim_bundle,
        "source_native_observations.json": observation_bundle,
        "observation_relation_index.json": relation_index,
        "evidence_events.json": event_bundle,
    }
