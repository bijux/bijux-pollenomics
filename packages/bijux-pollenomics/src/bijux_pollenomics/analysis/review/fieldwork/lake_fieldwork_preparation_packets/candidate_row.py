"""Evidence-preserving assembly of one lake preparation row."""

from __future__ import annotations

from collections.abc import Callable
from statistics import mean as default_mean

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceBandScore,
    LakeEvidenceRichnessAssessment,
)


def build_candidate_row(
    assessment: LakeEvidenceRichnessAssessment,
    *,
    fieldwork_rank: int,
    band_score: Callable[[LakeEvidenceRichnessAssessment, int], LakeEvidenceBandScore],
    shortlist_score: Callable[[LakeEvidenceRichnessAssessment], float],
    human_posture: Callable[[LakeEvidenceRichnessAssessment], str],
    identity_posture: Callable[[tuple[str, ...]], str],
    top20_presence_count: Callable[..., int],
    consistency_posture: Callable[[int], str],
    sead_posture: Callable[[int], str],
    palaeopen_posture: Callable[..., str],
    preparation_posture: Callable[..., str],
    required_actions: Callable[..., list[str]],
    maps_url: Callable[[float, float], str],
    mean_value: Callable[[tuple[int, ...]], float] = default_mean,
) -> dict[str, object]:
    candidate = assessment.candidate
    band_10 = band_score(assessment, 10)
    band_20 = band_score(assessment, 20)
    band_50 = band_score(assessment, 50)
    identity = identity_posture(candidate.ambiguity_flags)
    lake_human_context_posture = human_posture(assessment)
    scenario_ranks = {
        f"{score.radius_km}km": score.band_rank for score in assessment.band_scores
    }
    scenario_top20_presence_count = top20_presence_count(
        aggregate_rank=assessment.aggregate_rank,
        scenario_ranks=scenario_ranks,
    )
    scenario_best_rank = min((assessment.aggregate_rank, *scenario_ranks.values()))
    scenario_mean_rank = round(
        mean_value((assessment.aggregate_rank, *scenario_ranks.values())),
        2,
    )
    sampling_posture = candidate.lake_sampling_posture or "sampling_not_scored"
    scenario_consistency_posture = consistency_posture(scenario_top20_presence_count)
    sead_context_posture = sead_posture(band_20.sead_site_count)
    palaeopen_alignment_posture = palaeopen_posture(
        direct_pollen_source_count=candidate.direct_pollen_source_count,
        evidence_family_count=band_20.evidence_family_count,
    )
    preparation = preparation_posture(
        ambiguity_flags=candidate.ambiguity_flags,
        sampling_posture=sampling_posture,
        sampling_fit=candidate.lake_sampling_fit,
        human_context_posture=lake_human_context_posture,
        direct_pollen_source_count=candidate.direct_pollen_source_count,
        evidence_family_count=band_20.evidence_family_count,
        sead_site_count=band_20.sead_site_count,
        human_locality_count=band_20.human_adna_locality_count,
        scenario_consistency_posture=scenario_consistency_posture,
    )
    return {
        "fieldwork_rank": fieldwork_rank,
        "fieldwork_shortlist_score": shortlist_score(assessment),
        "aggregate_rank": assessment.aggregate_rank,
        "lake_label": candidate.lake_label,
        "latitude": candidate.latitude,
        "longitude": candidate.longitude,
        "google_maps_url": maps_url(candidate.latitude, candidate.longitude),
        "aggregate_score": assessment.aggregate_score,
        "preparation_posture": preparation,
        "identity_posture": identity,
        "sampling_posture": sampling_posture,
        "human_context_posture": lake_human_context_posture,
        "sampling_fit": candidate.lake_sampling_fit,
        "sampling_readiness_posture": candidate.lake_sampling_readiness_posture,
        "sampling_missing_inputs": list(candidate.lake_sampling_missing_inputs),
        "lake_area_km2": candidate.lake_area_km2,
        "scenario_consistency_posture": scenario_consistency_posture,
        "sead_context_posture": sead_context_posture,
        "palaeopen_alignment_posture": palaeopen_alignment_posture,
        "scenario_ranks": scenario_ranks,
        "scenario_top20_presence_count": scenario_top20_presence_count,
        "scenario_best_rank": scenario_best_rank,
        "scenario_mean_rank": scenario_mean_rank,
        "representative_source_record": candidate.representative_source_record,
        "lake_registry_id": candidate.lake_registry_id,
        "lake_name_status": candidate.lake_name_status,
        "coordinate_resolution_method": candidate.coordinate_resolution_method,
        "direct_pollen_source_count": candidate.direct_pollen_source_count,
        "time_aware_direct_pollen_records": candidate.time_aware_direct_pollen_records,
        "evidence_families_20km": band_20.evidence_family_count,
        "sead_sites_20km": band_20.sead_site_count,
        "human_localities_10km": band_10.human_adna_locality_count,
        "human_samples_10km": band_10.human_adna_sample_count,
        "human_localities_20km": band_20.human_adna_locality_count,
        "human_samples_20km": band_20.human_adna_sample_count,
        "domesticated_animal_localities_50km": band_50.domesticated_animal_locality_count,
        "ambiguity_flags": list(candidate.ambiguity_flags),
        "required_actions": required_actions(
            ambiguity_flags=candidate.ambiguity_flags,
            sampling_posture=sampling_posture,
            human_context_posture=lake_human_context_posture,
            scenario_consistency_posture=scenario_consistency_posture,
            sead_context_posture=sead_context_posture,
            palaeopen_alignment_posture=palaeopen_alignment_posture,
            preparation_posture=preparation,
        ),
    }
