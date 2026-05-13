from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from ...core.files import write_json, write_text
from ...core.temporal_semantics import build_temporal_semantics
from ..catalogs import render_csv_rows
from ..models import (
    ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
    ADNA_CHRONOLOGY_PRECISION_POSTURES,
)
from ..sources.ena import build_archive_project_catalog
from .sample_master import build_project_sample_master_rows
from .site_evidence import resolve_project_site_evidence

__all__ = [
    "ADNA_CHRONOLOGY_EVIDENCE_CLASSES",
    "ADNA_CHRONOLOGY_NORMALIZATION_STATUSES",
    "ADNA_CHRONOLOGY_PRECISION_POSTURES",
    "ADNA_CHRONOLOGY_STRENGTHS",
    "AdnaProjectSampleChronologyRow",
    "build_cross_project_sample_chronology_audit",
    "build_date_evidence_gap_queue",
    "build_project_chronology_completeness_rows",
    "build_project_sample_chronology_review_rows",
    "build_project_sample_chronology_rows",
    "build_sample_chronology_ambiguity_ledger",
    "build_sample_chronology_conflict_ledger",
    "build_sample_chronology_provenance_rows",
    "build_sample_chronology_precision_audit",
    "build_sample_chronology_review_rows",
    "build_species_chronology_completeness_rows",
    "materialize_project_sample_chronology_library",
]

ADNA_CHRONOLOGY_STRENGTHS = (
    "sample_owned_interval",
    "sample_owned_text_only",
    "project_context_interval",
    "project_context_text_only",
    "unresolved",
)
ADNA_CHRONOLOGY_NORMALIZATION_STATUSES = (
    "normalized_interval",
    "normalized_point",
    "text_only_unparsed",
    "unresolved",
)
_BROAD_PERIOD_TEXT_RE = re.compile(
    r"\b("
    r"bronze|iron|neolithic|mesolithic|palaeolithic|paleolithic|chalcolithic|eneolithic|"
    r"roman|medieval|viking|migration|hellenistic|dynasty|period|epoch|century|millennium|"
    r"late antiquity|prehistoric|historic|holocene"
    r")\b",
    re.IGNORECASE,
)
_MODELED_DATE_RE = re.compile(
    r"\b(modeled|modelled|bayesian|posterior|oxcal|phase|sigma|2σ|1σ|calibrated|cal\.)\b",
    re.IGNORECASE,
)
_APPROXIMATE_DATE_RE = re.compile(
    r"\b(ca\.?|circa|around|approx(?:\.|imately)?|c\.)\b",
    re.IGNORECASE,
)
_HISTORICAL_DATE_RE = re.compile(
    r"\b(modern|present|recent|historic|historical|ce|ad)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AdnaProjectSampleChronologyRow:
    species_latin_name: str
    species_common_name: str
    project_accession: str
    repo_stable_sample_id: str
    preferred_sample_label: str
    sample_basis: str
    sample_evidence_status: str
    sample_identity_resolution: str
    sample_ambiguity_note: str
    chronology_text: str
    chronology_strength: str
    chronology_evidence_class: str
    chronology_precision_posture: str
    chronology_provenance_path: str
    chronology_provenance_kind: str
    chronology_provenance_locator: str
    chronology_provenance_text: str
    chronology_normalization_status: str
    time_start_bp: int | None
    time_end_bp: int | None
    time_mean_bp: int | None
    dating_basis: str
    chronology_conflict_note: str
    review_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accession": self.project_accession,
            "repo_stable_sample_id": self.repo_stable_sample_id,
            "preferred_sample_label": self.preferred_sample_label,
            "sample_basis": self.sample_basis,
            "sample_evidence_status": self.sample_evidence_status,
            "sample_identity_resolution": self.sample_identity_resolution,
            "sample_ambiguity_note": self.sample_ambiguity_note,
            "chronology_text": self.chronology_text,
            "chronology_strength": self.chronology_strength,
            "chronology_evidence_class": self.chronology_evidence_class,
            "chronology_precision_posture": self.chronology_precision_posture,
            "chronology_provenance_path": self.chronology_provenance_path,
            "chronology_provenance_kind": self.chronology_provenance_kind,
            "chronology_provenance_locator": self.chronology_provenance_locator,
            "chronology_provenance_text": self.chronology_provenance_text,
            "chronology_normalization_status": self.chronology_normalization_status,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "time_mean_bp": self.time_mean_bp,
            "dating_basis": self.dating_basis,
            "chronology_conflict_note": self.chronology_conflict_note,
            "review_note": self.review_note,
        }


