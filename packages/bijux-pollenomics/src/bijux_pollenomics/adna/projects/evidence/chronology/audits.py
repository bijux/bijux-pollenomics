from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar, cast

from bijux_pollenomics.adna.domain.models import (
    ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
    ADNA_CHRONOLOGY_PRECISION_POSTURES,
)
from bijux_pollenomics.adna.sources.ena import build_archive_project_catalog

from .constants import (
    ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
    ADNA_CHRONOLOGY_STRENGTHS,
)
from .models import AdnaProjectSampleChronologyRow
from .rows import build_project_sample_chronology_rows
from .semantics import (
    _normalization_rule_for,
    _temporal_semantics_for_chronology_row,
    _uncertainty_note_for,
)

_RowT = TypeVar("_RowT")


def build_project_sample_chronology_review_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        chronology_rows = build_project_sample_chronology_rows(
            output_root, project.project_accession
        )
        strength_counts = _counts_by_key(
            chronology_rows,
            ADNA_CHRONOLOGY_STRENGTHS,
            lambda row: row.chronology_strength,
        )
        evidence_counts = _counts_by_key(
            chronology_rows,
            ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
            lambda row: row.chronology_evidence_class,
        )
        precision_counts = _counts_by_key(
            chronology_rows,
            ADNA_CHRONOLOGY_PRECISION_POSTURES,
            lambda row: row.chronology_precision_posture,
        )
        normalization_counts = _counts_by_key(
            chronology_rows,
            ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
            lambda row: row.chronology_normalization_status,
        )
        conflict_count = sum(
            1 for row in chronology_rows if row.chronology_conflict_note.strip()
        )
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "recovered_sample_row_count": len(chronology_rows),
                "sample_owned_interval_count": strength_counts["sample_owned_interval"],
                "sample_owned_text_only_count": strength_counts[
                    "sample_owned_text_only"
                ],
                "project_context_interval_count": strength_counts[
                    "project_context_interval"
                ],
                "project_context_text_only_count": strength_counts[
                    "project_context_text_only"
                ],
                "unresolved_count": strength_counts["unresolved"],
                "direct_radiocarbon_date_count": evidence_counts[
                    "direct_radiocarbon_date"
                ],
                "modeled_sample_date_count": evidence_counts["modeled_sample_date"],
                "archaeological_context_date_count": evidence_counts[
                    "archaeological_context_date"
                ],
                "broad_period_label_count": evidence_counts["broad_period_label"],
                "historical_or_recent_date_count": evidence_counts[
                    "historical_or_recent_date"
                ],
                "evidence_class_unresolved_count": evidence_counts["unresolved"],
                "sample_precise_point_count": precision_counts["sample_precise_point"],
                "sample_precise_interval_count": precision_counts[
                    "sample_precise_interval"
                ],
                "sample_approximate_or_modeled_count": precision_counts[
                    "sample_approximate_or_modeled"
                ],
                "contextual_interval_count": precision_counts["contextual_interval"],
                "broad_period_only_count": precision_counts["broad_period_only"],
                "precision_unresolved_count": precision_counts["unresolved"],
                "normalized_interval_count": normalization_counts[
                    "normalized_interval"
                ],
                "normalized_point_count": normalization_counts["normalized_point"],
                "text_only_unparsed_count": normalization_counts["text_only_unparsed"],
                "normalization_unresolved_count": normalization_counts["unresolved"],
                "conflicting_context_count": conflict_count,
            }
        )
    return tuple(rows)


