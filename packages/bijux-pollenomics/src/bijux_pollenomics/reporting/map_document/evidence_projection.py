"""Project governed source evidence into record-addressed atlas detail tabs."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Final, cast

from ...core.geojson import JsonObject
from ...data_downloader.sources.neotoma.materialization import (
    validate_neotoma_relational_materialization,
)
from ...data_downloader.sources.sead.evidence_reader import (
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    governed_sead_evidence_root,
    read_validated_sead_evidence_documents,
)
from .evidence import DETAIL_TAB_KEYS

PROJECTION_SCHEMA_VERSION: Final = "atlas-evidence-projection.v2"
_NEOTOMA_LAYER_KEY: Final = "neotoma-pollen"
_SEAD_LAYER_KEYS: Final = frozenset(
    {
        "sead-sites",
        "sead-temporal-evidence",
        "sweden-archaeology-site-discovery",
    }
)
_UNAVAILABLE_RELATION = {
    "status": "unavailable",
    "reason_code": "governed_relation_model_not_available",
}
_UNAVAILABLE_CLASSIFICATION = {
    "status": "unavailable",
    "reason_code": "accepted_scientific_classification_not_available",
}
_SEAD_CLAIM_FIELDS: Final = (
    "chronology_claim_id",
    "source_table",
    "source_record_id",
    "source_native_record_id",
    "subject_type",
    "subject_id",
    "sample_group_id",
    "physical_sample_id",
    "analysis_entity_id",
    "analysis_value_id",
    "dataset_id",
    "claim_type",
    "source_age_type",
    "source_age_value",
    "source_age_unit",
    "original_interval_orientation",
    "younger_bp",
    "older_bp",
    "calibration_status",
    "comparability_status",
    "chronology_eligibility",
    "propagation_eligibility",
    "propagation_reason_codes",
    "publication_role",
    "reason_codes",
    "transformation_id",
    "selection_status",
    "selection_rule_version",
    "observation_link_status",
    "observation_relation_id",
    "linked_source_native_observation_count",
    "source_relation_path",
    "source_payload_sha256",
)
_SEAD_CLAIM_COMMON_FIELDS: Final = (
    "source_family",
    "source_site_id",
    "site_uuid",
    "country_code",
    "latitude_dd",
    "longitude_dd",
    "country_assignment_method",
    "provenance_record_id",
    "build_id",
    "schema_version",
    "acquisition_manifest_sha256",
)
_SEAD_DICTIONARY_FIELDS: Final = frozenset(
    {
        "source_table",
        "subject_type",
        "claim_type",
        "source_age_type",
        "source_age_unit",
        "original_interval_orientation",
        "calibration_status",
        "comparability_status",
        "chronology_eligibility",
        "propagation_eligibility",
        "publication_role",
        "transformation_id",
        "selection_status",
        "selection_rule_version",
        "observation_link_status",
    }
)
_SEAD_LIST_DICTIONARY_FIELDS: Final = frozenset(
    {"propagation_reason_codes", "reason_codes"}
)
_SEAD_EVIDENCE_DOCUMENTS: Final = (
    "chronology_claims.json",
    "source_native_observations.json",
    "observation_relation_index.json",
    "evidence_events.json",
)
_SEAD_OBSERVATION_FIELDS: Final = (
    "observation_id",
    "source_table",
    "source_record_id",
    "entity_relation_id",
    "analysis_entity_id",
    "physical_sample_id",
    "sample_group_id",
    "dataset_id",
    "source_value",
    "source_value_field",
    "source_value_state",
    "source_unit_id",
    "unit_status",
    "value_semantics_id",
    "dataset_semantics_id",
    "dataset_semantics_status",
    "taxon_relation_id",
    "taxon_status",
    "dimension_relation_ids",
    "dimension_status",
    "chronology_link_status",
    "chronology_claim_count",
    "chronology_eligible_claim_count",
    "event_eligibility",
    "event_refusal_reason_codes",
    "source_payload_sha256",
)
_SEAD_OBSERVATION_DICTIONARY_FIELDS: Final = frozenset(
    {
        "source_table",
        "source_value_field",
        "source_value_state",
        "unit_status",
        "dataset_semantics_status",
        "taxon_status",
        "dimension_status",
        "chronology_link_status",
        "event_eligibility",
    }
)
_SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS: Final = frozenset(
    {"event_refusal_reason_codes"}
)
_SEAD_ENTITY_FIELDS: Final = (
    "entity_relation_id",
    "analysis_entity_id",
    "physical_sample_id",
    "sample_group_id",
    "dataset_id",
    "chronology_claim_ids",
    "eligible_chronology_claim_ids",
)
_SEAD_TAXON_FIELDS: Final = (
    "taxon_relation_id",
    "taxon_id",
    "species",
    "genus_name",
    "family_name",
    "order_name",
    "author_name",
    "source_ecocodes",
    "derived_classification_status",
)
_SEAD_DIMENSION_FIELDS: Final = (
    "dimension_relation_id",
    "owner_kind",
    "owner_id",
    "source_table",
    "source_record_id",
    "dimension_semantics_id",
    "dimension_value",
    "qualifier_id",
    "unit_status",
)
_SEAD_DIMENSION_SEMANTIC_FIELDS: Final = (
    "dimension_semantics_id",
    "dimension_id",
    "dimension_name",
    "dimension_abbrev",
    "dimension_description",
    "source_unit_id",
    "unit_name",
    "unit_abbrev",
    "unit_description",
    "unit_status",
)
_SEAD_DATASET_SEMANTIC_FIELDS: Final = (
    "dataset_semantics_id",
    "dataset_id",
    "dataset_uuid",
    "dataset_name",
    "data_type_id",
    "data_type_name",
    "data_type_group_name",
)
_SEAD_VALUE_SEMANTIC_FIELDS: Final = (
    "value_semantics_id",
    "value_class_id",
    "value_class_name",
    "value_class_description",
    "value_type_id",
    "value_type_name",
    "base_type",
    "source_unit_id",
    "unit_name",
    "unit_abbrev",
    "unit_description",
)
_SEAD_SOURCE_AGE_INHERITED_FIELDS: Final = {
    "analysis_entity_id": "analysis_entity_id",
    "physical_sample_id": "physical_sample_id",
    "sample_group_id": "sample_group_id",
    "dataset_id": "dataset_id",
    "analysis_value_id": "analysis_value_id",
}
_SEAD_RELATION_VALUE_FIELDS: Final = {
    "site_id": "common_fields.source_site_id",
    "sample_group_id": "sample_group_id",
    "physical_sample_id": "physical_sample_id",
    "analysis_entity_id": "analysis_entity_id",
    "dataset_id": "dataset_id",
    "analysis_value_id": "analysis_value_id",
    "analysis_dating_range_id": "source_record_id",
    "dendro_date_id": "source_record_id",
    "relative_date_id": "source_record_id",
    "geochron_id": "source_record_id",
    "analysis_entity_age_id": "source_record_id",
}


@dataclass(frozen=True)
class MapEvidenceProjection:
    """Deterministic detail records and their feature/detail accounting."""

    detail_records: tuple[JsonObject, ...]
    reconciliation: JsonObject


def build_map_evidence_projection(
    context_root: Path,
    point_layers: Sequence[MutableMapping[str, object]],
) -> MapEvidenceProjection:
    """Bind governed source evidence to map features through stable record IDs.

    The caller-owned point-layer dictionaries are annotated with source-qualified
    ``record_id`` values. Repeated chronology features for one SEAD site share its
    site detail record; the feature retains its own interval and native locator.
    """
    root = _regular_absolute_directory(context_root, "atlas context root")
    selected_layers = {
        _required_text(layer.get("key"), "point layer key"): layer
        for layer in point_layers
        if str(layer.get("key", "")).strip() in {_NEOTOMA_LAYER_KEY, *_SEAD_LAYER_KEYS}
    }
    records: list[dict[str, object]] = []
    source_accounting: dict[str, dict[str, object]] = {}

    neotoma_layer = selected_layers.get(_NEOTOMA_LAYER_KEY)
    if neotoma_layer is not None:
        neotoma_records, neotoma_accounting = _project_neotoma(root, neotoma_layer)
        records.extend(neotoma_records)
        source_accounting["neotoma"] = neotoma_accounting

    sead_layers = [
        selected_layers[key]
        for key in sorted(_SEAD_LAYER_KEYS & selected_layers.keys())
    ]
    if sead_layers:
        sead_records, sead_accounting = _project_sead(root, sead_layers)
        records.extend(sead_records)
        source_accounting["sead"] = sead_accounting

    records.sort(key=lambda row: str(row["record_id"]))
    record_ids = [str(row["record_id"]) for row in records]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("atlas evidence projection produced duplicate detail records")

    relevant_features = [
        feature for layer in selected_layers.values() for feature in _features(layer)
    ]
    feature_record_ids = [
        _required_text(row.get("record_id"), "feature record_id")
        for row in relevant_features
    ]
    unmatched = sorted(set(feature_record_ids) - set(record_ids))
    unreferenced = sorted(set(record_ids) - set(feature_record_ids))
    if unmatched or unreferenced:
        raise ValueError(
            "atlas evidence projection does not reconcile; "
            f"unmatched_features={unmatched[:5]}, unreferenced_details={unreferenced[:5]}"
        )
    tab_counts = {
        tab: {
            "available": sum(
                1 for record in records if not _is_unavailable(_tabs(record)[tab])
            ),
            "unavailable": sum(
                1 for record in records if _is_unavailable(_tabs(record)[tab])
            ),
            "denominator": len(records),
        }
        for tab in DETAIL_TAB_KEYS
    }
    reconciliation: dict[str, object] = {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "status": "reconciled",
        "source_layer_count": len(selected_layers),
        "source_feature_count": len(relevant_features),
        "matched_feature_count": len(feature_record_ids),
        "detail_record_count": len(records),
        "unique_feature_record_id_count": len(set(feature_record_ids)),
        "repeated_feature_reference_count": len(feature_record_ids)
        - len(set(feature_record_ids)),
        "unmatched_feature_count": 0,
        "unreferenced_detail_count": 0,
        "tab_availability": tab_counts,
        "sources": source_accounting,
    }
    return MapEvidenceProjection(
        detail_records=tuple(cast(JsonObject, row) for row in records),
        reconciliation=reconciliation,
    )


def _project_neotoma(
    context_root: Path,
    layer: MutableMapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    relational_root = context_root / "neotoma" / "relational"
    manifest = validate_neotoma_relational_materialization(relational_root.absolute())
    sites = _unique_rows(
        _load_neotoma_surface(relational_root, manifest, "sites"),
        "site_id",
        "Neotoma sites",
    )
    collection_rows = _compact_rows_by_site(
        _load_neotoma_surface(relational_root, manifest, "collection_units"),
        fields=("collection_unit_id", "source_collection_unit_id", "source_payload"),
        label="Neotoma collection unit",
    )
    dataset_rows = _compact_rows_by_site(
        _load_neotoma_surface(relational_root, manifest, "datasets"),
        fields=(
            "dataset_id",
            "collection_unit_id",
            "source_dataset_id",
            "source_payload",
        ),
        label="Neotoma dataset",
    )
    sample_rows = _compact_rows_by_site(
        _load_neotoma_surface(relational_root, manifest, "samples"),
        fields=(
            "sample_id",
            "collection_unit_id",
            "dataset_id",
            "source_sample_id",
            "source_analysis_unit_id",
            "source_payload",
        ),
        label="Neotoma sample",
    )
    age_fields = (
        "chronology_claim_id",
        "subject_type",
        "subject_id",
        "source_record_id",
        "chronology_id",
        "chronology_name",
        "collection_unit_id",
        "dataset_id",
        "source_age_type",
        "source_age_unit",
        "source_age_value",
        "source_age_younger",
        "source_age_older",
        "younger_bp",
        "older_bp",
        "calibration_status",
        "comparability_status",
        "admission_reason",
        "refusal_reason",
        "is_default_chronology",
        "provenance_record_id",
        "source_relation_path",
    )
    age_rows = _compact_rows_by_site(
        _load_neotoma_surface(relational_root, manifest, "age_claims"),
        fields=age_fields,
        label="Neotoma age claim",
    )
    observation_fields = (
        "observation_id",
        "sample_id",
        "variable_id",
        "source_taxon_id",
        "source_value",
        "source_unit",
        "source_denominator",
        "denominator_status",
        "detection_status",
        "source_context",
        "source_ecological_group",
        "source_element",
        "source_element_type",
        "aggregation_key",
        "unit_family",
        "source_part_number",
    )
    observation_rows = _compact_rows_by_site(
        _load_neotoma_surface(relational_root, manifest, "observations"),
        fields=observation_fields,
        label="Neotoma observation",
    )
    variable_fields = (
        "variable_id",
        "source_taxon_id",
        "source_reported_name",
        "source_semantics",
        "source_units",
    )
    variables = _unique_rows(
        _load_neotoma_surface(relational_root, manifest, "variables"),
        "variable_id",
        "Neotoma variables",
    )
    site_ids = set(sites)
    for label, grouped_rows in (
        ("collection units", collection_rows),
        ("datasets", dataset_rows),
        ("samples", sample_rows),
        ("age claims", age_rows),
        ("observations", observation_rows),
    ):
        unknown_site_ids = sorted(set(grouped_rows) - site_ids)
        if unknown_site_ids:
            raise ValueError(
                f"Neotoma {label} reference unknown sites: {unknown_site_ids[:5]}"
            )
    referenced_variable_ids = {
        _required_text(row[2], "Neotoma observation variable ID")
        for rows in observation_rows.values()
        for row in rows
    }
    if referenced_variable_ids != set(variables):
        raise ValueError("Neotoma variable and observation identities do not reconcile")

    source_snapshot_id = _required_text(
        manifest.get("source_snapshot_id"), "Neotoma source snapshot ID"
    )
    build_id = _required_text(manifest.get("build_id"), "Neotoma build ID")
    materialization_sha256 = _required_text(
        manifest.get("materialization_sha256"), "Neotoma materialization SHA-256"
    )
    records: list[dict[str, object]] = []
    observed_sites: set[str] = set()
    features = _features(layer)
    for feature in features:
        source_site_id = _required_text(
            feature.get("evidence_row_id"), "Neotoma feature evidence_row_id"
        )
        site_id = f"neotoma:site:{source_site_id}"
        site = sites.get(site_id)
        if site is None:
            raise ValueError(f"Neotoma map feature has no relational site: {site_id}")
        _set_feature_record_id(feature, site_id)
        if site_id in observed_sites:
            raise ValueError(f"Neotoma map features duplicate site identity: {site_id}")
        observed_sites.add(site_id)
        site_age_rows = age_rows[site_id]
        site_observation_rows = observation_rows[site_id]
        site_variable_ids = sorted(
            {
                _required_text(row[2], "Neotoma observation variable ID")
                for row in site_observation_rows
            }
        )
        missing_variables = [
            variable_id
            for variable_id in site_variable_ids
            if variable_id not in variables
        ]
        if missing_variables:
            raise ValueError(
                f"Neotoma observations reference unknown variables: {missing_variables[:5]}"
            )
        site_variable_rows = [
            [variables[variable_id].get(field) for field in variable_fields]
            for variable_id in site_variable_ids
        ]
        records.append(
            {
                "record_id": site_id,
                "tabs": {
                    "overview": {
                        "source_family": "neotoma",
                        "site_id": site_id,
                        "source_site_id": source_site_id,
                        "country_code": site.get("country_code"),
                        "country_decision_status": site.get("country_decision_status"),
                    },
                    "samples": {
                        "collection_units": _row_table(
                            (
                                "collection_unit_id",
                                "source_collection_unit_id",
                                "source_payload",
                            ),
                            collection_rows[site_id],
                        ),
                        "datasets": _row_table(
                            (
                                "dataset_id",
                                "collection_unit_id",
                                "source_dataset_id",
                                "source_payload",
                            ),
                            dataset_rows[site_id],
                        ),
                        "samples": _row_table(
                            (
                                "sample_id",
                                "collection_unit_id",
                                "dataset_id",
                                "source_sample_id",
                                "source_analysis_unit_id",
                                "source_payload",
                            ),
                            sample_rows[site_id],
                        ),
                    },
                    "chronology": (
                        {
                            **_row_table(
                                age_fields,
                                site_age_rows,
                                identifier_prefixes={
                                    "chronology_claim_id": "neotoma:age-claim:",
                                    "subject_id": "neotoma:sample:",
                                    "source_record_id": "neotoma:sample:",
                                    "chronology_id": "neotoma:chronology:",
                                    "collection_unit_id": "neotoma:collection-unit:",
                                    "dataset_id": "neotoma:dataset:",
                                },
                            ),
                            "interval_semantics": "[younger_bp, older_bp]",
                            "null_semantics": "source null remains null",
                            "selection_posture": "all source age assignments retained",
                        }
                        if site_age_rows
                        else _unavailable("neotoma_site_age_claims_not_available")
                    ),
                    "pollen_composition": (
                        {
                            **_row_table(
                                observation_fields,
                                site_observation_rows,
                                identifier_prefixes={
                                    "observation_id": "neotoma:observation:",
                                    "sample_id": "neotoma:sample:",
                                    "variable_id": "neotoma:variable:",
                                    "aggregation_key": "neotoma:exact-unit:",
                                },
                            ),
                            "variables": _row_table(
                                variable_fields,
                                site_variable_rows,
                                identifier_prefixes={
                                    "variable_id": "neotoma:variable:"
                                },
                            ),
                            "aggregation_posture": "source rows retained without cross-unit summing",
                            "classification_status": "not_accepted",
                        }
                        if site_observation_rows
                        else _unavailable("neotoma_site_observations_not_available")
                    ),
                    "relation": dict(_UNAVAILABLE_RELATION),
                    "classification": dict(_UNAVAILABLE_CLASSIFICATION),
                    "provenance": {
                        "source_snapshot_id": source_snapshot_id,
                        "build_id": build_id,
                        "materialization_sha256": materialization_sha256,
                        "record_locator": f"surfaces/sites#site_id={site_id}",
                        "compact_lineage_path": "data/neotoma/review/compact_relational_lineage.json",
                        "observation_locator_contract": "surfaces/observations/part-{source_part_number:05d}.json#observation_id={observation_id}",
                    },
                },
            }
        )
    if observed_sites != set(sites):
        raise ValueError("Neotoma map and relational site identities do not reconcile")
    detail_row_counts = {
        "collection_units": sum(len(rows) for rows in collection_rows.values()),
        "datasets": sum(len(rows) for rows in dataset_rows.values()),
        "samples": sum(len(rows) for rows in sample_rows.values()),
        "age_claims": sum(len(rows) for rows in age_rows.values()),
        "observations": sum(len(rows) for rows in observation_rows.values()),
        "variables": len(variables),
    }
    return records, {
        "source_feature_count": len(features),
        "source_site_denominator": len(sites),
        "projected_site_count": len(records),
        "unprojected_source_site_count": len(sites) - len(records),
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
        "materialization_sha256": materialization_sha256,
        "detail_row_counts": detail_row_counts,
        "detail_row_denominators": dict(detail_row_counts),
    }


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


def _compact_sead_observation(
    observation: Mapping[str, object],
    *,
    entity_by_id: Mapping[str, Mapping[str, object]],
    refusal_by_observation: Mapping[str, Mapping[str, object]],
    taxon_by_id: Mapping[str, Mapping[str, object]],
    dimension_by_id: Mapping[str, Mapping[str, object]],
    dataset_semantic_by_id: Mapping[str, Mapping[str, object]],
    value_semantic_by_id: Mapping[str, Mapping[str, object]],
) -> tuple[
    list[object],
    str,
    tuple[str | None, tuple[str, ...], str | None, str | None],
]:
    observation_id = _required_text(
        observation.get("observation_id"), "SEAD observation ID"
    )
    if observation.get("source_family") != "sead":
        raise ValueError("SEAD observation source family changed")
    entity_id = _required_text(
        observation.get("entity_relation_id"), "SEAD observation entity relation"
    )
    entity = entity_by_id.get(entity_id)
    if entity is None:
        raise ValueError("SEAD observation references unknown entity relation")
    site_id = _identifier_text(entity.get("site_id"), "SEAD entity site ID")
    if observation.get("country_code") != entity.get("country_code"):
        raise ValueError("SEAD observation country disagrees with entity relation")
    source_value = observation.get("source_value")
    source_value_state = _required_text(
        observation.get("source_value_state"), "SEAD observation value state"
    )
    if (source_value is None) is not (source_value_state == "source_null"):
        raise ValueError("SEAD source null and value state disagree")

    chronology = _mapping(
        observation.get("chronology_link"), "SEAD observation chronology link"
    )
    entity_chronology = _mapping(
        entity.get("chronology_link"), "SEAD entity chronology link"
    )
    claim_ids = entity_chronology.get("claim_ids")
    eligible_claim_ids = entity_chronology.get("eligible_claim_ids")
    if not isinstance(claim_ids, list) or not isinstance(eligible_claim_ids, list):
        raise ValueError("SEAD entity chronology IDs must be lists")
    if chronology.get("claim_count") != len(claim_ids) or chronology.get(
        "eligible_claim_count"
    ) != len(eligible_claim_ids):
        raise ValueError("SEAD observation chronology counts do not reconcile")
    if chronology.get("entity_relation_id") != entity_id:
        raise ValueError("SEAD observation chronology relation changed")

    refusal = refusal_by_observation.get(observation_id)
    if refusal is None or refusal.get("status") != "refused":
        raise ValueError("SEAD observation lacks its event refusal")
    refusal_reasons = observation.get("event_refusal_reason_codes")
    if not isinstance(refusal_reasons, list) or any(
        not isinstance(reason, str) or not reason for reason in refusal_reasons
    ):
        raise ValueError("SEAD event refusal reasons must be text rows")
    if refusal.get("reason_codes") != refusal_reasons:
        raise ValueError("SEAD observation and event refusal reasons differ")
    if "source_classification_not_accepted" not in refusal_reasons:
        raise ValueError("SEAD event refusal lacks classification reason")
    if observation.get("event_eligibility") != "refused":
        raise ValueError("SEAD observation event eligibility changed")

    semantics = _mapping(
        observation.get("source_semantics"), "SEAD observation semantics"
    )
    dataset_id_value = semantics.get("dataset_semantics_id")
    dataset_id = (
        None
        if dataset_id_value is None
        else _required_text(dataset_id_value, "SEAD dataset semantics ID")
    )
    dataset_status = _required_text(
        semantics.get("dataset_semantics_status"), "SEAD dataset semantics status"
    )
    if (dataset_id is None) is not (dataset_status == "not_exposed_by_relation"):
        raise ValueError("SEAD dataset semantics identity and status disagree")
    if dataset_id is not None and dataset_id not in dataset_semantic_by_id:
        raise ValueError("SEAD observation references unknown dataset semantics")
    value_id_value = semantics.get("value_semantics_id")
    value_id = (
        None
        if value_id_value is None
        else _required_text(value_id_value, "SEAD value semantics ID")
    )
    if value_id is not None and value_id not in value_semantic_by_id:
        raise ValueError("SEAD observation references unknown value semantics")
    taxon_id_value = observation.get("taxon_relation_id")
    taxon_id = (
        None
        if taxon_id_value is None
        else _required_text(taxon_id_value, "SEAD taxon relation ID")
    )
    if taxon_id is not None and taxon_id not in taxon_by_id:
        raise ValueError("SEAD observation references unknown taxon relation")
    raw_dimension_ids = observation.get("dimension_relation_ids")
    if not isinstance(raw_dimension_ids, list) or any(
        not isinstance(value, str) or not value for value in raw_dimension_ids
    ):
        raise ValueError("SEAD observation dimension relation IDs must be text rows")
    dimension_ids = tuple(cast(list[str], raw_dimension_ids))
    if len(dimension_ids) != len(set(dimension_ids)):
        raise ValueError("SEAD observation dimension relations are duplicated")
    if any(dimension_id not in dimension_by_id for dimension_id in dimension_ids):
        raise ValueError("SEAD observation references unknown dimension relation")

    compact = [
        observation_id,
        observation.get("source_table"),
        observation.get("source_record_id"),
        entity_id,
        entity.get("analysis_entity_id"),
        entity.get("physical_sample_id"),
        entity.get("sample_group_id"),
        entity.get("dataset_id"),
        source_value,
        observation.get("source_value_field"),
        source_value_state,
        semantics.get("source_unit_id"),
        semantics.get("unit_status"),
        value_id,
        dataset_id,
        dataset_status,
        taxon_id,
        observation.get("taxon_status"),
        list(dimension_ids),
        observation.get("dimension_status"),
        chronology.get("status"),
        chronology.get("claim_count"),
        chronology.get("eligible_claim_count"),
        observation.get("event_eligibility"),
        refusal_reasons,
        observation.get("source_payload_sha256"),
    ]
    return compact, site_id, (taxon_id, dimension_ids, dataset_id, value_id)


def _sead_observation_table(rows: Sequence[Sequence[object]]) -> dict[str, object]:
    field_indexes = {
        field: index for index, field in enumerate(_SEAD_OBSERVATION_FIELDS)
    }
    dictionaries: dict[str, list[str]] = {}
    dictionary_indexes: dict[str, dict[str, int]] = {}
    for field in sorted(_SEAD_OBSERVATION_DICTIONARY_FIELDS):
        index = field_indexes[field]
        values = sorted(
            {_required_text(row[index], f"SEAD observation {field}") for row in rows}
        )
        dictionaries[field] = values
        dictionary_indexes[field] = {
            value: value_index for value_index, value in enumerate(values)
        }
    list_values = sorted(
        {
            value
            for field in _SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS
            for row in rows
            for value in cast(list[str], row[field_indexes[field]])
        }
    )
    list_value_indexes = {
        value: value_index for value_index, value in enumerate(list_values)
    }
    encoded_rows: list[list[object]] = []
    for row in rows:
        if len(row) != len(_SEAD_OBSERVATION_FIELDS):
            raise ValueError("SEAD compact observation fields changed")
        encoded = list(row)
        for field, indexes in dictionary_indexes.items():
            index = field_indexes[field]
            encoded[index] = indexes[cast(str, encoded[index])]
        for field in _SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS:
            index = field_indexes[field]
            encoded[index] = [
                list_value_indexes[value] for value in cast(list[str], encoded[index])
            ]
        encoded_rows.append(encoded)
    return {
        "record_count": len(encoded_rows),
        "fields": list(_SEAD_OBSERVATION_FIELDS),
        "records": encoded_rows,
        "encoding": "sead-source-native-observation-table.v1",
        "column_dictionaries": dictionaries,
        "list_dictionary_fields": sorted(_SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS),
        "list_value_dictionary": list_values,
    }


def _compact_sead_entity(row: Mapping[str, object]) -> list[object]:
    chronology = _mapping(row.get("chronology_link"), "SEAD entity chronology")
    return [
        row.get("entity_relation_id"),
        row.get("analysis_entity_id"),
        row.get("physical_sample_id"),
        row.get("sample_group_id"),
        row.get("dataset_id"),
        chronology.get("claim_ids"),
        chronology.get("eligible_claim_ids"),
    ]


def _compact_sead_taxon(row: Mapping[str, object]) -> list[object]:
    taxon = _mapping(row.get("taxon"), "SEAD native taxon")
    genus = _optional_mapping(row.get("genus"), "SEAD native taxon genus")
    family = _optional_mapping(row.get("family"), "SEAD native taxon family")
    order = _optional_mapping(row.get("order"), "SEAD native taxon order")
    author = _optional_mapping(row.get("author"), "SEAD native taxon author")
    return [
        row.get("taxon_relation_id"),
        row.get("taxon_id"),
        taxon.get("species"),
        genus.get("genus_name"),
        family.get("family_name"),
        order.get("order_name"),
        author.get("author_name"),
        row.get("source_ecocodes"),
        row.get("derived_classification_status"),
    ]


def _compact_sead_dimension(row: Mapping[str, object]) -> list[object]:
    source_row = _mapping(row.get("source_row"), "SEAD dimension source row")
    return [
        row.get("dimension_relation_id"),
        row.get("owner_kind"),
        row.get("owner_id"),
        row.get("source_table"),
        row.get("source_record_id"),
        row.get("dimension_semantics_id"),
        source_row.get("dimension_value"),
        source_row.get("qualifier_id"),
        row.get("unit_status"),
    ]


def _compact_sead_dimension_semantics(row: Mapping[str, object]) -> list[object]:
    dimension = _mapping(row.get("source_dimension"), "SEAD dimension semantics")
    unit = _mapping(row.get("source_unit"), "SEAD dimension unit")
    return [
        row.get("dimension_semantics_id"),
        row.get("dimension_id"),
        dimension.get("dimension_name"),
        dimension.get("dimension_abbrev"),
        dimension.get("dimension_description"),
        row.get("source_unit_id"),
        unit.get("unit_name"),
        unit.get("unit_abbrev"),
        unit.get("description"),
        row.get("unit_status"),
    ]


def _compact_sead_dataset_semantics(row: Mapping[str, object]) -> list[object]:
    dataset = _mapping(row.get("dataset"), "SEAD dataset semantics")
    data_type = _mapping(row.get("source_data_type"), "SEAD source data type")
    group = _mapping(row.get("source_data_type_group"), "SEAD source data type group")
    return [
        row.get("dataset_semantics_id"),
        dataset.get("dataset_id"),
        dataset.get("dataset_uuid"),
        dataset.get("dataset_name"),
        dataset.get("data_type_id"),
        data_type.get("data_type_name"),
        group.get("data_type_group_name"),
    ]


def _compact_sead_value_semantics(row: Mapping[str, object]) -> list[object]:
    value_class = _mapping(row.get("value_class"), "SEAD value class")
    value_type = _mapping(row.get("source_value_type"), "SEAD value type")
    raw_unit = row.get("source_unit")
    unit = raw_unit if isinstance(raw_unit, Mapping) else {}
    return [
        row.get("value_semantics_id"),
        value_class.get("value_class_id"),
        value_class.get("name"),
        value_class.get("description"),
        value_type.get("value_type_id"),
        value_type.get("name"),
        value_type.get("base_type"),
        unit.get("unit_id"),
        unit.get("unit_name"),
        unit.get("unit_abbrev"),
        unit.get("description"),
    ]


def _optional_mapping(value: object, label: str) -> Mapping[str, object]:
    if value is None:
        return {}
    return _mapping(value, label)


def _sead_claim_table(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Encode complete SEAD claims without repeating shared source vocabulary."""
    if not rows:
        raise ValueError("SEAD chronology claim table cannot be empty")
    ordered = sorted(
        rows,
        key=lambda row: _required_text(
            row.get("chronology_claim_id"), "SEAD chronology claim ID"
        ),
    )
    required_fields = {*_SEAD_CLAIM_FIELDS, *_SEAD_CLAIM_COMMON_FIELDS}
    for row in ordered:
        missing = sorted(required_fields - set(row))
        if missing:
            raise ValueError(f"SEAD chronology claim fields are missing: {missing}")
        for field in (
            "chronology_claim_id",
            "source_family",
            "source_table",
            "site_uuid",
            "source_site_id",
            "country_code",
            "country_assignment_method",
            "subject_type",
            "claim_type",
            "source_age_type",
            "source_age_unit",
            "original_interval_orientation",
            "calibration_status",
            "comparability_status",
            "chronology_eligibility",
            "propagation_eligibility",
            "publication_role",
            "selection_status",
            "selection_rule_version",
            "provenance_record_id",
            "build_id",
            "schema_version",
            "source_payload_sha256",
            "acquisition_manifest_sha256",
        ):
            _required_text(row.get(field), f"SEAD chronology claim {field}")
        for field in ("source_record_id", "source_native_record_id", "subject_id"):
            _identifier_text(row.get(field), f"SEAD chronology claim {field}")

    common_fields: dict[str, object] = {}
    for field in _SEAD_CLAIM_COMMON_FIELDS:
        value = ordered[0].get(field)
        if any(row.get(field) != value for row in ordered[1:]):
            raise ValueError(f"SEAD site claims disagree on shared field: {field}")
        common_fields[field] = value
    if common_fields["source_family"] != "sead":
        raise ValueError("SEAD chronology claim source family changed")

    column_dictionaries: dict[str, list[object]] = {}
    column_dictionary_indexes: dict[str, dict[object, int]] = {}
    for field in sorted(_SEAD_DICTIONARY_FIELDS):
        raw_dictionary_values = [row.get(field) for row in ordered]
        if any(
            value is not None and not isinstance(value, str)
            for value in raw_dictionary_values
        ):
            raise ValueError(f"SEAD chronology claim {field} must be text or null")
        dictionary_values = sorted(
            set(raw_dictionary_values),
            key=lambda value: (value is not None, str(value)),
        )
        column_dictionaries[field] = dictionary_values
        column_dictionary_indexes[field] = {
            value: index for index, value in enumerate(dictionary_values)
        }

    list_values: set[str] = set()
    for field in _SEAD_LIST_DICTIONARY_FIELDS:
        for row in ordered:
            raw_values = row.get(field)
            if not isinstance(raw_values, list) or any(
                not isinstance(value, str) or not value for value in raw_values
            ):
                raise ValueError(f"SEAD chronology claim {field} must be text rows")
            list_values.update(cast(list[str], raw_values))
    list_value_dictionary = sorted(list_values)
    list_value_indexes = {
        value: index for index, value in enumerate(list_value_dictionary)
    }

    source_age_columns: dict[str, list[str]] = {}
    source_age_inherited: dict[str, dict[str, str]] = {}
    source_age_dictionaries: dict[str, dict[str, list[object]]] = {}
    source_age_dictionary_indexes: dict[str, dict[str, dict[object, int]]] = {}
    claim_types = sorted(
        {
            _required_text(row.get("claim_type"), "SEAD chronology claim type")
            for row in ordered
        }
    )
    for claim_type in claim_types:
        type_rows = [row for row in ordered if row.get("claim_type") == claim_type]
        age_values = [
            _mapping(row.get("source_age_value"), "SEAD source age value")
            for row in type_rows
        ]
        source_keys = set(age_values[0])
        if any(set(value) != source_keys for value in age_values[1:]):
            raise ValueError(
                f"SEAD {claim_type} source age value fields are inconsistent"
            )
        inherited: dict[str, str] = {}
        for source_field, claim_field in _SEAD_SOURCE_AGE_INHERITED_FIELDS.items():
            if source_field not in source_keys:
                continue
            if any(
                value.get(source_field) != row.get(claim_field)
                for row, value in zip(type_rows, age_values, strict=True)
            ):
                raise ValueError(
                    f"SEAD {claim_type} source age {source_field} disagrees with claim"
                )
            inherited[source_field] = claim_field
        columns = sorted(source_keys - set(inherited))
        source_age_columns[claim_type] = columns
        source_age_inherited[claim_type] = inherited
        dictionaries: dict[str, list[object]] = {}
        dictionary_indexes: dict[str, dict[object, int]] = {}
        for field in columns:
            values = [value.get(field) for value in age_values]
            if all(value is None or isinstance(value, str) for value in values):
                dictionary = sorted(
                    set(values), key=lambda value: (value is not None, str(value))
                )
                dictionaries[field] = dictionary
                dictionary_indexes[field] = {
                    value: index for index, value in enumerate(dictionary)
                }
        source_age_dictionaries[claim_type] = dictionaries
        source_age_dictionary_indexes[claim_type] = dictionary_indexes

    relation_shapes: list[list[list[str]]] = []
    encoded_rows: list[list[object]] = []
    for row in ordered:
        claim_type = _required_text(row.get("claim_type"), "SEAD chronology claim type")
        relation_path = row.get("source_relation_path")
        if not isinstance(relation_path, list) or not relation_path:
            raise ValueError("SEAD chronology claim relation path is missing")
        relation_shape: list[list[str]] = []
        for raw_entry in relation_path:
            entry = _mapping(raw_entry, "SEAD chronology relation entry")
            if set(entry) != {"table", "key", "value"}:
                raise ValueError("SEAD chronology relation entry fields changed")
            table = _required_text(entry.get("table"), "SEAD relation table")
            key = _required_text(entry.get("key"), "SEAD relation key")
            value_field = _SEAD_RELATION_VALUE_FIELDS.get(key)
            if value_field is None:
                raise ValueError(f"SEAD chronology relation key is unsupported: {key}")
            expected = (
                common_fields["source_site_id"]
                if value_field == "common_fields.source_site_id"
                else row.get(value_field)
            )
            if _identifier_text(entry.get("value"), "SEAD relation value") != (
                _identifier_text(expected, f"SEAD claim {value_field}")
            ):
                raise ValueError(
                    f"SEAD chronology relation {key} disagrees with its claim"
                )
            relation_shape.append([table, key, value_field])
        if relation_shape not in relation_shapes:
            relation_shapes.append(relation_shape)
        relation_index = relation_shapes.index(relation_shape)

        encoded: list[object] = []
        for field in _SEAD_CLAIM_FIELDS:
            value = row.get(field)
            if field in column_dictionary_indexes:
                value = column_dictionary_indexes[field][value]
            elif field in _SEAD_LIST_DICTIONARY_FIELDS:
                value = [list_value_indexes[item] for item in cast(list[str], value)]
            elif field == "source_age_value":
                source_age_value = _mapping(value, "SEAD source age value")
                value = [
                    source_age_dictionary_indexes[claim_type]
                    .get(source_field, {})
                    .get(
                        source_age_value.get(source_field),
                        source_age_value.get(source_field),
                    )
                    for source_field in source_age_columns[claim_type]
                ]
            elif field == "source_relation_path":
                value = relation_index
            encoded.append(value)
        encoded_rows.append(encoded)

    return {
        "record_count": len(encoded_rows),
        "fields": list(_SEAD_CLAIM_FIELDS),
        "records": encoded_rows,
        "encoding": "sead-chronology-claim-table.v1",
        "common_fields": common_fields,
        "column_dictionaries": column_dictionaries,
        "list_dictionary_fields": sorted(_SEAD_LIST_DICTIONARY_FIELDS),
        "list_value_dictionary": list_value_dictionary,
        "source_age_value_columns_by_claim_type": source_age_columns,
        "source_age_value_inherited_fields_by_claim_type": source_age_inherited,
        "source_age_value_dictionaries_by_claim_type": source_age_dictionaries,
        "source_relation_path_dictionary": relation_shapes,
        "source_relation_path_value_semantics": (
            "Each relation tuple is [table, key, claim/common field containing value]."
        ),
    }