def build_project_sample_chronology_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[AdnaProjectSampleChronologyRow, ...]:
    output_root = Path(output_root)
    project = _project_by_accession(project_accession)
    master_rows = build_project_sample_master_rows(output_root, project_accession)
    site_rows = resolve_project_site_evidence(project_accession)
    site_row = site_rows[0] if site_rows else None
    rows: list[AdnaProjectSampleChronologyRow] = []

    for master_row in master_rows:
        source = _resolve_chronology_source(
            master_row=master_row,
            site_row=site_row,
            dating_basis=project.dating_basis or "unknown",
        )
        rows.append(
            AdnaProjectSampleChronologyRow(
                species_latin_name=master_row.species_latin_name,
                species_common_name=master_row.species_common_name,
                project_accession=master_row.project_accession,
                repo_stable_sample_id=master_row.repo_stable_sample_id,
                preferred_sample_label=master_row.preferred_sample_label,
                sample_basis=master_row.sample_basis,
                sample_evidence_status=master_row.sample_evidence_status,
                sample_identity_resolution=master_row.sample_identity_resolution,
                sample_ambiguity_note=master_row.sample_ambiguity_note,
                chronology_text=source.chronology_text,
                chronology_strength=source.chronology_strength,
                chronology_evidence_class=source.chronology_evidence_class,
                chronology_precision_posture=source.chronology_precision_posture,
                chronology_provenance_path=source.chronology_provenance_path,
                chronology_provenance_kind=source.chronology_provenance_kind,
                chronology_provenance_locator=source.chronology_provenance_locator,
                chronology_provenance_text=source.chronology_provenance_text,
                chronology_normalization_status=source.chronology_normalization_status,
                time_start_bp=source.time_start_bp,
                time_end_bp=source.time_end_bp,
                time_mean_bp=source.time_mean_bp,
                dating_basis=project.dating_basis or "unknown",
                chronology_conflict_note=source.chronology_conflict_note,
                review_note=source.review_note,
            )
        )

    rows.sort(key=lambda row: (row.project_accession, row.repo_stable_sample_id))
    return tuple(rows)


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
            -int(row["missing_date_count"]),
            -int(row["broad_label_count"]),
            str(row["project_accession"]),
        )
    )
    return tuple(queue)


