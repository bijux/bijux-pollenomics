"""Narrow host entry point for source-owned LRA refusal accounting."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .models import AdmissionReport
from .workflow import run_materialization


def audit_neotoma_lra_source(
    *,
    raw_root: Path,
    normalized_root: Path,
    output_directory: Path,
    selected_sample_ids: Sequence[str] | None = None,
) -> AdmissionReport:
    """Audit the full source ledger; no executable LRA request or approval is produced."""
    return run_materialization(
        raw_root=raw_root,
        normalized_root=normalized_root,
        output_directory=output_directory,
        selected_sample_ids=selected_sample_ids,
    )
