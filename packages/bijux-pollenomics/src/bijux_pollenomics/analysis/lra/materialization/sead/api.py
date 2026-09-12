"""Narrow public entry point for the SEAD source-admission audit."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
)

from ..models import AdmissionReport
from .workflow import run_audit


def audit_sead_lra_source(
    *,
    raw_root: Path,
    normalized_root: Path,
    expected_identity: SeadAdmissionExpectedIdentity,
    output_directory: Path,
) -> AdmissionReport:
    """Audit all native rows; reported samples are entity-linked physical samples, never approved LRA inputs."""
    return run_audit(
        raw_root=raw_root,
        normalized_root=normalized_root,
        expected_identity=expected_identity,
        output_directory=output_directory,
    )
