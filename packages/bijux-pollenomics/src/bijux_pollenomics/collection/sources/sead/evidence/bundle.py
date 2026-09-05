"""Stage every source-native observation from an admitted SEAD evidence graph."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import hashlib
import json
import os
from pathlib import Path
from typing import Final, cast

from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
    validate_materialized_sead_full_evidence_admission,
)
from bijux_pollenomics.collection.sources.sead.evidence.claims import (
    build_sead_chronology_claim_bundle,
)

EVIDENCE_BUNDLE_SCHEMA_VERSION: Final = "sead-source-native-evidence-bundle.v1"
OBSERVATION_SCHEMA_VERSION: Final = "sead-source-native-observation.v1"
RELATION_INDEX_SCHEMA_VERSION: Final = "sead-evidence-relation-index.v1"
EVENT_BUNDLE_SCHEMA_VERSION: Final = "sead-evidence-event-bundle.v1"
EVIDENCE_MANIFEST_SCHEMA_VERSION: Final = "sead-evidence-materialization-manifest.v1"
MULTIPART_SCHEMA_VERSION: Final = "sead-evidence-multipart.v1"
_MAX_GOVERNED_FILE_BYTES: Final = 50 * 1024 * 1024
_PART_TARGET_BYTES: Final = 12 * 1024 * 1024

_OBSERVATION_TABLES: Final = (
    ("tbl_abundances", "abundance_id", "abundance"),
    ("tbl_analysis_taxon_counts", "analysis_taxon_count_id", "value"),
    ("tbl_analysis_values", "analysis_value_id", "analysis_value"),
    ("tbl_measured_values", "measured_value_id", "measured_value"),
)
_ANALYSIS_VALUE_COMPONENTS: Final = (
    "tbl_analysis_numerical_values",
    "tbl_analysis_integer_values",
    "tbl_analysis_categorical_values",
    "tbl_analysis_boolean_values",
)
_ABUNDANCE_COMPONENTS: Final = (
    "tbl_abundance_ident_levels",
    "tbl_abundance_modifications",
    "tbl_abundance_properties",
)
_DIMENSION_RELATION_TABLES: Final = (
    (
        "tbl_analysis_value_dimensions",
        "analysis_value_dimension_id",
        "analysis_value_id",
        "analysis_value",
    ),
    (
        "tbl_measured_value_dimensions",
        "measured_value_dimension_id",
        "measured_value_id",
        "measured_value",
    ),
    (
        "tbl_analysis_entity_dimensions",
        "analysis_entity_dimension_id",
        "analysis_entity_id",
        "analysis_entity",
    ),
    (
        "tbl_sample_dimensions",
        "sample_dimension_id",
        "physical_sample_id",
        "physical_sample",
    ),
    (
        "tbl_sample_group_dimensions",
        "sample_group_dimension_id",
        "sample_group_id",
        "sample_group",
    ),
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


def write_sead_source_native_evidence_bundle(
    acquisition_root: Path,
    output_directory: Path,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> tuple[Path, ...]:
    """Atomically publish deterministic SEAD evidence files and their manifest."""
    if (
        not output_directory.is_absolute()
        or output_directory.name in {"", ".", ".."}
        or ".." in output_directory.parts
    ):
        raise ValueError("SEAD evidence output must be a safe absolute path")
    parent = output_directory.parent
    _reject_symlink_ancestors(parent)
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("SEAD evidence output parent must be a regular directory")
    output = parent / output_directory.name
    payloads = build_sead_source_native_evidence_bundle(
        acquisition_root, expected_identity=expected_identity
    )
    materialized, multipart_documents = _materialize_payloads(payloads)
    evidence_manifest = {
        "schema_version": EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "source_family": "sead",
        "source_run_id": payloads["source_native_observations.json"]["source_run_id"],
        "build_id": payloads["source_native_observations.json"]["build_id"],
        "acquisition_manifest_sha256": payloads["source_native_observations.json"][
            "acquisition_manifest_sha256"
        ],
        "acquisition_bundle_sha256": payloads["source_native_observations.json"][
            "acquisition_bundle_sha256"
        ],
        "parent_admission_sha256": payloads["source_native_observations.json"][
            "parent_admission_sha256"
        ],
        "source_table_count": 61,
        "chronology_claim_count": payloads["chronology_claims.json"]["claim_count"],
        "observation_count": payloads["source_native_observations.json"][
            "observation_count"
        ],
        "eligible_event_count": payloads["evidence_events.json"][
            "eligible_event_count"
        ],
        "refused_event_count": payloads["evidence_events.json"]["refused_event_count"],
        "maximum_file_byte_count": _MAX_GOVERNED_FILE_BYTES,
        "multipart_documents": multipart_documents,
        "files": [
            {
                "path": name,
                "byte_count": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for name, content in sorted(materialized.items())
        ],
        "file_set_sha256": _stable_id(
            "sead-evidence-files",
            *(
                f"{name}:{hashlib.sha256(content).hexdigest()}:{len(content)}"
                for name, content in sorted(materialized.items())
            ),
        ).removeprefix("sead-evidence-files:"),
    }
    materialized["evidence_materialization_manifest.json"] = _canonical_bytes(
        evidence_manifest
    )
    if output.exists() or output.is_symlink():
        if output.is_symlink() or not output.is_dir():
            raise FileExistsError(f"Unsafe existing SEAD evidence bundle: {output}")
        if _directory_bytes(output) == materialized:
            return tuple(output / name for name in sorted(materialized))
        raise FileExistsError(f"Non-identical SEAD evidence bundle exists: {output}")
    staging = parent / f".{output.name}.staging-{os.getpid()}"
    if staging.exists() or staging.is_symlink():
        raise FileExistsError(f"SEAD evidence staging collision: {staging}")
    staging.mkdir()
    try:
        for name, content in sorted(materialized.items()):
            destination = staging.joinpath(*Path(name).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        if _directory_bytes(staging) != materialized:
            raise ValueError("Staged SEAD evidence bundle bytes changed")
        validate_sead_source_native_evidence_materialization(staging)
        os.replace(staging, output)
    finally:
        if staging.exists() and not staging.is_symlink():
            for path in sorted(staging.rglob("*"), reverse=True):
                if path.is_file() and not path.is_symlink():
                    path.unlink()
                elif path.is_dir() and not path.is_symlink():
                    path.rmdir()
            staging.rmdir()
    return tuple(output / name for name in sorted(materialized))


def validate_sead_source_native_evidence_materialization(
    output_directory: Path,
) -> dict[str, object]:
    """Independently verify a bounded evidence materialization and its parts."""
    root = Path(output_directory)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("SEAD evidence materialization must be a safe absolute path")
    _reject_symlink_ancestors(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("SEAD evidence materialization must be a regular directory")
    manifest_path = root / "evidence_materialization_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = _decode_object(manifest_bytes, manifest_path.as_posix())
    if manifest_bytes != _canonical_bytes(manifest):
        raise ValueError("SEAD evidence manifest is not canonical")
    if manifest.get("schema_version") != EVIDENCE_MANIFEST_SCHEMA_VERSION:
        raise ValueError("SEAD evidence manifest schema version changed")
    records_value = manifest.get("files")
    if not isinstance(records_value, list):
        raise TypeError("SEAD evidence manifest files must be a list")
    records: dict[str, Mapping[str, object]] = {}
    contents: dict[str, bytes] = {}
    for record in records_value:
        if not isinstance(record, Mapping):
            raise TypeError("SEAD evidence file record must be an object")
        relative_path = _safe_evidence_relative_path(record.get("path"))
        if relative_path in records:
            raise ValueError(f"Duplicate SEAD evidence path: {relative_path}")
        content_path = root.joinpath(*Path(relative_path).parts)
        if content_path.is_symlink() or not content_path.is_file():
            raise ValueError(f"SEAD evidence file is not regular: {relative_path}")
        content = content_path.read_bytes()
        _verify_record(content, record, relative_path)
        if len(content) > _MAX_GOVERNED_FILE_BYTES:
            raise ValueError(f"SEAD evidence file exceeds size limit: {relative_path}")
        records[relative_path] = record
        contents[relative_path] = content
    actual_paths = set(_directory_bytes(root))
    logical_document_names = {
        "chronology_claims.json",
        "source_native_observations.json",
        "observation_relation_index.json",
        "evidence_events.json",
    }
    if not logical_document_names <= set(records):
        raise ValueError("SEAD evidence materialization lacks a logical document")
    expected_paths = set(records) | {"evidence_materialization_manifest.json"}
    if actual_paths != expected_paths:
        raise ValueError("SEAD evidence manifest does not cover the exact file set")
    expected_file_set_sha256 = _stable_id(
        "sead-evidence-files",
        *(
            f"{name}:{hashlib.sha256(content).hexdigest()}:{len(content)}"
            for name, content in sorted(contents.items())
        ),
    ).removeprefix("sead-evidence-files:")
    if manifest.get("file_set_sha256") != expected_file_set_sha256:
        raise ValueError("SEAD evidence file-set digest does not reconcile")

    multipart_value = manifest.get("multipart_documents")
    if not isinstance(multipart_value, Mapping):
        raise TypeError("SEAD evidence multipart_documents must be an object")
    referenced_parts: set[str] = set()
    logical_documents: dict[str, dict[str, object]] = {}
    for document_name in logical_document_names:
        document_content = contents[document_name]
        document = _decode_object(document_content, document_name)
        if document_content != _canonical_bytes(document):
            raise ValueError(
                f"SEAD evidence document is not canonical: {document_name}"
            )
        logical_documents[document_name] = document
    for document_name, declared in sorted(multipart_value.items()):
        if not isinstance(document_name, str) or not isinstance(declared, Mapping):
            raise TypeError("SEAD evidence multipart declaration is invalid")
        root_document = logical_documents[document_name]
        partitioned = root_document.get("partitioned_fields")
        if not isinstance(partitioned, Mapping):
            raise TypeError("SEAD multipart index lacks partitioned_fields")
        declared_fields = declared.get("partitioned_fields")
        if declared_fields != sorted(partitioned):
            raise ValueError("SEAD multipart field declaration changed")
        document_parts: list[str] = []
        for field, field_record in sorted(partitioned.items()):
            if not isinstance(field, str) or not isinstance(field_record, Mapping):
                raise TypeError("SEAD evidence partition record is invalid")
            parts = field_record.get("parts")
            if not isinstance(parts, list):
                raise TypeError("SEAD evidence partition parts must be a list")
            if field_record.get("part_count") != len(parts):
                raise ValueError("SEAD evidence partition part count changed")
            row_cursor = 0
            for part_number, part_record in enumerate(parts, start=1):
                if not isinstance(part_record, Mapping):
                    raise TypeError("SEAD evidence part record must be an object")
                part_path = _safe_evidence_relative_path(part_record.get("path"))
                if part_path in referenced_parts:
                    raise ValueError(f"SEAD evidence part is duplicated: {part_path}")
                part_content = contents.get(part_path)
                if part_content is None:
                    raise ValueError(f"SEAD evidence part is absent: {part_path}")
                _verify_record(part_content, part_record, part_path)
                part = _decode_object(part_content, part_path)
                if part_content != _canonical_bytes(part):
                    raise ValueError(
                        f"SEAD evidence part is not canonical: {part_path}"
                    )
                rows = part.get(field)
                if not isinstance(rows, list):
                    raise TypeError(f"SEAD evidence part rows are invalid: {part_path}")
                row_end = row_cursor + len(rows)
                for key, expected in (
                    ("schema_version", MULTIPART_SCHEMA_VERSION),
                    ("logical_document", document_name),
                    ("field", field),
                    ("part_number", part_number),
                    ("row_start", row_cursor),
                    ("row_end", row_end),
                ):
                    if part.get(key) != expected:
                        raise ValueError(
                            f"SEAD evidence part {key} changed: {part_path}"
                        )
                for key, expected in (
                    ("part_number", part_number),
                    ("row_start", row_cursor),
                    ("row_end", row_end),
                ):
                    if part_record.get(key) != expected:
                        raise ValueError(
                            f"SEAD evidence part record {key} changed: {part_path}"
                        )
                if part_record.get("row_count") != len(rows):
                    raise ValueError(
                        f"SEAD evidence part row count changed: {part_path}"
                    )
                row_cursor = row_end
                document_parts.append(part_path)
                referenced_parts.add(part_path)
            if field_record.get("row_count") != row_cursor:
                raise ValueError("SEAD evidence partition row denominator changed")
        if declared.get("part_count") != len(document_parts):
            raise ValueError("SEAD multipart document part count changed")
        if declared.get("parts") != sorted(document_parts):
            raise ValueError("SEAD multipart document file set changed")
    unreferenced_parts = set(records) - logical_document_names
    if referenced_parts != unreferenced_parts:
        raise ValueError("SEAD multipart evidence has unreferenced files")
    observations = logical_documents["source_native_observations.json"]
    chronology = logical_documents["chronology_claims.json"]
    events = logical_documents["evidence_events.json"]
    relations = logical_documents["observation_relation_index.json"]
    for field, expected_value in (
        ("source_run_id", observations.get("source_run_id")),
        ("build_id", observations.get("build_id")),
        (
            "acquisition_manifest_sha256",
            observations.get("acquisition_manifest_sha256"),
        ),
        ("acquisition_bundle_sha256", observations.get("acquisition_bundle_sha256")),
        ("parent_admission_sha256", observations.get("parent_admission_sha256")),
    ):
        if manifest.get(field) != expected_value:
            raise ValueError(f"SEAD evidence manifest {field} does not reconcile")
    _required_sha256(manifest, "acquisition_manifest_sha256")
    _required_sha256(manifest, "parent_admission_sha256")
    _required_prefixed_sha256(manifest, "acquisition_bundle_sha256")
    for document_name, document in logical_documents.items():
        for field in ("source_run_id", "acquisition_manifest_sha256"):
            if document.get(field) != observations.get(field):
                raise ValueError(f"SEAD evidence {field} diverges in {document_name}")
        document_build_id = document.get(
            "source_build_id"
            if document_name == "chronology_claims.json"
            else "build_id"
        )
        if document_build_id != observations.get("build_id"):
            raise ValueError(
                f"SEAD evidence build identity diverges in {document_name}"
            )
    reconciliation = (
        (chronology, "claims", "claim_count"),
        (observations, "observations", "observation_count"),
        (events, "events", "eligible_event_count"),
        (events, "refusals", "refused_event_count"),
        (relations, "entity_relations", "entity_relation_count"),
        (relations, "dataset_semantics", "dataset_semantic_count"),
        (relations, "value_semantics", "value_semantic_count"),
        (relations, "taxon_relations", "taxon_relation_count"),
        (relations, "dimension_semantics", "dimension_semantic_count"),
        (relations, "dimension_relations", "dimension_relation_count"),
    )
    for document, row_field, count_field in reconciliation:
        if _logical_row_count(document, row_field) != document.get(count_field):
            raise ValueError(f"SEAD evidence {count_field} does not reconcile")
    for field, expected_value in (
        ("chronology_claim_count", chronology.get("claim_count")),
        ("observation_count", observations.get("observation_count")),
        ("eligible_event_count", events.get("eligible_event_count")),
        ("refused_event_count", events.get("refused_event_count")),
    ):
        if manifest.get(field) != expected_value:
            raise ValueError(f"SEAD evidence manifest {field} does not reconcile")
    source_table_counts = relations.get("source_table_counts")
    if not isinstance(source_table_counts, Mapping):
        raise TypeError("SEAD evidence source table counts are missing")
    expected_source_tables = set(SEAD_FULL_EVIDENCE_SOURCE_TABLES)
    if set(source_table_counts) != expected_source_tables or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in source_table_counts.values()
    ):
        raise ValueError("SEAD evidence requires exact 61-table source denominators")
    if manifest.get("source_table_count") != len(expected_source_tables):
        raise ValueError("SEAD evidence manifest source table count must equal 61")
    if observations.get("source_table_counts") != source_table_counts:
        raise ValueError("SEAD observation source table denominators do not reconcile")
    relation_table_sha256 = relations.get("source_table_sha256")
    if (
        not isinstance(relation_table_sha256, Mapping)
        or set(relation_table_sha256) != expected_source_tables
        or any(
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
            for value in relation_table_sha256.values()
        )
    ):
        raise ValueError("SEAD evidence requires exact 61-table source digests")
    if observations.get("source_table_sha256") != relation_table_sha256:
        raise ValueError("SEAD observation source table digests do not reconcile")
    expected_observation_table_counts = {
        table: source_table_counts.get(table) for table, _, _ in _OBSERVATION_TABLES
    }
    if (
        observations.get("observation_table_counts")
        != expected_observation_table_counts
    ):
        raise ValueError("SEAD observation table denominators do not reconcile")
    expected_dimension_table_counts = {
        table: source_table_counts.get(table)
        for table, *_ in _DIMENSION_RELATION_TABLES
    }
    if (
        relations.get("dimension_relation_table_counts")
        != expected_dimension_table_counts
    ):
        raise ValueError("SEAD dimension table denominators do not reconcile")
    observation_count = observations.get("observation_count")
    if isinstance(observation_count, bool) or not isinstance(observation_count, int):
        raise TypeError("SEAD observation count must be an integer")
    for field in (
        "country_counts",
        "chronology_link_status_counts",
        "unit_status_counts",
        "taxon_status_counts",
    ):
        counts = observations.get(field)
        if not isinstance(counts, Mapping) or not all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in counts.values()
        ):
            raise TypeError(f"SEAD observation {field} is invalid")
        if sum(cast(int, value) for value in counts.values()) != observation_count:
            raise ValueError(f"SEAD observation {field} does not reconcile")
    if (
        events.get("observation_denominator") != observation_count
        or events.get("refused_event_count") != observation_count
    ):
        raise ValueError("SEAD event observation denominator does not reconcile")
    return manifest


def _materialize_payloads(
    payloads: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, bytes], dict[str, object]]:
    materialized: dict[str, bytes] = {}
    multipart_documents: dict[str, object] = {}
    for name, payload in sorted(payloads.items()):
        content = _canonical_bytes(payload)
        if len(content) <= _MAX_GOVERNED_FILE_BYTES:
            materialized[name] = content
            continue
        root_payload = dict(payload)
        partitioned_fields: dict[str, object] = {}
        document_parts: list[str] = []
        for field, value in sorted(payload.items()):
            if not isinstance(value, list) or not value:
                continue
            records = []
            row_start = 0
            chunks = _bounded_chunks(value)
            for part_number, rows in enumerate(chunks, start=1):
                row_end = row_start + len(rows)
                part_path = (
                    f"{name.removesuffix('.json')}/{field}-{part_number:05d}.json"
                )
                part_payload = {
                    "schema_version": MULTIPART_SCHEMA_VERSION,
                    "logical_document": name,
                    "field": field,
                    "part_number": part_number,
                    "row_start": row_start,
                    "row_end": row_end,
                    field: rows,
                }
                part_content = _canonical_bytes(part_payload)
                if len(part_content) > _MAX_GOVERNED_FILE_BYTES:
                    raise ValueError(
                        f"SEAD evidence part exceeds file limit: {part_path}"
                    )
                materialized[part_path] = part_content
                records.append(
                    {
                        "path": part_path,
                        "part_number": part_number,
                        "row_start": row_start,
                        "row_end": row_end,
                        "row_count": len(rows),
                        "byte_count": len(part_content),
                        "sha256": hashlib.sha256(part_content).hexdigest(),
                    }
                )
                document_parts.append(part_path)
                row_start = row_end
            if row_start != len(value):
                raise ValueError(
                    f"SEAD evidence partition rows do not reconcile: {name}"
                )
            root_payload.pop(field)
            partitioned_fields[field] = {
                "row_count": len(value),
                "part_count": len(records),
                "parts": records,
            }
        if not partitioned_fields:
            raise ValueError(
                f"SEAD evidence document cannot be safely partitioned: {name}"
            )
        root_payload["partitioned_fields"] = partitioned_fields
        root_content = _canonical_bytes(root_payload)
        if len(root_content) > _MAX_GOVERNED_FILE_BYTES:
            raise ValueError(f"SEAD evidence index exceeds file limit: {name}")
        materialized[name] = root_content
        multipart_documents[name] = {
            "partitioned_fields": sorted(partitioned_fields),
            "part_count": len(document_parts),
            "parts": sorted(document_parts),
        }
    return materialized, multipart_documents


def _bounded_chunks(rows: Sequence[object]) -> list[list[object]]:
    chunks: list[list[object]] = []
    current: list[object] = []
    current_bytes = 0
    for row in rows:
        row_bytes = len(_canonical_bytes(row))
        if row_bytes > _PART_TARGET_BYTES:
            raise ValueError("A single SEAD evidence row exceeds the partition target")
        if current and current_bytes + row_bytes > _PART_TARGET_BYTES:
            chunks.append(current)
            current = []
            current_bytes = 0
        current.append(row)
        current_bytes += row_bytes
    if current:
        chunks.append(current)
    return chunks


def _logical_row_count(document: Mapping[str, object], field: str) -> int:
    direct = document.get(field)
    if isinstance(direct, list):
        return len(direct)
    partitioned = document.get("partitioned_fields")
    if not isinstance(partitioned, Mapping):
        raise ValueError(f"SEAD evidence rows are absent: {field}")
    record = partitioned.get(field)
    if not isinstance(record, Mapping):
        raise ValueError(f"SEAD evidence partition is absent: {field}")
    value = record.get("row_count")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"SEAD evidence partition row count is invalid: {field}")
    return value


def _load_full_admission(
    acquisition_root: Path,
    *,
    validated_admission: Mapping[str, object],
) -> tuple[Path, dict[str, list[dict[str, object]]], dict[str, str]]:
    root = Path(acquisition_root)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("SEAD evidence acquisition must be a safe absolute path")
    _reject_symlink_ancestors(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("SEAD evidence acquisition must be a regular directory")
    admission = _read_object(root / "admission.json")
    if admission != validated_admission:
        raise ValueError("SEAD evidence admission changed after independent validation")
    scope = admission.get("declared_scope")
    if not isinstance(scope, Mapping):
        raise TypeError("SEAD evidence admission declared_scope is missing")
    if scope.get("scope_key") != "full_evidence_relations":
        raise ValueError("SEAD evidence requires a full-evidence admission")
    expected_tables = sorted(SEAD_FULL_EVIDENCE_SOURCE_TABLES)
    if scope.get("tables") != expected_tables or scope.get("table_count") != 61:
        raise ValueError("SEAD evidence admission must bind the exact 61 tables")
    if scope.get("join_count") != 86:
        raise ValueError("SEAD evidence admission must bind the exact 86 joins")
    copied = admission.get("copied_files")
    if not isinstance(copied, list):
        raise TypeError("SEAD evidence admission copied_files is missing")
    records: dict[str, Mapping[str, object]] = {}
    for item in copied:
        if not isinstance(item, Mapping):
            raise TypeError("SEAD copied-file record must be an object")
        name = _required_text(item, "path")
        if name in records:
            raise ValueError(f"Duplicate SEAD copied-file path: {name}")
        records[name] = item
    tables: dict[str, list[dict[str, object]]] = {}
    digests: dict[str, str] = {}
    for table in SEAD_FULL_EVIDENCE_SOURCE_TABLES:
        name = f"payloads/{table}.json"
        record = records.get(name)
        if record is None:
            raise ValueError(f"SEAD full-evidence payload is missing: {table}")
        content = (root / name).read_bytes()
        _verify_record(content, record, name)
        payload = _decode_object(content, name)
        if payload.get("table") != table:
            raise ValueError(f"SEAD evidence table identity changed: {table}")
        rows = payload.get("rows")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise TypeError(f"SEAD evidence rows are invalid: {table}")
        tables[table] = cast(list[dict[str, object]], rows)
        digests[table] = hashlib.sha256(content).hexdigest()
    return root, tables, digests


def _entity_relations(
    tables: Mapping[str, list[dict[str, object]]],
    *,
    country_by_site: Mapping[int, str],
) -> tuple[list[dict[str, object]], dict[int, dict[str, object]]]:
    sites = _unique_index(tables["tbl_sites"], "site_id")
    groups = _unique_index(tables["tbl_sample_groups"], "sample_group_id")
    samples = _unique_index(tables["tbl_physical_samples"], "physical_sample_id")
    rows: list[dict[str, object]] = []
    by_entity: dict[int, dict[str, object]] = {}
    for entity in tables["tbl_analysis_entities"]:
        entity_id = _positive_int(entity.get("analysis_entity_id"), "analysis entity")
        sample_id = _positive_int(entity.get("physical_sample_id"), "physical sample")
        source_dataset_id = entity.get("dataset_id")
        dataset_id = (
            None
            if source_dataset_id is None
            else _positive_int(source_dataset_id, "dataset")
        )
        sample = samples.get(sample_id)
        if sample is None:
            raise ValueError(f"SEAD entity lacks physical sample: {entity_id}")
        group_id = _positive_int(sample.get("sample_group_id"), "sample group")
        group = groups.get(group_id)
        if group is None:
            raise ValueError(f"SEAD sample lacks sample group: {sample_id}")
        site_id = _positive_int(group.get("site_id"), "site")
        site = sites.get(site_id)
        if site is None or site_id not in country_by_site:
            raise ValueError(f"SEAD group lacks governed site: {group_id}")
        row = {
            "entity_relation_id": f"sead-analysis-entity:{entity_id}",
            "analysis_entity_id": entity_id,
            "physical_sample_id": sample_id,
            "sample_group_id": group_id,
            "dataset_id": dataset_id,
            "site_id": site_id,
            "site_uuid": _required_text(site, "site_uuid"),
            "country_code": country_by_site[site_id],
            "latitude_dd": site.get("latitude_dd"),
            "longitude_dd": site.get("longitude_dd"),
        }
        rows.append(row)
        by_entity[entity_id] = row
    return rows, by_entity


def _country_by_site(root: Path) -> dict[int, str]:
    document = _read_object(root / "country-decisions.json")
    rows = document.get("decisions")
    if not isinstance(rows, list):
        raise TypeError("SEAD country decisions are missing")
    result: dict[int, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise TypeError("SEAD country decision must be an object")
        code = row.get("governed_country_code")
        if code in {"SE", "DK", "NO", "FI"}:
            result[_positive_int(row.get("site_id"), "country site")] = cast(str, code)
    return result


def _component_indices(
    tables: Mapping[str, list[dict[str, object]]],
) -> dict[str, dict[int, list[dict[str, object]]]]:
    result: dict[str, dict[int, list[dict[str, object]]]] = {}
    for table in _ANALYSIS_VALUE_COMPONENTS:
        result[table] = _child_index(tables[table], "analysis_value_id")
    for table in _ABUNDANCE_COMPONENTS:
        result[table] = _child_index(tables[table], "abundance_id")
    return result


def _observation_components(
    table: str,
    *,
    source_id: int,
    components: Mapping[str, Mapping[int, list[dict[str, object]]]],
) -> dict[str, list[dict[str, object]]]:
    names = (
        _ANALYSIS_VALUE_COMPONENTS
        if table == "tbl_analysis_values"
        else (_ABUNDANCE_COMPONENTS if table == "tbl_abundances" else ())
    )
    return {name: components[name].get(source_id, []) for name in names}


def _dimension_relation_index(
    tables: Mapping[str, list[dict[str, object]]],
    *,
    manifest_sha256: str,
) -> tuple[
    dict[int, dict[str, object]],
    list[dict[str, object]],
    dict[tuple[str, int], list[str]],
]:
    units = _unique_index(tables["tbl_units"], "unit_id")
    semantics: dict[int, dict[str, object]] = {}
    for dimension in tables["tbl_dimensions"]:
        dimension_id = _positive_int(dimension.get("dimension_id"), "dimension")
        raw_unit_id = dimension.get("unit_id")
        unit_id = (
            None
            if raw_unit_id is None
            else _positive_int(raw_unit_id, "dimension unit")
        )
        unit = units.get(unit_id) if unit_id is not None else None
        semantics[dimension_id] = {
            "dimension_semantics_id": f"sead-dimension:{dimension_id}",
            "dimension_id": dimension_id,
            "source_dimension": dimension,
            "source_unit": unit,
            "source_unit_id": unit_id,
            "unit_status": (
                "source_native_linked"
                if unit is not None
                else (
                    "source_unit_not_reported"
                    if unit_id is None
                    else "source_unit_relation_unavailable"
                )
            ),
        }

    relations: list[dict[str, object]] = []
    by_owner: dict[tuple[str, int], list[str]] = defaultdict(list)
    for table, primary_key, owner_field, owner_kind in _DIMENSION_RELATION_TABLES:
        for source_row in tables[table]:
            source_id = _positive_int(source_row.get(primary_key), f"{table} key")
            owner_id = _positive_int(source_row.get(owner_field), f"{table} owner")
            raw_dimension_id = source_row.get("dimension_id")
            relation_dimension_id = (
                None
                if raw_dimension_id is None
                else _positive_int(raw_dimension_id, f"{table} dimension")
            )
            semantic = (
                semantics.get(relation_dimension_id)
                if relation_dimension_id is not None
                else None
            )
            relation_id = _stable_id(
                "sead-dimension-relation",
                manifest_sha256,
                table,
                str(source_id),
            )
            relations.append(
                {
                    "dimension_relation_id": relation_id,
                    "source_table": table,
                    "source_record_id": str(source_id),
                    "source_row": dict(source_row),
                    "owner_kind": owner_kind,
                    "owner_id": owner_id,
                    "dimension_semantics_id": (
                        semantic["dimension_semantics_id"]
                        if semantic is not None
                        else None
                    ),
                    "dimension_status": (
                        "source_native_linked"
                        if semantic is not None
                        else "source_dimension_relation_unavailable"
                    ),
                    "unit_status": (
                        semantic["unit_status"]
                        if semantic is not None
                        else "source_dimension_relation_unavailable"
                    ),
                }
            )
            by_owner[(owner_kind, owner_id)].append(relation_id)
    for relation_ids in by_owner.values():
        relation_ids.sort()
    expected = sum(len(tables[table]) for table, *_ in _DIMENSION_RELATION_TABLES)
    if len(relations) != expected:
        raise ValueError("SEAD dimension relation rows do not reconcile")
    relation_ids = [
        cast(str, relation["dimension_relation_id"]) for relation in relations
    ]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("SEAD dimension relation identities are duplicated")
    return semantics, relations, dict(by_owner)


def _observation_dimension_relation_ids(
    table: str,
    *,
    source_id: int,
    analysis_value_id: int | None,
    entity_relation: Mapping[str, object],
    dimensions_by_owner: Mapping[tuple[str, int], list[str]],
) -> list[str]:
    owner_keys: list[tuple[str, int]] = []
    if table == "tbl_analysis_values":
        owner_keys.append(("analysis_value", source_id))
    elif table == "tbl_analysis_taxon_counts":
        if analysis_value_id is None:
            raise ValueError("SEAD taxon count must bind an analysis value")
        owner_keys.append(("analysis_value", analysis_value_id))
    elif table == "tbl_measured_values":
        owner_keys.append(("measured_value", source_id))
    for owner_kind, relation_field in (
        ("analysis_entity", "analysis_entity_id"),
        ("physical_sample", "physical_sample_id"),
        ("sample_group", "sample_group_id"),
    ):
        owner_keys.append(
            (
                owner_kind,
                _positive_int(entity_relation.get(relation_field), relation_field),
            )
        )
    return sorted(
        {
            relation_id
            for owner_key in owner_keys
            for relation_id in dimensions_by_owner.get(owner_key, [])
        }
    )


def _taxonomy_index(
    tables: Mapping[str, list[dict[str, object]]],
) -> dict[int, dict[str, object]]:
    authors = _unique_index(tables["tbl_taxa_tree_authors"], "author_id")
    genera = _unique_index(tables["tbl_taxa_tree_genera"], "genus_id")
    families = _unique_index(tables["tbl_taxa_tree_families"], "family_id")
    orders = _unique_index(tables["tbl_taxa_tree_orders"], "order_id")
    definitions = _unique_index(
        tables["tbl_ecocode_definitions"], "ecocode_definition_id"
    )
    groups = _unique_index(tables["tbl_ecocode_groups"], "ecocode_group_id")
    systems = _unique_index(tables["tbl_ecocode_systems"], "ecocode_system_id")
    ecocodes = _child_index(tables["tbl_ecocodes"], "taxon_id")
    result: dict[int, dict[str, object]] = {}
    for taxon in tables["tbl_taxa_tree_master"]:
        taxon_id = _positive_int(taxon.get("taxon_id"), "taxon")
        genus = genera.get(cast(int, taxon.get("genus_id")))
        family = families.get(cast(int, genus.get("family_id"))) if genus else None
        order = orders.get(cast(int, family.get("order_id"))) if family else None
        native_ecocodes = []
        for ecocode in ecocodes.get(taxon_id, []):
            definition = definitions.get(
                cast(int, ecocode.get("ecocode_definition_id"))
            )
            group = (
                groups.get(cast(int, definition.get("ecocode_group_id")))
                if definition
                else None
            )
            system = (
                systems.get(cast(int, group.get("ecocode_system_id")))
                if group
                else None
            )
            native_ecocodes.append(
                {
                    "ecocode": ecocode,
                    "definition": definition,
                    "group": group,
                    "system": system,
                }
            )
        result[taxon_id] = {
            "taxon_relation_id": f"sead-taxon:{taxon_id}",
            "taxon_id": taxon_id,
            "taxon": taxon,
            "author": authors.get(cast(int, taxon.get("author_id"))),
            "genus": genus,
            "family": family,
            "order": order,
            "source_ecocodes": native_ecocodes,
            "derived_classification_status": "not_accepted",
        }
    return result


def _dataset_semantics_index(
    tables: Mapping[str, list[dict[str, object]]],
) -> dict[int, dict[str, object]]:
    data_types = _unique_index(tables["tbl_data_types"], "data_type_id")
    groups = _unique_index(tables["tbl_data_type_groups"], "data_type_group_id")
    result: dict[int, dict[str, object]] = {}
    for dataset in tables["tbl_datasets"]:
        dataset_id = _positive_int(dataset.get("dataset_id"), "dataset")
        data_type = data_types.get(cast(int, dataset.get("data_type_id")))
        group = (
            groups.get(cast(int, data_type.get("data_type_group_id")))
            if data_type
            else None
        )
        result[dataset_id] = {
            "dataset_semantics_id": f"sead-dataset:{dataset_id}",
            "dataset": dataset,
            "source_data_type": data_type,
            "source_data_type_group": group,
        }
    return result


def _value_semantics_index(
    tables: Mapping[str, list[dict[str, object]]],
) -> dict[int, dict[str, object]]:
    value_types = _unique_index(tables["tbl_value_types"], "value_type_id")
    units = _unique_index(tables["tbl_units"], "unit_id")
    data_types = _unique_index(tables["tbl_data_types"], "data_type_id")
    result: dict[int, dict[str, object]] = {}
    for value_class in tables["tbl_value_classes"]:
        class_id = _positive_int(value_class.get("value_class_id"), "value class")
        value_type = value_types.get(cast(int, value_class.get("value_type_id")))
        result[class_id] = {
            "value_semantics_id": f"sead-value-class:{class_id}",
            "value_class": value_class,
            "source_value_type": value_type,
            "source_unit": units.get(cast(int, value_type.get("unit_id")))
            if value_type
            else None,
            "source_data_type": data_types.get(
                cast(int, value_type.get("data_type_id"))
            )
            if value_type
            else None,
        }
    return result


def _observation_semantics(
    table: str,
    *,
    source_row: Mapping[str, object],
    dataset_id: int | None,
    dataset_semantics: Mapping[int, Mapping[str, object]],
    value_semantics: Mapping[int, Mapping[str, object]],
) -> dict[str, object]:
    semantics = (
        value_semantics.get(cast(int, source_row.get("value_class_id")))
        if table in {"tbl_analysis_values", "tbl_analysis_taxon_counts"}
        else None
    )
    source_unit = semantics.get("source_unit") if semantics else None
    return {
        "dataset_semantics_id": (
            dataset_semantics[dataset_id]["dataset_semantics_id"]
            if dataset_id is not None and dataset_id in dataset_semantics
            else None
        ),
        "dataset_semantics_status": (
            "source_native_linked"
            if dataset_id is not None and dataset_id in dataset_semantics
            else "not_exposed_by_relation"
        ),
        "value_semantics_id": (
            semantics["value_semantics_id"] if semantics is not None else None
        ),
        "source_unit_id": (
            source_unit.get("unit_id") if isinstance(source_unit, Mapping) else None
        ),
        "unit_status": (
            "source_native_linked"
            if source_unit is not None
            else "not_exposed_by_relation"
        ),
    }


def _assert_observation_reconciliation(
    tables: Mapping[str, list[dict[str, object]]],
    observations: Sequence[Mapping[str, object]],
    dispositions: Sequence[Mapping[str, object]],
    *,
    component_indices: Mapping[str, Mapping[int, list[dict[str, object]]]],
) -> None:
    expected = sum(len(tables[table]) for table, _, _ in _OBSERVATION_TABLES)
    if len(observations) != expected or len(dispositions) != expected:
        raise ValueError("SEAD observation/event disposition counts do not reconcile")
    identities = [item.get("observation_id") for item in observations]
    if len(identities) != len(set(identities)):
        raise ValueError("SEAD source-native observation identities are duplicated")
    disposition_ids = [item.get("observation_id") for item in dispositions]
    if identities != disposition_ids:
        raise ValueError("SEAD observation and event disposition identities diverge")
    for table, index in component_indices.items():
        linked_count = sum(len(rows) for rows in index.values())
        if linked_count != len(tables[table]):
            raise ValueError(f"SEAD component rows do not reconcile: {table}")


def _unique_index(
    rows: Sequence[dict[str, object]], key: str
) -> dict[int, dict[str, object]]:
    result = {}
    for row in rows:
        identifier = _positive_int(row.get(key), key)
        if identifier in result:
            raise ValueError(f"Duplicate SEAD source identifier: {key}={identifier}")
        result[identifier] = row
    return result


def _child_index(
    rows: Sequence[dict[str, object]], key: str
) -> dict[int, list[dict[str, object]]]:
    result: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        result[_positive_int(row.get(key), key)].append(row)
    return dict(result)


def _four_country_counts(counts: Mapping[str, int]) -> dict[str, int]:
    return {code: counts.get(code, 0) for code in ("SE", "DK", "NO", "FI")}


def _copied_file_sha256(admission: Mapping[str, object], path: str) -> str:
    copied = admission.get("copied_files")
    if not isinstance(copied, list):
        raise TypeError("SEAD admission copied_files is missing")
    matches = [
        item
        for item in copied
        if isinstance(item, Mapping) and item.get("path") == path
    ]
    if len(matches) != 1:
        raise ValueError(f"SEAD admission must bind one {path}")
    return _required_sha256(matches[0], "sha256")


def _verify_record(content: bytes, record: Mapping[str, object], label: str) -> None:
    if record.get("byte_count") != len(content):
        raise ValueError(f"SEAD admitted byte count changed: {label}")
    if _required_sha256(record, "sha256") != hashlib.sha256(content).hexdigest():
        raise ValueError(f"SEAD admitted digest changed: {label}")


def _directory_bytes(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are forbidden in SEAD evidence: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def _reject_symlink_ancestors(path: Path) -> None:
    for ancestor in (path, *path.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError(
                f"SEAD evidence acquisition path traverses a symlink: {ancestor}"
            )


def _safe_evidence_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("SEAD evidence path must be nonempty text")
    candidate = Path(value)
    if candidate.is_absolute() or value != candidate.as_posix():
        raise ValueError(f"Unsafe SEAD evidence path: {value!r}")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError(f"Unsafe SEAD evidence path: {value!r}")
    return value


def _read_object(path: Path) -> dict[str, object]:
    return _decode_object(path.read_bytes(), path.as_posix())


def _decode_object(payload: bytes, label: str) -> dict[str, object]:
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"SEAD JSON is invalid: {label}") from exc
    if not isinstance(document, dict):
        raise TypeError(f"SEAD JSON object is required: {label}")
    return document


def _required_text(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"SEAD {field} must be nonempty text")
    return value.strip()


def _required_sha256(document: Mapping[str, object], field: str) -> str:
    value = _required_text(document, field)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"SEAD {field} must be a lowercase SHA-256")
    return value


def _required_prefixed_sha256(document: Mapping[str, object], field: str) -> str:
    value = _required_text(document, field)
    digest = value.removeprefix("sha256:")
    if (
        value == digest
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"SEAD {field} must be a prefixed lowercase SHA-256")
    return value


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"SEAD {label} must be a positive integer")
    return value


def _stable_id(namespace: str, *parts: str) -> str:
    digest = hashlib.sha256(_canonical_bytes(list(parts))).hexdigest()
    return f"{namespace}:{digest}"


def _canonical_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


__all__ = [
    "EVIDENCE_BUNDLE_SCHEMA_VERSION",
    "EVIDENCE_MANIFEST_SCHEMA_VERSION",
    "EVENT_BUNDLE_SCHEMA_VERSION",
    "OBSERVATION_SCHEMA_VERSION",
    "RELATION_INDEX_SCHEMA_VERSION",
    "build_sead_source_native_evidence_bundle",
    "validate_sead_source_native_evidence_materialization",
    "write_sead_source_native_evidence_bundle",
]
