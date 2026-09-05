"""Validate the raw SEAD acquisition bound to the governed evidence release."""

from __future__ import annotations

import hashlib
from pathlib import Path

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_BBOX_PAYLOAD_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST,
    SEAD_GOVERNED_COUNTRY_AUTHORITY_ID,
    SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_EVIDENCE_SCOPE_ID,
    SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
    SEAD_GOVERNED_PARENT_RUN_ID,
)

from .admission import (
    SeadAdmissionExpectedIdentity,
    SeadMaterializedAdmissionSnapshot,
    read_materialized_sead_full_evidence_admission,
)


def validate_governed_sead_admission(
    acquisition_root: Path,
    *,
    data_root: Path,
) -> SeadMaterializedAdmissionSnapshot:
    """Validate every raw file against the exact governed admission authority."""
    root = Path(acquisition_root)
    admission_path = root / "admission.json"
    if admission_path.is_symlink() or not admission_path.is_file():
        raise ValueError("governed SEAD admission file is missing or unsafe")
    admission_bytes = admission_path.read_bytes()
    if hashlib.sha256(admission_bytes).hexdigest() != SEAD_GOVERNED_ADMISSION_SHA256:
        raise ValueError("governed SEAD admission identity changed")
    return read_materialized_sead_full_evidence_admission(
        root,
        expected_identity=SeadAdmissionExpectedIdentity(
            scope_id=SEAD_GOVERNED_EVIDENCE_SCOPE_ID,
            run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
            parent_run_id=SEAD_GOVERNED_PARENT_RUN_ID,
            build_id=SEAD_GOVERNED_BUILD_ID,
            country_authority_id=SEAD_GOVERNED_COUNTRY_AUTHORITY_ID,
            country_authority_artifact_digest=SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST,
            country_authority_root=(Path(data_root) / "boundaries").resolve(),
            bbox_payload_sha256=SEAD_GOVERNED_BBOX_PAYLOAD_SHA256,
            acquisition_manifest_sha256=SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
            country_decisions_sha256=SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256,
            parent_admission_sha256=SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
        ),
    )
