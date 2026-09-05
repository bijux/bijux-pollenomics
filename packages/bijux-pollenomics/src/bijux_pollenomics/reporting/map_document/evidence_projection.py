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
from .evidence import DETAIL_TAB_KEYS

PROJECTION_SCHEMA_VERSION: Final = "atlas-evidence-projection.v1"
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
    }
)
_SEAD_LIST_DICTIONARY_FIELDS: Final = frozenset(
    {"propagation_reason_codes", "reason_codes"}
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
    claims_path = context_root / "sead" / "normalized" / "chronology_claims.json"
    claims_bundle = _read_json_object(claims_path, "SEAD chronology claim bundle")
    if claims_bundle.get("schema_version") != "sead-chronology-claim-bundle.v1":
        raise ValueError("SEAD chronology claim bundle schema is unsupported")
    if claims_bundle.get("source_family") != "sead":
        raise ValueError("SEAD chronology claim bundle source family changed")
    run_id = _required_text(claims_bundle.get("source_run_id"), "SEAD source run ID")
    acquisition_root = context_root / "sead" / "raw" / "acquisitions" / run_id
    admission = _validate_sead_claim_parents(acquisition_root, claims_bundle)

    raw_claims = claims_bundle.get("claims")
    if not isinstance(raw_claims, list) or any(
        not isinstance(row, Mapping) for row in raw_claims
    ):
        raise ValueError("SEAD chronology claims must be object rows")
    if claims_bundle.get("claim_count") != len(raw_claims):
        raise ValueError("SEAD chronology claim count does not reconcile")
    claims_by_site: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    claim_ids: set[str] = set()
    for row in cast(list[Mapping[str, object]], raw_claims):
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
                            "coverage_posture": "chronology_linked_claim_rows_only",
                            "sample_group_ids": sample_group_ids,
                            "physical_sample_ids": physical_sample_ids,
                            "analysis_entity_ids": analysis_entity_ids,
                            "dataset_ids": dataset_ids,
                        }
                        if site_claims
                        else _unavailable(
                            "sead_chronology_linked_sample_records_not_available"
                        )
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
                    "pollen_composition": _unavailable(
                        "sead_observation_relations_not_captured"
                    ),
                    "relation": dict(_UNAVAILABLE_RELATION),
                    "classification": dict(_UNAVAILABLE_CLASSIFICATION),
                    "provenance": {
                        "source_run_id": run_id,
                        "build_id": claims_bundle.get("source_build_id"),
                        "acquisition_manifest_sha256": claims_bundle.get(
                            "acquisition_manifest_sha256"
                        ),
                        "claim_bundle_path": "data/sead/normalized/chronology_claims.json",
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
        "projected_site_claim_count": sum(
            len(claims_by_site[site_id]) for site_id in feature_site_ids
        ),
        "detail_row_counts": {
            "chronology_claims": sum(
                len(claims_by_site[site_id]) for site_id in feature_site_ids
            )
        },
        "detail_row_denominators": {"chronology_claims": len(raw_claims)},
        "source_run_id": run_id,
        "build_id": claims_bundle.get("source_build_id"),
        "acquisition_manifest_sha256": claims_bundle.get("acquisition_manifest_sha256"),
        "acquisition_release_status": admission.get("release_status"),
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
