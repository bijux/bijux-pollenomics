from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)

from .candidate_features import (
    _candidate_temporal_sources,
    _temporal_popup_rows,
    _temporal_properties,
    _temporal_record_id,
)

from .scenario_metrics import scenario_metric_map as _scenario_metric_map

from .presentation import (
    _candidate_description,
    _candidate_media_links,
    _render_ambiguity_cell,
)
from ..lake_fieldwork_priority import band_score as _band_score

from .ranking_tables import (
    _consensus_rows,
    _fieldwork_rank_map,
    _fieldwork_rows,
    _fieldwork_shortlist_score,
)


class LakeEvidenceScenario(TypedDict):
    key: str
    label: str
    rows: list[LakeEvidenceRichnessAssessment]
    rank_getter: Callable[[LakeEvidenceRichnessAssessment], int]
    score_getter: Callable[[LakeEvidenceRichnessAssessment], float | int]
    scenario_label: str


def _map_scenarios(report: LakeEvidenceRichnessReport) -> list[LakeEvidenceScenario]:
    scenario_metrics = _scenario_metric_map(report)

    def aggregate_rank(assessment: LakeEvidenceRichnessAssessment) -> int:
        return assessment.aggregate_rank

    def aggregate_score(assessment: LakeEvidenceRichnessAssessment) -> float:
        return assessment.aggregate_score

    scenarios: list[LakeEvidenceScenario] = [
        {
            "key": "lake-evidence-aggregate",
            "label": "Aggregate top 20",
            "rows": sorted(report.assessments, key=lambda item: item.aggregate_rank)[
                :20
            ],
            "rank_getter": aggregate_rank,
            "score_getter": aggregate_score,
            "scenario_label": "Aggregate",
        }
    ]
    consensus_rows = _consensus_rows(report)[:20]

    def consensus_rank(assessment: LakeEvidenceRichnessAssessment) -> int:
        return consensus_rows.index(assessment) + 1

    def consensus_score(assessment: LakeEvidenceRichnessAssessment) -> int:
        return scenario_metrics[assessment.candidate.lake_token][
            "scenario_top20_presence_count"
        ]

    scenarios.append(
        {
            "key": "lake-evidence-consensus",
            "label": "Consensus top 20",
            "rows": consensus_rows,
            "rank_getter": consensus_rank,
            "score_getter": consensus_score,
            "scenario_label": "Consensus",
        }
    )
    fieldwork_rows = _fieldwork_rows(report)
    fieldwork_rank_map = _fieldwork_rank_map(report)

    def fieldwork_rank(assessment: LakeEvidenceRichnessAssessment) -> int:
        return fieldwork_rank_map[assessment.candidate.lake_token]

    scenarios.append(
        {
            "key": "lake-evidence-fieldwork",
            "label": "Fieldwork shortlist",
            "rows": fieldwork_rows,
            "rank_getter": fieldwork_rank,
            "score_getter": _fieldwork_shortlist_score,
            "scenario_label": "Fieldwork shortlist",
        }
    )
    for radius in report.radii_km:

        def radius_rank(
            assessment: LakeEvidenceRichnessAssessment,
            selected_radius: int = radius,
        ) -> int:
            return _band_score(assessment, selected_radius).band_rank

        def radius_score(
            assessment: LakeEvidenceRichnessAssessment,
            selected_radius: int = radius,
        ) -> float:
            return _band_score(assessment, selected_radius).total_score

        scenarios.append(
            {
                "key": f"lake-evidence-{radius}km",
                "label": f"{radius} km top 20",
                "rows": sorted(
                    report.assessments,
                    key=lambda item: _band_score(item, radius).band_rank,
                )[:20],
                "rank_getter": radius_rank,
                "score_getter": radius_score,
                "scenario_label": f"{radius} km",
            }
        )
    return scenarios


def _build_scenario_feature_collection(
    report: LakeEvidenceRichnessReport,
    scenario: LakeEvidenceScenario,
) -> dict[str, object]:
    features = []
    rows = scenario["rows"]
    rank_getter = scenario["rank_getter"]
    score_getter = scenario["score_getter"]
    for assessment in rows:
        candidate = assessment.candidate
        temporal_sources = _candidate_temporal_sources(candidate)
        for source_point in temporal_sources or (None,):
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [candidate.longitude, candidate.latitude],
                    },
                    "properties": {
                        "source": "bijux-pollenomics",
                        "layer_key": scenario["key"],
                        "layer_label": scenario["label"],
                        "category": "Lake evidence candidate",
                        "country": "Sweden",
                        "record_id": _temporal_record_id(candidate, source_point),
                        "name": candidate.lake_label,
                        "geometry_type": "Point",
                        "subtitle": "Lake evidence ranking scenario",
                        "description": candidate.ambiguity_note
                        or _candidate_description(candidate),
                        "source_url": candidate.representative_source_url,
                        "record_count": 1,
                        "media_links": _candidate_media_links(candidate),
                        "popup_rows": [
                            {
                                "label": "Scenario",
                                "value": str(scenario["scenario_label"]),
                            },
                            {
                                "label": "Scenario rank",
                                "value": str(rank_getter(assessment)),
                            },
                            {
                                "label": "Scenario score",
                                "value": f"{score_getter(assessment):.4f}",
                            },
                            {
                                "label": "Aggregate rank",
                                "value": str(assessment.aggregate_rank),
                            },
                            {
                                "label": "Coordinates",
                                "value": f"{candidate.latitude:.6f}, {candidate.longitude:.6f}",
                            },
                            {
                                "label": "Representative source",
                                "value": candidate.representative_source_record,
                            },
                            {
                                "label": "Lake registry id",
                                "value": candidate.lake_registry_id or "Not available",
                            },
                            {
                                "label": "Lake area",
                                "value": (
                                    f"{candidate.lake_area_km2:.3f} km²"
                                    if candidate.lake_area_km2 is not None
                                    else "Not available"
                                ),
                            },
                            {
                                "label": "Sampling posture",
                                "value": candidate.lake_sampling_posture
                                or "Not available",
                            },
                            {
                                "label": "Sampling fit",
                                "value": f"{candidate.lake_sampling_fit:.4f}",
                            },
                            {
                                "label": "Sampling readiness",
                                "value": candidate.lake_sampling_readiness_posture,
                            },
                            {
                                "label": "Sampling evidence still required",
                                "value": ", ".join(
                                    candidate.lake_sampling_missing_inputs
                                )
                                or "Not recorded",
                            },
                            {
                                "label": "Identity diagnostics",
                                "value": _render_ambiguity_cell(
                                    candidate.ambiguity_flags
                                ),
                            },
                            {
                                "label": "Identity note",
                                "value": candidate.ambiguity_note
                                or "No explicit identity warning.",
                            },
                            *_temporal_popup_rows(source_point),
                        ],
                        **_temporal_properties(source_point),
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}


def _lake_bounds(
    report: LakeEvidenceRichnessReport,
) -> tuple[tuple[float, float], tuple[float, float]]:
    latitudes = [assessment.candidate.latitude for assessment in report.assessments]
    longitudes = [assessment.candidate.longitude for assessment in report.assessments]
    if not latitudes or not longitudes:
        return ((54.0, 10.0), (69.0, 25.0))
    padding = 0.8
    return (
        (min(latitudes) - padding, min(longitudes) - padding),
        (max(latitudes) + padding, max(longitudes) + padding),
    )