def build_cross_project_sample_chronology_audit(
    output_root: Path,
) -> dict[str, object]:
    review_rows = build_project_sample_chronology_review_rows(output_root)
    sample_rows = [
        row
        for project in build_archive_project_catalog()
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        )
    ]
    normalization_counts = _counts_by_key(
        sample_rows,
        ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
        lambda row: row.chronology_normalization_status,
    )
    evidence_counts = _counts_by_key(
        sample_rows,
        ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
        lambda row: row.chronology_evidence_class,
    )
    precision_counts = _counts_by_key(
        sample_rows,
        ADNA_CHRONOLOGY_PRECISION_POSTURES,
        lambda row: row.chronology_precision_posture,
    )
    projects_requiring_manual_review = [
        row["project_accession"]
        for row in review_rows
        if row["text_only_unparsed_count"]
        or row["normalization_unresolved_count"]
        or row["conflicting_context_count"]
    ]
    return {
        "schema_version": "animal-sample-chronology-normalization-audit.v1",
        "sample_row_count": len(sample_rows),
        "normalized_interval_count": normalization_counts["normalized_interval"],
        "normalized_point_count": normalization_counts["normalized_point"],
        "text_only_unparsed_count": normalization_counts["text_only_unparsed"],
        "unresolved_count": normalization_counts["unresolved"],
        "evidence_counts": evidence_counts,
        "precision_counts": precision_counts,
        "projects_requiring_manual_review": projects_requiring_manual_review,
        "rows": list(review_rows),
    }


def build_sample_chronology_ambiguity_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            if not _row_requires_attention(row):
                continue
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "chronology_strength": row.chronology_strength,
                    "chronology_evidence_class": row.chronology_evidence_class,
                    "chronology_precision_posture": row.chronology_precision_posture,
                    "chronology_normalization_status": row.chronology_normalization_status,
                    "chronology_text": row.chronology_text,
                    "chronology_conflict_note": row.chronology_conflict_note,
                    "chronology_provenance_path": row.chronology_provenance_path,
                    "chronology_provenance_locator": row.chronology_provenance_locator,
                    "review_note": row.review_note,
                }
            )
    return tuple(rows)


def build_species_chronology_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    grouped: dict[str, list[AdnaProjectSampleChronologyRow]] = {}
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            grouped.setdefault(row.species_latin_name, []).append(row)
    rows: list[dict[str, object]] = []
    for species_name, chronology_rows in sorted(grouped.items()):
        completeness = _chronology_completeness_counts(chronology_rows)
        recovered_count = len(chronology_rows)
        rows.append(
            {
                "species_latin_name": species_name,
                "recovered_sample_row_count": recovered_count,
                "normalized_row_count": completeness["usable_date_evidence_count"],
                "exact_sample_date_count": completeness["exact_sample_date_count"],
                "modeled_or_approximate_sample_date_count": completeness[
                    "modeled_or_approximate_sample_date_count"
                ],
                "contextual_date_count": completeness["contextual_date_count"],
                "broad_label_count": completeness["broad_label_count"],
                "text_only_unparsed_count": completeness["text_only_unparsed_count"],
                "unresolved_count": completeness["missing_date_count"],
                "chronology_completeness_ratio": 0.0
                if recovered_count == 0
                else round(
                    completeness["usable_date_evidence_count"] / recovered_count, 4
                ),
            }
        )
    return tuple(rows)


def build_project_chronology_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        chronology_rows = build_project_sample_chronology_rows(
            output_root, project.project_accession
        )
        completeness = _chronology_completeness_counts(chronology_rows)
        recovered_count = len(chronology_rows)
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "recovered_sample_row_count": recovered_count,
                "normalized_row_count": completeness["usable_date_evidence_count"],
                "exact_sample_date_count": completeness["exact_sample_date_count"],
                "modeled_or_approximate_sample_date_count": completeness[
                    "modeled_or_approximate_sample_date_count"
                ],
                "contextual_date_count": completeness["contextual_date_count"],
                "broad_label_count": completeness["broad_label_count"],
                "text_only_unparsed_count": completeness["text_only_unparsed_count"],
                "unresolved_count": completeness["missing_date_count"],
                "chronology_completeness_ratio": 0.0
                if recovered_count == 0
                else round(
                    completeness["usable_date_evidence_count"] / recovered_count, 4
                ),
            }
        )
    return tuple(rows)