def materialize_project_sample_chronology_library(output_root: Path) -> None:
    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    project_review_rows = list(build_project_sample_chronology_review_rows(output_root))
    audit_payload = build_cross_project_sample_chronology_audit(output_root)
    ambiguity_rows = list(build_sample_chronology_ambiguity_ledger(output_root))
    conflict_rows = list(build_sample_chronology_conflict_ledger(output_root))
    precision_audit_payload = build_sample_chronology_precision_audit(output_root)
    gap_queue_rows = list(build_date_evidence_gap_queue(output_root))
    species_rows = list(build_species_chronology_completeness_rows(output_root))
    project_rows = list(build_project_chronology_completeness_rows(output_root))
    sample_review_rows = list(build_sample_chronology_review_rows(output_root))
    provenance_rows = list(build_sample_chronology_provenance_rows(output_root))

    for project in build_archive_project_catalog():
        project_root = source_root / "projects" / project.project_accession
        project_root.mkdir(parents=True, exist_ok=True)
        chronology_rows = [
            row.as_dict()
            for row in build_project_sample_chronology_rows(
                output_root, project.project_accession
            )
        ]
        evidence_payload = {
            "schema_version": "animal-project-sample-chronology-evidence.v1",
            "project_accession": project.project_accession,
            "species_latin_name": project.species_latin_name,
            "row_count": len(chronology_rows),
            "rows": chronology_rows,
        }
        write_json(
            project_root / "sample_chronology.json",
            {
                "schema_version": "animal-project-sample-chronology.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(chronology_rows),
                "rows": chronology_rows,
            },
        )
        write_text(
            project_root / "sample_chronology.csv",
            render_csv_rows(
                tuple(chronology_rows)
                if chronology_rows
                else (_empty_sample_chronology_row(project),)
            ),
        )
        write_json(project_root / "sample_chronology_evidence.json", evidence_payload)
        write_text(
            project_root / "sample_chronology_evidence.csv",
            render_csv_rows(
                tuple(chronology_rows)
                if chronology_rows
                else (_empty_sample_chronology_row(project),)
            ),
        )
        project_provenance_rows = tuple(
            row
            for row in provenance_rows
            if row["project_accession"] == project.project_accession
        )
        write_json(
            project_root / "sample_chronology_provenance.json",
            {
                "schema_version": "animal-project-sample-chronology-provenance.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(project_provenance_rows),
                "rows": list(project_provenance_rows),
            },
        )
        write_text(
            project_root / "sample_chronology_provenance.csv",
            render_csv_rows(
                project_provenance_rows
                if project_provenance_rows
                else (_empty_sample_chronology_provenance_row(project),)
            ),
        )

    write_json(
        source_root / "project_sample_chronology_review.json",
        {
            "schema_version": "animal-project-sample-chronology-review.v1",
            "rows": project_review_rows,
        },
    )
    write_text(
        source_root / "project_sample_chronology_review.csv",
        render_csv_rows(tuple(project_review_rows)),
    )
    write_json(
        source_root / "sample_chronology_normalization_audit.json", audit_payload
    )
    write_text(
        source_root / "sample_chronology_normalization_audit.md",
        _render_sample_chronology_audit_markdown(audit_payload),
    )
    write_json(
        source_root / "sample_chronology_ambiguity_ledger.json",
        {
            "schema_version": "animal-sample-chronology-ambiguity-ledger.v1",
            "rows": ambiguity_rows,
        },
    )
    write_text(
        source_root / "sample_chronology_ambiguity_ledger.md",
        _render_sample_chronology_ambiguity_markdown(ambiguity_rows),
    )
    write_json(
        source_root / "sample_chronology_conflict_ledger.json",
        {
            "schema_version": "animal-sample-chronology-conflict-ledger.v1",
            "rows": conflict_rows,
        },
    )
    write_text(
        source_root / "sample_chronology_conflict_ledger.md",
        _render_sample_chronology_conflict_markdown(conflict_rows),
    )
    write_json(
        source_root / "sample_chronology_precision_audit.json", precision_audit_payload
    )
    write_text(
        source_root / "sample_chronology_precision_audit.md",
        _render_sample_chronology_precision_audit_markdown(precision_audit_payload),
    )
    write_json(
        source_root / "species_chronology_completeness.json",
        {
            "schema_version": "animal-species-chronology-completeness.v1",
            "rows": species_rows,
        },
    )
    write_text(
        source_root / "species_chronology_completeness.csv",
        render_csv_rows(tuple(species_rows)),
    )
    write_json(
        source_root / "project_chronology_completeness.json",
        {
            "schema_version": "animal-project-chronology-completeness.v1",
            "rows": project_rows,
        },
    )
    write_text(
        source_root / "project_chronology_completeness.csv",
        render_csv_rows(tuple(project_rows)),
    )
    write_json(
        source_root / "sample_chronology_review.json",
        {
            "schema_version": "animal-sample-chronology-review.v1",
            "rows": sample_review_rows,
        },
    )
    write_text(
        source_root / "sample_chronology_review.md",
        _render_sample_chronology_review_markdown(sample_review_rows),
    )
    write_json(
        source_root / "sample_chronology_provenance_review.json",
        {
            "schema_version": "animal-sample-chronology-provenance-review.v1",
            "rows": provenance_rows,
        },
    )
    write_text(
        source_root / "sample_chronology_provenance_review.md",
        _render_sample_chronology_provenance_markdown(provenance_rows),
    )
    write_json(
        source_root / "date_evidence_gap_queue.json",
        {
            "schema_version": "animal-date-evidence-gap-queue.v1",
            "rows": gap_queue_rows,
        },
    )
    write_text(
        source_root / "date_evidence_gap_queue.md",
        _render_date_evidence_gap_queue_markdown(gap_queue_rows),
    )


