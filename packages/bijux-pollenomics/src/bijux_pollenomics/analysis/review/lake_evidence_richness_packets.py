from __future__ import annotations

import csv
from dataclasses import replace
import json
from pathlib import Path
from statistics import mean

from ...reporting.context.points import build_external_point_layer
from ...reporting.map_document import render_multi_country_map_html
from ...reporting.map_publication import resolve_map_scope_policy
from ...reporting.rendering.artifacts import copy_map_assets
from ..lake_evidence_richness import LakeEvidenceRichnessReport

__all__ = [
    "build_lake_evidence_richness_geojson",
    "build_lake_evidence_richness_payload",
    "render_lake_evidence_richness_map_html",
    "render_lake_evidence_richness_markdown",
    "render_lake_evidence_richness_section",
    "write_lake_evidence_richness_band_csv",
    "write_lake_evidence_richness_geojson",
    "write_lake_evidence_richness_json",
    "write_lake_evidence_richness_map_html",
    "write_lake_evidence_richness_registry_csv",
    "write_lake_evidence_richness_scenario_csv",
]


def build_lake_evidence_richness_payload(
    report: LakeEvidenceRichnessReport,
) -> dict[str, object]:
    """Build the machine-readable lake evidence richness payload."""
    return report.as_dict()


def build_lake_evidence_richness_geojson(
    report: LakeEvidenceRichnessReport,
) -> dict[str, object]:
    """Build one GeoJSON feature collection for all Sweden lake candidates."""
    return {
        "type": "FeatureCollection",
        "features": [
            _build_candidate_feature(assessment) for assessment in report.assessments
        ],
    }