def build_sample_chronology_review_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            rows.append(row.as_dict())
    rows.sort(
        key=lambda row: (
            str(row["species_latin_name"]),
            str(row["project_accession"]),
            str(row["repo_stable_sample_id"]),
        )
    )
    return tuple(rows)


def build_sample_chronology_provenance_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    """Build one per-sample chronology provenance packet across tracked projects."""
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            temporal_semantics = _temporal_semantics_for_chronology_row(row)
            rows.append(
                {
                    "species_latin_name": row.species_latin_name,
                    "species_common_name": row.species_common_name,
                    "project_accession": row.project_accession,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "published_wording": row.chronology_text,
                    "source_wording_excerpt": row.chronology_provenance_text,
                    "provenance_surface": row.chronology_provenance_path,
                    "provenance_kind": row.chronology_provenance_kind,
                    "provenance_locator": row.chronology_provenance_locator,
                    "dating_basis": row.dating_basis,
                    "evidence_class": row.chronology_evidence_class,
                    "precision_posture": row.chronology_precision_posture,
                    "normalization_status": row.chronology_normalization_status,
                    "normalization_rule": _normalization_rule_for(row),
                    "uncertainty_note": _uncertainty_note_for(row),
                    "time_start_bp": row.time_start_bp,
                    "time_end_bp": row.time_end_bp,
                    "time_mean_bp": row.time_mean_bp,
                    "temporal_semantics": temporal_semantics,
                }
            )
    rows.sort(
        key=lambda row: (
            str(row["project_accession"]),
            str(row["repo_stable_sample_id"]),
        )
    )
    return tuple(rows)


def build_sample_chronology_conflict_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            if not row.chronology_conflict_note.strip():
                continue
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "chronology_strength": row.chronology_strength,
                    "chronology_evidence_class": row.chronology_evidence_class,
                    "chronology_precision_posture": row.chronology_precision_posture,
                    "chronology_normalization_status": row.chronology_normalization_status,
                    "chronology_text": row.chronology_text,
                    "time_start_bp": row.time_start_bp,
                    "time_end_bp": row.time_end_bp,
                    "dating_basis": row.dating_basis,
                    "chronology_provenance_path": row.chronology_provenance_path,
                    "chronology_provenance_locator": row.chronology_provenance_locator,
                    "chronology_provenance_text": row.chronology_provenance_text,
                    "chronology_conflict_note": row.chronology_conflict_note,
                }
            )
    return tuple(rows)


def build_sample_chronology_precision_audit(
    output_root: Path,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            if row.chronology_precision_posture == "sample_precise_point":
                precision_bucket = "sample_precise_point"
            elif row.chronology_precision_posture == "sample_precise_interval":
                precision_bucket = "sample_precise_interval"
            elif row.chronology_precision_posture == "sample_approximate_or_modeled":
                precision_bucket = "sample_approximate_or_modeled"
            elif row.chronology_precision_posture == "contextual_interval":
                precision_bucket = "contextual_interval"
            elif row.chronology_precision_posture == "broad_period_only":
                precision_bucket = "broad_period_only"
            else:
                precision_bucket = "unresolved"
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "chronology_text": row.chronology_text,
                    "chronology_strength": row.chronology_strength,
                    "chronology_evidence_class": row.chronology_evidence_class,
                    "chronology_precision_posture": row.chronology_precision_posture,
                    "chronology_normalization_status": row.chronology_normalization_status,
                    "time_start_bp": row.time_start_bp,
                    "time_end_bp": row.time_end_bp,
                    "dating_basis": row.dating_basis,
                    "precision_bucket": precision_bucket,
                    "precision_review_note": row.review_note,
                    "chronology_conflict_note": row.chronology_conflict_note,
                }
            )
    precision_counts = _counts_by_key(
        rows,
        ADNA_CHRONOLOGY_PRECISION_POSTURES,
        lambda row: str(row["chronology_precision_posture"]),
    )
    return {
        "schema_version": "animal-sample-chronology-precision-audit.v1",
        "row_count": len(rows),
        "precision_counts": precision_counts,
        "rows": rows,
    }