@dataclass(frozen=True)
class _ResolvedChronologySource:
    chronology_text: str
    chronology_strength: str
    chronology_evidence_class: str
    chronology_precision_posture: str
    chronology_provenance_path: str
    chronology_provenance_kind: str
    chronology_provenance_locator: str
    chronology_provenance_text: str
    chronology_normalization_status: str
    time_start_bp: int | None
    time_end_bp: int | None
    time_mean_bp: int | None
    chronology_conflict_note: str
    review_note: str


def _resolve_chronology_source(
    *,
    master_row: object,
    site_row: object | None,
    dating_basis: str,
) -> _ResolvedChronologySource:
    from ..normalization import normalize_chronology_text

    sample_text = str(getattr(master_row, "chronology_text", "")).strip()
    site_text = (
        ""
        if site_row is None
        else str(getattr(site_row, "chronology_text", "")).strip()
    )
    if sample_text:
        chronology = normalize_chronology_text(sample_text, dating_basis=dating_basis)
        conflict_note = _build_conflict_note(
            preferred_text=sample_text,
            preferred_chronology=chronology,
            comparison_text=site_text,
            comparison_chronology=_site_chronology(site_row, dating_basis=dating_basis),
        )
        normalization_status = _normalization_status_for(chronology)
        chronology_strength = (
            "sample_owned_interval"
            if normalization_status in {"normalized_interval", "normalized_point"}
            else "sample_owned_text_only"
        )
        evidence_class = _evidence_class_for(
            chronology_text=sample_text,
            chronology=chronology,
            chronology_strength=chronology_strength,
            dating_basis=dating_basis,
        )
        precision_posture = _precision_posture_for(
            chronology_text=sample_text,
            chronology=chronology,
            chronology_strength=chronology_strength,
            chronology_evidence_class=evidence_class,
            chronology_normalization_status=normalization_status,
        )
        return _ResolvedChronologySource(
            chronology_text=sample_text,
            chronology_strength=chronology_strength,
            chronology_evidence_class=evidence_class,
            chronology_precision_posture=precision_posture,
            chronology_provenance_path=str(
                getattr(master_row, "sample_lineage_path", "")
            ),
            chronology_provenance_kind=_artifact_kind_from_path(
                str(getattr(master_row, "sample_lineage_path", ""))
            ),
            chronology_provenance_locator=str(
                getattr(master_row, "sample_lineage_locator", "")
            ),
            chronology_provenance_text=str(
                getattr(master_row, "sample_lineage_excerpt", "")
            ),
            chronology_normalization_status=normalization_status,
            time_start_bp=chronology.time_start_bp,
            time_end_bp=chronology.time_end_bp,
            time_mean_bp=chronology.time_mean_bp,
            chronology_conflict_note=conflict_note,
            review_note=(
                "Chronology comes from the recovered sample-owned source row."
                if not conflict_note
                else "Chronology keeps the sample-owned claim because it conflicts with the project-level context row."
            ),
        )
    if site_text:
        chronology = _site_chronology(site_row, dating_basis=dating_basis)
        normalization_status = _normalization_status_for(chronology)
        chronology_strength = (
            "project_context_interval"
            if normalization_status in {"normalized_interval", "normalized_point"}
            else "project_context_text_only"
        )
        evidence_class = _evidence_class_for(
            chronology_text=site_text,
            chronology=chronology,
            chronology_strength=chronology_strength,
            dating_basis=dating_basis,
        )
        precision_posture = _precision_posture_for(
            chronology_text=site_text,
            chronology=chronology,
            chronology_strength=chronology_strength,
            chronology_evidence_class=evidence_class,
            chronology_normalization_status=normalization_status,
        )
        return _ResolvedChronologySource(
            chronology_text=site_text,
            chronology_strength=chronology_strength,
            chronology_evidence_class=evidence_class,
            chronology_precision_posture=precision_posture,
            chronology_provenance_path=str(
                getattr(site_row, "source_artifact_path", "")
            ),
            chronology_provenance_kind=str(
                getattr(site_row, "source_artifact_kind", "")
            ),
            chronology_provenance_locator=str(getattr(site_row, "source_locator", "")),
            chronology_provenance_text=str(getattr(site_row, "exact_source_text", "")),
            chronology_normalization_status=normalization_status,
            time_start_bp=chronology.time_start_bp,
            time_end_bp=chronology.time_end_bp,
            time_mean_bp=chronology.time_mean_bp,
            chronology_conflict_note="",
            review_note="Chronology falls back to the current project-level context row.",
        )
    return _ResolvedChronologySource(
        chronology_text="",
        chronology_strength="unresolved",
        chronology_evidence_class="unresolved",
        chronology_precision_posture="unresolved",
        chronology_provenance_path="",
        chronology_provenance_kind="",
        chronology_provenance_locator="",
        chronology_provenance_text="",
        chronology_normalization_status="unresolved",
        time_start_bp=None,
        time_end_bp=None,
        time_mean_bp=None,
        chronology_conflict_note="",
        review_note="No chronology claim has been recovered yet for this sample row.",
    )


