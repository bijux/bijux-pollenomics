from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
)

from .constants import (
    _DIMENSION_RELATION_TABLES,
    _MAX_GOVERNED_FILE_BYTES,
    _OBSERVATION_TABLES,
    EVIDENCE_MANIFEST_SCHEMA_VERSION,
    MULTIPART_SCHEMA_VERSION,
)
from .serialization import (
    _canonical_bytes,
    _decode_object,
    _directory_bytes,
    _logical_row_count,
    _reject_symlink_ancestors,
    _required_prefixed_sha256,
    _required_sha256,
    _safe_evidence_relative_path,
    _stable_id,
    _verify_record,
)


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
