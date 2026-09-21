"""Narrow host entry point for source-owned LRA refusal accounting."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .models import AdmissionReport
from .neotoma_candidate_groups import (
    NeotomaCandidateGroups,
    summarize_neotoma_candidate_groups,
)
from .neotoma_frontier import NeotomaLraFrontier, assess_neotoma_lra_frontier
from .neotoma_pollen_screen import NeotomaPollenScreen, assess_neotoma_pollen_screen
from .neotoma_series import NeotomaCandidateSeries, build_neotoma_candidate_series
from .reading import read_neotoma_evidence
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


def inspect_neotoma_lra_frontier(
    *,
    raw_root: Path,
    normalized_root: Path,
    selected_sample_ids: Sequence[str] | None = None,
) -> NeotomaLraFrontier:
    """Return authenticated prerequisite accounting without creating a request."""
    evidence = read_neotoma_evidence(raw_root, normalized_root)
    return assess_neotoma_lra_frontier(evidence, selected_sample_ids)


def inspect_neotoma_lra_candidate_series(
    *,
    raw_root: Path,
    normalized_root: Path,
    selected_sample_ids: Sequence[str],
) -> NeotomaCandidateSeries:
    """Return a bounded, refusal-only sample series from authenticated parents."""
    evidence = read_neotoma_evidence(raw_root, normalized_root)
    return build_neotoma_candidate_series(evidence, selected_sample_ids)


def inspect_neotoma_lra_pollen_screen(
    *, raw_root: Path, normalized_root: Path
) -> NeotomaPollenScreen:
    """Screen every authenticated source sample without admitting LRA input."""
    evidence = read_neotoma_evidence(raw_root, normalized_root)
    return assess_neotoma_pollen_screen(evidence)


def inspect_neotoma_lra_candidate_groups(
    *, raw_root: Path, normalized_root: Path
) -> NeotomaCandidateGroups:
    """Count authenticated source IDs behind pollen prerequisite samples."""
    screen = inspect_neotoma_lra_pollen_screen(
        raw_root=raw_root, normalized_root=normalized_root
    )
    return summarize_neotoma_candidate_groups(screen)