def _site_chronology(site_row: object | None, *, dating_basis: str) -> object:
    from ..normalization import (
        normalize_chronology_text,
        normalize_explicit_bp_window,
    )

    if site_row is None:
        return normalize_chronology_text("", dating_basis=dating_basis)
    start_bp = getattr(site_row, "time_start_bp", None)
    end_bp = getattr(site_row, "time_end_bp", None)
    chronology_text = str(getattr(site_row, "chronology_text", "")).strip()
    if start_bp is not None and end_bp is not None:
        return normalize_explicit_bp_window(
            start_bp,
            end_bp,
            original_text=chronology_text,
            dating_basis=dating_basis,
        )
    return normalize_chronology_text(chronology_text, dating_basis=dating_basis)


def _build_conflict_note(
    *,
    preferred_text: str,
    preferred_chronology: object,
    comparison_text: str,
    comparison_chronology: object,
) -> str:
    comparison_text = comparison_text.strip()
    if not comparison_text or preferred_text.strip() == comparison_text:
        return ""
    preferred_interval = (
        getattr(preferred_chronology, "time_start_bp", None),
        getattr(preferred_chronology, "time_end_bp", None),
    )
    comparison_interval = (
        getattr(comparison_chronology, "time_start_bp", None),
        getattr(comparison_chronology, "time_end_bp", None),
    )
    if all(item is not None for item in preferred_interval + comparison_interval):
        if preferred_interval == comparison_interval:
            return ""
        return "Sample-owned chronology disagrees with the project-level chronology interval."
    return "Sample-owned chronology text disagrees with the project-level chronology wording."


def _normalization_status_for(chronology: object) -> str:
    start_bp = getattr(chronology, "time_start_bp", None)
    end_bp = getattr(chronology, "time_end_bp", None)
    original_text = str(getattr(chronology, "original_text", "")).strip()
    if start_bp is None or end_bp is None:
        return "unresolved" if not original_text else "text_only_unparsed"
    if start_bp == end_bp:
        return "normalized_point"
    return "normalized_interval"