def build_date_evidence_gap_queue(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    queue: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        chronology_rows = build_project_sample_chronology_rows(
            output_root, project.project_accession
        )
        completeness = _chronology_completeness_counts(chronology_rows)
        recovered_count = len(chronology_rows)
        sample_owned_count = sum(
            1
            for row in chronology_rows
            if row.chronology_strength
            in {"sample_owned_interval", "sample_owned_text_only"}
        )
        if (
            sample_owned_count == recovered_count
            and completeness["missing_date_count"] == 0
            and completeness["broad_label_count"] == 0
        ):
            continue
        gap_reasons = []
        if sample_owned_count == 0:
            gap_reasons.append("no_sample_owned_chronology_recovered")
        if completeness["missing_date_count"]:
            gap_reasons.append("missing_sample_level_date_evidence")
        if completeness["broad_label_count"]:
            gap_reasons.append("broad_period_labels_still_need_stronger_date_support")
        if (
            completeness["contextual_date_count"]
            and not completeness["exact_sample_date_count"]
        ):
            gap_reasons.append("project_context_dates_still_dominate")
        queue.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "recovered_sample_row_count": recovered_count,
                "sample_owned_date_row_count": sample_owned_count,
                "exact_sample_date_count": completeness["exact_sample_date_count"],
                "modeled_or_approximate_sample_date_count": completeness[
                    "modeled_or_approximate_sample_date_count"
                ],
                "contextual_date_count": completeness["contextual_date_count"],
                "broad_label_count": completeness["broad_label_count"],
                "missing_date_count": completeness["missing_date_count"],
                "gap_reasons": gap_reasons,
            }
        )
    queue.sort(
        key=lambda row: (
            -cast(int, row["missing_date_count"]),
            -cast(int, row["broad_label_count"]),
            str(row["project_accession"]),
        )
    )
    return tuple(queue)


def _row_requires_attention(row: AdnaProjectSampleChronologyRow) -> bool:
    return (
        row.chronology_strength != "sample_owned_interval"
        or row.chronology_precision_posture
        not in {"sample_precise_interval", "sample_precise_point"}
        or bool(row.chronology_conflict_note.strip())
    )


def _chronology_completeness_counts(
    rows: Sequence[AdnaProjectSampleChronologyRow],
) -> dict[str, int]:
    exact_sample_date_count = sum(
        1
        for row in rows
        if row.chronology_precision_posture
        in {"sample_precise_point", "sample_precise_interval"}
    )
    modeled_or_approximate_sample_date_count = sum(
        1
        for row in rows
        if row.chronology_precision_posture == "sample_approximate_or_modeled"
    )
    contextual_date_count = sum(
        1 for row in rows if row.chronology_precision_posture == "contextual_interval"
    )
    broad_label_count = sum(
        1 for row in rows if row.chronology_precision_posture == "broad_period_only"
    )
    text_only_unparsed_count = sum(
        1 for row in rows if row.chronology_normalization_status == "text_only_unparsed"
    )
    missing_date_count = sum(
        1 for row in rows if row.chronology_precision_posture == "unresolved"
    )
    return {
        "exact_sample_date_count": exact_sample_date_count,
        "modeled_or_approximate_sample_date_count": modeled_or_approximate_sample_date_count,
        "contextual_date_count": contextual_date_count,
        "broad_label_count": broad_label_count,
        "text_only_unparsed_count": text_only_unparsed_count,
        "missing_date_count": missing_date_count,
        "usable_date_evidence_count": (
            exact_sample_date_count
            + modeled_or_approximate_sample_date_count
            + contextual_date_count
        ),
    }


def _counts_by_key(
    rows: Sequence[_RowT],
    keys: tuple[str, ...],
    selector: Callable[[_RowT], str],
) -> dict[str, int]:
    counts = dict.fromkeys(keys, 0)
    for row in rows:
        counts[selector(row)] += 1
    return counts
