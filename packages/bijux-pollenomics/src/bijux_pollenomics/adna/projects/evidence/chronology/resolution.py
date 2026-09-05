from __future__ import annotations

from bijux_pollenomics.adna.domain.models import AdnaChronology, AdnaSiteEvidenceRecord
from bijux_pollenomics.adna.projects.sample_master import AdnaProjectSampleMasterRow

from .constants import (
    _APPROXIMATE_DATE_RE,
    _BROAD_PERIOD_TEXT_RE,
    _HISTORICAL_DATE_RE,
    _MODELED_DATE_RE,
)
from .models import _ResolvedChronologySource


def _resolve_chronology_source(
    *,
    master_row: AdnaProjectSampleMasterRow,
    site_row: AdnaSiteEvidenceRecord | None,
    dating_basis: str,
) -> _ResolvedChronologySource:
    from bijux_pollenomics.adna.workflow.normalization import normalize_chronology_text

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


def _site_chronology(
    site_row: AdnaSiteEvidenceRecord | None, *, dating_basis: str
) -> AdnaChronology:
    from bijux_pollenomics.adna.workflow.normalization import (
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
    preferred_chronology: AdnaChronology,
    comparison_text: str,
    comparison_chronology: AdnaChronology,
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


def _normalization_status_for(chronology: AdnaChronology) -> str:
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
    chronology: AdnaChronology,
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
    chronology: AdnaChronology,
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