def _evidence_class_for(
    *,
    chronology_text: str,
    chronology: object,
    chronology_strength: str,
    dating_basis: str,
) -> str:
    text = chronology_text.strip()
    if not text and getattr(chronology, "time_start_bp", None) is None:
        return "unresolved"
    lowered_basis = dating_basis.casefold()
    if _MODELED_DATE_RE.search(text):
        return "modeled_sample_date"
    if _HISTORICAL_DATE_RE.search(text) or lowered_basis in {
        "historical_attribution",
        "historical_and_archaeological_context",
        "modern_sampling",
    }:
        return "historical_or_recent_date"
    if (
        _BROAD_PERIOD_TEXT_RE.search(text)
        and getattr(chronology, "time_start_bp", None) is None
    ):
        return "broad_period_label"
    if chronology_strength.startswith("project_context"):
        return "archaeological_context_date"
    if "radiocarbon" in lowered_basis or "bp" in text.casefold():
        return "direct_radiocarbon_date"
    if _BROAD_PERIOD_TEXT_RE.search(text):
        return "broad_period_label"
    if getattr(chronology, "time_start_bp", None) is not None:
        return (
            "modeled_sample_date"
            if _APPROXIMATE_DATE_RE.search(text)
            else "direct_radiocarbon_date"
        )
    return "unresolved"


def _precision_posture_for(
    *,
    chronology_text: str,
    chronology: object,
    chronology_strength: str,
    chronology_evidence_class: str,
    chronology_normalization_status: str,
) -> str:
    text = chronology_text.strip()
    start_bp = getattr(chronology, "time_start_bp", None)
    end_bp = getattr(chronology, "time_end_bp", None)
    if chronology_evidence_class == "unresolved":
        return "unresolved"
    if chronology_evidence_class == "broad_period_label":
        return "broad_period_only"
    if chronology_strength.startswith("project_context"):
        return (
            "contextual_interval"
            if start_bp is not None and end_bp is not None
            else "broad_period_only"
        )
    if (
        chronology_evidence_class == "modeled_sample_date"
        or _APPROXIMATE_DATE_RE.search(text)
    ):
        return "sample_approximate_or_modeled"
    if chronology_normalization_status == "normalized_point":
        return "sample_precise_point"
    if chronology_normalization_status == "normalized_interval":
        return "sample_precise_interval"
    if chronology_normalization_status == "text_only_unparsed" and text:
        return "sample_approximate_or_modeled"
    return "unresolved"


def _row_requires_attention(row: AdnaProjectSampleChronologyRow) -> bool:
    return (
        row.chronology_strength != "sample_owned_interval"
        or row.chronology_precision_posture
        not in {"sample_precise_interval", "sample_precise_point"}
        or bool(row.chronology_conflict_note.strip())
    )


def _chronology_completeness_counts(
    rows: list[AdnaProjectSampleChronologyRow]
    | tuple[AdnaProjectSampleChronologyRow, ...],
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
    rows: list[object] | tuple[object, ...],
    keys: tuple[str, ...],
    selector,
) -> dict[str, int]:
    counts = dict.fromkeys(keys, 0)
    for row in rows:
        counts[selector(row)] += 1
    return counts


def _project_by_accession(project_accession: str) -> object:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project
    raise KeyError(project_accession)


def _artifact_kind_from_path(path: str) -> str:
    if "#Supplementary_Data_" in path:
        return "supplementary_spreadsheet_row"
    if path.endswith(".xlsx"):
        return "supplementary_spreadsheet_row"
    if path.endswith(".pdf"):
        return "supplementary_pdf_text"
    if path.endswith(".html"):
        return "article_or_archive_text"
    return "tracked_source_artifact"


def _empty_sample_chronology_row(project: object) -> dict[str, object]:
    return {
        "species_latin_name": project.species_latin_name,
        "species_common_name": "",
        "project_accession": project.project_accession,
        "repo_stable_sample_id": "",
        "preferred_sample_label": "",
        "sample_basis": "",
        "sample_evidence_status": "not_yet_recoverable",
        "sample_identity_resolution": "provisional",
        "sample_ambiguity_note": "",
        "chronology_text": "",
        "chronology_strength": "unresolved",
        "chronology_evidence_class": "unresolved",
        "chronology_precision_posture": "unresolved",
        "chronology_provenance_path": "",
        "chronology_provenance_kind": "",
        "chronology_provenance_locator": "",
        "chronology_provenance_text": "",
        "chronology_normalization_status": "unresolved",
        "time_start_bp": "",
        "time_end_bp": "",
        "time_mean_bp": "",
        "dating_basis": "",
        "chronology_conflict_note": "",
        "review_note": "No recovered sample rows are published yet for this project.",
    }


