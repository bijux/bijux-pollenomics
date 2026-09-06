from __future__ import annotations

import csv
from pathlib import Path

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessReport,
)

from ..lake_fieldwork_priority import band_score as _band_score
from .candidate_features import (
    _render_context_evidence_json,
    _render_temporal_evidence_json,
)
from .presentation import (
    _google_maps_url,
    _render_source_point_cell,
)
from .ranking_tables import (
    _fieldwork_rank_map,
    _fieldwork_rows,
    _fieldwork_shortlist_score,
)
from .scenario_metrics import scenario_metric_map as _scenario_metric_map


def write_lake_evidence_richness_band_csv(
    path: Path,
    report: LakeEvidenceRichnessReport,
) -> None:
    """Write one long-form CSV row per lake and distance-band scenario."""
    scenario_metrics = _scenario_metric_map(report)
    fieldnames = (
        "lake_name",
        "lake_label",
        "lake_token",
        "name_key",
        "latitude",
        "longitude",
        "google_maps_url",
        "representative_source_record",
        "representative_source_layer_key",
        "representative_source_name",
        "representative_source_url",
        "coordinate_resolution_method",
        "duplicate_name_count",
        "coordinate_spread_km",
        "ambiguity_flags",
        "ambiguity_note",
        "lake_registry_id",
        "lake_registry_uuid",
        "lake_water_identity",
        "lake_name_status",
        "lake_area_km2",
        "lake_sampling_posture",
        "lake_sampling_fit",
        "lake_sampling_notes",
        "lake_sampling_readiness_posture",
        "lake_sampling_missing_inputs",
        "supporting_source_records",
        "supporting_source_points",
        "direct_pollen_temporal_evidence",
        "temporal_context_evidence",
        "aggregate_rank",
        "aggregate_score",
        "scenario_top20_presence_count",
        "scenario_top20_labels",
        "scenario_best_rank",
        "scenario_worst_rank",
        "scenario_mean_rank",
        "direct_pollen_signal",
        "direct_pollen_source_count",
        "direct_pollen_record_count",
        "time_aware_direct_pollen_records",
        "band_radius_km",
        "band_rank",
        "band_score",
        "nearby_pollen_lake_count",
        "time_aware_pollen_site_count",
        "human_overlap_pollen_site_count",
        "human_adna_locality_count",
        "human_adna_sample_count",
        "domesticated_animal_locality_count",
        "domesticated_animal_sample_count",
        "sead_site_count",
        "time_aware_sead_site_count",
        "human_overlap_sead_site_count",
        "raa_density_site_count",
        "evidence_family_count",
        "nearby_pollen_signal",
        "human_signal",
        "animal_signal",
        "archaeology_signal",
        "diversity_signal",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for assessment in report.assessments:
            candidate = assessment.candidate
            scenario_metric = scenario_metrics[candidate.lake_token]
            for band in assessment.band_scores:
                writer.writerow(
                    {
                        "lake_name": candidate.lake_name,
                        "lake_label": candidate.lake_label,
                        "lake_token": candidate.lake_token,
                        "name_key": candidate.name_key,
                        "latitude": round(candidate.latitude, 6),
                        "longitude": round(candidate.longitude, 6),
                        "google_maps_url": _google_maps_url(
                            candidate.latitude, candidate.longitude
                        ),
                        "representative_source_record": candidate.representative_source_record,
                        "representative_source_layer_key": candidate.representative_source_layer_key,
                        "representative_source_name": candidate.representative_source_name,
                        "representative_source_url": candidate.representative_source_url,
                        "coordinate_resolution_method": candidate.coordinate_resolution_method,
                        "duplicate_name_count": candidate.duplicate_name_count,
                        "coordinate_spread_km": candidate.coordinate_spread_km,
                        "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                        "ambiguity_note": candidate.ambiguity_note,
                        "lake_registry_id": candidate.lake_registry_id,
                        "lake_registry_uuid": candidate.lake_registry_uuid,
                        "lake_water_identity": candidate.lake_water_identity,
                        "lake_name_status": candidate.lake_name_status,
                        "lake_area_km2": candidate.lake_area_km2,
                        "lake_sampling_posture": candidate.lake_sampling_posture,
                        "lake_sampling_fit": candidate.lake_sampling_fit,
                        "lake_sampling_notes": "; ".join(candidate.lake_sampling_notes),
                        "lake_sampling_readiness_posture": candidate.lake_sampling_readiness_posture,
                        "lake_sampling_missing_inputs": "; ".join(
                            candidate.lake_sampling_missing_inputs
                        ),
                        "supporting_source_records": "; ".join(
                            candidate.supporting_source_records
                        ),
                        "supporting_source_points": "; ".join(
                            _render_source_point_cell(source_point)
                            for source_point in candidate.supporting_source_points
                        ),
                        "direct_pollen_temporal_evidence": _render_temporal_evidence_json(
                            candidate
                        ),
                        "temporal_context_evidence": _render_context_evidence_json(
                            candidate
                        ),
                        "aggregate_rank": assessment.aggregate_rank,
                        "aggregate_score": assessment.aggregate_score,
                        "scenario_top20_presence_count": scenario_metric[
                            "scenario_top20_presence_count"
                        ],
                        "scenario_top20_labels": "; ".join(
                            scenario_metric["scenario_top20_labels"]
                        ),
                        "scenario_best_rank": scenario_metric["scenario_best_rank"],
                        "scenario_worst_rank": scenario_metric["scenario_worst_rank"],
                        "scenario_mean_rank": scenario_metric["scenario_mean_rank"],
                        "direct_pollen_signal": candidate.direct_pollen_signal,
                        "direct_pollen_source_count": candidate.direct_pollen_source_count,
                        "direct_pollen_record_count": candidate.direct_pollen_record_count,
                        "time_aware_direct_pollen_records": candidate.time_aware_direct_pollen_records,
                        "band_radius_km": band.radius_km,
                        "band_rank": band.band_rank,
                        "band_score": band.total_score,
                        "nearby_pollen_lake_count": band.nearby_pollen_lake_count,
                        "time_aware_pollen_site_count": band.time_aware_pollen_site_count,
                        "human_overlap_pollen_site_count": band.human_overlap_pollen_site_count,
                        "human_adna_locality_count": band.human_adna_locality_count,
                        "human_adna_sample_count": band.human_adna_sample_count,
                        "domesticated_animal_locality_count": band.domesticated_animal_locality_count,
                        "domesticated_animal_sample_count": band.domesticated_animal_sample_count,
                        "sead_site_count": band.sead_site_count,
                        "time_aware_sead_site_count": band.time_aware_sead_site_count,
                        "human_overlap_sead_site_count": band.human_overlap_sead_site_count,
                        "raa_density_site_count": band.raa_density_site_count,
                        "evidence_family_count": band.evidence_family_count,
                        "nearby_pollen_signal": band.nearby_pollen_signal,
                        "human_signal": band.human_signal,
                        "animal_signal": band.animal_signal,
                        "archaeology_signal": band.archaeology_signal,
                        "diversity_signal": band.diversity_signal,
                    }
                )


def write_lake_evidence_richness_registry_csv(
    path: Path,
    report: LakeEvidenceRichnessReport,
) -> None:
    """Write one registry row per lake candidate."""
    scenario_metrics = _scenario_metric_map(report)
    fieldnames = (
        "lake_name",
        "lake_label",
        "lake_token",
        "name_key",
        "latitude",
        "longitude",
        "google_maps_url",
        "aggregate_rank",
        "aggregate_score",
        "scenario_top20_presence_count",
        "scenario_top20_labels",
        "scenario_best_rank",
        "scenario_worst_rank",
        "scenario_mean_rank",
        "representative_source_record",
        "representative_source_layer_key",
        "representative_source_name",
        "representative_source_url",
        "coordinate_resolution_method",
        "duplicate_name_count",
        "coordinate_spread_km",
        "ambiguity_flags",
        "ambiguity_note",
        "lake_registry_id",
        "lake_registry_uuid",
        "lake_water_identity",
        "lake_name_status",
        "lake_area_km2",
        "lake_sampling_posture",
        "lake_sampling_fit",
        "lake_sampling_notes",
        "lake_sampling_readiness_posture",
        "lake_sampling_missing_inputs",
        "pollen_sources",
        "supporting_pollen_names",
        "supporting_source_records",
        "supporting_source_points",
        "direct_pollen_temporal_evidence",
        "temporal_context_evidence",
        "direct_pollen_source_count",
        "direct_pollen_record_count",
        "time_aware_direct_pollen_records",
        "direct_pollen_signal",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for assessment in report.assessments:
            candidate = assessment.candidate
            scenario_metric = scenario_metrics[candidate.lake_token]
            writer.writerow(
                {
                    "lake_name": candidate.lake_name,
                    "lake_label": candidate.lake_label,
                    "lake_token": candidate.lake_token,
                    "name_key": candidate.name_key,
                    "latitude": round(candidate.latitude, 6),
                    "longitude": round(candidate.longitude, 6),
                    "google_maps_url": _google_maps_url(
                        candidate.latitude, candidate.longitude
                    ),
                    "aggregate_rank": assessment.aggregate_rank,
                    "aggregate_score": assessment.aggregate_score,
                    "scenario_top20_presence_count": scenario_metric[
                        "scenario_top20_presence_count"
                    ],
                    "scenario_top20_labels": "; ".join(
                        scenario_metric["scenario_top20_labels"]
                    ),
                    "scenario_best_rank": scenario_metric["scenario_best_rank"],
                    "scenario_worst_rank": scenario_metric["scenario_worst_rank"],
                    "scenario_mean_rank": scenario_metric["scenario_mean_rank"],
                    "representative_source_record": candidate.representative_source_record,
                    "representative_source_layer_key": candidate.representative_source_layer_key,
                    "representative_source_name": candidate.representative_source_name,
                    "representative_source_url": candidate.representative_source_url,
                    "coordinate_resolution_method": candidate.coordinate_resolution_method,
                    "duplicate_name_count": candidate.duplicate_name_count,
                    "coordinate_spread_km": candidate.coordinate_spread_km,
                    "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                    "ambiguity_note": candidate.ambiguity_note,
                    "lake_registry_id": candidate.lake_registry_id,
                    "lake_registry_uuid": candidate.lake_registry_uuid,
                    "lake_water_identity": candidate.lake_water_identity,
                    "lake_name_status": candidate.lake_name_status,
                    "lake_area_km2": candidate.lake_area_km2,
                    "lake_sampling_posture": candidate.lake_sampling_posture,
                    "lake_sampling_fit": candidate.lake_sampling_fit,
                    "lake_sampling_notes": "; ".join(candidate.lake_sampling_notes),
                    "lake_sampling_readiness_posture": candidate.lake_sampling_readiness_posture,
                    "lake_sampling_missing_inputs": "; ".join(
                        candidate.lake_sampling_missing_inputs
                    ),
                    "pollen_sources": "; ".join(candidate.pollen_sources),
                    "supporting_pollen_names": "; ".join(
                        candidate.supporting_pollen_names
                    ),
                    "supporting_source_records": "; ".join(
                        candidate.supporting_source_records
                    ),
                    "supporting_source_points": "; ".join(
                        _render_source_point_cell(source_point)
                        for source_point in candidate.supporting_source_points
                    ),
                    "direct_pollen_temporal_evidence": _render_temporal_evidence_json(
                        candidate
                    ),
                    "temporal_context_evidence": _render_context_evidence_json(
                        candidate
                    ),
                    "direct_pollen_source_count": candidate.direct_pollen_source_count,
                    "direct_pollen_record_count": candidate.direct_pollen_record_count,
                    "time_aware_direct_pollen_records": candidate.time_aware_direct_pollen_records,
                    "direct_pollen_signal": candidate.direct_pollen_signal,
                }
            )


def write_lake_evidence_richness_scenario_csv(
    path: Path,
    report: LakeEvidenceRichnessReport,
) -> None:
    """Write one long-form ranking row per candidate and scenario."""
    fieldnames = (
        "scenario_key",
        "scenario_label",
        "radius_km",
        "rank",
        "score",
        "lake_name",
        "lake_label",
        "lake_token",
        "latitude",
        "longitude",
        "google_maps_url",
        "aggregate_rank",
        "aggregate_score",
        "scenario_top20_presence_count",
        "scenario_top20_labels",
        "lake_registry_id",
        "lake_name_status",
        "lake_area_km2",
        "lake_sampling_posture",
        "lake_sampling_fit",
        "lake_sampling_notes",
        "lake_sampling_readiness_posture",
        "lake_sampling_missing_inputs",
        "duplicate_name_count",
        "coordinate_spread_km",
        "ambiguity_flags",
        "ambiguity_note",
        "direct_pollen_temporal_evidence",
        "temporal_context_evidence",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in _scenario_rows(report):
            writer.writerow(row)


def _scenario_rows(report: LakeEvidenceRichnessReport) -> list[dict[str, object]]:
    scenario_metrics = _scenario_metric_map(report)
    rows: list[dict[str, object]] = []
    for assessment in report.assessments:
        candidate = assessment.candidate
        scenario_metric = scenario_metrics[candidate.lake_token]
        rows.append(
            {
                "scenario_key": "aggregate",
                "scenario_label": "Aggregate",
                "radius_km": "",
                "rank": assessment.aggregate_rank,
                "score": assessment.aggregate_score,
                "lake_name": candidate.lake_name,
                "lake_label": candidate.lake_label,
                "lake_token": candidate.lake_token,
                "latitude": round(candidate.latitude, 6),
                "longitude": round(candidate.longitude, 6),
                "google_maps_url": _google_maps_url(
                    candidate.latitude, candidate.longitude
                ),
                "aggregate_rank": assessment.aggregate_rank,
                "aggregate_score": assessment.aggregate_score,
                "scenario_top20_presence_count": scenario_metric[
                    "scenario_top20_presence_count"
                ],
                "scenario_top20_labels": "; ".join(
                    scenario_metric["scenario_top20_labels"]
                ),
                "lake_registry_id": candidate.lake_registry_id,
                "lake_name_status": candidate.lake_name_status,
                "lake_area_km2": candidate.lake_area_km2,
                "lake_sampling_posture": candidate.lake_sampling_posture,
                "lake_sampling_fit": candidate.lake_sampling_fit,
                "lake_sampling_notes": "; ".join(candidate.lake_sampling_notes),
                "lake_sampling_readiness_posture": candidate.lake_sampling_readiness_posture,
                "lake_sampling_missing_inputs": "; ".join(
                    candidate.lake_sampling_missing_inputs
                ),
                "duplicate_name_count": candidate.duplicate_name_count,
                "coordinate_spread_km": candidate.coordinate_spread_km,
                "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                "ambiguity_note": candidate.ambiguity_note,
                "direct_pollen_temporal_evidence": _render_temporal_evidence_json(
                    candidate
                ),
                "temporal_context_evidence": _render_context_evidence_json(candidate),
            }
        )
    for radius in report.radii_km:
        ordered = sorted(
            report.assessments,
            key=lambda assessment: _band_score(assessment, radius).band_rank,
        )
        for assessment in ordered:
            candidate = assessment.candidate
            band = _band_score(assessment, radius)
            scenario_metric = scenario_metrics[candidate.lake_token]
            rows.append(
                {
                    "scenario_key": f"radius_{radius}km",
                    "scenario_label": f"{radius} km",
                    "radius_km": radius,
                    "rank": band.band_rank,
                    "score": band.total_score,
                    "lake_name": candidate.lake_name,
                    "lake_label": candidate.lake_label,
                    "lake_token": candidate.lake_token,
                    "latitude": round(candidate.latitude, 6),
                    "longitude": round(candidate.longitude, 6),
                    "google_maps_url": _google_maps_url(
                        candidate.latitude, candidate.longitude
                    ),
                    "aggregate_rank": assessment.aggregate_rank,
                    "aggregate_score": assessment.aggregate_score,
                    "scenario_top20_presence_count": scenario_metric[
                        "scenario_top20_presence_count"
                    ],
                    "scenario_top20_labels": "; ".join(
                        scenario_metric["scenario_top20_labels"]
                    ),
                    "lake_registry_id": candidate.lake_registry_id,
                    "lake_name_status": candidate.lake_name_status,
                    "lake_area_km2": candidate.lake_area_km2,
                    "lake_sampling_posture": candidate.lake_sampling_posture,
                    "lake_sampling_fit": candidate.lake_sampling_fit,
                    "lake_sampling_notes": "; ".join(candidate.lake_sampling_notes),
                    "lake_sampling_readiness_posture": candidate.lake_sampling_readiness_posture,
                    "lake_sampling_missing_inputs": "; ".join(
                        candidate.lake_sampling_missing_inputs
                    ),
                    "duplicate_name_count": candidate.duplicate_name_count,
                    "coordinate_spread_km": candidate.coordinate_spread_km,
                    "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                    "ambiguity_note": candidate.ambiguity_note,
                    "direct_pollen_temporal_evidence": _render_temporal_evidence_json(
                        candidate
                    ),
                    "temporal_context_evidence": _render_context_evidence_json(
                        candidate
                    ),
                }
            )
    fieldwork_rank_map = _fieldwork_rank_map(report)
    for assessment in _fieldwork_rows(report):
        candidate = assessment.candidate
        scenario_metric = scenario_metrics[candidate.lake_token]
        rows.append(
            {
                "scenario_key": "fieldwork_shortlist",
                "scenario_label": "Fieldwork shortlist",
                "radius_km": "",
                "rank": fieldwork_rank_map[candidate.lake_token],
                "score": _fieldwork_shortlist_score(assessment),
                "lake_name": candidate.lake_name,
                "lake_label": candidate.lake_label,
                "lake_token": candidate.lake_token,
                "latitude": round(candidate.latitude, 6),
                "longitude": round(candidate.longitude, 6),
                "google_maps_url": _google_maps_url(
                    candidate.latitude, candidate.longitude
                ),
                "aggregate_rank": assessment.aggregate_rank,
                "aggregate_score": assessment.aggregate_score,
                "scenario_top20_presence_count": scenario_metric[
                    "scenario_top20_presence_count"
                ],
                "scenario_top20_labels": "; ".join(
                    scenario_metric["scenario_top20_labels"]
                ),
                "lake_registry_id": candidate.lake_registry_id,
                "lake_name_status": candidate.lake_name_status,
                "lake_area_km2": candidate.lake_area_km2,
                "lake_sampling_posture": candidate.lake_sampling_posture,
                "lake_sampling_fit": candidate.lake_sampling_fit,
                "lake_sampling_notes": "; ".join(candidate.lake_sampling_notes),
                "lake_sampling_readiness_posture": candidate.lake_sampling_readiness_posture,
                "lake_sampling_missing_inputs": "; ".join(
                    candidate.lake_sampling_missing_inputs
                ),
                "duplicate_name_count": candidate.duplicate_name_count,
                "coordinate_spread_km": candidate.coordinate_spread_km,
                "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                "ambiguity_note": candidate.ambiguity_note,
                "direct_pollen_temporal_evidence": _render_temporal_evidence_json(
                    candidate
                ),
                "temporal_context_evidence": _render_context_evidence_json(candidate),
            }
        )
    return rows
