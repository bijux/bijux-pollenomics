"""Admission validation, materialization, and snapshot orchestration."""

from __future__ import annotations

import hashlib
import os
import shutil
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from types import MappingProxyType

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    ACQUISITION_MANIFEST_SCHEMA_VERSION,
)

from .codec import (
    _canonical_bytes,
    _common_text,
    _directory_bytes,
    _expect_equal,
    _file_set_digest,
    _json_object,
    _read_regular_file,
    _reject_output_overlap,
    _required_text,
    _string_list,
    _validated_output_parent,
    _validated_source_directory,
    _validated_source_file,
)
from .models import (
    _FULL_EVIDENCE_PROFILE,
    _SCOPED_PROFILE,
    ADMISSION_SCHEMA_VERSION,
    SeadAcquisitionAdmission,
    SeadAdmissionExpectedIdentity,
    SeadMaterializedAdmissionSnapshot,
    _AdmissionProfile,
    _ValidatedAdmission,
)
from .validation.authority import _load_validated_boundary_authority
from .validation.countries import _validate_country_accounting, _validate_site_rows
from .validation.identity import (
    _validate_embedded_identities,
    _validate_expected_identity,
)
from .validation.joins import _validate_joins
from .validation.manifests import _validate_manifest_files, _validate_table_payload
from .validation.parents import (
    _downstream_statuses,
    _release_reason_codes,
    _validate_parent_admission,
)
from .validation.receipts import _validate_scoped_receipts


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