def write_lake_evidence_richness_json(
    path: Path,
    report: LakeEvidenceRichnessReport,
) -> None:
    """Write one JSON payload describing Sweden lake evidence richness."""
    path.write_text(
        json.dumps(build_lake_evidence_richness_payload(report), indent=2),
        encoding="utf-8",
    )


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
        "supporting_source_records",
        "supporting_source_points",
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
                        "lake_sampling_notes": "; ".join(
                            candidate.lake_sampling_notes
                        ),
                        "supporting_source_records": "; ".join(
                            candidate.supporting_source_records
                        ),
                        "supporting_source_points": "; ".join(
                            _render_source_point_cell(source_point)
                            for source_point in candidate.supporting_source_points
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
        "pollen_sources",
        "supporting_pollen_names",
        "supporting_source_records",
        "supporting_source_points",
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
        "duplicate_name_count",
        "coordinate_spread_km",
        "ambiguity_flags",
        "ambiguity_note",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in _scenario_rows(report):
            writer.writerow(row)


def write_lake_evidence_richness_geojson(
    path: Path,
    report: LakeEvidenceRichnessReport,
) -> None:
    """Write one GeoJSON feature collection for Sweden lake candidates."""
    path.write_text(
        json.dumps(build_lake_evidence_richness_geojson(report), indent=2),
        encoding="utf-8",
    )


def write_lake_evidence_richness_map_html(
    path: Path,
    report: LakeEvidenceRichnessReport,
    *,
    version: str,
    generated_on: str,
) -> None:
    """Write one standalone map for the Sweden lake ranking scenarios."""
    copy_map_assets(path.parent)
    path.write_text(
        render_lake_evidence_richness_map_html(
            report,
            version=version,
            generated_on=generated_on,
        ),
        encoding="utf-8",
    )


def render_lake_evidence_richness_markdown(
    report: LakeEvidenceRichnessReport,
) -> str:
    """Render the Sweden lake evidence richness report as markdown."""
    scenario_metrics = _scenario_metric_map(report)
    registry_backed = _is_registry_backed_report(report)
    overall_rows = (
        "\n".join(
            (
                f"| {assessment.aggregate_rank} | {assessment.candidate.lake_label} | "
                f"{_render_coordinate_link(assessment.candidate.latitude, assessment.candidate.longitude)} | "
                f"{_render_lake_identity_cell(assessment.candidate.lake_registry_id)} | "
                f"{assessment.candidate.lake_name_status or 'not_available'} | "
                f"{assessment.aggregate_score:.4f} | "
                f"{scenario_metrics[assessment.candidate.lake_token]['scenario_top20_presence_count']}/"
                f"{scenario_metrics[assessment.candidate.lake_token]['scenario_count']} | "
                f"{_render_ambiguity_cell(assessment.candidate.ambiguity_flags)} | "
                f"{', '.join(assessment.candidate.pollen_sources) or 'none'} | "
                f"{_band_score(assessment, 20).human_adna_locality_count} | "
                f"{_band_score(assessment, 20).sead_site_count} | "
                f"{_band_score(assessment, 50).domesticated_animal_locality_count} |"
            )
            for assessment in report.assessments[:20]
        )
        or "| - | No lake candidates | - | not_available | not_available | 0.0000 | 0/0 | - | - | 0 | 0 | 0 |"
    )
    consensus_section = _render_consensus_table(report)
    fieldwork_section = _render_fieldwork_shortlist_table(report)
    band_sections = "\n\n".join(
        _render_band_table(report, radius_km=radius) for radius in report.radii_km
    )
    return f"""# Sweden lake evidence richness

This report ranks Sweden lake candidates by the richness of tracked pollen, archaeology, human aDNA, and domesticated-animal aDNA evidence around each lake. The ranking keeps lake identity diagnostics visible so duplicate names and registry naming cautions are not hidden inside one synthetic lake label.

{_lake_ranking_summary_paragraph(registry_backed)}

## Methodology

- Candidate derivation: {report.methodology["candidate_derivation"]}
- Distance bands: {", ".join(f"{radius} km" for radius in report.radii_km)}
- Identity diagnostics: {_render_identity_methodology(report)}
- Coordinate targeting: {_render_coordinate_targeting(report)}
- Human aDNA weighting: {_render_human_weighting(report)}
- Ranking decision rule: {_render_ranking_decision_rule(report)}
- Temporal alignment rule: {_render_temporal_alignment_rule(report)}
- Sampling note: {_render_optional_methodology_note(report, "sampling_note")}
- Archaeology note: {report.methodology["archaeology_note"]}
- Pollen note: {_render_optional_methodology_note(report, "pollen_note")}
- Animal note: {report.methodology["animal_note"]}

## Aggregate Ranking

| Rank | Lake | Coordinates | Lake registry id | Name status | Aggregate score | Top-20 scenario presence | Identity diagnostics | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
{overall_rows}

{consensus_section}

{fieldwork_section}

{band_sections}
"""


def render_lake_evidence_richness_map_html(
    report: LakeEvidenceRichnessReport,
    *,
    version: str,
    generated_on: str,
) -> str:
    """Render a standalone interactive map for Sweden lake ranking scenarios."""
    if not report.assessments:
        return _render_empty_lake_map_html(version=version, generated_on=generated_on)
    base_policy = resolve_map_scope_policy(None)
    minimum_bounds = _lake_bounds(report)
    policy = replace(
        base_policy,
        label="Sweden Lake Evidence",
        eyebrow_label="Sweden Lake Evidence",
        summary=(
            "This map highlights Sweden lake candidates ranked by surrounding pollen, "
            "archaeology, human aDNA, and domesticated-animal aDNA evidence."
        ),
        bounds_summary=(
            "The opening extent follows the Sweden candidate registry rather than the "
            "broader Nordic map scope so ranking differences stay legible."
        ),
        minimum_bounds=minimum_bounds,
    )
    point_layers = [
        build_external_point_layer(_build_scenario_feature_collection(report, scenario))
        for scenario in _map_scenarios(report)
    ]
    return render_multi_country_map_html(
        title="Sweden lake evidence richness",
        version=version,
        generated_on=generated_on,
        countries=("Sweden",),
        policy=policy,
        point_layers=point_layers,
        polygon_layers=[],
        asset_base_path="./_map_assets",
    )


def render_lake_evidence_richness_section(
    *,
    json_name: str,
    band_csv_name: str,
    registry_csv_name: str,
    scenario_csv_name: str,
    geojson_name: str,
    map_html_name: str,
    markdown_name: str,
) -> str:
    """Render the README section that links the Sweden lake evidence richness outputs."""
    return f"""

## Lake Evidence Richness

- Sweden lake evidence richness JSON: [`{json_name}`](./{json_name})
- Sweden lake evidence registry CSV: [`{registry_csv_name}`](./{registry_csv_name})
- Sweden lake evidence scenario CSV: [`{scenario_csv_name}`](./{scenario_csv_name})
- Sweden lake evidence distance-band CSV: [`{band_csv_name}`](./{band_csv_name})
- Sweden lake evidence GeoJSON: [`{geojson_name}`](./{geojson_name})
- Sweden lake evidence map: [`{map_html_name}`](./{map_html_name})
- Sweden lake evidence markdown: [`{markdown_name}`](./{markdown_name})
"""


def _render_band_table(report: LakeEvidenceRichnessReport, *, radius_km: int) -> str:
    ordered = sorted(
        report.assessments,
        key=lambda assessment: _band_score(assessment, radius_km).band_rank,
    )[:20]
    rows = (
        "\n".join(
            (
                f"| {_band_score(assessment, radius_km).band_rank} | "
                f"{assessment.candidate.lake_label} | "
                f"{_render_coordinate_link(assessment.candidate.latitude, assessment.candidate.longitude)} | "
                f"{_band_score(assessment, radius_km).total_score:.4f} | "
                f"{_render_ambiguity_cell(assessment.candidate.ambiguity_flags)} | "
                f"{_band_score(assessment, radius_km).human_adna_locality_count} | "
                f"{_band_score(assessment, radius_km).human_adna_sample_count} | "
                f"{_band_score(assessment, radius_km).domesticated_animal_locality_count} | "
                f"{_band_score(assessment, radius_km).sead_site_count} | "
                f"{_band_score(assessment, radius_km).raa_density_site_count} | "
                f"{_band_score(assessment, radius_km).nearby_pollen_lake_count} | "
                f"{_band_score(assessment, radius_km).evidence_family_count} |"
            )
            for assessment in ordered
        )
        or "| - | No lake candidates | - | 0.0000 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 |"
    )
    return f"""## {radius_km} km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{rows}"""


def _band_score(assessment, radius_km: int):
    for score in assessment.band_scores:
        if score.radius_km == radius_km:
            return score
    raise ValueError(f"Missing band score for radius {radius_km}")


def _render_ambiguity_cell(flags: tuple[str, ...]) -> str:
    return ", ".join(flags) if flags else "none"


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
                "duplicate_name_count": candidate.duplicate_name_count,
                "coordinate_spread_km": candidate.coordinate_spread_km,
                "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                "ambiguity_note": candidate.ambiguity_note,
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
                    "duplicate_name_count": candidate.duplicate_name_count,
                    "coordinate_spread_km": candidate.coordinate_spread_km,
                    "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                    "ambiguity_note": candidate.ambiguity_note,
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
                "duplicate_name_count": candidate.duplicate_name_count,
                "coordinate_spread_km": candidate.coordinate_spread_km,
                "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                "ambiguity_note": candidate.ambiguity_note,
            }
        )
    return rows


