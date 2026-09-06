from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path

from .constants import (
    _SEAD_ACQUISITION_BUNDLE_SHA256,
    _SEAD_ACQUISITION_MANIFEST_SHA256,
    _SEAD_ADMISSION_SHA256,
    _SEAD_BUILD_ID,
    _SEAD_COUNTRY_DECISIONS_SHA256,
    _SEAD_EVIDENCE_MANIFEST_SHA256,
    _SEAD_NORMALIZED_CHRONOLOGY,
    _SEAD_PARENT_ADMISSION_SHA256,
    _SEAD_RUN_ID,
    _SEAD_SCOPE_ID,
    SEAD_NORMALIZED_EVIDENCE_EVENTS,
    SEAD_NORMALIZED_OBSERVATIONS,
    SEAD_NORMALIZED_RELATIONS,
)
from .primitives import (
    _non_negative_int,
    _positive_int,
    _regular_non_symlink,
    _safe_relative_path,
    _sha256_text,
)


def _valid_sead_evidence_manifest(path: Path, payload: Mapping[str, object]) -> bool:
    records = payload.get("files")
    try:
        manifest_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return False
    if (
        payload.get("schema_version") != "sead-evidence-materialization-manifest.v1"
        or payload.get("source_family") != "sead"
        or payload.get("source_run_id") != _SEAD_RUN_ID
        or payload.get("source_table_count") != len(_sead_full_source_tables())
        or not isinstance(records, list)
        or not records
        or _positive_int(payload.get("observation_count")) is None
        or _positive_int(payload.get("chronology_claim_count")) is None
        or _non_negative_int(payload.get("eligible_event_count")) is None
        or _non_negative_int(payload.get("refused_event_count")) is None
        or manifest_sha256 != _SEAD_EVIDENCE_MANIFEST_SHA256
    ):
        return False
    try:
        # Lazy import is deliberate: the SEAD package imports model contracts that
        # themselves import this module. Validation only runs after package startup.
        from ...sources.sead.evidence.bundle import (
            validate_sead_source_native_evidence_materialization,
        )

        validated = validate_sead_source_native_evidence_materialization(path.parent)
        return validated == payload and _valid_sead_normalized_admission_link(
            path, payload
        )
    except (OSError, TypeError, ValueError):
        return False


def _valid_sead_evidence_member(
    path: Path,
    payload: Mapping[str, object],
    repository_path: str,
) -> bool:
    manifest_path = path.parent / "evidence_materialization_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest["files"]
        relative_path = path.relative_to(manifest_path.parent).as_posix()
        record = next(
            item
            for item in records
            if isinstance(item, dict) and item.get("path") == relative_path
        )
        content = path.read_bytes()
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        StopIteration,
        TypeError,
        ValueError,
    ):
        return False
    if (
        record.get("byte_count") != len(content)
        or record.get("sha256") != hashlib.sha256(content).hexdigest()
        or payload.get("source_family") != "sead"
        or payload.get("source_run_id") != _SEAD_RUN_ID
    ):
        return False
    build_id = payload.get(
        "source_build_id"
        if repository_path == _SEAD_NORMALIZED_CHRONOLOGY
        else "build_id"
    )
    if build_id != manifest.get("build_id"):
        return False
    if repository_path == SEAD_NORMALIZED_OBSERVATIONS:
        return (
            payload.get("schema_version") == "sead-source-native-evidence-bundle.v1"
            and payload.get("observation_count") == manifest.get("observation_count")
            and _exact_sead_table_counts(payload.get("source_table_counts"))
            and _exact_mapping_keys(payload.get("partitioned_fields"), {"observations"})
        )
    if repository_path == SEAD_NORMALIZED_RELATIONS:
        return (
            payload.get("schema_version") == "sead-evidence-relation-index.v1"
            and _exact_sead_table_counts(payload.get("source_table_counts"))
            and all(
                _non_negative_int(payload.get(field)) is not None
                for field in (
                    "dataset_semantic_count",
                    "dimension_relation_count",
                    "dimension_semantic_count",
                    "entity_relation_count",
                    "taxon_relation_count",
                    "value_semantic_count",
                )
            )
            and isinstance(payload.get("partitioned_fields"), dict)
        )
    if repository_path == _SEAD_NORMALIZED_CHRONOLOGY:
        return (
            payload.get("schema_version") == "sead-chronology-claim-bundle.v1"
            and payload.get("claim_count") == manifest.get("chronology_claim_count")
            and payload.get("propagation_status") == "refused"
            and payload.get("propagation_reason_code")
            == "source_classification_not_accepted"
            and _exact_mapping_keys(payload.get("partitioned_fields"), {"claims"})
        )
    if repository_path == SEAD_NORMALIZED_EVIDENCE_EVENTS:
        return (
            payload.get("schema_version") == "sead-evidence-event-bundle.v1"
            and payload.get("eligible_event_count")
            == manifest.get("eligible_event_count")
            and payload.get("refused_event_count")
            == manifest.get("refused_event_count")
            and payload.get("observation_denominator")
            == manifest.get("observation_count")
            and payload.get("eligible_event_count") == 0
            and payload.get("refused_event_count")
            == payload.get("observation_denominator")
            and payload.get("events") == []
            and _exact_mapping_keys(payload.get("partitioned_fields"), {"refusals"})
        )
    return False


