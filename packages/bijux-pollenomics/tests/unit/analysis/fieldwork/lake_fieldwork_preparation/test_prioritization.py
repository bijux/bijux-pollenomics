"""Sampling and human-context prioritization tests."""

from dataclasses import replace

from bijux_pollenomics.analysis import build_lake_fieldwork_preparation_payload

from .support import _band, _report


def test_lake_fieldwork_preparation_prioritizes_sampling_candidates_over_small_lakes() -> (
    None
):
    report = _report()
    small_review_candidate = replace(
        report.assessments[0].candidate,
        lake_label="Small Review Lake",
        lake_sampling_posture="small_lake_review",
        lake_sampling_fit=0.39,
        lake_area_km2=0.02,
    )
    small_review_assessment = replace(
        report.assessments[0],
        candidate=small_review_candidate,
        aggregate_rank=1,
        aggregate_score=0.84,
    )
    sampling_candidate = replace(
        report.assessments[1].candidate,
        lake_label="Sampling Candidate Lake",
        ambiguity_flags=(),
        lake_sampling_posture="sampling_lake_candidate",
        lake_sampling_fit=0.96,
    )
    sampling_assessment = replace(
        report.assessments[1],
        candidate=sampling_candidate,
        aggregate_rank=2,
        aggregate_score=0.71,
    )
    ranked_report = replace(
        report,
        assessments=(small_review_assessment, sampling_assessment),
    )

    payload = build_lake_fieldwork_preparation_payload(ranked_report)

    assert payload["rows"][0]["lake_label"] == "Sampling Candidate Lake"
    assert payload["rows"][0]["fieldwork_rank"] == 1
    assert payload["rows"][0]["aggregate_rank"] == 2
    assert payload["rows"][1]["lake_label"] == "Small Review Lake"
    assert payload["rows"][1]["fieldwork_rank"] == 2
    assert payload["rows"][1]["aggregate_rank"] == 1


def test_lake_fieldwork_preparation_keeps_distant_human_context_review_first() -> None:
    report = _report()
    distant_human_bands = (
        _band(
            10,
            band_rank=1,
            total_score=0.64,
            sead_site_count=18,
            evidence_family_count=4,
            human_adna_locality_count=0,
        ),
        _band(
            20,
            band_rank=1,
            total_score=0.66,
            sead_site_count=24,
            evidence_family_count=4,
            human_adna_locality_count=0,
        ),
        _band(
            30,
            band_rank=1,
            total_score=0.68,
            sead_site_count=31,
            evidence_family_count=4,
            human_adna_locality_count=1,
        ),
        _band(
            40,
            band_rank=1,
            total_score=0.65,
            sead_site_count=35,
            evidence_family_count=4,
            human_adna_locality_count=1,
        ),
        _band(
            50,
            band_rank=1,
            total_score=0.63,
            sead_site_count=38,
            evidence_family_count=4,
            human_adna_locality_count=1,
        ),
    )
    distant_candidate = replace(
        report.assessments[0].candidate,
        lake_label="Distant Human Lake",
        lake_sampling_posture="sampling_lake_candidate",
        lake_sampling_fit=1.0,
    )
    distant_assessment = replace(
        report.assessments[0],
        candidate=distant_candidate,
        aggregate_rank=1,
        aggregate_score=0.78,
        band_scores=distant_human_bands,
    )
    near_candidate = replace(
        report.assessments[1].candidate,
        lake_label="Near Human Lake",
        ambiguity_flags=(),
        duplicate_name_count=1,
        ambiguity_note="",
        lake_sampling_posture="sampling_lake_candidate",
        lake_sampling_fit=0.92,
    )
    near_assessment = replace(
        report.assessments[1],
        candidate=near_candidate,
        aggregate_rank=2,
        aggregate_score=0.67,
    )
    prioritized_report = replace(
        report,
        assessments=(distant_assessment, near_assessment),
    )

    payload = build_lake_fieldwork_preparation_payload(prioritized_report)

    assert payload["rows"][0]["lake_label"] == "Near Human Lake"
    assert payload["rows"][0]["human_context_posture"] == "near_human_adna_context"
    assert payload["rows"][1]["lake_label"] == "Distant Human Lake"
    assert payload["rows"][1]["human_context_posture"] == "extended_human_adna_context"
    assert payload["rows"][1]["preparation_posture"] == "human_context_review_required"
    assert (
        "treat this lake as context-rich but aDNA-distant until a nearer human aDNA locality supports field planning"
        in payload["rows"][1]["required_actions"]
    )