def _build_candidate_feature(assessment) -> dict[str, object]:
    candidate = assessment.candidate
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [candidate.longitude, candidate.latitude],
        },
        "properties": {
            "source": "bijux-pollenomics",
            "layer_key": "lake-evidence-candidates",
            "layer_label": "Sweden lake evidence candidates",
            "category": "Lake evidence candidate",
            "country": "Sweden",
            "record_id": candidate.lake_token,
            "name": candidate.lake_label,
            "geometry_type": "Point",
            "subtitle": "Sweden lake evidence candidate",
            "description": candidate.ambiguity_note
            or _candidate_description(candidate),
            "source_url": candidate.representative_source_url,
            "record_count": 1,
            "media_links": _candidate_media_links(candidate),
            "popup_rows": _candidate_popup_rows(assessment),
        },
    }


def _candidate_popup_rows(assessment) -> list[dict[str, str]]:
    candidate = assessment.candidate
    return [
        {"label": "Aggregate rank", "value": str(assessment.aggregate_rank)},
        {"label": "Aggregate score", "value": f"{assessment.aggregate_score:.4f}"},
        {
            "label": "Coordinates",
            "value": f"{candidate.latitude:.6f}, {candidate.longitude:.6f}",
        },
        {
            "label": "Coordinate method",
            "value": candidate.coordinate_resolution_method,
        },
        {
            "label": "Representative source",
            "value": (
                f"{candidate.representative_source_record} "
                f"({candidate.representative_source_name})"
            ),
        },
        {
            "label": "Lake registry id",
            "value": candidate.lake_registry_id or "Not available",
        },
        {
            "label": "Lake name status",
            "value": candidate.lake_name_status or "Not available",
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
            "value": candidate.lake_sampling_posture or "Not available",
        },
        {
            "label": "Sampling fit",
            "value": f"{candidate.lake_sampling_fit:.4f}",
        },
        {
            "label": "Pollen sources",
            "value": ", ".join(candidate.pollen_sources) or "None",
        },
        {
            "label": "Direct pollen with numeric chronology",
            "value": str(candidate.time_aware_direct_pollen_records),
        },
        {
            "label": "20 km pollen with numeric chronology",
            "value": str(_band_score(assessment, 20).time_aware_pollen_site_count),
        },
        {
            "label": "20 km pollen overlapping nearby human chronology",
            "value": str(_band_score(assessment, 20).human_overlap_pollen_site_count),
        },
        {
            "label": "20 km SEAD with numeric chronology",
            "value": str(_band_score(assessment, 20).time_aware_sead_site_count),
        },
        {
            "label": "20 km SEAD overlapping nearby human chronology",
            "value": str(_band_score(assessment, 20).human_overlap_sead_site_count),
        },
        {
            "label": "Duplicate Sweden names",
            "value": str(candidate.duplicate_name_count),
        },
        {
            "label": "Coordinate spread",
            "value": f"{candidate.coordinate_spread_km:.2f} km",
        },
        {
            "label": "Identity diagnostics",
            "value": _render_ambiguity_cell(candidate.ambiguity_flags),
        },
        {
            "label": "Identity note",
            "value": candidate.ambiguity_note or "No explicit identity warning.",
        },
    ]


