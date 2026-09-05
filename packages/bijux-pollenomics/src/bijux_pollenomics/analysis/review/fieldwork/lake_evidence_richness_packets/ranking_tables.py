from __future__ import annotations


from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)
from ..lake_fieldwork_priority import (
    band_score as fieldwork_band_score,
    fieldwork_rows,
    fieldwork_shortlist_score,
    human_context_posture,
)

from .scenario_metrics import scenario_metric_map as _scenario_metric_map

from .presentation import (
    _render_coordinate_link,
    _render_lake_area,
)


def _fieldwork_rows(
    report: LakeEvidenceRichnessReport,
) -> list[LakeEvidenceRichnessAssessment]:
    return fieldwork_rows(report, top_n=20)


def _fieldwork_rank_map(report: LakeEvidenceRichnessReport) -> dict[str, int]:
    return {
        assessment.candidate.lake_token: rank
        for rank, assessment in enumerate(_fieldwork_rows(report), start=1)
    }


def _fieldwork_shortlist_score(assessment: LakeEvidenceRichnessAssessment) -> float:
    return fieldwork_shortlist_score(assessment)


def _consensus_rows(
    report: LakeEvidenceRichnessReport,
) -> list[LakeEvidenceRichnessAssessment]:
    scenario_metrics = _scenario_metric_map(report)
    return sorted(
        report.assessments,
        key=lambda assessment: (
            -scenario_metrics[assessment.candidate.lake_token][
                "scenario_top20_presence_count"
            ],
            scenario_metrics[assessment.candidate.lake_token]["scenario_mean_rank"]
            or 10_000,
            assessment.aggregate_rank,
            assessment.candidate.lake_label,
        ),
    )


def _render_consensus_table(report: LakeEvidenceRichnessReport) -> str:
    scenario_metrics = _scenario_metric_map(report)
    ordered = _consensus_rows(report)[:20]
    rows = (
        "\n".join(
            (
                f"| {index} | {assessment.candidate.lake_label} | "
                f"{_render_coordinate_link(assessment.candidate.latitude, assessment.candidate.longitude)} | "
                f"{_render_lake_identity_cell(assessment.candidate.lake_registry_id)} | "
                f"{assessment.candidate.lake_name_status or 'not_available'} | "
                f"{scenario_metrics[assessment.candidate.lake_token]['scenario_top20_presence_count']}/"
                f"{scenario_metrics[assessment.candidate.lake_token]['scenario_count']} | "
                f"{scenario_metrics[assessment.candidate.lake_token]['scenario_best_rank']} | "
                f"{scenario_metrics[assessment.candidate.lake_token]['scenario_mean_rank']:.2f} | "
                f"{assessment.aggregate_rank} | "
                f"{assessment.candidate.coordinate_resolution_method} |"
            )
            for index, assessment in enumerate(ordered, start=1)
        )
        or "| - | No lake candidates | - | not_available | not_available | 0/0 | - | - | - | - |"
    )
    return f"""## Scenario Consensus

| Consensus rank | Lake | Coordinates | Lake registry id | Name status | Top-20 scenario presence | Best scenario rank | Mean scenario rank | Aggregate rank | Coordinate method |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
{rows}"""


def _render_fieldwork_shortlist_table(report: LakeEvidenceRichnessReport) -> str:
    fieldwork_rank_map = _fieldwork_rank_map(report)
    rows = (
        "\n".join(
            (
                f"| {fieldwork_rank_map[assessment.candidate.lake_token]} | "
                f"{assessment.candidate.lake_label} | "
                f"{_render_coordinate_link(assessment.candidate.latitude, assessment.candidate.longitude)} | "
                f"{_render_lake_identity_cell(assessment.candidate.lake_registry_id)} | "
                f"{assessment.candidate.lake_name_status or 'not_available'} | "
                f"{_fieldwork_shortlist_score(assessment):.4f} | "
                f"{assessment.candidate.lake_sampling_posture or 'not_scored'} | "
                f"{human_context_posture(assessment)} | "
                f"{assessment.candidate.lake_sampling_fit:.4f} | "
                f"{_render_lake_area(assessment.candidate)} | "
                f"{fieldwork_band_score(assessment, 20).human_adna_locality_count} | "
                f"{fieldwork_band_score(assessment, 20).evidence_family_count} |"
            )
            for assessment in _fieldwork_rows(report)
        )
        or "| - | No lake candidates | - | not_available | not_available | 0.0000 | - | - | 0.0000 | - | 0 | 0 |"
    )
    return f"""## Fieldwork Shortlist

| Fieldwork rank | Lake | Coordinates | Lake registry id | Name status | Shortlist score | Sampling posture | Human context | Sampling fit | Area km² | Human localities within 20 km | Evidence families within 20 km |
| ---: | --- | --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
{rows}"""


def _render_lake_identity_cell(lake_registry_id: str) -> str:
    return lake_registry_id or "not_available"