def _empty_sample_chronology_provenance_row(project: object) -> dict[str, object]:
    return {
        "species_latin_name": str(getattr(project, "species_latin_name", "")),
        "species_common_name": str(getattr(project, "species_common_name", "")),
        "project_accession": str(getattr(project, "project_accession", "")),
        "repo_stable_sample_id": "",
        "preferred_sample_label": "",
        "published_wording": "",
        "source_wording_excerpt": "",
        "provenance_surface": "",
        "provenance_kind": "",
        "provenance_locator": "",
        "dating_basis": "",
        "evidence_class": "",
        "precision_posture": "",
        "normalization_status": "",
        "normalization_rule": "",
        "uncertainty_note": "",
        "time_start_bp": "",
        "time_end_bp": "",
        "time_mean_bp": "",
        "temporal_semantics": {},
    }


def _render_sample_chronology_audit_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Sample chronology normalization audit",
        "",
        f"- Sample rows: `{payload['sample_row_count']}`",
        f"- Normalized intervals: `{payload['normalized_interval_count']}`",
        f"- Normalized points: `{payload['normalized_point_count']}`",
        f"- Text-only rows: `{payload['text_only_unparsed_count']}`",
        f"- Unresolved rows: `{payload['unresolved_count']}`",
        f"- Direct radiocarbon rows: `{payload['evidence_counts']['direct_radiocarbon_date']}`",
        f"- Modeled sample-date rows: `{payload['evidence_counts']['modeled_sample_date']}`",
        f"- Archaeological-context rows: `{payload['evidence_counts']['archaeological_context_date']}`",
        f"- Broad period rows: `{payload['evidence_counts']['broad_period_label']}`",
        "",
    ]
    if payload["projects_requiring_manual_review"]:
        lines.append("## Projects requiring manual chronology review")
        lines.append("")
        for item in payload["projects_requiring_manual_review"]:
            lines.append(f"- `{item}`")
        lines.append("")
    lines.extend(
        [
            "| Project accession | Sample rows | Interval rows | Point rows | Text-only rows | Unresolved rows | Conflicts |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['project_accession']} | {row['recovered_sample_row_count']} | "
            f"{row['normalized_interval_count']} | {row['normalized_point_count']} | "
            f"{row['text_only_unparsed_count']} | {row['normalization_unresolved_count']} | "
            f"{row['conflicting_context_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_ambiguity_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample chronology ambiguity ledger",
        "",
        f"- Rows requiring chronology review: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No sample chronology rows currently require manual review.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Strength | Normalization | Chronology | Note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        note = row["chronology_conflict_note"] or row["review_note"]
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['chronology_strength']} / {row['chronology_precision_posture']} | {row['chronology_normalization_status']} | "
            f"{row['chronology_text']} | {note} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_review_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample chronology review",
        "",
        f"- Sample chronology rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No sample chronology rows are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Species | Project accession | Sample id | Strength | Evidence class | Precision posture | Normalization | Chronology | Provenance |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['repo_stable_sample_id']} | {row['chronology_strength']} | "
            f"{row['chronology_evidence_class']} | {row['chronology_precision_posture']} | "
            f"{row['chronology_normalization_status']} | {row['chronology_text']} | "
            f"{row['chronology_provenance_path']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_conflict_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample chronology conflict ledger",
        "",
        f"- Conflicting rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No cross-source chronology conflicts are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Evidence class | Precision posture | Chronology | Conflict note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['chronology_evidence_class']} | {row['chronology_precision_posture']} | "
            f"{row['chronology_text']} | {row['chronology_conflict_note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_provenance_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample chronology provenance review",
        "",
        f"- Provenance packets: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No chronology provenance packets are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Published wording | Provenance surface | Provenance locator | Normalization rule | Uncertainty note |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['published_wording']} | {row['provenance_surface']} | "
            f"{row['provenance_locator']} | {row['normalization_rule']} | "
            f"{row['uncertainty_note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_chronology_precision_audit_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Sample chronology precision audit",
        "",
        f"- Rows audited: `{payload['row_count']}`",
        f"- Precise point rows: `{payload['precision_counts']['sample_precise_point']}`",
        f"- Precise interval rows: `{payload['precision_counts']['sample_precise_interval']}`",
        f"- Approximate or modeled rows: `{payload['precision_counts']['sample_approximate_or_modeled']}`",
        f"- Contextual rows: `{payload['precision_counts']['contextual_interval']}`",
        f"- Broad period rows: `{payload['precision_counts']['broad_period_only']}`",
        f"- Unresolved rows: `{payload['precision_counts']['unresolved']}`",
        "",
        "| Project accession | Sample id | Evidence class | Precision posture | Normalization | Chronology |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        if row["chronology_precision_posture"] in {
            "sample_precise_point",
            "sample_precise_interval",
        }:
            continue
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['chronology_evidence_class']} | {row['chronology_precision_posture']} | "
            f"{row['chronology_normalization_status']} | {row['chronology_text']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_date_evidence_gap_queue_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Date evidence gap queue",
        "",
        f"- Projects still needing stronger sample-level chronology: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append(
            "All tracked projects currently publish defensible sample-level chronology surfaces."
        )
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Species | Sample rows | Exact sample dates | Contextual dates | Broad labels | Missing dates | Gap reasons |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['species_latin_name']} | "
            f"{row['recovered_sample_row_count']} | {row['exact_sample_date_count']} | "
            f"{row['contextual_date_count']} | {row['broad_label_count']} | "
            f"{row['missing_date_count']} | {', '.join(row['gap_reasons'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def _normalization_rule_for(row: AdnaProjectSampleChronologyRow) -> str:
    if row.chronology_normalization_status == "normalized_point":
        return "keep one sample-owned point without widening it into a fake interval"
    if row.chronology_normalization_status == "normalized_interval":
        return "keep one normalized interval and preserve its evidence class and precision posture"
    if row.chronology_normalization_status == "text_only_unparsed":
        return "publish the wording as text and refuse fake numeric precision"
    return "keep the row unresolved until stronger chronology evidence exists"


