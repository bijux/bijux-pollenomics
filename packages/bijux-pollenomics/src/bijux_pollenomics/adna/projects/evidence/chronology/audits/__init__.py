"""Chronology review, completeness, provenance, and refusal audits."""

from __future__ import annotations

from collections.abc import Callable as Callable
from collections.abc import Sequence as Sequence
from pathlib import Path as Path
from typing import TypeVar as TypeVar
from typing import cast as cast

from bijux_pollenomics.adna.domain.models import (
    ADNA_CHRONOLOGY_EVIDENCE_CLASSES as ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
)
from bijux_pollenomics.adna.domain.models import (
    ADNA_CHRONOLOGY_PRECISION_POSTURES as ADNA_CHRONOLOGY_PRECISION_POSTURES,
)
from bijux_pollenomics.adna.sources.archive import (
    build_archive_project_catalog as build_archive_project_catalog,
)

from ..constants import (
    ADNA_CHRONOLOGY_NORMALIZATION_STATUSES as ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
)
from ..constants import ADNA_CHRONOLOGY_STRENGTHS as ADNA_CHRONOLOGY_STRENGTHS
from ..models import (
    AdnaProjectSampleChronologyRow as AdnaProjectSampleChronologyRow,
)
from ..rows import (
    build_project_sample_chronology_rows as build_project_sample_chronology_rows,
)
from ..semantics import _normalization_rule_for as _normalization_rule_for
from ..semantics import (
    _temporal_semantics_for_chronology_row as _temporal_semantics_for_chronology_row,
)
from ..semantics import _uncertainty_note_for as _uncertainty_note_for
from .completeness import (
    _build_date_evidence_gap_queue,
    _build_project_chronology_completeness_rows,
    _build_species_chronology_completeness_rows,
    _chronology_completeness_counts_impl,
)
from .counting import _counts_by_key_impl
from .precision import _build_sample_chronology_precision_audit
from .provenance import _build_sample_chronology_provenance_rows
from .review import (
    _build_sample_chronology_ambiguity_ledger,
    _build_sample_chronology_conflict_ledger,
    _build_sample_chronology_review_rows,
    _row_requires_attention_impl,
)
from .summary import (
    _build_cross_project_sample_chronology_audit,
    _build_project_sample_chronology_review_rows,
)

_RowT = TypeVar("_RowT")


def build_project_sample_chronology_review_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    return _build_project_sample_chronology_review_rows(output_root)


def build_cross_project_sample_chronology_audit(
    output_root: Path,
) -> dict[str, object]:
    return _build_cross_project_sample_chronology_audit(output_root)


def build_sample_chronology_ambiguity_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    return _build_sample_chronology_ambiguity_ledger(output_root)


def build_species_chronology_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    return _build_species_chronology_completeness_rows(output_root)


def build_project_chronology_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    return _build_project_chronology_completeness_rows(output_root)


def build_sample_chronology_review_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    return _build_sample_chronology_review_rows(output_root)


def build_sample_chronology_provenance_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    """Build one per-sample chronology provenance packet across tracked projects."""
    return _build_sample_chronology_provenance_rows(output_root)


def build_sample_chronology_conflict_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    return _build_sample_chronology_conflict_ledger(output_root)


def build_sample_chronology_precision_audit(output_root: Path) -> dict[str, object]:
    return _build_sample_chronology_precision_audit(output_root)


def build_date_evidence_gap_queue(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    return _build_date_evidence_gap_queue(output_root)


def _row_requires_attention(row: AdnaProjectSampleChronologyRow) -> bool:
    return _row_requires_attention_impl(row)


def _chronology_completeness_counts(
    rows: Sequence[AdnaProjectSampleChronologyRow],
) -> dict[str, int]:
    return _chronology_completeness_counts_impl(rows)


def _counts_by_key(
    rows: Sequence[_RowT],
    keys: tuple[str, ...],
    selector: Callable[[_RowT], str],
) -> dict[str, int]:
    return _counts_by_key_impl(rows, keys, selector)
