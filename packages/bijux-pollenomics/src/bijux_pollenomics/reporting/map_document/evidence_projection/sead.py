"""SEAD evidence admission and atlas projection."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    governed_sead_evidence_root,
    read_validated_sead_evidence_documents,
)

from .constants import (
    _SEAD_DATASET_SEMANTIC_FIELDS,
    _SEAD_DIMENSION_FIELDS,
    _SEAD_DIMENSION_SEMANTIC_FIELDS,
    _SEAD_ENTITY_FIELDS,
    _SEAD_EVIDENCE_DOCUMENTS,
    _SEAD_OBSERVATION_FIELDS,
    _SEAD_TAXON_FIELDS,
    _SEAD_VALUE_SEMANTIC_FIELDS,
    _UNAVAILABLE_CLASSIFICATION,
)
from .io import (
    _identifier_text,
    _mapping,
    _numeric_text_key,
    _read_json_object,
    _read_regular_bytes,
    _required_text,
)
from .records import (
    _features,
    _non_null_unique,
    _row_table,
    _set_feature_record_id,
    _unavailable,
    _unique_rows,
)
from .sead_claims import _sead_claim_table, _validate_sead_claim_parents
from .sead_records import (
    _compact_sead_dataset_semantics,
    _compact_sead_dimension,
    _compact_sead_dimension_semantics,
    _compact_sead_entity,
    _compact_sead_observation,
    _compact_sead_taxon,
    _compact_sead_value_semantics,
    _sead_observation_table,
)


def _project_sead(
    context_root: Path,
    layers: Sequence[MutableMapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    evidence_root = governed_sead_evidence_root(context_root)
    documents = read_validated_sead_evidence_documents(
        evidence_root,
        _SEAD_EVIDENCE_DOCUMENTS,
        expected_run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
        expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )
    claims_bundle = documents["chronology_claims.json"]
    observations_bundle = documents["source_native_observations.json"]
    relation_index = documents["observation_relation_index.json"]
    events_bundle = documents["evidence_events.json"]
    _validate_sead_evidence_headers(
        claims_bundle, observations_bundle, relation_index, events_bundle
    )
    run_id = _required_text(claims_bundle.get("source_run_id"), "SEAD source run ID")
    acquisition_root = context_root / "sead" / "raw" / "acquisitions" / run_id
    admission = _validate_sead_claim_parents(acquisition_root, claims_bundle)
    evidence_manifest = _read_json_object(
        evidence_root / "evidence_materialization_manifest.json",
        "SEAD evidence materialization manifest",
    )
    file_set_sha256 = _required_text(
        evidence_manifest.get("file_set_sha256"), "SEAD evidence file-set SHA-256"
    )
    admission_sha256 = hashlib.sha256(
        _read_regular_bytes(acquisition_root / "admission.json", "SEAD admission")
    ).hexdigest()
    if admission_sha256 != SEAD_GOVERNED_ADMISSION_SHA256:
        raise ValueError("SEAD governed admission digest changed")

    raw_claims = _object_rows(claims_bundle, "claims", "SEAD chronology claims")
    if claims_bundle.get("claim_count") != len(raw_claims):
        raise ValueError("SEAD chronology claim count does not reconcile")
    claims_by_site: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    claim_ids: set[str] = set()
    claim_country_counts: Counter[str] = Counter()
    for row in raw_claims:
        claim_id = _required_text(
            row.get("chronology_claim_id"), "SEAD chronology claim ID"
        )
        if claim_id in claim_ids:
            raise ValueError(f"SEAD chronology claim ID is duplicated: {claim_id}")
        claim_ids.add(claim_id)
        site_id = _required_text(row.get("source_site_id"), "SEAD claim site ID")
        if row.get("build_id") != claims_bundle.get("source_build_id"):
            raise ValueError("SEAD claim build identity changed")
        if row.get("acquisition_manifest_sha256") != claims_bundle.get(
            "acquisition_manifest_sha256"
        ):
            raise ValueError("SEAD claim acquisition identity changed")
        claims_by_site[site_id].append(row)
        claim_country_counts[
            _required_text(row.get("country_code"), "SEAD claim country")
        ] += 1
    if dict(sorted(claim_country_counts.items())) != claims_bundle.get(
        "country_counts"
    ):
        raise ValueError("SEAD claim country counts do not reconcile")

    entity_rows = _object_rows(
        relation_index, "entity_relations", "SEAD entity relations"
    )
    taxon_rows = _object_rows(relation_index, "taxon_relations", "SEAD taxa")
    dimension_rows = _object_rows(
        relation_index, "dimension_relations", "SEAD dimension relations"
    )
    dimension_semantic_rows = _object_rows(
        relation_index, "dimension_semantics", "SEAD dimension semantics"
    )
    dataset_semantic_rows = _object_rows(
        relation_index, "dataset_semantics", "SEAD dataset semantics"
    )
    value_semantic_rows = _object_rows(
        relation_index, "value_semantics", "SEAD value semantics"
    )
    entity_by_id = _unique_rows(
        entity_rows, "entity_relation_id", "SEAD entity relations"
    )
    taxon_by_id = _unique_rows(taxon_rows, "taxon_relation_id", "SEAD taxa")
    dimension_by_id = _unique_rows(
        dimension_rows, "dimension_relation_id", "SEAD dimension relations"
    )
    dimension_semantic_by_id = _unique_rows(
        dimension_semantic_rows,
        "dimension_semantics_id",
        "SEAD dimension semantics",
    )
    dataset_semantic_by_id = _unique_rows(
        dataset_semantic_rows, "dataset_semantics_id", "SEAD dataset semantics"
    )
    value_semantic_by_id = _unique_rows(
        value_semantic_rows, "value_semantics_id", "SEAD value semantics"
    )
    site_by_analysis_entity = _site_by_entity_owner(
        entity_rows, owner_field="analysis_entity_id"
    )
    site_by_physical_sample = _site_by_entity_owner(
        entity_rows, owner_field="physical_sample_id"
    )
    site_by_sample_group = _site_by_entity_owner(
        entity_rows, owner_field="sample_group_id"
    )
    _reconcile_sead_relation_denominators(
        relation_index,
        entity_rows=entity_rows,
        taxon_rows=taxon_rows,
        dimension_rows=dimension_rows,
        dimension_semantic_rows=dimension_semantic_rows,
        dataset_semantic_rows=dataset_semantic_rows,
        value_semantic_rows=value_semantic_rows,
    )
    refusal_rows = _object_rows(events_bundle, "refusals", "SEAD event refusals")
    refusal_by_observation = _unique_rows(
        refusal_rows, "observation_id", "SEAD event refusals"
    )
    if (
        events_bundle.get("events") != []
        or events_bundle.get("eligible_event_count") != 0
    ):
        raise ValueError("SEAD evidence unexpectedly contains eligible events")
    if events_bundle.get("refused_event_count") != len(refusal_rows):
        raise ValueError("SEAD event refusal count does not reconcile")

    observations = _object_rows(
        observations_bundle, "observations", "SEAD observations"
    )
    if observations_bundle.get("observation_count") != len(observations):
        raise ValueError("SEAD observation count does not reconcile")
    if events_bundle.get("observation_denominator") != len(observations):
        raise ValueError("SEAD event denominator does not reconcile")
    for field, expected in (
        ("chronology_claim_count", len(raw_claims)),
        ("observation_count", len(observations)),
        ("eligible_event_count", 0),
        ("refused_event_count", len(refusal_rows)),
    ):
        if evidence_manifest.get(field) != expected:
            raise ValueError(f"SEAD evidence manifest {field} does not reconcile")
    observations_by_site: dict[str, list[list[object]]] = defaultdict(list)
    entities_by_site: dict[str, dict[str, list[object]]] = defaultdict(dict)
    taxon_ids_by_site: dict[str, set[str]] = defaultdict(set)
    dimension_ids_by_site: dict[str, set[str]] = defaultdict(set)
    dataset_semantic_ids_by_site: dict[str, set[str]] = defaultdict(set)
    value_semantic_ids_by_site: dict[str, set[str]] = defaultdict(set)
    observation_ids: set[str] = set()
    referenced_taxon_ids: set[str] = set()
    referenced_dimension_ids: set[str] = set()
    referenced_dataset_semantic_ids: set[str] = set()
    referenced_value_semantic_ids: set[str] = set()
    observation_count_by_entity: Counter[str] = Counter()
    observation_country_counts: Counter[str] = Counter()
    observation_table_counts: Counter[str] = Counter()
    refusal_reason_counts: Counter[str] = Counter()
    for observation in observations:
        if observation.get("build_id") != observations_bundle.get("build_id"):
            raise ValueError("SEAD observation build identity changed")
        if observation.get("acquisition_manifest_sha256") != observations_bundle.get(
            "acquisition_manifest_sha256"
        ):
            raise ValueError("SEAD observation acquisition identity changed")
        compact, site_id, references = _compact_sead_observation(
            observation,
            entity_by_id=entity_by_id,
            refusal_by_observation=refusal_by_observation,
            taxon_by_id=taxon_by_id,
            dimension_by_id=dimension_by_id,
            dataset_semantic_by_id=dataset_semantic_by_id,
            value_semantic_by_id=value_semantic_by_id,
        )
        observation_id = cast(str, compact[0])
        if observation_id in observation_ids:
            raise ValueError(f"SEAD observation ID is duplicated: {observation_id}")
        observation_ids.add(observation_id)
        observations_by_site[site_id].append(compact)
        entity_id = cast(str, compact[3])
        observation_count_by_entity[entity_id] += 1
        observation_country_counts[
            _required_text(observation.get("country_code"), "SEAD observation country")
        ] += 1
        observation_table_counts[
            _required_text(observation.get("source_table"), "SEAD observation table")
        ] += 1
        refusal_reason_counts.update(
            cast(
                list[str],
                compact[_SEAD_OBSERVATION_FIELDS.index("event_refusal_reason_codes")],
            )
        )
        entities_by_site[site_id][entity_id] = _compact_sead_entity(
            entity_by_id[entity_id]
        )
        taxon_id, dimension_ids, dataset_id, value_id = references
        if taxon_id is not None:
            taxon_ids_by_site[site_id].add(taxon_id)
            referenced_taxon_ids.add(taxon_id)
        dimension_ids_by_site[site_id].update(dimension_ids)
        referenced_dimension_ids.update(dimension_ids)
        if dataset_id is not None:
            dataset_semantic_ids_by_site[site_id].add(dataset_id)
            referenced_dataset_semantic_ids.add(dataset_id)
        if value_id is not None:
            value_semantic_ids_by_site[site_id].add(value_id)
            referenced_value_semantic_ids.add(value_id)
    dimension_owner_sites = {
        "analysis_entity": site_by_analysis_entity,
        "physical_sample": site_by_physical_sample,
        "sample_group": site_by_sample_group,
    }
    for dimension_id, dimension in dimension_by_id.items():
        owner_kind = _required_text(
            dimension.get("owner_kind"), "SEAD dimension owner kind"
        )
        owner_sites = dimension_owner_sites.get(owner_kind)
        if owner_sites is None:
            raise ValueError(f"SEAD dimension owner kind is unsupported: {owner_kind}")
        owner_id = _identifier_text(
            dimension.get("owner_id"), "SEAD dimension owner ID"
        )
        owner_site_id = owner_sites.get(owner_id)
        if owner_site_id is None:
            raise ValueError("SEAD dimension owner has no governed site relation")
        dimension_ids_by_site[owner_site_id].add(dimension_id)
        referenced_dimension_ids.add(dimension_id)
    if observation_ids != set(refusal_by_observation):
        raise ValueError("SEAD observations and event refusals do not reconcile")
    for label, actual, declared in (
        (
            "country counts",
            observation_country_counts,
            observations_bundle.get("country_counts"),
        ),
        (
            "observation table counts",
            observation_table_counts,
            observations_bundle.get("observation_table_counts"),
        ),
        (
            "event refusal reason counts",
            refusal_reason_counts,
            events_bundle.get("refusal_reason_counts"),
        ),
        (
            "event country observation counts",
            observation_country_counts,
            events_bundle.get("country_observation_counts"),
        ),
    ):
        declared_counts = _mapping(declared, f"SEAD {label}")
        nonzero_declared = {
            str(key): value for key, value in declared_counts.items() if value != 0
        }
        if dict(sorted(actual.items())) != nonzero_declared:
            raise ValueError(f"SEAD {label} do not reconcile")
    eligible_country_counts = _mapping(
        events_bundle.get("country_eligible_event_counts"),
        "SEAD eligible event country counts",
    )
    if set(eligible_country_counts) != set(observation_country_counts) or any(
        count != 0 for count in eligible_country_counts.values()
    ):
        raise ValueError("SEAD eligible event country counts do not reconcile")
    for claim in raw_claims:
        relation_id = _required_text(
            claim.get("observation_relation_id"),
            "SEAD claim observation relation ID",
        )
        entity = entity_by_id.get(relation_id)
        if entity is None:
            raise ValueError("SEAD claim references unknown observation relation")
        if _identifier_text(entity.get("site_id"), "SEAD claim relation site") != (
            _required_text(claim.get("source_site_id"), "SEAD claim site")
        ):
            raise ValueError("SEAD claim observation relation crosses sites")
        if (
            claim.get("linked_source_native_observation_count")
            != (observation_count_by_entity[relation_id])
        ):
            raise ValueError("SEAD claim observation count does not reconcile")
        chronology = _mapping(entity.get("chronology_link"), "SEAD entity chronology")
        entity_claim_ids = chronology.get("claim_ids")
        if (
            not isinstance(entity_claim_ids, list)
            or claim.get("chronology_claim_id") not in entity_claim_ids
        ):
            raise ValueError("SEAD claim is absent from its entity chronology relation")
    for dimension_id in referenced_dimension_ids:
        semantics_id = _required_text(
            dimension_by_id[dimension_id].get("dimension_semantics_id"),
            "SEAD dimension semantics ID",
        )
        if semantics_id not in dimension_semantic_by_id:
            raise ValueError("SEAD dimension relation references unknown semantics")

    site_artifact_path = (
        context_root / "sead" / "normalized" / "nordic_environmental_sites.geojson"
    )
    site_artifact = _read_json_object(site_artifact_path, "SEAD Nordic site artifact")
    if site_artifact.get("type") != "FeatureCollection":
        raise ValueError("SEAD Nordic site artifact is not a FeatureCollection")
    raw_site_features = site_artifact.get("features")
    if not isinstance(raw_site_features, list) or any(
        not isinstance(row, Mapping) for row in raw_site_features
    ):
        raise ValueError("SEAD Nordic site features must be object rows")
    site_rows: list[Mapping[str, object]] = []
    for raw_feature in cast(list[Mapping[str, object]], raw_site_features):
        properties = _mapping(
            raw_feature.get("properties"), "SEAD Nordic site properties"
        )
        if (
            properties.get("source") != "SEAD"
            or properties.get("layer_key") != "sead-sites"
        ):
            raise ValueError("SEAD Nordic site identity changed")
        site_rows.append(properties)
    sites = _unique_rows(site_rows, "record_id", "SEAD Nordic sites")
    admitted_site_payload = _read_json_object(
        acquisition_root / "payloads" / "tbl_sites.json", "SEAD admitted sites"
    )
    raw_admitted_sites = admitted_site_payload.get("rows")
    if not isinstance(raw_admitted_sites, list) or any(
        not isinstance(row, Mapping) for row in raw_admitted_sites
    ):
        raise ValueError("SEAD admitted site rows are invalid")
    admitted_site_ids = {
        str(row.get("site_id"))
        for row in cast(list[Mapping[str, object]], raw_admitted_sites)
    }
    decisions = _read_json_object(
        acquisition_root / "country-decisions.json", "SEAD country decisions"
    )
    raw_decisions = decisions.get("decisions")
    if not isinstance(raw_decisions, list) or any(
        not isinstance(row, Mapping) for row in raw_decisions
    ):
        raise ValueError("SEAD country decisions must be object rows")
    decision_rows = cast(list[Mapping[str, object]], raw_decisions)
    decision_by_site = _unique_rows(decision_rows, "site_id", "SEAD decisions")
    assigned_site_ids = {
        site_id
        for site_id, row in decision_by_site.items()
        if _mapping(row.get("decision"), "SEAD country decision").get("decision_status")
        == "assigned"
        and row.get("governed_country_code") in {"SE", "DK", "NO", "FI"}
    }
    if not set(sites) <= admitted_site_ids:
        raise ValueError("SEAD normalized sites are missing from admitted site rows")
    if set(sites) != assigned_site_ids:
        raise ValueError(
            "SEAD normalized sites do not match assigned country decisions"
        )
    unknown_claim_sites = sorted(set(claims_by_site) - set(sites))
    if unknown_claim_sites:
        raise ValueError(
            f"SEAD claims reference unknown admitted sites: {unknown_claim_sites[:5]}"
        )
    unknown_observation_sites = sorted(set(observations_by_site) - set(sites))
    if unknown_observation_sites:
        raise ValueError(
            "SEAD observations reference unknown admitted sites: "
            f"{unknown_observation_sites[:5]}"
        )

    feature_site_ids: set[str] = set()
    feature_count = 0
    for layer in layers:
        for feature in _features(layer):
            native_id = _required_text(
                feature.get("evidence_row_id"), "SEAD feature evidence_row_id"
            )
            source_site_id = native_id.split(":", 1)[0]
            if source_site_id not in sites:
                raise ValueError(
                    f"SEAD map feature has no governed Nordic site: {source_site_id}"
                )
            _set_feature_record_id(feature, f"sead:site:{source_site_id}")
            feature_site_ids.add(source_site_id)
            feature_count += 1
    if feature_site_ids != set(sites):
        missing = sorted(set(sites) - feature_site_ids, key=_numeric_text_key)
        raise ValueError(
            f"SEAD atlas does not expose every governed site: {missing[:5]}"
        )

    records: list[dict[str, object]] = []
    for source_site_id in sorted(feature_site_ids, key=_numeric_text_key):
        site = sites[source_site_id]
        site_claims = claims_by_site[source_site_id]
        claim_type_counts = Counter(
            _required_text(row.get("claim_type"), "SEAD claim type")
            for row in site_claims
        )
        comparability_counts = Counter(
            _required_text(
                row.get("comparability_status"), "SEAD claim comparability status"
            )
            for row in site_claims
        )
        eligibility_counts = Counter(
            _required_text(
                row.get("chronology_eligibility"), "SEAD chronology eligibility"
            )
            for row in site_claims
        )
        sample_group_ids = _non_null_unique(site_claims, "sample_group_id")
        physical_sample_ids = _non_null_unique(site_claims, "physical_sample_id")
        analysis_entity_ids = _non_null_unique(site_claims, "analysis_entity_id")
        dataset_ids = _non_null_unique(site_claims, "dataset_id")
        site_observations = sorted(
            observations_by_site[source_site_id], key=lambda row: str(row[0])
        )
        site_entities = [
            entities_by_site[source_site_id][entity_id]
            for entity_id in sorted(entities_by_site[source_site_id])
        ]
        site_taxa = [
            _compact_sead_taxon(taxon_by_id[relation_id])
            for relation_id in sorted(taxon_ids_by_site[source_site_id])
        ]
        site_dimensions = [
            _compact_sead_dimension(dimension_by_id[relation_id])
            for relation_id in sorted(dimension_ids_by_site[source_site_id])
        ]
        site_dimension_semantic_ids = {
            _required_text(
                dimension_by_id[relation_id].get("dimension_semantics_id"),
                "SEAD dimension semantics ID",
            )
            for relation_id in dimension_ids_by_site[source_site_id]
        }
        site_dimension_semantics = [
            _compact_sead_dimension_semantics(dimension_semantic_by_id[semantic_id])
            for semantic_id in sorted(site_dimension_semantic_ids)
        ]
        site_dataset_semantics = [
            _compact_sead_dataset_semantics(dataset_semantic_by_id[semantic_id])
            for semantic_id in sorted(dataset_semantic_ids_by_site[source_site_id])
        ]
        site_value_semantics = [
            _compact_sead_value_semantics(value_semantic_by_id[semantic_id])
            for semantic_id in sorted(value_semantic_ids_by_site[source_site_id])
        ]
        site_refusal_reason_counts = Counter(
            reason
            for row in site_observations
            for reason in cast(
                list[str],
                row[_SEAD_OBSERVATION_FIELDS.index("event_refusal_reason_codes")],
            )
        )
        record_id = f"sead:site:{source_site_id}"
        records.append(
            {
                "record_id": record_id,
                "tabs": {
                    "overview": {
                        "source_family": "sead",
                        "site_id": record_id,
                        "source_site_id": source_site_id,
                        "site_name": site.get("name"),
                        "country": site.get("country"),
                        "source_url": site.get("source_url"),
                    },
                    "samples": (
                        {
                            **_row_table(_SEAD_ENTITY_FIELDS, site_entities),
                            "coverage_posture": "all_source_native_observation_entities",
                            "chronology_linked_sample_group_ids": sample_group_ids,
                            "chronology_linked_physical_sample_ids": physical_sample_ids,
                            "chronology_linked_analysis_entity_ids": analysis_entity_ids,
                            "chronology_linked_dataset_ids": dataset_ids,
                        }
                        if site_entities or site_claims
                        else _unavailable("sead_site_sample_records_not_available")
                    ),
                    "chronology": (
                        {
                            **_sead_claim_table(site_claims),
                            "chronology_claim_count": len(site_claims),
                            "claim_type_counts": dict(
                                sorted(claim_type_counts.items())
                            ),
                            "comparability_counts": dict(
                                sorted(comparability_counts.items())
                            ),
                            "eligibility_counts": dict(
                                sorted(eligibility_counts.items())
                            ),
                            "selection_posture": "retain_all_without_preferred_model",
                            "publication_role": "chronology_display_only",
                            "interval_semantics": "[younger_bp, older_bp]",
                            "null_semantics": "source null remains null",
                        }
                        if site_claims
                        else _unavailable("sead_site_numeric_chronology_not_available")
                    ),
                    "pollen_composition": (
                        {
                            **_sead_observation_table(site_observations),
                            "taxa": _row_table(_SEAD_TAXON_FIELDS, site_taxa),
                            "dimensions": _row_table(
                                _SEAD_DIMENSION_FIELDS, site_dimensions
                            ),
                            "dimension_semantics": _row_table(
                                _SEAD_DIMENSION_SEMANTIC_FIELDS,
                                site_dimension_semantics,
                            ),
                            "dataset_semantics": _row_table(
                                _SEAD_DATASET_SEMANTIC_FIELDS,
                                site_dataset_semantics,
                            ),
                            "value_semantics": _row_table(
                                _SEAD_VALUE_SEMANTIC_FIELDS, site_value_semantics
                            ),
                            "aggregation_posture": "source rows retained without cross-unit summing",
                            "evidence_posture": "complete source-native observations; tab name does not imply pollen classification",
                            "source_value_posture": "source null, zero, false, and text zero remain distinct",
                            "classification_status": "not_accepted",
                        }
                        if site_observations or site_dimensions
                        else _unavailable("sead_site_observations_not_available")
                    ),
                    "relation": {
                        "status": "refused",
                        "reason_code": "source_classification_not_accepted",
                        "eligible_event_count": 0,
                        "refused_observation_count": len(site_observations),
                        "refusal_reason_counts": dict(
                            sorted(site_refusal_reason_counts.items())
                        ),
                        "scientific_posture": "observation succession is not proof of migration or causation",
                    },
                    "classification": dict(_UNAVAILABLE_CLASSIFICATION),
                    "provenance": {
                        "source_run_id": run_id,
                        "build_id": claims_bundle.get("source_build_id"),
                        "acquisition_manifest_sha256": claims_bundle.get(
                            "acquisition_manifest_sha256"
                        ),
                        "evidence_bundle_path": (
                            f"data/sead/normalized/acquisitions/{run_id}"
                        ),
                        "evidence_file_set_sha256": file_set_sha256,
                        "claim_locator_contract": "chronology_claims.json#chronology_claim_id={chronology_claim_id}",
                        "observation_locator_contract": "source_native_observations.json#observation_id={observation_id}",
                        "relation_locator_contract": "observation_relation_index.json#{relation_id}",
                        "event_refusal_locator_contract": "evidence_events.json#observation_id={observation_id}",
                        "record_locator": f"tbl_sites#site_id={source_site_id}",
                        "acquisition_release_status": admission.get("release_status"),
                        "propagation_status": claims_bundle.get("propagation_status"),
                        "propagation_reason_code": claims_bundle.get(
                            "propagation_reason_code"
                        ),
                    },
                },
            }
        )
    return records, {
        "source_feature_count": feature_count,
        "source_site_denominator": len(sites),
        "bbox_site_denominator": len(decision_rows),
        "assigned_site_count": len(assigned_site_ids),
        "excluded_site_count": len(decision_rows) - len(assigned_site_ids),
        "decision_status_counts": dict(
            sorted(
                Counter(
                    _required_text(
                        _mapping(row.get("decision"), "SEAD country decision").get(
                            "decision_status"
                        ),
                        "SEAD country decision status",
                    )
                    for row in decision_rows
                ).items()
            )
        ),
        "projected_site_count": len(records),
        "unprojected_source_site_count": len(sites) - len(records),
        "source_claim_denominator": len(raw_claims),
        "source_observation_denominator": len(observations),
        "source_taxon_relation_denominator": len(taxon_rows),
        "source_dimension_relation_denominator": len(dimension_rows),
        "source_event_refusal_denominator": len(refusal_rows),
        "projected_site_claim_count": sum(
            len(claims_by_site[site_id]) for site_id in feature_site_ids
        ),
        "projected_site_observation_count": sum(
            len(observations_by_site[site_id]) for site_id in feature_site_ids
        ),
        "projected_unique_taxon_relation_count": len(referenced_taxon_ids),
        "projected_dimension_relation_count": len(referenced_dimension_ids),
        "unprojected_dimension_relation_count": len(dimension_rows)
        - len(referenced_dimension_ids),
        "projected_unique_dataset_semantic_count": len(referenced_dataset_semantic_ids),
        "projected_unique_value_semantic_count": len(referenced_value_semantic_ids),
        "eligible_event_count": 0,
        "claim_country_counts": dict(sorted(claim_country_counts.items())),
        "observation_country_counts": dict(sorted(observation_country_counts.items())),
        "eligible_event_country_counts": dict(sorted(eligible_country_counts.items())),
        "propagation_status": "refused",
        "propagation_reason_code": "source_classification_not_accepted",
        "detail_row_counts": {
            "chronology_claims": sum(
                len(claims_by_site[site_id]) for site_id in feature_site_ids
            ),
            "observations": sum(
                len(observations_by_site[site_id]) for site_id in feature_site_ids
            ),
            "dimension_relations": len(referenced_dimension_ids),
            "taxon_relations_unique": len(referenced_taxon_ids),
            "event_refusals": len(refusal_rows),
        },
        "detail_row_denominators": {
            "chronology_claims": len(raw_claims),
            "observations": len(observations),
            "dimension_relations": len(dimension_rows),
            "taxon_relations_unique": len(taxon_rows),
            "event_refusals": len(refusal_rows),
        },
        "source_run_id": run_id,
        "build_id": claims_bundle.get("source_build_id"),
        "acquisition_manifest_sha256": claims_bundle.get("acquisition_manifest_sha256"),
        "acquisition_release_status": admission.get("release_status"),
        "evidence_file_set_sha256": file_set_sha256,
        "country_site_counts": dict(
            sorted(
                Counter(
                    _required_text(site.get("country"), "SEAD site country")
                    for site in sites.values()
                ).items()
            )
        ),
        "map_feature_country_counts": dict(
            sorted(
                Counter(
                    _required_text(feature.get("country"), "SEAD feature country")
                    for layer in layers
                    for feature in _features(layer)
                ).items()
            )
        ),
    }


def _validate_sead_evidence_headers(
    claims: Mapping[str, object],
    observations: Mapping[str, object],
    relations: Mapping[str, object],
    events: Mapping[str, object],
) -> None:
    documents = (
        (claims, "sead-chronology-claim-bundle.v1", "source_build_id"),
        (observations, "sead-source-native-evidence-bundle.v1", "build_id"),
        (relations, "sead-evidence-relation-index.v1", "build_id"),
        (events, "sead-evidence-event-bundle.v1", "build_id"),
    )
    run_id = claims.get("source_run_id")
    build_id = claims.get("source_build_id")
    acquisition_digest = claims.get("acquisition_manifest_sha256")
    for document, schema, build_field in documents:
        if document.get("schema_version") != schema:
            raise ValueError(f"SEAD evidence schema is unsupported: {schema}")
        if document.get("source_family") != "sead":
            raise ValueError("SEAD evidence source family changed")
        if document.get("source_run_id") != run_id:
            raise ValueError("SEAD evidence source run identities diverge")
        if document.get(build_field) != build_id:
            raise ValueError("SEAD evidence build identities diverge")
        if document.get("acquisition_manifest_sha256") != acquisition_digest:
            raise ValueError("SEAD evidence acquisition identities diverge")
    if (
        claims.get("propagation_status") != "refused"
        or claims.get("propagation_reason_code") != "source_classification_not_accepted"
    ):
        raise ValueError("SEAD propagation refusal posture changed")


def _object_rows(
    document: Mapping[str, object], field: str, label: str
) -> list[Mapping[str, object]]:
    rows = document.get(field)
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError(f"{label} must be object rows")
    return cast(list[Mapping[str, object]], rows)


def _reconcile_sead_relation_denominators(
    relation_index: Mapping[str, object],
    *,
    entity_rows: Sequence[Mapping[str, object]],
    taxon_rows: Sequence[Mapping[str, object]],
    dimension_rows: Sequence[Mapping[str, object]],
    dimension_semantic_rows: Sequence[Mapping[str, object]],
    dataset_semantic_rows: Sequence[Mapping[str, object]],
    value_semantic_rows: Sequence[Mapping[str, object]],
) -> None:
    for field, rows in (
        ("entity_relation_count", entity_rows),
        ("taxon_relation_count", taxon_rows),
        ("dimension_relation_count", dimension_rows),
        ("dimension_semantic_count", dimension_semantic_rows),
        ("dataset_semantic_count", dataset_semantic_rows),
        ("value_semantic_count", value_semantic_rows),
    ):
        if relation_index.get(field) != len(rows):
            raise ValueError(f"SEAD {field} does not reconcile")


def _site_by_entity_owner(
    entity_rows: Sequence[Mapping[str, object]], *, owner_field: str
) -> dict[str, str]:
    sites_by_owner: dict[str, str] = {}
    for entity in entity_rows:
        owner_value = entity.get(owner_field)
        if owner_value is None:
            continue
        owner_id = _identifier_text(owner_value, f"SEAD {owner_field}")
        site_id = _identifier_text(entity.get("site_id"), "SEAD entity site ID")
        existing = sites_by_owner.setdefault(owner_id, site_id)
        if existing != site_id:
            raise ValueError(f"SEAD {owner_field} crosses governed sites")
    return sites_by_owner