def _uncertainty_note_for(row: AdnaProjectSampleChronologyRow) -> str:
    for value in (
        row.chronology_conflict_note,
        row.review_note,
        row.chronology_precision_posture
        if row.chronology_precision_posture
        not in {"sample_precise_point", "sample_precise_interval"}
        else "",
    ):
        text = str(value).strip()
        if text:
            return text
    return "No additional uncertainty note published."


def _temporal_semantics_for_chronology_row(
    row: AdnaProjectSampleChronologyRow,
) -> dict[str, object]:
    if row.chronology_precision_posture in {
        "sample_precise_point",
        "sample_precise_interval",
    }:
        comparability_posture = "numeric_interval"
    elif row.chronology_precision_posture in {
        "sample_approximate_or_modeled",
        "contextual_interval",
    }:
        comparability_posture = "numeric_interval_with_caveat"
    elif row.chronology_precision_posture == "broad_period_only":
        comparability_posture = "contextual_label_only"
    else:
        comparability_posture = "unresolved"
    return build_temporal_semantics(
        source_family="animal_adna",
        evidence_class=row.chronology_evidence_class,
        precision_posture=row.chronology_precision_posture,
        comparability_posture=comparability_posture,
        time_start_bp=row.time_start_bp,
        time_end_bp=row.time_end_bp,
        time_mean_bp=row.time_mean_bp,
        summary_label=row.chronology_text,
        comparison_note=_uncertainty_note_for(row),
        provenance_path=row.chronology_provenance_path,
        provenance_locator=row.chronology_provenance_locator,
        provenance_excerpt=row.chronology_provenance_text,
        original_labels=(row.chronology_text,) if row.chronology_text else (),
    ).as_dict()
