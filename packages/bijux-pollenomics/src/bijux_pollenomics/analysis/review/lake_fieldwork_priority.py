from __future__ import annotations

from ..lake_evidence_richness import (
    LakeEvidenceBandScore,
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)


def band_score(
    assessment: LakeEvidenceRichnessAssessment,
    radius_km: int,
) -> LakeEvidenceBandScore:
    for score in assessment.band_scores:
        if score.radius_km == radius_km:
            return score
    raise ValueError(f"Missing band score for radius {radius_km}")


def human_context_posture(assessment: LakeEvidenceRichnessAssessment) -> str:
    if band_score(assessment, 10).human_adna_locality_count > 0:
        return "core_human_adna_context"
    if band_score(assessment, 20).human_adna_locality_count > 0:
        return "near_human_adna_context"
    if band_score(assessment, 30).human_adna_locality_count > 0:
        return "extended_human_adna_context"
    if band_score(assessment, 50).human_adna_locality_count > 0:
        return "outer_human_adna_context"
    return "human_adna_context_absent"


def fieldwork_rows(
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int = 20,
) -> list[LakeEvidenceRichnessAssessment]:
    return sorted(
        report.assessments,
        key=lambda assessment: (
            _human_context_gate_rank(assessment),
            _sampling_priority_rank(
                assessment.candidate.lake_sampling_posture or "sampling_not_scored"
            ),
            _human_context_priority_rank(assessment),
            -fieldwork_shortlist_score(assessment),
            assessment.aggregate_rank,
            assessment.candidate.lake_label,
        ),
    )[:top_n]


def fieldwork_shortlist_score(assessment: LakeEvidenceRichnessAssessment) -> float:
    candidate = assessment.candidate
    band_10 = band_score(assessment, 10)
    band_20 = band_score(assessment, 20)
    band_30 = band_score(assessment, 30)
    human_priority_signal = _weighted_average(
        (band_10.human_signal, 0.35),
        (band_20.human_signal, 0.45),
        (band_30.human_signal, 0.15),
        (1.0 if band_20.human_adna_locality_count > 0 else 0.0, 0.05),
    )
    posture_bonus = {
        "sampling_lake_candidate": 0.03,
        "compact_lake_candidate": 0.0,
        "small_lake_review": -0.06,
    }.get(candidate.lake_sampling_posture, -0.02)
    return round(
        human_priority_signal * 0.46
        + min(1.0, candidate.direct_pollen_source_count / 2.0) * 0.14
        + candidate.direct_pollen_signal * 0.1
        + assessment.aggregate_score * 0.12
        + min(1.0, band_20.evidence_family_count / 4.0) * 0.08
        + candidate.lake_sampling_fit * 0.08
        + min(1.0, band_20.sead_site_count / 20.0) * 0.02
        + posture_bonus,
        4,
    )


def _human_context_priority_rank(
    assessment: LakeEvidenceRichnessAssessment,
) -> int:
    return {
        "core_human_adna_context": 0,
        "near_human_adna_context": 1,
        "extended_human_adna_context": 2,
        "outer_human_adna_context": 3,
        "human_adna_context_absent": 4,
    }[human_context_posture(assessment)]


def _human_context_gate_rank(
    assessment: LakeEvidenceRichnessAssessment,
) -> int:
    posture = human_context_posture(assessment)
    if posture in {"core_human_adna_context", "near_human_adna_context"}:
        return 0
    if posture == "extended_human_adna_context":
        return 1
    if posture == "outer_human_adna_context":
        return 2
    return 3


def _sampling_priority_rank(sampling_posture: str) -> int:
    return {
        "sampling_lake_candidate": 0,
        "compact_lake_candidate": 1,
        "small_lake_review": 2,
        "sampling_not_scored": 3,
    }.get(sampling_posture, 4)


def _weighted_average(*pairs: tuple[float, float]) -> float:
    numerator = sum(value * weight for value, weight in pairs)
    denominator = sum(weight for _, weight in pairs)
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)
