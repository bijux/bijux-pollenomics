"""Species/project completeness denominators and date-evidence gaps."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import AdnaProjectSampleChronologyRow


def _build_species_chronology_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    from . import (
        _chronology_completeness_counts,
        build_archive_project_catalog,
        build_project_sample_chronology_rows,
    )

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
                **_completeness_fields(completeness, recovered_count),
            }
        )
    return tuple(rows)


def _build_project_chronology_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    from . import (
        _chronology_completeness_counts,
        build_archive_project_catalog,
        build_project_sample_chronology_rows,
    )

    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        chronology_rows = build_project_sample_chronology_rows(
            output_root, project.project_accession
        )
        completeness = _chronology_completeness_counts(chronology_rows)
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                **_completeness_fields(completeness, len(chronology_rows)),
            }
        )
    return tuple(rows)


def _completeness_fields(
    completeness: dict[str, int], recovered_count: int
) -> dict[str, object]:
    return {
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
        else round(completeness["usable_date_evidence_count"] / recovered_count, 4),
    }


def _build_date_evidence_gap_queue(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    from . import (
        _chronology_completeness_counts,
        build_archive_project_catalog,
        build_project_sample_chronology_rows,
        cast,
    )

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


def _chronology_completeness_counts_impl(
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