def _map_scenarios(report: LakeEvidenceRichnessReport) -> list[dict[str, object]]:
    scenario_metrics = _scenario_metric_map(report)
    scenarios: list[dict[str, object]] = [
        {
            "key": "lake-evidence-aggregate",
            "label": "Aggregate top 20",
            "rows": sorted(report.assessments, key=lambda item: item.aggregate_rank)[
                :20
            ],
            "rank_getter": lambda assessment: assessment.aggregate_rank,
            "score_getter": lambda assessment: assessment.aggregate_score,
            "scenario_label": "Aggregate",
        }
    ]
    consensus_rows = _consensus_rows(report)[:20]
    scenarios.append(
        {
            "key": "lake-evidence-consensus",
            "label": "Consensus top 20",
            "rows": consensus_rows,
            "rank_getter": lambda assessment, rows=consensus_rows: (
                rows.index(assessment) + 1
            ),
            "score_getter": lambda assessment, metrics=scenario_metrics: metrics[
                assessment.candidate.lake_token
            ]["scenario_top20_presence_count"],
            "scenario_label": "Consensus",
        }
    )
    fieldwork_rows = _fieldwork_rows(report)
    fieldwork_rank_map = _fieldwork_rank_map(report)
    scenarios.append(
        {
            "key": "lake-evidence-fieldwork",
            "label": "Fieldwork shortlist",
            "rows": fieldwork_rows,
            "rank_getter": lambda assessment, rank_map=fieldwork_rank_map: rank_map[
                assessment.candidate.lake_token
            ],
            "score_getter": lambda assessment: _fieldwork_shortlist_score(assessment),
            "scenario_label": "Fieldwork shortlist",
        }
    )
    for radius in report.radii_km:
        scenarios.append(
            {
                "key": f"lake-evidence-{radius}km",
                "label": f"{radius} km top 20",
                "rows": sorted(
                    report.assessments,
                    key=lambda item: _band_score(item, radius).band_rank,
                )[:20],
                "rank_getter": lambda assessment, radius=radius: (
                    _band_score(assessment, radius).band_rank
                ),
                "score_getter": lambda assessment, radius=radius: (
                    _band_score(assessment, radius).total_score
                ),
                "scenario_label": f"{radius} km",
            }
        )
    return scenarios