def _valid_sead_normalized_admission_link(
    path: Path, manifest: Mapping[str, object]
) -> bool:
    admission_path = (
        path.parents[3] / "raw" / "acquisitions" / _SEAD_RUN_ID / "admission.json"
    )
    if not _valid_sead_admission(admission_path):
        return False
    try:
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
        observations = json.loads(
            (path.parent / "source_native_observations.json").read_text(
                encoding="utf-8"
            )
        )
        relations = json.loads(
            (path.parent / "observation_relation_index.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not all(
        manifest.get(field) == admission.get(field)
        for field in (
            "acquisition_bundle_sha256",
            "acquisition_manifest_sha256",
            "build_id",
            "parent_admission_sha256",
        )
    ):
        return False
    expected_tables = _sead_full_source_tables()
    raw_counts: dict[str, int] = {}
    raw_sha256: dict[str, str] = {}
    try:
        for table in expected_tables:
            payload_path = admission_path.parent / "payloads" / f"{table}.json"
            payload_bytes = payload_path.read_bytes()
            payload = json.loads(payload_bytes)
            rows = payload.get("rows")
            if (
                not isinstance(payload, dict)
                or payload.get("table") != table
                or not isinstance(rows, list)
            ):
                return False
            raw_counts[table] = len(rows)
            raw_sha256[table] = hashlib.sha256(payload_bytes).hexdigest()
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return False
    return bool(
        admission.get("table_counts") == raw_counts
        and observations.get("source_table_counts") == raw_counts
        and observations.get("source_table_sha256") == raw_sha256
        and relations.get("source_table_counts") == raw_counts
        and relations.get("source_table_sha256") == raw_sha256
    )


def _exact_sead_table_counts(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _sead_full_source_tables()
        and all(_non_negative_int(count) is not None for count in value.values())
    )


def _exact_mapping_keys(value: object, expected: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _sead_full_source_tables() -> frozenset[str]:
    # Lazy loading avoids the SEAD package's model imports while this module is
    # itself initializing through source-family contracts.
    from ...sources.sead.acquisition.archive import SEAD_FULL_EVIDENCE_SOURCE_TABLES

    return frozenset(SEAD_FULL_EVIDENCE_SOURCE_TABLES)


def _valid_sead_table_payload(path: Path, payload: Mapping[str, object]) -> bool:
    rows = payload.get("rows")
    admission_path = path.parents[1] / "admission.json"
    if not (
        payload.get("schema_version") == "sead-table-payload.v1"
        and payload.get("table") == path.stem
        and isinstance(rows, list)
        and bool(rows)
    ):
        return False
    try:
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
        copied_files = admission["copied_files"]
        relative_path = path.relative_to(admission_path.parent).as_posix()
        record = next(
            item
            for item in copied_files
            if isinstance(item, dict) and item.get("path") == relative_path
        )
        content = path.read_bytes()
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        StopIteration,
        TypeError,
        ValueError,
    ):
        return False
    return (
        record.get("byte_count") == len(content)
        and record.get("sha256") == hashlib.sha256(content).hexdigest()
    )


def _valid_sead_admission(path: Path) -> bool:
    manifest_path = path.parent / "manifest.json"
    try:
        admission_bytes = path.read_bytes()
        if hashlib.sha256(admission_bytes).hexdigest() != _SEAD_ADMISSION_SHA256:
            return False
        admission = json.loads(admission_bytes)
        declared_scope = admission.get("declared_scope")
        copied_files = admission.get("copied_files")
        if (
            not isinstance(declared_scope, dict)
            or not isinstance(copied_files, list)
            or not copied_files
            or not manifest_path.is_file()
        ):
            return False
        copied_paths: list[str] = []
        for item in copied_files:
            if not isinstance(item, dict):
                return False
            relative_path = item.get("path")
            if (
                not isinstance(relative_path, str)
                or not _safe_relative_path(relative_path)
                or _non_negative_int(item.get("byte_count")) is None
                or not _sha256_text(item.get("sha256"))
            ):
                return False
            copied_paths.append(relative_path)
        expected_tables = _sead_full_source_tables()
        expected_copied_paths = {
            "country-decisions.json",
            "manifest.json",
            "parent-admission.json",
            "reconciliation/countries.json",
            "reconciliation/joins.json",
            *(f"payloads/{table}.json" for table in expected_tables),
            *(f"receipts/{table}.json" for table in expected_tables),
        }
        if (
            len(copied_paths) != len(set(copied_paths))
            or set(copied_paths) != expected_copied_paths
        ):
            return False
        actual_paths: set[str] = set()
        for candidate in path.parent.rglob("*"):
            if candidate.is_symlink():
                return False
            if candidate.is_file():
                actual_paths.add(candidate.relative_to(path.parent).as_posix())
            elif not candidate.is_dir():
                return False
        if actual_paths != expected_copied_paths | {"admission.json"}:
            return False
        records_by_path = {
            str(item["path"]): item
            for item in copied_files
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        for relative_path, record in records_by_path.items():
            content_path = path.parent.joinpath(*Path(relative_path).parts)
            if not _regular_non_symlink(content_path):
                return False
            content = content_path.read_bytes()
            if (
                record.get("byte_count") != len(content)
                or record.get("sha256") != hashlib.sha256(content).hexdigest()
            ):
                return False
        if (
            records_by_path["country-decisions.json"].get("sha256")
            != _SEAD_COUNTRY_DECISIONS_SHA256
            or records_by_path["parent-admission.json"].get("sha256")
            != _SEAD_PARENT_ADMISSION_SHA256
        ):
            return False
        table_values = declared_scope.get("tables")
        if not isinstance(table_values, list):
            return False
        tables: list[str] = []
        for table in table_values:
            if not isinstance(table, str):
                return False
            tables.append(table)
        manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        if admission.get("schema_version") != "sead-acquisition-admission.v1":
            return False
        if admission.get("source_family") != "sead":
            return False
        if (
            admission.get("run_id") != path.parent.name
            or path.parent.name != _SEAD_RUN_ID
        ):
            return False
        if (
            admission.get("scope_id") != _SEAD_SCOPE_ID
            or admission.get("build_id") != _SEAD_BUILD_ID
            or admission.get("acquisition_manifest_sha256")
            != _SEAD_ACQUISITION_MANIFEST_SHA256
            or manifest_digest != _SEAD_ACQUISITION_MANIFEST_SHA256
            or admission.get("acquisition_bundle_sha256")
            != _SEAD_ACQUISITION_BUNDLE_SHA256
            or admission.get("parent_admission_sha256") != _SEAD_PARENT_ADMISSION_SHA256
        ):
            return False
        if declared_scope.get("scope_key") != "full_evidence_relations":
            return False
        if declared_scope.get("status") != "complete_for_declared_relations":
            return False
        if len(expected_tables) != 61 or declared_scope.get("table_count") != 61:
            return False
        if len(tables) != len(set(tables)) or frozenset(tables) != expected_tables:
            return False
        return (
            declared_scope.get("join_count") == 86
            and declared_scope.get("wp01_complete") is False
            and admission.get("release_status") == "refused"
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return False
