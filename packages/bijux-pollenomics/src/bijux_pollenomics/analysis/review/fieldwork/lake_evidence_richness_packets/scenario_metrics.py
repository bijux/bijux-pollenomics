from __future__ import annotations

from statistics import mean
from typing import TypedDict

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)

from ..lake_fieldwork_priority import band_score, fieldwork_rows


class ScenarioMetrics(TypedDict):
    scenario_count: int
    scenario_top20_presence_count: int
    scenario_top20_labels: tuple[str, ...]
    scenario_best_rank: int | None
    scenario_worst_rank: int | None
    scenario_mean_rank: float | None


def scenario_metric_map(
    report: LakeEvidenceRichnessReport,
) -> dict[str, ScenarioMetrics]:
    """Summarize each candidate's rank stability across declared scenarios."""
    scenario_orders: list[tuple[str, list[LakeEvidenceRichnessAssessment]]] = [
        ("aggregate", sorted(report.assessments, key=lambda item: item.aggregate_rank)),
        ("fieldwork shortlist", fieldwork_rows(report, top_n=20)),
    ]
    for radius in report.radii_km:
        scenario_orders.append(
            (
                f"{radius} km",
                sorted(
                    report.assessments,
                    key=lambda item: band_score(item, radius).band_rank,
                ),
            )
        )
    scenario_rank_maps = [
        (
            label,
            {
                assessment.candidate.lake_token: rank
                for rank, assessment in enumerate(ordered, start=1)
            },
        )
        for label, ordered in scenario_orders
    ]
    metrics: dict[str, ScenarioMetrics] = {}
    for assessment in report.assessments:
        ranks: list[int] = []
        top20_labels: list[str] = []
        lake_token = assessment.candidate.lake_token
        for label, rank_map in scenario_rank_maps:
            rank = rank_map.get(lake_token)
            if rank is None:
                continue
            ranks.append(rank)
            if rank <= 20:
                top20_labels.append(label)
        metrics[lake_token] = {
            "scenario_count": len(scenario_orders),
            "scenario_top20_presence_count": len(top20_labels),
            "scenario_top20_labels": tuple(top20_labels),
            "scenario_best_rank": min(ranks) if ranks else None,
            "scenario_worst_rank": max(ranks) if ranks else None,
            "scenario_mean_rank": round(mean(ranks), 2) if ranks else None,
        }
    return metrics