def _validate_sead_claim_parents(
    acquisition_root: Path, claims_bundle: Mapping[str, object]
) -> Mapping[str, object]:
    root = _regular_absolute_directory(acquisition_root, "SEAD acquisition root")
    admission = _read_json_object(root / "admission.json", "SEAD admission")
    if admission.get("schema_version") != "sead-acquisition-admission.v1":
        raise ValueError("SEAD admission schema is unsupported")
    for field, claim_field in (
        ("run_id", "source_run_id"),
        ("build_id", "source_build_id"),
        ("acquisition_manifest_sha256", "acquisition_manifest_sha256"),
        ("acquisition_bundle_sha256", "acquisition_bundle_sha256"),
    ):
        if admission.get(field) != claims_bundle.get(claim_field):
            raise ValueError(f"SEAD admission and claim bundle {field} differ")
    copied_rows = admission.get("copied_files")
    if not isinstance(copied_rows, list) or any(
        not isinstance(row, Mapping) for row in copied_rows
    ):
        raise ValueError("SEAD admission copied-file inventory is invalid")
    copied = {
        _safe_relative_path(row.get("path")): row
        for row in cast(list[Mapping[str, object]], copied_rows)
    }
    if len(copied) != len(copied_rows):
        raise ValueError("SEAD admission copied-file paths are duplicated")
    required: dict[str, str] = {
        "manifest.json": _required_text(
            admission.get("acquisition_manifest_sha256"),
            "SEAD acquisition manifest SHA-256",
        ),
        "country-decisions.json": _required_text(
            claims_bundle.get("country_decisions_sha256"),
            "SEAD country decisions SHA-256",
        ),
    }
    table_digests = _mapping(
        claims_bundle.get("table_payload_sha256"), "SEAD table payload digests"
    )
    for table, digest in table_digests.items():
        required[f"payloads/{table}.json"] = _required_text(
            digest, f"SEAD {table} payload SHA-256"
        )
    for relative_path, expected_digest in required.items():
        copied_row = copied.get(relative_path)
        if copied_row is None or copied_row.get("sha256") != expected_digest:
            raise ValueError(f"SEAD admitted parent is not declared: {relative_path}")
        payload = _read_regular_bytes(root / relative_path, relative_path)
        if copied_row.get("byte_count") != len(payload):
            raise ValueError(f"SEAD admitted byte count changed: {relative_path}")
        if hashlib.sha256(payload).hexdigest() != expected_digest:
            raise ValueError(f"SEAD admitted digest changed: {relative_path}")
    return admission


