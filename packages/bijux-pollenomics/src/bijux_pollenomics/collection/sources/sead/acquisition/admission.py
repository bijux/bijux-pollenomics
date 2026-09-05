"""Validate and immutably admit a completed scoped SEAD acquisition."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
from types import MappingProxyType

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    ACQUISITION_MANIFEST_SCHEMA_VERSION,
    ACQUISITION_RECEIPT_SCHEMA_VERSION,
    NORDIC_COUNTRY_CODES,
    TABLE_PAYLOAD_SCHEMA_VERSION,
    reconcile_sead_join,
)
from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    SEAD_LIMIT,
    SEAD_POSTGREST_ROOT,
    build_sead_in_filter,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    SCOPED_ORCHESTRATOR_VERSION,
    SCOPED_RECEIPT_SCHEMA_VERSION,
    SEAD_FULL_EVIDENCE_JOIN_PLANS,
    SEAD_FULL_EVIDENCE_TABLE_PLANS,
    SEAD_SCOPED_TABLE_PLANS,
    SeadJoinPlan,
    SeadScopedTablePlan,
)

ADMISSION_SCHEMA_VERSION = "sead-acquisition-admission.v1"
ADMISSION_SCOPE = "declared_chronology_relations"
FULL_EVIDENCE_ADMISSION_SCOPE = "full_evidence_relations"

__all__ = [
    "ADMISSION_SCHEMA_VERSION",
    "SeadAcquisitionAdmission",
    "SeadAdmissionExpectedIdentity",
    "SeadMaterializedAdmissionSnapshot",
    "materialize_sead_full_evidence_admission",
    "materialize_sead_acquisition_admission",
    "validate_materialized_sead_full_evidence_admission",
    "read_materialized_sead_full_evidence_admission",
    "validate_sead_full_evidence_admission",
    "validate_sead_acquisition_admission",
]

_SAFE_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SHA256_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
_TARGET_COUNTRY_CODES = NORDIC_COUNTRY_CODES[:-1]
_COUNTRY_SCOPE = list(_TARGET_COUNTRY_CODES)
_SITE_PRIMARY_KEY = "site_id"
_SITE_PROJECTION = (
    "site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
    "altitude,site_description,site_uuid"
)
_AGGREGATE_ROUTE = "postgrest_dependency_scoped"
_QUERY_ROUTE = "postgrest"
_QUERY_TOOL_VERSION = "sead-postgrest-acquisition.v1"
_QUERY_MAX_PAGES = 10_000
_PREFLIGHT_MAX_PAGES = 100
_COUNTRY_NAMES = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}
_COUNTRY_DECISIONS_SCHEMA_VERSION = "sead-live-country-decisions.v1"
_COUNTRY_RECONCILIATION_SCHEMA_VERSION = "sead-country-reconciliation.v1"
_JOIN_RECONCILIATIONS_SCHEMA_VERSION = "sead-join-reconciliations.v1"
_EXPECTED_JOIN_SPECS = {
    "sites.sample_groups": (
        "tbl_sites",
        "tbl_sample_groups",
        "site_id",
        "sample_group_id",
        "site_id",
        True,
    ),
    "sample_groups.physical_samples": (
        "tbl_sample_groups",
        "tbl_physical_samples",
        "sample_group_id",
        "physical_sample_id",
        "sample_group_id",
        True,
    ),
    "physical_samples.analysis_entities": (
        "tbl_physical_samples",
        "tbl_analysis_entities",
        "physical_sample_id",
        "analysis_entity_id",
        "physical_sample_id",
        True,
    ),
    "analysis_entities.analysis_entity_ages": (
        "tbl_analysis_entities",
        "tbl_analysis_entity_ages",
        "analysis_entity_id",
        "analysis_entity_age_id",
        "analysis_entity_id",
        True,
    ),
    "analysis_entities.geochronology": (
        "tbl_analysis_entities",
        "tbl_geochronology",
        "analysis_entity_id",
        "geochron_id",
        "analysis_entity_id",
        True,
    ),
    "analysis_entities.dendro_dates": (
        "tbl_analysis_entities",
        "tbl_dendro_dates",
        "analysis_entity_id",
        "dendro_date_id",
        "analysis_entity_id",
        True,
    ),
    "analysis_entities.analysis_values": (
        "tbl_analysis_entities",
        "tbl_analysis_values",
        "analysis_entity_id",
        "analysis_value_id",
        "analysis_entity_id",
        True,
    ),
    "analysis_values.analysis_dating_ranges": (
        "tbl_analysis_values",
        "tbl_analysis_dating_ranges",
        "analysis_value_id",
        "analysis_dating_range_id",
        "analysis_value_id",
        True,
    ),
    "analysis_entities.relative_dates": (
        "tbl_analysis_entities",
        "tbl_relative_dates",
        "analysis_entity_id",
        "relative_date_id",
        "analysis_entity_id",
        True,
    ),
    "relative_ages.relative_age_refs": (
        "tbl_relative_ages",
        "tbl_relative_age_refs",
        "relative_age_id",
        "relative_age_ref_id",
        "relative_age_id",
        True,
    ),
    "sites.site_references": (
        "tbl_sites",
        "tbl_site_references",
        "site_id",
        "site_reference_id",
        "site_id",
        True,
    ),
    "sample_groups.sample_group_references": (
        "tbl_sample_groups",
        "tbl_sample_group_references",
        "sample_group_id",
        "sample_group_reference_id",
        "sample_group_id",
        True,
    ),
    "age_types.analysis_dating_ranges": (
        "tbl_age_types",
        "tbl_analysis_dating_ranges",
        "age_type_id",
        "analysis_dating_range_id",
        "age_type_id",
        False,
    ),
    "age_types.dendro_dates": (
        "tbl_age_types",
        "tbl_dendro_dates",
        "age_type_id",
        "dendro_date_id",
        "age_type_id",
        False,
    ),
    "relative_ages.relative_dates": (
        "tbl_relative_ages",
        "tbl_relative_dates",
        "relative_age_id",
        "relative_date_id",
        "relative_age_id",
        False,
    ),
    "dating_uncertainty.analysis_dating_ranges": (
        "tbl_dating_uncertainty",
        "tbl_analysis_dating_ranges",
        "dating_uncertainty_id",
        "analysis_dating_range_id",
        "dating_uncertainty_id",
        False,
    ),
    "dating_uncertainty.geochronology": (
        "tbl_dating_uncertainty",
        "tbl_geochronology",
        "dating_uncertainty_id",
        "geochron_id",
        "dating_uncertainty_id",
        False,
    ),
    "dating_uncertainty.dendro_dates": (
        "tbl_dating_uncertainty",
        "tbl_dendro_dates",
        "dating_uncertainty_id",
        "dendro_date_id",
        "dating_uncertainty_id",
        False,
    ),
    "dating_uncertainty.relative_dates": (
        "tbl_dating_uncertainty",
        "tbl_relative_dates",
        "dating_uncertainty_id",
        "relative_date_id",
        "dating_uncertainty_id",
        False,
    ),
    "methods.relative_dates": (
        "tbl_methods",
        "tbl_relative_dates",
        "method_id",
        "relative_date_id",
        "method_id",
        False,
    ),
    "datasets.analysis_entities": (
        "tbl_datasets",
        "tbl_analysis_entities",
        "dataset_id",
        "analysis_entity_id",
        "dataset_id",
        False,
    ),
    "biblio.datasets": (
        "tbl_biblio",
        "tbl_datasets",
        "biblio_id",
        "dataset_id",
        "biblio_id",
        False,
    ),
    "biblio.site_references": (
        "tbl_biblio",
        "tbl_site_references",
        "biblio_id",
        "site_reference_id",
        "biblio_id",
        False,
    ),
    "biblio.sample_group_references": (
        "tbl_biblio",
        "tbl_sample_group_references",
        "biblio_id",
        "sample_group_reference_id",
        "biblio_id",
        False,
    ),
    "biblio.relative_age_refs": (
        "tbl_biblio",
        "tbl_relative_age_refs",
        "biblio_id",
        "relative_age_ref_id",
        "biblio_id",
        False,
    ),
}
_DOWNSTREAM_REFUSALS = {
    "chronology_claims": "typed_chronology_claims_not_materialized",
    "evidence_events": "observation_relations_not_captured",
    "propagation_events": "propagation_events_not_materialized",
}


@dataclass(frozen=True)
class _AdmissionProfile:
    scope_key: str
    relation_scope: str
    tables: tuple[str, ...]
    table_plans: tuple[SeadScopedTablePlan, ...]
    join_plans: tuple[SeadJoinPlan, ...]
    orchestrator_version: str
    wp01_complete: bool


_SCOPED_PROFILE = _AdmissionProfile(
    scope_key=ADMISSION_SCOPE,
    relation_scope="chronology_relations",
    tables=SEAD_LINKED_SOURCE_TABLES,
    table_plans=SEAD_SCOPED_TABLE_PLANS,
    join_plans=tuple(
        SeadJoinPlan(edge, *spec) for edge, spec in _EXPECTED_JOIN_SPECS.items()
    ),
    orchestrator_version=SCOPED_ORCHESTRATOR_VERSION,
    wp01_complete=False,
)
_FULL_EVIDENCE_PROFILE = _AdmissionProfile(
    scope_key=FULL_EVIDENCE_ADMISSION_SCOPE,
    relation_scope="full_evidence_relations",
    tables=SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    table_plans=SEAD_FULL_EVIDENCE_TABLE_PLANS,
    join_plans=SEAD_FULL_EVIDENCE_JOIN_PLANS,
    orchestrator_version=FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    wp01_complete=False,
)


@dataclass(frozen=True)
class SeadAcquisitionAdmission:
    """One validated immutable acquisition admission."""

    run_id: str
    output_root: Path
    admission_path: Path
    admission: dict[str, object]


@dataclass(frozen=True)
class SeadAdmissionExpectedIdentity:
    """Caller-pinned identities required before an acquisition can be admitted."""

    scope_id: str
    run_id: str
    parent_run_id: str
    build_id: str
    country_authority_id: str
    country_authority_artifact_digest: str
    country_authority_root: Path
    bbox_payload_sha256: str
    acquisition_manifest_sha256: str
    country_decisions_sha256: str
    parent_admission_sha256: str | None = None


@dataclass(frozen=True)
class SeadMaterializedAdmissionSnapshot:
    """Admission metadata and the exact bytes verified in one validation pass."""

    admission: Mapping[str, object]
    copied_files: Mapping[str, bytes]


@dataclass(frozen=True)
class _ValidatedAdmission:
    source_root: Path
    decisions_path: Path
    admission: dict[str, object]
    copied_files: dict[str, bytes]


@dataclass(frozen=True)
class _BoundaryAuthority:
    boundaries: dict[str, dict[str, object]]
    artifact_digest: str
    version: str
    source_version: str
    authority_id: str
    manifest_sha256: str
    source_asset_sha256: str
    country_artifact_sha256: dict[str, str]


def validate_sead_acquisition_admission(
    snapshot_root: Path,
    *,
    country_decisions_path: Path,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> dict[str, object]:
    """Validate one scoped acquisition and return its admission record."""
    return _validate_cached_admission(
        snapshot_root,
        country_decisions_path=country_decisions_path,
        expected_identity=expected_identity,
        profile=_SCOPED_PROFILE,
        parent_admission_path=None,
    ).admission


def validate_sead_full_evidence_admission(
    snapshot_root: Path,
    *,
    country_decisions_path: Path,
    parent_admission_path: Path,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> dict[str, object]:
    """Validate the complete immutable SEAD evidence relation capture."""
    return _validate_cached_admission(
        snapshot_root,
        country_decisions_path=country_decisions_path,
        expected_identity=expected_identity,
        profile=_FULL_EVIDENCE_PROFILE,
        parent_admission_path=parent_admission_path,
        admitted_root=False,
    ).admission


def validate_materialized_sead_full_evidence_admission(
    acquisition_root: Path,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> dict[str, object]:
    """Recompute and validate an already materialized full-evidence admission."""
    return dict(
        read_materialized_sead_full_evidence_admission(
            acquisition_root,
            expected_identity=expected_identity,
        ).admission
    )


def read_materialized_sead_full_evidence_admission(
    acquisition_root: Path,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> SeadMaterializedAdmissionSnapshot:
    """Return only bytes retained by the full materialized-admission validation."""
    root = _validated_source_directory(acquisition_root)
    observed_bytes = _read_regular_file(root / "admission.json")
    observed = _json_object(observed_bytes, "admission.json")
    _expect_equal(
        observed_bytes, _canonical_bytes(observed), "canonical admission bytes"
    )
    validated = _validate_cached_admission(
        root,
        country_decisions_path=root / "country-decisions.json",
        expected_identity=expected_identity,
        profile=_FULL_EVIDENCE_PROFILE,
        parent_admission_path=root / "parent-admission.json",
        admitted_root=True,
    )
    _expect_equal(
        observed_bytes,
        _canonical_bytes(validated.admission),
        "independently recomputed full-evidence admission",
    )
    return SeadMaterializedAdmissionSnapshot(
        admission=MappingProxyType(dict(validated.admission)),
        copied_files=MappingProxyType(dict(validated.copied_files)),
    )


def _validate_cached_admission(
    snapshot_root: Path,
    *,
    country_decisions_path: Path,
    expected_identity: SeadAdmissionExpectedIdentity,
    profile: _AdmissionProfile,
    parent_admission_path: Path | None,
    admitted_root: bool = False,
) -> _ValidatedAdmission:
    root = _validated_source_directory(snapshot_root)
    decisions_path = _validated_source_file(country_decisions_path)
    manifest_bytes = _read_regular_file(root / "manifest.json")
    decisions_bytes = _read_regular_file(decisions_path)
    _validate_expected_identity(expected_identity)
    boundary_authority = _load_validated_boundary_authority(
        expected_identity.country_authority_root,
        expected_identity=expected_identity,
    )
    _expect_equal(
        hashlib.sha256(manifest_bytes).hexdigest(),
        expected_identity.acquisition_manifest_sha256,
        "caller-pinned acquisition manifest SHA-256",
    )
    _expect_equal(
        hashlib.sha256(decisions_bytes).hexdigest(),
        expected_identity.country_decisions_sha256,
        "caller-pinned country decisions SHA-256",
    )
    manifest = _json_object(manifest_bytes, "manifest.json")
    _expect_equal(
        manifest.get("schema_version"),
        ACQUISITION_MANIFEST_SCHEMA_VERSION,
        "manifest schema_version",
    )
    _expect_equal(manifest.get("status"), "complete", "manifest status")
    for field in (
        "missing_required_tables",
        "incomplete_required_tables",
        "failed_join_edges",
    ):
        _expect_equal(manifest.get(field), [], f"manifest {field}")
    _expect_equal(
        manifest.get("country_reconciliation_status"),
        "complete",
        "manifest country_reconciliation_status",
    )
    required_tables = _string_list(
        manifest.get("required_tables"), "manifest required_tables"
    )
    if required_tables != sorted(profile.tables):
        raise ValueError(
            "SEAD admission requires the exact declared "
            f"{len(profile.tables)}-table scope"
        )

    source_files = _validate_manifest_files(
        root,
        manifest,
        manifest_bytes,
        tables=profile.tables,
        allowed_extra_paths=(
            {"admission.json", "country-decisions.json", "parent-admission.json"}
            if admitted_root
            else set()
        ),
    )
    receipts: dict[str, Mapping[str, object]] = {}
    rows_by_table: dict[str, list[Mapping[str, object]]] = {}
    table_counts: dict[str, int] = {}
    for table in sorted(required_tables):
        payload_path = root / "payloads" / f"{table}.json"
        receipt_path = root / "receipts" / f"{table}.json"
        payload_bytes = source_files[payload_path.relative_to(root).as_posix()]
        receipt_bytes = source_files[receipt_path.relative_to(root).as_posix()]
        payload = _json_object(payload_bytes, f"payloads/{table}.json")
        receipt = _json_object(receipt_bytes, f"receipts/{table}.json")
        rows = _validate_table_payload(
            table, payload, payload_bytes, receipt, profile=profile
        )
        receipts[table] = receipt
        rows_by_table[table] = rows
        table_counts[table] = len(rows)

    identities = {
        field: _common_text(receipts.values(), field)
        for field in ("scope_id", "run_id", "parent_run_id", "build_id")
    }
    _validate_embedded_identities(identities, expected_identity)
    run_id = identities["run_id"]
    _validate_site_rows(rows_by_table["tbl_sites"])
    _validate_scoped_receipts(
        receipts,
        rows_by_table=rows_by_table,
        identities=identities,
        profile=profile,
    )

    country_reconciliation = _json_object(
        source_files["reconciliation/countries.json"],
        "reconciliation/countries.json",
    )
    joins = _json_object(
        source_files["reconciliation/joins.json"],
        "reconciliation/joins.json",
    )
    country_summary = _validate_country_accounting(
        country_reconciliation,
        decisions_bytes=decisions_bytes,
        site_rows=rows_by_table["tbl_sites"],
        site_receipt=receipts["tbl_sites"],
        identities=identities,
        expected_identity=expected_identity,
        boundary_authority=boundary_authority,
        profile=profile,
    )
    _validate_joins(
        joins,
        rows_by_table=rows_by_table,
        identities=identities,
        join_plans=profile.join_plans,
    )

    copied_files = {
        **source_files,
        "country-decisions.json": decisions_bytes,
    }
    parent_admission_sha256 = None
    if profile is _FULL_EVIDENCE_PROFILE:
        if parent_admission_path is None:
            raise ValueError("Full-evidence admission requires its parent admission")
        parent_bytes = _read_regular_file(_validated_source_file(parent_admission_path))
        parent_admission_sha256 = _validate_parent_admission(
            parent_bytes,
            expected_identity=expected_identity,
            parent_run_id=identities["parent_run_id"],
            country_decisions_sha256=hashlib.sha256(decisions_bytes).hexdigest(),
        )
        copied_files["parent-admission.json"] = parent_bytes
    copied_file_records = [
        {
            "path": relative_path,
            "sha256": hashlib.sha256(content).hexdigest(),
            "byte_count": len(content),
        }
        for relative_path, content in sorted(copied_files.items())
    ]
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    admission: dict[str, object] = {
        "schema_version": ADMISSION_SCHEMA_VERSION,
        "source_family": "sead",
        "run_id": run_id,
        "scope_id": identities["scope_id"],
        "parent_run_id": identities["parent_run_id"],
        "build_id": identities["build_id"],
        "acquisition_manifest_sha256": manifest_sha256,
        "acquisition_bundle_sha256": _file_set_digest(copied_file_records),
        "declared_scope": {
            "scope_key": profile.scope_key,
            "table_count": len(required_tables),
            "tables": sorted(required_tables),
            "join_count": len(profile.join_plans),
            "status": "complete_for_declared_relations",
            "wp01_complete": profile.wp01_complete,
        },
        "table_counts": dict(sorted(table_counts.items())),
        "country_accounting": country_summary,
        "validation_limitations": [
            {
                "status": "not_independently_verified",
                "reason_code": "excluded_country_coordinates_lack_preserved_preflight_payload",
                "subject": "scope_excluded_country_decisions",
            }
        ],
        "downstream_statuses": _downstream_statuses(profile),
        "release_status": "refused",
        "release_reason_codes": sorted(_release_reason_codes(profile)),
        "copied_files": copied_file_records,
    }
    if parent_admission_sha256 is not None:
        admission["parent_admission_sha256"] = parent_admission_sha256
    return _ValidatedAdmission(
        source_root=root,
        decisions_path=decisions_path,
        admission=admission,
        copied_files=copied_files,
    )


def materialize_sead_acquisition_admission(
    snapshot_root: Path,
    *,
    country_decisions_path: Path,
    output_root: Path,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> SeadAcquisitionAdmission:
    """Atomically copy one validated acquisition without permitting replacement."""
    validated = _validate_cached_admission(
        snapshot_root,
        country_decisions_path=country_decisions_path,
        expected_identity=expected_identity,
        profile=_SCOPED_PROFILE,
        parent_admission_path=None,
        admitted_root=False,
    )
    return _materialize_validated_admission(validated, output_root=output_root)


def materialize_sead_full_evidence_admission(
    snapshot_root: Path,
    *,
    country_decisions_path: Path,
    parent_admission_path: Path,
    output_root: Path,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> SeadAcquisitionAdmission:
    """Atomically admit the exact 61-table, 86-join SEAD evidence graph."""
    validated = _validate_cached_admission(
        snapshot_root,
        country_decisions_path=country_decisions_path,
        expected_identity=expected_identity,
        profile=_FULL_EVIDENCE_PROFILE,
        parent_admission_path=parent_admission_path,
        admitted_root=False,
    )
    return _materialize_validated_admission(validated, output_root=output_root)


def _materialize_validated_admission(
    validated: _ValidatedAdmission, *, output_root: Path
) -> SeadAcquisitionAdmission:
    admission = validated.admission
    run_id = _required_text(admission.get("run_id"), "admission run_id")
    parent = _validated_output_parent(output_root)
    final_root = parent / run_id
    _reject_output_overlap(
        final_root,
        source_root=validated.source_root,
        decisions_path=validated.decisions_path,
    )
    expected_files = dict(validated.copied_files)
    expected_files["admission.json"] = _canonical_bytes(admission)

    if final_root.exists() or final_root.is_symlink():
        if final_root.is_symlink() or not final_root.is_dir():
            raise FileExistsError(f"Unsafe existing SEAD admission: {final_root}")
        if _directory_bytes(final_root) == expected_files:
            return SeadAcquisitionAdmission(
                run_id=run_id,
                output_root=final_root,
                admission_path=final_root / "admission.json",
                admission=admission,
            )
        raise FileExistsError(f"Non-identical SEAD admission exists: {final_root}")

    staging_root = parent / f".{run_id}.staging-{os.getpid()}"
    if staging_root.exists() or staging_root.is_symlink():
        raise FileExistsError(f"SEAD admission staging collision: {staging_root}")
    staging_root.mkdir()
    try:
        for relative_path, content in sorted(expected_files.items()):
            destination = staging_root.joinpath(*PurePosixPath(relative_path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        _expect_equal(
            _directory_bytes(staging_root),
            expected_files,
            "staged SEAD admission bytes",
        )
        os.replace(staging_root, final_root)
    except Exception:
        if staging_root.exists() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)
        raise
    return SeadAcquisitionAdmission(
        run_id=run_id,
        output_root=final_root,
        admission_path=final_root / "admission.json",
        admission=admission,
    )


def _validate_manifest_files(
    root: Path,
    manifest: Mapping[str, object],
    manifest_bytes: bytes,
    *,
    tables: Sequence[str],
    allowed_extra_paths: set[str],
) -> dict[str, bytes]:
    records = manifest.get("files")
    if not isinstance(records, list):
        raise TypeError("SEAD manifest files must be a list")
    expected_paths = {
        *(f"payloads/{table}.json" for table in tables),
        *(f"receipts/{table}.json" for table in tables),
        "reconciliation/countries.json",
        "reconciliation/joins.json",
    }
    files: dict[str, bytes] = {"manifest.json": manifest_bytes}
    for item in records:
        if not isinstance(item, Mapping):
            raise TypeError("SEAD manifest file record must be an object")
        relative_path = _safe_relative_path(item.get("path"))
        if relative_path in files:
            raise ValueError(f"Duplicate SEAD manifest path: {relative_path}")
        content = _read_regular_file(root.joinpath(*PurePosixPath(relative_path).parts))
        _expect_equal(
            len(content),
            _non_negative_int(item.get("byte_count"), f"{relative_path} byte_count"),
            f"{relative_path} byte_count",
        )
        _expect_equal(
            hashlib.sha256(content).hexdigest(),
            _sha256(item.get("sha256"), relative_path),
            f"{relative_path} SHA-256",
        )
        files[relative_path] = content
    if set(files) - {"manifest.json"} != expected_paths:
        raise ValueError("SEAD manifest does not cover the exact acquisition file set")
    actual_paths: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are forbidden in SEAD acquisition: {path}")
        if path.is_file():
            actual_paths.add(path.relative_to(root).as_posix())
    if actual_paths != set(files) | allowed_extra_paths:
        raise ValueError("SEAD acquisition contains missing or unmanifested files")
    return files


def _validate_table_payload(
    table: str,
    payload: Mapping[str, object],
    payload_bytes: bytes,
    receipt: Mapping[str, object],
    *,
    profile: _AdmissionProfile,
) -> list[Mapping[str, object]]:
    _expect_equal(
        payload.get("schema_version"),
        TABLE_PAYLOAD_SCHEMA_VERSION,
        f"{table} payload schema_version",
    )
    _expect_equal(payload.get("table"), table, f"{table} payload table")
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError(f"SEAD payload rows must be objects: {table}")
    typed_rows = [row for row in rows if isinstance(row, Mapping)]
    _expect_equal(payload_bytes, _canonical_bytes(payload), f"{table} canonical bytes")
    _expect_equal(
        receipt.get("schema_version"),
        SCOPED_RECEIPT_SCHEMA_VERSION,
        f"{table} receipt schema_version",
    )
    _expect_equal(receipt.get("source"), "SEAD", f"{table} receipt source")
    _expect_equal(receipt.get("status"), "complete", f"{table} receipt status")
    _expect_equal(receipt.get("table"), table, f"{table} receipt table")
    _expect_equal(
        _non_negative_int(receipt.get("row_count"), f"{table} receipt row_count"),
        len(typed_rows),
        f"{table} receipt row_count",
    )
    _expect_equal(
        receipt.get("content_sha256"),
        hashlib.sha256(payload_bytes).hexdigest(),
        f"{table} receipt content_sha256",
    )
    observed_schema = _observed_schema(typed_rows)
    _expect_equal(
        receipt.get("canonical_schema"),
        observed_schema,
        f"{table} canonical schema",
    )
    _expect_equal(
        receipt.get("canonical_schema_sha256"),
        hashlib.sha256(_canonical_bytes(observed_schema)).hexdigest(),
        f"{table} canonical schema SHA-256",
    )
    receipt_without_id = dict(receipt)
    receipt_id = receipt_without_id.pop("receipt_id", None)
    _expect_equal(
        receipt_id,
        "sead-scoped-receipt:"
        + hashlib.sha256(_canonical_bytes(receipt_without_id)).hexdigest(),
        f"{table} receipt_id",
    )
    expected_primary_key, expected_projection, _ = _declared_table_contract(
        table, plans=profile.table_plans
    )
    primary_key = _required_text(receipt.get("primary_key"), f"{table} primary_key")
    projection = _required_text(receipt.get("projection"), f"{table} projection")
    _expect_equal(primary_key, expected_primary_key, f"{table} declared primary_key")
    _expect_equal(projection, expected_projection, f"{table} declared projection")
    projected_fields = set(projection.split(","))
    identifiers: list[int] = []
    for index, row in enumerate(typed_rows):
        missing = sorted(projected_fields - set(row))
        if missing:
            raise ValueError(f"SEAD {table} row {index} misses fields: {missing}")
        extra = sorted(set(row) - projected_fields)
        if extra:
            raise ValueError(f"SEAD {table} row {index} has undeclared fields: {extra}")
        identifiers.append(
            _positive_int(row.get(primary_key), f"{table}.{primary_key}")
        )
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"SEAD {table} contains duplicate primary keys")
    if identifiers != sorted(identifiers):
        raise ValueError(f"SEAD {table} rows are not ordered by primary key")
    return typed_rows


def _validate_scoped_receipts(
    receipts: Mapping[str, Mapping[str, object]],
    *,
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
    identities: Mapping[str, str],
    profile: _AdmissionProfile,
) -> None:
    plans = {plan.table: plan for plan in profile.table_plans}
    site_scope = _mapping(
        receipts["tbl_sites"].get("spatial_scope"), "tbl_sites spatial_scope"
    )
    canonical_bbox = _bbox(site_scope.get("bbox"), "tbl_sites spatial bbox")
    canonical_assignment_id = _required_text(
        site_scope.get("country_assignment_id"), "tbl_sites country_assignment_id"
    )
    canonical_assignment_sha256 = _sha256(
        site_scope.get("country_assignment_sha256"),
        "tbl_sites country_assignment_sha256",
    )
    for table, receipt in receipts.items():
        primary_key, projection, filter_field = _declared_table_contract(
            table, plans=profile.table_plans
        )
        _expect_equal(receipt.get("route"), _AGGREGATE_ROUTE, f"{table} route")
        _expect_equal(
            receipt.get("tool_version"),
            profile.orchestrator_version,
            f"{table} tool_version",
        )
        _expect_equal(
            receipt.get("country_scope"), _COUNTRY_SCOPE, f"{table} country_scope"
        )
        _expect_equal(
            receipt.get("filter_field"), filter_field, f"{table} filter_field"
        )
        spatial_scope = _mapping(receipt.get("spatial_scope"), f"{table} spatial_scope")
        for field in ("scope_id", "parent_run_id", "build_id"):
            _expect_equal(
                spatial_scope.get(field),
                identities[field],
                f"{table} spatial_scope {field}",
            )
        _expect_equal(
            spatial_scope.get("orchestration_run_id"),
            identities["run_id"],
            f"{table} spatial_scope orchestration_run_id",
        )
        _expect_equal(
            spatial_scope.get("relation_scope"),
            profile.relation_scope,
            f"{table} relation_scope",
        )
        _expect_equal(
            spatial_scope.get("countries"),
            _COUNTRY_SCOPE,
            f"{table} spatial countries",
        )
        _expect_equal(
            spatial_scope.get("bbox"), list(canonical_bbox), f"{table} spatial bbox"
        )
        _expect_equal(
            spatial_scope.get("country_assignment_id"),
            canonical_assignment_id,
            f"{table} country assignment authority ID",
        )
        _expect_equal(
            spatial_scope.get("country_assignment_sha256"),
            canonical_assignment_sha256,
            f"{table} country assignment SHA-256",
        )
        if table == "tbl_sites":
            assignments = receipt.get("governed_country_assignments")
            if not isinstance(assignments, list):
                raise TypeError("SEAD site receipt lacks governed country assignments")
            expected_requested = sorted(
                _positive_int(item.get("site_id"), "assignment site_id")
                for item in assignments
                if isinstance(item, Mapping)
            )
        else:
            plan = plans.get(table)
            if plan is None:
                raise ValueError(f"Missing SEAD scoped table plan: {table}")
            expected_requested = sorted(
                {
                    _positive_int(row.get(dependency.field), dependency.field)
                    for dependency in plan.dependencies
                    for row in rows_by_table[dependency.table]
                    if row.get(dependency.field) is not None
                }
            )
        requested = _positive_int_list(
            receipt.get("requested_identities"), f"{table} requested identities"
        )
        _expect_equal(requested, sorted(set(requested)), f"{table} requested ordering")
        _expect_equal(requested, expected_requested, f"{table} requested identities")
        _expect_equal(
            receipt.get("requested_identity_count"),
            len(requested),
            f"{table} requested identity count",
        )
        _expect_equal(
            receipt.get("completion_basis"),
            (
                "governed_bbox_filter"
                if table == "tbl_sites"
                else (
                    "all_dependency_batches_complete"
                    if requested
                    else "empty_dependency_identity_set"
                )
            ),
            f"{table} completion_basis",
        )
        _validate_query_receipts(
            table,
            receipt,
            identities=identities,
            requested_identities=requested,
            expected_result_count=(
                _non_negative_int(receipt.get("bbox_row_count"), "bbox row count")
                if table == "tbl_sites"
                else len(rows_by_table[table])
            ),
            primary_key=primary_key,
            projection=projection,
            filter_field=filter_field,
            bbox=canonical_bbox,
            table_rows=rows_by_table[table],
            country_assignment_id=canonical_assignment_id,
            country_assignment_sha256=canonical_assignment_sha256,
            relation_scope=profile.relation_scope,
        )


def _validate_query_receipts(
    table: str,
    receipt: Mapping[str, object],
    *,
    identities: Mapping[str, str],
    requested_identities: Sequence[int],
    expected_result_count: int,
    primary_key: str,
    projection: str,
    filter_field: str,
    bbox: tuple[float, float, float, float],
    table_rows: Sequence[Mapping[str, object]],
    country_assignment_id: str,
    country_assignment_sha256: str,
    relation_scope: str,
) -> None:
    query_receipts = receipt.get("query_receipts")
    if not isinstance(query_receipts, list) or any(
        not isinstance(item, Mapping) for item in query_receipts
    ):
        raise ValueError(f"SEAD query receipts must be objects: {table}")
    _expect_equal(
        _non_negative_int(receipt.get("query_count"), f"{table} query_count"),
        len(query_receipts),
        f"{table} query_count",
    )
    if expected_result_count > 0 and not query_receipts:
        raise ValueError(f"Nonempty SEAD table lacks query receipts: {table}")
    if table != "tbl_sites" and not requested_identities and query_receipts:
        raise ValueError(
            f"Empty-identity SEAD table must not contain query receipts: {table}"
        )
    observed_filter_ids: list[int] = []
    observed_row_count = 0
    for index, item in enumerate(query_receipts):
        if not isinstance(item, Mapping):
            raise TypeError(f"Invalid SEAD query receipt: {table}[{index}]")
        spatial_scope = _mapping(
            item.get("spatial_scope"), f"{table} query spatial_scope"
        )
        _expect_equal(
            spatial_scope.get("relation_scope"),
            relation_scope,
            f"{table} query relation_scope",
        )
        _expect_equal(
            spatial_scope.get("countries"),
            _COUNTRY_SCOPE,
            f"{table} query spatial countries",
        )
        _expect_equal(
            spatial_scope.get("country_assignment_id"),
            country_assignment_id,
            f"{table} query country assignment authority ID",
        )
        _expect_equal(
            spatial_scope.get("country_assignment_sha256"),
            country_assignment_sha256,
            f"{table} query country assignment SHA-256",
        )
        if table != "tbl_sites":
            _expect_equal(
                spatial_scope.get("filter_field"),
                receipt.get("filter_field"),
                f"{table} query filter_field",
            )
            filter_ids = _positive_int_list(
                spatial_scope.get("filter_ids"), f"{table} query filter IDs"
            )
            observed_filter_ids.extend(filter_ids)
            expected_parameters = [
                ["select", projection],
                [filter_field, build_sead_in_filter(filter_ids)],
                ["order", f"{filter_field},{primary_key}"],
            ]
            expected_order = [filter_field, primary_key]
            expected_kind = "dependency_identity_filter"
            allowed = set(filter_ids)
            expected_rows = sorted(
                (
                    dict(row)
                    for row in table_rows
                    if _positive_int(row.get(filter_field), filter_field) in allowed
                ),
                key=lambda row: (
                    _positive_int(row.get(filter_field), filter_field),
                    _positive_int(row.get(primary_key), primary_key),
                ),
            )
        else:
            expected_parameters = _bbox_query_parameters(bbox, projection)
            expected_order = [primary_key]
            expected_kind = "governed_bbox"
            expected_rows = None
        _expect_equal(
            spatial_scope.get("kind"), expected_kind, f"{table} query scope kind"
        )
        _expect_equal(
            spatial_scope.get("bbox"), list(bbox), f"{table} query spatial bbox"
        )
        observed_row_count += _validate_acquisition_receipt(
            item,
            table=table,
            identities=identities,
            label=f"{table} query receipt {index}",
            require_orchestration_identity=True,
            expected_parameters=expected_parameters,
            expected_order=expected_order,
            expected_max_pages=_QUERY_MAX_PAGES,
            expected_rows=expected_rows,
        )
    _expect_equal(observed_row_count, expected_result_count, f"{table} query rows")
    if table != "tbl_sites":
        _expect_equal(
            observed_filter_ids,
            requested_identities,
            f"{table} query requested identity batches",
        )


def _validate_acquisition_receipt(
    receipt: Mapping[str, object],
    *,
    table: str,
    identities: Mapping[str, str],
    label: str,
    require_orchestration_identity: bool,
    expected_parameters: Sequence[Sequence[str]],
    expected_order: Sequence[str],
    expected_max_pages: int | None,
    expected_rows: Sequence[Mapping[str, object]] | None,
) -> int:
    _expect_equal(
        receipt.get("schema_version"),
        ACQUISITION_RECEIPT_SCHEMA_VERSION,
        f"{label} schema_version",
    )
    _expect_equal(receipt.get("source"), "SEAD", f"{label} source")
    _expect_equal(receipt.get("route"), _QUERY_ROUTE, f"{label} route")
    _expect_equal(
        receipt.get("tool_version"), _QUERY_TOOL_VERSION, f"{label} tool_version"
    )
    _expect_equal(receipt.get("table"), table, f"{label} table")
    _expect_equal(
        receipt.get("endpoint"),
        f"{SEAD_POSTGREST_ROOT}/{table}",
        f"{label} endpoint",
    )
    _expect_equal(
        receipt.get("country_scope"), _COUNTRY_SCOPE, f"{label} country_scope"
    )
    _expect_equal(receipt.get("order_by"), list(expected_order), f"{label} order_by")
    _expect_equal(
        receipt.get("parameters"),
        [list(item) for item in expected_parameters],
        f"{label} parameters",
    )
    _expect_equal(receipt.get("status"), "complete", f"{label} status")
    _expect_equal(receipt.get("failure_reason"), None, f"{label} failure_reason")
    _expect_equal(receipt.get("failures"), [], f"{label} failures")
    for field in ("parent_run_id", "build_id"):
        _expect_equal(receipt.get(field), identities[field], f"{label} {field}")
    spatial_scope = _mapping(receipt.get("spatial_scope"), f"{label} spatial_scope")
    _expect_equal(
        spatial_scope.get("scope_id"), identities["scope_id"], f"{label} scope_id"
    )
    if require_orchestration_identity:
        for field in ("parent_run_id", "build_id"):
            _expect_equal(
                spatial_scope.get(field), identities[field], f"{label} scope {field}"
            )
        _expect_equal(
            spatial_scope.get("orchestration_run_id"),
            identities["run_id"],
            f"{label} orchestration_run_id",
        )
    row_count = _non_negative_int(receipt.get("row_count"), f"{label} row_count")
    canonical_schema = _mapping(
        receipt.get("canonical_schema"), f"{label} canonical_schema"
    )
    _expect_equal(
        canonical_schema.get("row_count"), row_count, f"{label} schema row_count"
    )
    _expect_equal(
        receipt.get("canonical_schema_sha256"),
        hashlib.sha256(_canonical_bytes(canonical_schema)).hexdigest(),
        f"{label} canonical schema SHA-256",
    )
    content_sha256 = _sha256(receipt.get("content_sha256"), f"{label} content")
    if expected_rows is not None:
        expected_schema = _observed_schema(expected_rows)
        _expect_equal(row_count, len(expected_rows), f"{label} reconstructed row_count")
        _expect_equal(
            dict(canonical_schema),
            expected_schema,
            f"{label} reconstructed canonical_schema",
        )
        expected_payload = _canonical_bytes(
            {
                "schema_version": TABLE_PAYLOAD_SCHEMA_VERSION,
                "table": table,
                "rows": list(expected_rows),
            }
        )
        _expect_equal(
            content_sha256,
            hashlib.sha256(expected_payload).hexdigest(),
            f"{label} reconstructed content_sha256",
        )
    pagination = _mapping(receipt.get("pagination"), f"{label} pagination")
    _expect_equal(pagination.get("complete"), True, f"{label} pagination complete")
    page_size = _positive_int(pagination.get("page_size"), f"{label} page_size")
    max_pages = _positive_int(pagination.get("max_pages"), f"{label} max_pages")
    _expect_equal(page_size, SEAD_LIMIT, f"{label} page_size")
    if expected_max_pages is not None:
        _expect_equal(max_pages, expected_max_pages, f"{label} max_pages")
    pages = pagination.get("pages")
    if not isinstance(pages, list) or any(
        not isinstance(page, Mapping) for page in pages
    ):
        raise ValueError(f"SEAD {label} pagination pages must be object rows")
    if not pages or len(pages) > max_pages:
        raise ValueError(f"SEAD {label} pagination page count is invalid")
    page_rows = 0
    for index, page in enumerate(pages, start=1):
        if not isinstance(page, Mapping):
            raise TypeError(f"SEAD {label} page must be an object")
        _expect_equal(page.get("page"), index, f"{label} page number")
        first = (index - 1) * page_size
        _expect_equal(
            page.get("range"),
            f"{first}-{first + page_size - 1}",
            f"{label} page range",
        )
        count = _non_negative_int(page.get("row_count"), f"{label} page row_count")
        if count > page_size:
            raise ValueError(f"SEAD {label} page row_count exceeds page_size")
        if index < len(pages) and count != page_size:
            raise ValueError(f"SEAD {label} has a short nonterminal page")
        page_rows += count
    if (
        _non_negative_int(pages[-1].get("row_count"), f"{label} terminal row_count")
        >= page_size
    ):
        raise ValueError(f"SEAD {label} lacks a short terminal page")
    _expect_equal(page_rows, row_count, f"{label} pagination row_count")
    result = _mapping(receipt.get("result"), f"{label} result")
    _expect_equal(result.get("failure_count"), 0, f"{label} failure count")
    attempt_count = _non_negative_int(
        result.get("attempt_count"), f"{label} attempt count"
    )
    retry_count = _non_negative_int(result.get("retry_count"), f"{label} retry count")
    _expect_equal(attempt_count, len(pages), f"{label} attempt count")
    _expect_equal(retry_count, 0, f"{label} retry count")
    receipt_without_id = dict(receipt)
    receipt_id = receipt_without_id.pop("receipt_id", None)
    _expect_equal(
        receipt_id,
        "sead-receipt:"
        + hashlib.sha256(_canonical_bytes(receipt_without_id)).hexdigest(),
        f"{label} receipt_id",
    )
    return row_count


def _validate_site_rows(rows: Sequence[Mapping[str, object]]) -> None:
    uuids: list[str] = []
    for row in rows:
        uuids.append(_required_text(row.get("site_uuid"), "tbl_sites.site_uuid"))
    if len(uuids) != len(set(uuids)):
        raise ValueError("SEAD site_uuid values must be unique")


def _validate_country_accounting(
    reconciliation: Mapping[str, object],
    *,
    decisions_bytes: bytes,
    site_rows: Sequence[Mapping[str, object]],
    site_receipt: Mapping[str, object],
    identities: Mapping[str, str],
    expected_identity: SeadAdmissionExpectedIdentity,
    boundary_authority: _BoundaryAuthority,
    profile: _AdmissionProfile,
) -> dict[str, object]:
    from ....spatial import decide_country_attribution

    _expect_equal(
        reconciliation.get("schema_version"),
        _COUNTRY_RECONCILIATION_SCHEMA_VERSION,
        "country reconciliation schema_version",
    )
    _validate_identities(reconciliation, identities, "country reconciliation")
    _expect_equal(reconciliation.get("reconciles"), True, "country reconciliation")
    _expect_equal(reconciliation.get("duplicate_site_ids"), [], "duplicate site IDs")
    counts = _country_counts(reconciliation.get("counts"), "country reconciliation")
    row_count = _non_negative_int(reconciliation.get("row_count"), "country row_count")
    _expect_equal(sum(counts.values()), row_count, "country partition row_count")
    _expect_equal(row_count, len(site_rows), "country rows versus site payload")
    _expect_equal(counts["UNASSIGNED"], 0, "admitted UNASSIGNED rows")
    _expect_equal(
        reconciliation.get("assigned_count"),
        sum(counts[code] for code in _TARGET_COUNTRY_CODES),
        "assigned country count",
    )
    _expect_equal(reconciliation.get("unassigned_count"), 0, "unassigned count")

    decisions = _json_object(decisions_bytes, "country-decisions.json")
    _expect_equal(
        decisions.get("schema_version"),
        _COUNTRY_DECISIONS_SCHEMA_VERSION,
        "country decisions schema_version",
    )
    decision_identities = (
        {
            "scope_id": _required_text(decisions.get("input_id"), "decisions input_id"),
            "run_id": _required_text(decisions.get("run_id"), "decisions run_id"),
            "parent_run_id": _required_text(
                decisions.get("job_id"), "decisions job_id"
            ),
            "build_id": _required_text(decisions.get("build_id"), "decisions build_id"),
        }
        if profile is _FULL_EVIDENCE_PROFILE
        else identities
    )
    _expect_equal(
        decisions.get("run_id"), decision_identities["run_id"], "decisions run_id"
    )
    _expect_equal(
        decisions.get("input_id"), decision_identities["scope_id"], "decisions scope_id"
    )
    _expect_equal(
        decisions.get("job_id"),
        decision_identities["parent_run_id"],
        "decisions parent_run_id",
    )
    _expect_equal(
        decisions.get("build_id"), decision_identities["build_id"], "decisions build_id"
    )
    if profile is _FULL_EVIDENCE_PROFILE:
        _expect_equal(
            decisions.get("run_id"),
            identities["parent_run_id"],
            "full-evidence parent country-decision run",
        )
    bbox = _bbox(decisions.get("bbox"), "country decisions bbox")
    boundary_record = _mapping(
        decisions.get("boundary_authority"), "country boundary authority"
    )
    _expect_equal(
        boundary_record.get("authority_id"),
        expected_identity.country_authority_id,
        "country boundary authority ID",
    )
    _expect_equal(
        boundary_record.get("artifact_digest"),
        expected_identity.country_authority_artifact_digest,
        "country boundary authority artifact digest",
    )
    _sha256_id(boundary_record.get("authority_id"), "country authority ID")
    _sha256_id(
        boundary_record.get("artifact_digest"), "country authority artifact digest"
    )
    _expect_equal(
        boundary_record.get("version"),
        boundary_authority.source_version,
        "country boundary authority version",
    )
    for field, expected in (
        ("manifest_sha256", boundary_authority.manifest_sha256),
        (
            "normalized_artifact_sha256",
            boundary_authority.artifact_digest.removeprefix("sha256:"),
        ),
        ("source_asset_sha256", boundary_authority.source_asset_sha256),
        ("country_artifact_sha256", boundary_authority.country_artifact_sha256),
    ):
        _expect_equal(
            boundary_record.get(field), expected, f"country boundary authority {field}"
        )
    preflight = _mapping(
        decisions.get("preflight_receipt"), "country preflight receipt"
    )
    preflight_count = _validate_acquisition_receipt(
        preflight,
        table="tbl_sites",
        identities=decision_identities,
        label="country preflight receipt",
        require_orchestration_identity=False,
        expected_parameters=_bbox_query_parameters(bbox, _SITE_PROJECTION),
        expected_order=[_SITE_PRIMARY_KEY],
        expected_max_pages=_PREFLIGHT_MAX_PAGES,
        expected_rows=None,
    )
    _expect_equal(
        _mapping(preflight.get("spatial_scope"), "preflight spatial_scope").get("kind"),
        "governed_bbox_country_decision_preflight",
        "preflight scope kind",
    )
    _expect_equal(
        _mapping(preflight.get("spatial_scope"), "preflight spatial_scope").get("bbox"),
        list(bbox),
        "preflight spatial bbox",
    )
    _expect_equal(
        _mapping(preflight.get("spatial_scope"), "preflight spatial_scope").get(
            "boundary_authority_id"
        ),
        expected_identity.country_authority_id,
        "preflight boundary authority ID",
    )
    _expect_equal(
        preflight.get("content_sha256"),
        expected_identity.bbox_payload_sha256,
        "caller-pinned preflight payload SHA-256",
    )
    decision_rows = decisions.get("decisions")
    if not isinstance(decision_rows, list) or any(
        not isinstance(row, Mapping) for row in decision_rows
    ):
        raise ValueError("SEAD country decisions must be object rows")
    bbox_count = _non_negative_int(
        decisions.get("bbox_site_count"), "decisions bbox_site_count"
    )
    _expect_equal(len(decision_rows), bbox_count, "country decision denominator")
    decision_codes: Counter[str] = Counter(dict.fromkeys(NORDIC_COUNTRY_CODES, 0))
    decision_statuses: Counter[str] = Counter()
    decision_methods: Counter[str] = Counter()
    decision_by_site: dict[int, tuple[str, str]] = {}
    site_coordinates = {
        _positive_int(row.get("site_id"), "tbl_sites.site_id"): (
            _coordinate(row.get("latitude_dd"), "tbl_sites.latitude_dd", -90, 90),
            _coordinate(row.get("longitude_dd"), "tbl_sites.longitude_dd", -180, 180),
        )
        for row in site_rows
    }
    for row in decision_rows:
        if not isinstance(row, Mapping):
            raise TypeError("SEAD country decision row must be an object")
        site_id = _positive_int(row.get("site_id"), "country decision site_id")
        if site_id in decision_by_site:
            raise ValueError(f"Duplicate SEAD country decision: {site_id}")
        site_uuid = _required_text(row.get("site_uuid"), "country decision site_uuid")
        code = _required_text(row.get("governed_country_code"), "governed country code")
        if code not in NORDIC_COUNTRY_CODES:
            raise ValueError(f"Invalid governed SEAD country code: {code}")
        decision = row.get("decision")
        if not isinstance(decision, Mapping):
            raise TypeError("SEAD country decision detail must be an object")
        status = _required_text(decision.get("decision_status"), "decision status")
        method = _required_text(decision.get("decision_method"), "decision method")
        _validate_country_decision_vocabulary(
            code, decision, expected_identity=expected_identity
        )
        latitude = _coordinate(row.get("latitude_dd"), "decision latitude", -90, 90)
        longitude = _coordinate(
            row.get("longitude_dd"), "decision longitude", -180, 180
        )
        if not (bbox[1] <= latitude <= bbox[3] and bbox[0] <= longitude <= bbox[2]):
            raise ValueError(f"SEAD country decision is outside bbox: {site_id}")
        _expect_equal(decision.get("raw_country"), None, "country decision raw_country")
        recomputed = decide_country_attribution(
            longitude,
            latitude,
            boundary_authority.boundaries,
            boundary_artifact_digest=boundary_authority.artifact_digest,
            boundary_version=boundary_authority.version,
        )
        recomputed_code = (
            next(
                (
                    country_code
                    for country_code, country_name in _COUNTRY_NAMES.items()
                    if country_name == recomputed.derived_country
                ),
                "UNASSIGNED",
            )
            if recomputed.decision_status == "assigned"
            else "UNASSIGNED"
        )
        _expect_equal(code, recomputed_code, f"country geometry assignment {site_id}")
        for field, expected_value in (
            ("decision_status", recomputed.decision_status),
            ("decision_method", recomputed.decision_method),
            ("ambiguity_reason", recomputed.ambiguity_reason),
            ("refusal_reason", recomputed.refusal_reason),
            ("derived_country", recomputed.derived_country),
            ("candidate_countries", list(recomputed.candidate_countries)),
            ("raw_country_comparison", recomputed.raw_country_comparison),
            ("boundary_artifact_digest", recomputed.boundary_artifact_digest),
            ("boundary_version", recomputed.boundary_version),
        ):
            _expect_equal(
                decision.get(field),
                expected_value,
                f"country geometry {field} {site_id}",
            )
        if code in _TARGET_COUNTRY_CODES:
            _expect_equal(
                (latitude, longitude),
                site_coordinates.get(site_id),
                f"admitted country decision coordinates {site_id}",
            )
        decision_by_site[site_id] = (code, site_uuid)
        decision_codes[code] += 1
        decision_statuses[status] += 1
        decision_methods[method] += 1
    _expect_equal(
        dict(decision_codes),
        _country_counts(decisions.get("country_counts"), "country decisions"),
        "country decision counts",
    )
    _expect_equal(
        dict(sorted(decision_statuses.items())),
        decisions.get("decision_status_counts"),
        "country decision status counts",
    )
    _expect_equal(
        dict(sorted(decision_methods.items())),
        decisions.get("decision_method_counts"),
        "country decision method counts",
    )
    for code in _TARGET_COUNTRY_CODES:
        _expect_equal(decision_codes[code], counts[code], f"{code} country count")

    admitted_sites = {
        _positive_int(row.get("site_id"), "tbl_sites.site_id"): _required_text(
            row.get("site_uuid"), "tbl_sites.site_uuid"
        )
        for row in site_rows
    }
    expected_admitted = {
        site_id: site_uuid
        for site_id, (code, site_uuid) in decision_by_site.items()
        if code in _TARGET_COUNTRY_CODES
    }
    _expect_equal(admitted_sites, expected_admitted, "admitted country site identities")
    excluded_ids = sorted(
        site_id
        for site_id, (code, _) in decision_by_site.items()
        if code == "UNASSIGNED"
    )
    _expect_equal(
        reconciliation.get("bbox_row_count"), bbox_count, "bbox site denominator"
    )
    _expect_equal(preflight_count, bbox_count, "preflight bbox site denominator")
    _expect_equal(
        reconciliation.get("scope_excluded_count"),
        len(excluded_ids),
        "scope exclusion count",
    )
    _expect_equal(
        reconciliation.get("scope_excluded_site_ids"),
        excluded_ids,
        "scope exclusion IDs",
    )
    _expect_equal(row_count + len(excluded_ids), bbox_count, "bbox disposition")
    _expect_equal(
        site_receipt.get("scope_excluded_site_ids"),
        excluded_ids,
        "site receipt exclusions",
    )
    assignments = site_receipt.get("governed_country_assignments")
    if not isinstance(assignments, list):
        raise TypeError("SEAD site receipt lacks governed country assignments")
    assignment_map: dict[int, str] = {}
    for item in assignments:
        if not isinstance(item, Mapping):
            raise TypeError("SEAD governed country assignment must be an object")
        site_id = _positive_int(item.get("site_id"), "assignment site_id")
        code = _required_text(item.get("country_code"), "assignment country_code")
        if site_id in assignment_map:
            raise ValueError(f"Duplicate governed country assignment: {site_id}")
        assignment_map[site_id] = code
    _expect_equal(
        assignment_map,
        {site_id: code for site_id, (code, _) in decision_by_site.items()},
        "governed country assignments",
    )
    assignment_payload = [
        {"site_id": site_id, "country_code": code}
        for site_id, code in sorted(assignment_map.items())
    ]
    assignment_sha256 = hashlib.sha256(_canonical_bytes(assignment_payload)).hexdigest()
    site_scope = _mapping(site_receipt.get("spatial_scope"), "site spatial_scope")
    _expect_equal(
        site_scope.get("country_assignment_id"),
        expected_identity.country_authority_id,
        "site country assignment authority ID",
    )
    _expect_equal(
        site_scope.get("country_assignment_sha256"),
        assignment_sha256,
        "site country assignment SHA-256",
    )
    _expect_equal(
        reconciliation.get("country_assignment_id"),
        expected_identity.country_authority_id,
        "country reconciliation authority ID",
    )
    _expect_equal(
        reconciliation.get("country_assignment_sha256"),
        assignment_sha256,
        "country reconciliation assignment SHA-256",
    )
    site_queries = site_receipt.get("query_receipts")
    if not isinstance(site_queries, list) or len(site_queries) != 1:
        raise ValueError(
            "SEAD site receipt must preserve exactly one bbox query receipt"
        )
    site_query = _mapping(site_queries[0], "site bbox query receipt")
    _expect_equal(
        site_query.get("content_sha256"),
        expected_identity.bbox_payload_sha256,
        "caller-pinned site-query payload SHA-256",
    )
    for field in ("content_sha256", "canonical_schema", "canonical_schema_sha256"):
        _expect_equal(preflight.get(field), site_query.get(field), f"preflight {field}")
    _expect_equal(
        _mapping(site_query.get("spatial_scope"), "site query spatial_scope").get(
            "bbox"
        ),
        list(bbox),
        "site query bbox",
    )
    return {
        "bbox_site_count": bbox_count,
        "admitted_site_count": row_count,
        "scope_excluded_count": len(excluded_ids),
        "country_counts": {code: counts[code] for code in _TARGET_COUNTRY_CODES},
        "review_site_count": decision_statuses["review"],
        "unassigned_site_count": decision_statuses["unassigned"],
        "country_assignment_sha256": assignment_sha256,
        "boundary_authority_id": expected_identity.country_authority_id,
        "excluded_coordinate_validation": {
            "status": "not_independently_verified",
            "reason_code": "preflight_payload_not_preserved",
        },
        "reconciles": True,
    }


def _validate_joins(
    payload: Mapping[str, object],
    *,
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
    identities: Mapping[str, str],
    join_plans: Sequence[SeadJoinPlan],
) -> None:
    _expect_equal(
        payload.get("schema_version"),
        _JOIN_RECONCILIATIONS_SCHEMA_VERSION,
        "join reconciliations schema_version",
    )
    edges = payload.get("edges")
    if not isinstance(edges, list) or any(
        not isinstance(edge, Mapping) for edge in edges
    ):
        raise ValueError("SEAD join reconciliations must be object rows")
    by_name: dict[str, Mapping[str, object]] = {}
    for edge in edges:
        if not isinstance(edge, Mapping):
            raise TypeError("SEAD join reconciliation must be an object")
        name = _required_text(edge.get("edge"), "join edge")
        if name in by_name:
            raise ValueError(f"Duplicate SEAD join reconciliation: {name}")
        by_name[name] = edge
    expected_specs = {
        plan.edge: (
            plan.parent_table,
            plan.child_table,
            plan.parent_key,
            plan.child_key,
            plan.child_foreign_key,
            plan.reference_required,
        )
        for plan in join_plans
    }
    if set(by_name) != set(expected_specs) or len(by_name) != len(expected_specs):
        raise ValueError(
            f"SEAD admission requires exactly the {len(expected_specs)} declared joins"
        )
    for name, spec in expected_specs.items():
        edge = by_name[name]
        expected = _recompute_join(
            name,
            spec=spec,
            rows_by_table=rows_by_table,
            identities=identities,
        )
        _expect_equal(dict(edge), expected, f"{name} independently recomputed ledger")


def _recompute_join(
    name: str,
    *,
    spec: tuple[str, str, str, str, str, bool],
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
    identities: Mapping[str, str],
) -> dict[str, object]:
    (
        parent_table,
        child_table,
        parent_key,
        child_key,
        child_foreign_key,
        reference_required,
    ) = spec
    parent_rows = rows_by_table[parent_table]
    all_child_rows = rows_by_table[child_table]
    referenced_child_rows = tuple(
        row
        for row in all_child_rows
        if reference_required or row.get(child_foreign_key) is not None
    )
    result = reconcile_sead_join(
        edge=name,
        parent_rows=parent_rows,
        child_rows=referenced_child_rows,
        parent_key=parent_key,
        child_key=child_key,
        child_foreign_key=child_foreign_key,
    )
    parent_ids = {
        str(row[parent_key]) for row in parent_rows if row.get(parent_key) is not None
    }
    child_counts = Counter(
        str(row[child_foreign_key])
        for row in referenced_child_rows
        if row.get(child_foreign_key) is not None
    )
    matched_parent_ids = sorted(parent_ids & set(child_counts))
    zero_child_parent_ids = sorted(parent_ids - set(child_counts))
    null_reference_child_ids = sorted(
        _row_identity(row, index, child_key)
        for index, row in enumerate(all_child_rows)
        if row.get(child_foreign_key) is None
    )
    result.update(
        {
            **identities,
            "reference_required": reference_required,
            "total_child_row_count": len(all_child_rows),
            "referenced_child_row_count": len(referenced_child_rows),
            "null_reference_child_count": len(null_reference_child_ids),
            "null_reference_child_ids": null_reference_child_ids,
            "matched_parent_count": len(matched_parent_ids),
            "matched_parent_ids": matched_parent_ids,
            "zero_child_parent_count": len(zero_child_parent_ids),
            "zero_child_parent_ids": zero_child_parent_ids,
            "one_child_parent_count": sum(
                child_counts[parent_id] == 1 for parent_id in parent_ids
            ),
            "many_child_parent_count": sum(
                child_counts[parent_id] > 1 for parent_id in parent_ids
            ),
        }
    )
    return result


def _validate_identities(
    payload: Mapping[str, object], identities: Mapping[str, str], label: str
) -> None:
    for field, expected in identities.items():
        _expect_equal(payload.get(field), expected, f"{label} {field}")


def _declared_table_contract(
    table: str, *, plans: Sequence[SeadScopedTablePlan]
) -> tuple[str, str, str]:
    if table == "tbl_sites":
        return _SITE_PRIMARY_KEY, _SITE_PROJECTION, _SITE_PRIMARY_KEY
    for plan in plans:
        if plan.table == table:
            return plan.primary_key, plan.projection, plan.filter_field
    raise ValueError(f"Missing declared SEAD table plan: {table}")


def _bbox_query_parameters(
    bbox: tuple[float, float, float, float], projection: str
) -> list[list[str]]:
    return [
        ["select", projection],
        ["latitude_dd", f"gte.{bbox[1]}"],
        ["latitude_dd", f"lte.{bbox[3]}"],
        ["longitude_dd", f"gte.{bbox[0]}"],
        ["longitude_dd", f"lte.{bbox[2]}"],
        ["order", _SITE_PRIMARY_KEY],
    ]


def _validate_expected_identity(expected: SeadAdmissionExpectedIdentity) -> None:
    for field in (
        "scope_id",
        "build_id",
        "country_authority_id",
        "country_authority_artifact_digest",
    ):
        _sha256_id(getattr(expected, field), f"expected {field}")
    _sha256(
        expected.acquisition_manifest_sha256,
        "expected acquisition_manifest_sha256",
    )
    _sha256(expected.bbox_payload_sha256, "expected bbox_payload_sha256")
    _sha256(expected.country_decisions_sha256, "expected country_decisions_sha256")
    if expected.parent_admission_sha256 is not None:
        _sha256(
            expected.parent_admission_sha256,
            "expected parent_admission_sha256",
        )
    for value, label in (
        (expected.run_id, "expected run_id"),
        (expected.parent_run_id, "expected parent_run_id"),
    ):
        if not _SAFE_RUN_ID.fullmatch(value):
            raise ValueError(f"SEAD {label} is not a safe path identity")


def _validate_parent_admission(
    payload: bytes,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
    parent_run_id: str,
    country_decisions_sha256: str,
) -> str:
    expected_sha256 = expected_identity.parent_admission_sha256
    if expected_sha256 is None:
        raise ValueError(
            "Full-evidence expected identity lacks parent admission SHA-256"
        )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    _expect_equal(
        observed_sha256,
        expected_sha256,
        "caller-pinned parent admission SHA-256",
    )
    parent = _json_object(payload, "parent-admission.json")
    _expect_equal(
        parent.get("schema_version"),
        ADMISSION_SCHEMA_VERSION,
        "parent admission schema_version",
    )
    _expect_equal(parent.get("source_family"), "sead", "parent admission source")
    _expect_equal(parent.get("run_id"), parent_run_id, "parent admission run_id")
    copied_files = parent.get("copied_files")
    if not isinstance(copied_files, list):
        raise TypeError("Parent SEAD admission copied_files must be a list")
    country_records = [
        item
        for item in copied_files
        if isinstance(item, Mapping) and item.get("path") == "country-decisions.json"
    ]
    if len(country_records) != 1:
        raise ValueError("Parent SEAD admission must bind one country-decisions file")
    _expect_equal(
        country_records[0].get("sha256"),
        country_decisions_sha256,
        "parent admission country decisions SHA-256",
    )
    return observed_sha256


def _downstream_statuses(profile: _AdmissionProfile) -> dict[str, dict[str, str]]:
    reasons = (
        {
            "chronology_claims": "typed_chronology_claims_not_materialized",
            "evidence_events": "source_native_evidence_events_not_materialized",
            "propagation_events": "propagation_events_not_materialized",
        }
        if profile is _FULL_EVIDENCE_PROFILE
        else _DOWNSTREAM_REFUSALS
    )
    return {
        name: {"status": "refused", "reason_code": reason}
        for name, reason in reasons.items()
    }


def _release_reason_codes(profile: _AdmissionProfile) -> set[str]:
    reasons = {item["reason_code"] for item in _downstream_statuses(profile).values()}
    reasons.add("excluded_country_coordinates_lack_preserved_preflight_payload")
    if profile is _SCOPED_PROFILE:
        reasons.add("declared_relation_scope_is_not_full_wp01_scope")
    return reasons


def _load_validated_boundary_authority(
    boundary_root: Path, *, expected_identity: SeadAdmissionExpectedIdentity
) -> _BoundaryAuthority:
    from ...boundaries.collection import (
        BOUNDARY_CODES,
        NATURAL_EARTH_ADMIN0_URL,
        NATURAL_EARTH_RELEASE_PAGE_URL,
        NATURAL_EARTH_TERMS_URL,
        NATURAL_EARTH_VERSION,
    )
    from ...boundaries.store import load_country_boundaries

    root = _validated_source_directory(boundary_root)
    manifest_path = root / "raw" / "source_manifest.json"
    manifest_bytes = _read_regular_file(manifest_path)
    manifest = _json_object(manifest_bytes, str(manifest_path))
    boundaries = load_country_boundaries(
        output_root=root,
        boundary_codes=BOUNDARY_CODES,
        natural_earth_version=NATURAL_EARTH_VERSION,
        natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
        natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
    )
    if boundaries is None or set(boundaries) != set(BOUNDARY_CODES):
        raise ValueError("Pinned Nordic boundary authority is incomplete")
    for field, expected in (
        ("dataset", "Admin 0 - Countries"),
        ("release_page_url", NATURAL_EARTH_RELEASE_PAGE_URL),
        ("feature_count", 258),
        ("country_codes", BOUNDARY_CODES),
    ):
        _expect_equal(manifest.get(field), expected, f"boundary manifest {field}")
    source_digest = _sha256(manifest.get("sha256"), "boundary source asset")
    country_artifacts = _mapping(
        manifest.get("country_artifacts"), "boundary country artifacts"
    )
    if set(country_artifacts) != set(BOUNDARY_CODES):
        raise ValueError("Boundary manifest country artifacts are not exactly Nordic")
    country_digests: dict[str, str] = {}
    for country in BOUNDARY_CODES:
        record = _mapping(country_artifacts.get(country), f"{country} artifact")
        path = root / "raw" / f"{country.lower()}.geojson"
        content = _read_regular_file(path)
        digest = hashlib.sha256(content).hexdigest()
        _expect_equal(record.get("path"), path.name, f"{country} boundary path")
        _expect_equal(record.get("sha256"), digest, f"{country} boundary digest")
        features = boundaries[country].get("features")
        if not isinstance(features, list):
            raise TypeError(f"Invalid {country} boundary features")
        _expect_equal(
            record.get("feature_count"), len(features), f"{country} feature count"
        )
        country_digests[country] = digest
    normalized = _mapping(
        manifest.get("normalized_artifact"), "normalized boundary artifact"
    )
    _expect_equal(
        normalized.get("path"),
        "normalized/nordic_country_boundaries.geojson",
        "normalized boundary path",
    )
    normalized_path = root / "normalized" / "nordic_country_boundaries.geojson"
    normalized_bytes = _read_regular_file(normalized_path)
    normalized_digest = hashlib.sha256(normalized_bytes).hexdigest()
    _expect_equal(
        normalized.get("sha256"), normalized_digest, "normalized boundary digest"
    )
    normalized_payload = _json_object(normalized_bytes, str(normalized_path))
    _expect_equal(
        normalized_payload.get("type"), "FeatureCollection", "normalized type"
    )
    normalized_features = normalized_payload.get("features")
    if not isinstance(normalized_features, list):
        raise TypeError("Normalized boundary features must be a list")
    _expect_equal(
        normalized.get("feature_count"),
        len(normalized_features),
        "normalized feature count",
    )
    _expect_equal(
        len(normalized_features), len(BOUNDARY_CODES), "normalized country count"
    )
    identity = {
        "schema": "nordic-boundary-authority-identity.v1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_asset_sha256": source_digest,
        "country_artifact_sha256": country_digests,
        "normalized_artifact_sha256": normalized_digest,
        "version": NATURAL_EARTH_VERSION,
    }
    authority = _BoundaryAuthority(
        boundaries=boundaries,
        artifact_digest=f"sha256:{normalized_digest}",
        version=f"natural-earth:{NATURAL_EARTH_VERSION}",
        source_version=NATURAL_EARTH_VERSION,
        authority_id=f"sha256:{hashlib.sha256(_canonical_bytes(identity)).hexdigest()}",
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        source_asset_sha256=source_digest,
        country_artifact_sha256=country_digests,
    )
    _expect_equal(
        authority.authority_id,
        expected_identity.country_authority_id,
        "loaded country boundary authority ID",
    )
    _expect_equal(
        authority.artifact_digest,
        expected_identity.country_authority_artifact_digest,
        "loaded country authority artifact digest",
    )
    return authority


def _validate_embedded_identities(
    identities: Mapping[str, str],
    expected: SeadAdmissionExpectedIdentity,
) -> None:
    for field in ("scope_id", "run_id", "parent_run_id", "build_id"):
        _expect_equal(
            identities[field], getattr(expected, field), f"caller-pinned {field}"
        )
    _sha256_id(identities["scope_id"], "scope_id")
    _sha256_id(identities["build_id"], "build_id")
    if not _SAFE_RUN_ID.fullmatch(identities["run_id"]):
        raise ValueError("SEAD admission run_id is not a safe path segment")
    if not _SAFE_RUN_ID.fullmatch(identities["parent_run_id"]):
        raise ValueError("SEAD admission parent_run_id is not a safe identity")


def _validate_country_decision_vocabulary(
    code: str,
    decision: Mapping[str, object],
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> None:
    status = _required_text(decision.get("decision_status"), "decision status")
    method = _required_text(decision.get("decision_method"), "decision method")
    _expect_equal(
        decision.get("boundary_artifact_digest"),
        expected_identity.country_authority_artifact_digest,
        "decision boundary artifact digest",
    )
    _required_text(decision.get("boundary_version"), "decision boundary version")
    candidates = decision.get("candidate_countries")
    if not isinstance(candidates, list) or any(
        candidate not in set(_COUNTRY_NAMES.values()) for candidate in candidates
    ):
        raise ValueError("SEAD country decision candidate vocabulary is invalid")
    if status == "assigned":
        if code not in _TARGET_COUNTRY_CODES:
            raise ValueError(
                "Assigned SEAD country decision requires a governed country"
            )
        expected_country = _COUNTRY_NAMES[code]
        expected = {
            "method": "strict_boundary_containment",
            "derived_country": expected_country,
            "ambiguity_reason": None,
            "refusal_reason": None,
            "candidate_countries": [expected_country],
        }
    elif status == "review":
        if code != "UNASSIGNED":
            raise ValueError("Review SEAD country decision must be UNASSIGNED")
        expected = {
            "method": "boundary_proximity",
            "derived_country": None,
            "refusal_reason": None,
        }
        if decision.get("ambiguity_reason") not in {
            "near_boundary_without_containment",
            "near_multiple_boundaries",
        }:
            raise ValueError("SEAD review decision has invalid ambiguity reason")
    elif status == "unassigned":
        if code != "UNASSIGNED":
            raise ValueError("Unassigned SEAD country decision has governed country")
        expected = {
            "method": "no_boundary_containment",
            "derived_country": None,
            "ambiguity_reason": None,
            "refusal_reason": "outside_governed_boundaries",
            "candidate_countries": [],
        }
    else:
        raise ValueError(f"Invalid SEAD country decision status: {status}")
    _expect_equal(method, expected.pop("method"), "country decision method")
    for field, value in expected.items():
        _expect_equal(decision.get(field), value, f"country decision {field}")


def _row_identity(row: Mapping[str, object], index: int, primary_key: str) -> str:
    value = row.get(primary_key)
    return f"{primary_key}:{value}" if value is not None else f"row:{index}"


def _validated_source_directory(path: Path) -> Path:
    root = Path(path)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("SEAD acquisition source must be a safe absolute path")
    if root.is_symlink():
        raise ValueError(f"SEAD acquisition source cannot be a symlink: {root}")
    if not root.is_dir():
        raise ValueError(f"SEAD acquisition source is not a directory: {root}")
    _reject_symlink_ancestors(root)
    return root


def _validated_source_file(path: Path) -> Path:
    source = Path(path)
    if not source.is_absolute() or source == Path(source.anchor):
        raise ValueError("SEAD country decisions must use a safe absolute path")
    _reject_symlink_ancestors(source)
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"SEAD country decisions are not a regular file: {source}")
    return source


def _validated_output_parent(path: Path) -> Path:
    parent = Path(path)
    if (
        not parent.is_absolute()
        or parent == Path(parent.anchor)
        or ".." in parent.parts
    ):
        raise ValueError("SEAD admission output must be a safe absolute path")
    _reject_symlink_ancestors(parent)
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        raise ValueError(f"SEAD admission parent is unsafe: {parent}")
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink():
        raise ValueError("SEAD admission parent cannot be a symlink")
    return parent


def _reject_output_overlap(
    output_root: Path, *, source_root: Path, decisions_path: Path
) -> None:
    output = Path(output_root)
    if not output.is_absolute():
        raise ValueError("SEAD admission output must be a safe absolute path")
    resolved_output = output.resolve(strict=False)
    resolved_source = source_root.resolve(strict=True)
    resolved_decisions = decisions_path.resolve(strict=True)
    if resolved_output.is_relative_to(
        resolved_source
    ) or resolved_source.is_relative_to(resolved_output):
        raise ValueError("SEAD admission output overlaps acquisition source")
    if resolved_decisions.is_relative_to(
        resolved_output
    ) or resolved_output.is_relative_to(resolved_decisions):
        raise ValueError("SEAD admission output overlaps country decisions")


def _reject_symlink_ancestors(path: Path) -> None:
    for ancestor in (path, *path.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError(f"SEAD acquisition path traverses a symlink: {ancestor}")


def _directory_bytes(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise FileExistsError(f"Symlink in SEAD admission output: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def _read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Required SEAD acquisition file is not regular: {path}")
    return path.read_bytes()


def _json_object(content: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid SEAD JSON object: {label}") from exc
    if not isinstance(value, dict):
        raise TypeError(f"SEAD JSON value must be an object: {label}")
    return value


def _safe_relative_path(value: object) -> str:
    text = _required_text(value, "manifest file path")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or text != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"Unsafe SEAD manifest file path: {text}")
    return text


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a string list")
    return list(value)


def _positive_int_list(value: object, label: str) -> list[int]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a positive integer list")
    return [_positive_int(item, label) for item in value]


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"SEAD {label} must be an object")
    return value


def _bbox(value: object, label: str) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"SEAD {label} must have four coordinates")
    coordinates = tuple(
        _coordinate(
            item, label, -180 if index % 2 == 0 else -90, 180 if index % 2 == 0 else 90
        )
        for index, item in enumerate(value)
    )
    minimum_longitude, minimum_latitude, maximum_longitude, maximum_latitude = (
        coordinates
    )
    if minimum_longitude >= maximum_longitude or minimum_latitude >= maximum_latitude:
        raise ValueError(f"SEAD {label} is reversed or empty")
    return (
        minimum_longitude,
        minimum_latitude,
        maximum_longitude,
        maximum_latitude,
    )


def _coordinate(value: object, label: str, minimum: float, maximum: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or not minimum <= float(value) <= maximum
    ):
        raise ValueError(f"SEAD {label} is not a valid coordinate")
    return float(value)


def _country_counts(value: object, label: str) -> dict[str, int]:
    if not isinstance(value, Mapping) or set(value) != set(NORDIC_COUNTRY_CODES):
        raise ValueError(f"{label} must partition SE, DK, NO, FI, and UNASSIGNED")
    return {
        code: _non_negative_int(value.get(code), f"{label} {code}")
        for code in NORDIC_COUNTRY_CODES
    }


def _common_text(rows: Iterable[Mapping[str, object]], field: str) -> str:
    values = {_required_text(row.get(field), f"receipt {field}") for row in rows}
    if len(values) != 1:
        raise ValueError(f"SEAD receipts disagree on {field}")
    return next(iter(values))


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be non-empty canonical text")
    return value


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _non_negative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"Invalid SHA-256 for {label}")
    return value


def _sha256_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_ID.fullmatch(value):
        raise ValueError(f"Invalid SHA-256 identity for {label}")
    return value


def _expect_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"SEAD {label} mismatch: {actual!r} != {expected!r}")


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _observed_schema(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    fields = sorted({field for row in rows for field in row})
    return {
        "row_count": len(rows),
        "fields": [
            {
                "name": field,
                "presence_count": sum(field in row for row in rows),
                "null_count": sum(
                    row.get(field) is None for row in rows if field in row
                ),
                "json_types": sorted(
                    {_json_type(row[field]) for row in rows if field in row}
                ),
            }
            for field in fields
        ],
    }


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _file_set_digest(records: Sequence[Mapping[str, object]]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(list(records))).hexdigest()