def _build_scenario_feature_collection(
    report: LakeEvidenceRichnessReport,
    scenario: dict[str, object],
) -> dict[str, object]:
    features = []
    rows = scenario["rows"]
    rank_getter = scenario["rank_getter"]
    score_getter = scenario["score_getter"]
    for assessment in rows:  # type: ignore[assignment]
        candidate = assessment.candidate
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
                    "record_id": candidate.lake_token,
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
                            "label": "Identity diagnostics",
                            "value": _render_ambiguity_cell(candidate.ambiguity_flags),
                        },
                        {
                            "label": "Identity note",
                            "value": candidate.ambiguity_note
                            or "No explicit identity warning.",
                        },
                    ],
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


def _google_maps_url(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={latitude:.6f},{longitude:.6f}"


def _render_coordinate_link(latitude: float, longitude: float) -> str:
    label = f"{latitude:.6f}, {longitude:.6f}"
    return f"[{label}]({_google_maps_url(latitude, longitude)})"


def _render_source_point_cell(source_point) -> str:
    return (
        f"{source_point.source_name} "
        f"({source_point.source_layer_key}; "
        f"{source_point.latitude:.6f}, {source_point.longitude:.6f})"
    )


def _render_lake_area(candidate) -> str:
    if candidate.lake_area_km2 is None:
        return "Not available"
    return f"{candidate.lake_area_km2:.3f}"


def _candidate_description(candidate) -> str:
    if candidate.representative_source_record.startswith("svar-lakes:"):
        return "Lake candidate anchored to the official Sweden lake registry."
    return "Lake candidate derived from Sweden pollen context."


def _is_registry_backed_report(report: LakeEvidenceRichnessReport) -> bool:
    methods = report.methodology.get("identity_diagnostics", {}).get(
        "coordinate_resolution_methods", []
    )
    if not isinstance(methods, list):
        return False
    return "svar_polygon_representative_point" in methods


def _lake_ranking_summary_paragraph(registry_backed: bool) -> str:
    if registry_backed:
        return (
            "Coordinates resolve to representative points drawn from official "
            "SMHI SVAR lake polygons, so map checks land on the lake itself "
            "rather than on a synthetic centroid or on one supporting pollen record."
        )
    return (
        "Coordinates resolve to one representative source-backed point per lake "
        "candidate so map checks land on a published source point rather than a "
        "synthetic centroid."
    )


def _render_identity_methodology(report: LakeEvidenceRichnessReport) -> str:
    diagnostics = report.methodology.get("identity_diagnostics", {})
    if _is_registry_backed_report(report):
        return (
            "duplicate Sweden lake names stay explicit, and registry names that do not "
            "come from the official register field remain flagged for review"
        )
    return (
        f"cleaned-name matching within {diagnostics['name_match_distance_km']} km, "
        f"coordinate-spread flag at {diagnostics['coordinate_spread_flag_km']} km, "
        "and explicit source-position notes when raw source notes say the lake "
        "position is uncertain"
    )


def _render_coordinate_targeting(report: LakeEvidenceRichnessReport) -> str:
    if _is_registry_backed_report(report):
        return (
            "each lake keeps one representative point derived from the official "
            "lake polygon, with registry identifiers and name status carried into "
            "the CSV, JSON, and map popups"
        )
    return (
        "each lake keeps one representative source-backed point chosen from its "
        "supporting pollen records using the method recorded in the registry CSV "
        "and JSON payload"
    )


def _render_human_weighting(report: LakeEvidenceRichnessReport) -> str:
    score_components = report.methodology.get("score_components", {})
    if (
        "human_adna_signal" in score_components
        and "direct_pollen_signal" in score_components
        and "nearby_pollen_signal" in score_components
    ):
        return (
            f"human aDNA contributes {score_components['human_adna_signal']:.2f} of each "
            f"band score, direct pollen contributes {score_components['direct_pollen_signal']:.2f}, "
            f"nearby pollen contributes {score_components['nearby_pollen_signal']:.2f}, "
            f"and archaeology contributes {score_components['archaeology_signal']:.2f}"
        )
    return "human aDNA is balanced with pollen and archaeology rather than acting as the decisive term"


def _render_ranking_decision_rule(report: LakeEvidenceRichnessReport) -> str:
    rule = report.methodology.get("ranking_decision_rule")
    if isinstance(rule, str) and rule:
        return rule
    return (
        "aggregate and band ranks use one blended score without an explicit "
        "decision chain"
    )


def _render_temporal_alignment_rule(report: LakeEvidenceRichnessReport) -> str:
    rule = report.methodology.get("temporal_alignment_rule")
    if isinstance(rule, str) and rule:
        return rule
    return (
        "time-aware chronology remains visible where available, but the ranking does "
        "not currently promote chronology overlap as a separate rule"
    )


def _render_optional_methodology_note(
    report: LakeEvidenceRichnessReport,
    key: str,
) -> str:
    value = report.methodology.get(key)
    if isinstance(value, str) and value:
        return value
    if key == "pollen_note":
        return (
            "Direct pollen signal reflects the quality of the lake-linked pollen "
            "records rather than a synthetic lake average."
        )
    return ""


def _candidate_media_links(candidate) -> list[dict[str, str]]:
    links = [
        {
            "label": "Open in Google Maps",
            "url": _google_maps_url(candidate.latitude, candidate.longitude),
            "kind": "link",
        }
    ]
    if candidate.representative_source_url:
        links.append(
            {
                "label": "Open representative source",
                "url": candidate.representative_source_url,
                "kind": "link",
            }
        )
    return links


def _scenario_metric_map(
    report: LakeEvidenceRichnessReport,
) -> dict[str, dict[str, object]]:
    scenario_orders: list[tuple[str, list]] = [
        ("aggregate", sorted(report.assessments, key=lambda item: item.aggregate_rank))
    ]
    scenario_orders.append(("fieldwork shortlist", _fieldwork_rows(report)))
    for radius in report.radii_km:
        scenario_orders.append(
            (
                f"{radius} km",
                sorted(
                    report.assessments,
                    key=lambda item: _band_score(item, radius).band_rank,
                ),
            )
        )
    metrics: dict[str, dict[str, object]] = {}
    for assessment in report.assessments:
        ranks: list[int] = []
        top20_labels: list[str] = []
        for label, ordered in scenario_orders:
            for rank, candidate_assessment in enumerate(ordered, start=1):
                if (
                    candidate_assessment.candidate.lake_token
                    != assessment.candidate.lake_token
                ):
                    continue
                ranks.append(rank)
                if rank <= 20:
                    top20_labels.append(label)
                break
        metrics[assessment.candidate.lake_token] = {
            "scenario_count": len(scenario_orders),
            "scenario_top20_presence_count": len(top20_labels),
            "scenario_top20_labels": tuple(top20_labels),
            "scenario_best_rank": min(ranks) if ranks else None,
            "scenario_worst_rank": max(ranks) if ranks else None,
            "scenario_mean_rank": round(mean(ranks), 2) if ranks else None,
        }
    return metrics


def _fieldwork_rows(report: LakeEvidenceRichnessReport) -> list:
    return sorted(
        report.assessments,
        key=lambda assessment: (
            _sampling_priority_rank(
                assessment.candidate.lake_sampling_posture or "sampling_not_scored"
            ),
            -_fieldwork_shortlist_score(assessment),
            assessment.aggregate_rank,
            assessment.candidate.lake_label,
        ),
    )[:20]


def _fieldwork_rank_map(report: LakeEvidenceRichnessReport) -> dict[str, int]:
    return {
        assessment.candidate.lake_token: rank
        for rank, assessment in enumerate(_fieldwork_rows(report), start=1)
    }


def _fieldwork_shortlist_score(assessment) -> float:
    candidate = assessment.candidate
    band_20 = _band_score(assessment, 20)
    posture_bonus = {
        "sampling_lake_candidate": 0.05,
        "compact_lake_candidate": 0.0,
        "small_lake_review": -0.08,
    }.get(candidate.lake_sampling_posture, -0.02)
    return round(
        assessment.aggregate_score * 0.62
        + candidate.lake_sampling_fit * 0.23
        + min(1.0, candidate.direct_pollen_source_count / 2.0) * 0.1
        + min(1.0, band_20.evidence_family_count / 4.0) * 0.05
        + posture_bonus,
        4,
    )


def _sampling_priority_rank(sampling_posture: str) -> int:
    return {
        "sampling_lake_candidate": 0,
        "compact_lake_candidate": 1,
        "small_lake_review": 2,
        "sampling_not_scored": 3,
    }.get(sampling_posture, 4)


def _consensus_rows(report: LakeEvidenceRichnessReport) -> list:
    scenario_metrics = _scenario_metric_map(report)
    return sorted(
        report.assessments,
        key=lambda assessment: (
            -int(
                scenario_metrics[assessment.candidate.lake_token][
                    "scenario_top20_presence_count"
                ]
            ),
            float(
                scenario_metrics[assessment.candidate.lake_token]["scenario_mean_rank"]
                or 10_000
            ),
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
                f"{assessment.candidate.lake_sampling_fit:.4f} | "
                f"{_render_lake_area(assessment.candidate)} | "
                f"{_band_score(assessment, 20).human_adna_locality_count} | "
                f"{_band_score(assessment, 20).evidence_family_count} |"
            )
            for assessment in _fieldwork_rows(report)
        )
        or "| - | No lake candidates | - | not_available | not_available | 0.0000 | - | 0.0000 | - | 0 | 0 |"
    )
    return f"""## Fieldwork Shortlist

| Fieldwork rank | Lake | Coordinates | Lake registry id | Name status | Shortlist score | Sampling posture | Sampling fit | Area km² | Human localities within 20 km | Evidence families within 20 km |
| ---: | --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
{rows}"""


def _render_lake_identity_cell(lake_registry_id: str) -> str:
    return lake_registry_id or "not_available"


def _render_empty_lake_map_html(*, version: str, generated_on: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sweden lake evidence richness</title>
  <style>
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, sans-serif;
      background: #f8fafc;
      color: #0f172a;
      display: grid;
      min-height: 100vh;
      place-items: center;
    }}
    main {{
      max-width: 42rem;
      padding: 2rem;
      background: white;
      border: 1px solid #cbd5e1;
      border-radius: 1rem;
      box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
    }}
    h1 {{
      margin-top: 0;
    }}
    p {{
      line-height: 1.6;
    }}
    .meta {{
      color: #475569;
      font-size: 0.95rem;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Sweden lake evidence richness</h1>
    <p>No Sweden lake candidates were available for this bundle because the required pollen context files were missing or did not produce any lake-basin candidates.</p>
    <p class="meta">Version {version} · generated {generated_on}</p>
  </main>
</body>
</html>
"""
