from __future__ import annotations

from bijux_pollenomics.core.temporal_semantics import build_temporal_semantics

from .models import AdnaProjectSampleChronologyRow


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
    has_numeric_interval = row.time_start_bp is not None and row.time_end_bp is not None
    if has_numeric_interval and row.chronology_precision_posture in {
        "sample_precise_point",
        "sample_precise_interval",
    }:
        comparability_posture = "numeric_interval"
    elif has_numeric_interval and row.chronology_precision_posture in {
        "sample_approximate_or_modeled",
        "contextual_interval",
    }:
        comparability_posture = "numeric_interval_with_caveat"
    elif row.chronology_text.strip():
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