def _load_neotoma_surface(
    root: Path, manifest: Mapping[str, object], surface_name: str
) -> list[Mapping[str, object]]:
    surfaces = _mapping(manifest.get("surfaces"), "Neotoma surfaces")
    surface = _mapping(surfaces.get(surface_name), f"Neotoma {surface_name} surface")
    parts = surface.get("parts")
    if not isinstance(parts, list) or any(
        not isinstance(row, Mapping) for row in parts
    ):
        raise ValueError(f"Neotoma {surface_name} parts are invalid")
    rows: list[Mapping[str, object]] = []
    for part_number, part_row in enumerate(
        cast(list[Mapping[str, object]], parts), start=1
    ):
        relative_path = _safe_relative_path(part_row.get("path"))
        expected_digest = _required_text(
            part_row.get("sha256"), f"Neotoma {relative_path} SHA-256"
        )
        payload_bytes = _read_regular_bytes(root / relative_path, relative_path)
        if hashlib.sha256(payload_bytes).hexdigest() != expected_digest:
            raise ValueError(f"Neotoma surface digest changed: {relative_path}")
        payload = _decode_json_object(payload_bytes, relative_path)
        raw_rows = payload.get("rows")
        if not isinstance(raw_rows, list) or any(
            not isinstance(row, Mapping) for row in raw_rows
        ):
            raise ValueError(f"Neotoma surface rows are invalid: {relative_path}")
        if payload.get("row_count") != len(raw_rows):
            raise ValueError(f"Neotoma surface row count changed: {relative_path}")
        rows.extend(
            {**row, "source_part_number": part_number}
            for row in cast(list[Mapping[str, object]], raw_rows)
        )
    if surface.get("row_count") != len(rows):
        raise ValueError(f"Neotoma {surface_name} row count does not reconcile")
    return rows


def _features(layer: Mapping[str, object]) -> list[MutableMapping[str, object]]:
    raw = layer.get("features")
    if not isinstance(raw, list) or any(
        not isinstance(row, MutableMapping) for row in raw
    ):
        raise ValueError("governed atlas point layer features must be mutable objects")
    return cast(list[MutableMapping[str, object]], raw)


def _set_feature_record_id(
    feature: MutableMapping[str, object], record_id: str
) -> None:
    current = feature.get("record_id")
    if current is not None and current != record_id:
        raise ValueError(
            "atlas feature record_id conflicts with governed source identity"
        )
    feature["record_id"] = record_id


def _unique_rows(
    rows: Sequence[Mapping[str, object]], key: str, label: str
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for row in rows:
        row_id = _identifier_text(row.get(key), f"{label} {key}")
        if row_id in result:
            raise ValueError(f"{label} contain duplicate {key}: {row_id}")
        result[row_id] = row
    return result


def _compact_rows_by_site(
    rows: Sequence[Mapping[str, object]],
    *,
    fields: Sequence[str],
    label: str,
) -> dict[str, list[list[object]]]:
    grouped: dict[str, list[list[object]]] = defaultdict(list)
    for row in rows:
        site_id = _required_text(row.get("site_id"), f"{label} site_id")
        grouped[site_id].append([row.get(field) for field in fields])
    return grouped


def _row_table(
    fields: Sequence[str],
    rows: Sequence[Sequence[object]],
    *,
    identifier_prefixes: Mapping[str, str] | None = None,
) -> dict[str, object]:
    prefixes = dict(identifier_prefixes or {})
    field_indexes = {field: index for index, field in enumerate(fields)}
    unknown_prefix_fields = sorted(set(prefixes) - set(field_indexes))
    if unknown_prefix_fields:
        raise ValueError(
            f"identifier prefixes name unknown fields: {unknown_prefix_fields}"
        )
    encoded_rows = [list(row) for row in rows]
    for field, prefix in prefixes.items():
        field_index = field_indexes[field]
        for row in encoded_rows:
            value = row[field_index]
            if value is None:
                continue
            if not isinstance(value, str) or not value.startswith(prefix):
                raise ValueError(
                    f"{field} does not match its declared identifier prefix"
                )
            row[field_index] = value.removeprefix(prefix)
    table: dict[str, object] = {
        "record_count": len(rows),
        "fields": list(fields),
        "records": encoded_rows,
    }
    if prefixes:
        table["identifier_prefixes"] = prefixes
    return table


def _non_null_unique(rows: Sequence[Mapping[str, object]], field: str) -> list[object]:
    values = {row.get(field) for row in rows if row.get(field) is not None}
    return sorted(values, key=lambda value: (type(value).__name__, str(value)))


def _tabs(record: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping(record.get("tabs"), "atlas detail tabs")


def _is_unavailable(value: object) -> bool:
    return isinstance(value, Mapping) and value.get("status") == "unavailable"


def _unavailable(reason_code: str) -> dict[str, object]:
    return {"status": "unavailable", "reason_code": reason_code}


def _regular_absolute_directory(path: Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError(f"{label} must be absolute")
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError(f"{label} must be a regular directory: {candidate}")
    return candidate


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    return _decode_json_object(_read_regular_bytes(path, label), label)


def _decode_json_object(payload: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return cast(dict[str, object], value)


def _read_regular_bytes(path: Path, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    return path.read_bytes()


def _safe_relative_path(value: object) -> str:
    text = _required_text(value, "artifact path")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"artifact path is unsafe: {text}")
    return path.as_posix()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return cast(Mapping[str, object], value)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _identifier_text(value: object, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{label} must be a text or integer identifier")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _numeric_text_key(value: str) -> tuple[int, int | str]:
    return (0, int(value)) if value.isdigit() else (1, value)


__all__ = [
    "MapEvidenceProjection",
    "PROJECTION_SCHEMA_VERSION",
    "build_map_evidence_projection",
]
