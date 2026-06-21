from __future__ import annotations

import csv
from dataclasses import replace
import json
from pathlib import Path

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
            _build_candidate_feature(assessment)
            for assessment in report.assessments
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
    fieldnames = (
        "lake_name",
        "lake_label",
        "lake_token",
        "name_key",
        "latitude",
        "longitude",
        "duplicate_name_count",
        "coordinate_spread_km",
        "ambiguity_flags",
        "ambiguity_note",
        "supporting_source_records",
        "aggregate_rank",
        "aggregate_score",
        "direct_pollen_signal",
        "direct_pollen_source_count",
        "direct_pollen_record_count",
        "time_aware_direct_pollen_records",
        "band_radius_km",
        "band_rank",
        "band_score",
        "nearby_pollen_lake_count",
        "human_adna_locality_count",
        "human_adna_sample_count",
        "domesticated_animal_locality_count",
        "domesticated_animal_sample_count",
        "sead_site_count",
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
            for band in assessment.band_scores:
                writer.writerow(
                    {
                        "lake_name": candidate.lake_name,
                        "lake_label": candidate.lake_label,
                        "lake_token": candidate.lake_token,
                        "name_key": candidate.name_key,
                        "latitude": round(candidate.latitude, 6),
                        "longitude": round(candidate.longitude, 6),
                        "duplicate_name_count": candidate.duplicate_name_count,
                        "coordinate_spread_km": candidate.coordinate_spread_km,
                        "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                        "ambiguity_note": candidate.ambiguity_note,
                        "supporting_source_records": "; ".join(
                            candidate.supporting_source_records
                        ),
                        "aggregate_rank": assessment.aggregate_rank,
                        "aggregate_score": assessment.aggregate_score,
                        "direct_pollen_signal": candidate.direct_pollen_signal,
                        "direct_pollen_source_count": candidate.direct_pollen_source_count,
                        "direct_pollen_record_count": candidate.direct_pollen_record_count,
                        "time_aware_direct_pollen_records": candidate.time_aware_direct_pollen_records,
                        "band_radius_km": band.radius_km,
                        "band_rank": band.band_rank,
                        "band_score": band.total_score,
                        "nearby_pollen_lake_count": band.nearby_pollen_lake_count,
                        "human_adna_locality_count": band.human_adna_locality_count,
                        "human_adna_sample_count": band.human_adna_sample_count,
                        "domesticated_animal_locality_count": band.domesticated_animal_locality_count,
                        "domesticated_animal_sample_count": band.domesticated_animal_sample_count,
                        "sead_site_count": band.sead_site_count,
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
    fieldnames = (
        "lake_name",
        "lake_label",
        "lake_token",
        "name_key",
        "latitude",
        "longitude",
        "aggregate_rank",
        "aggregate_score",
        "duplicate_name_count",
        "coordinate_spread_km",
        "ambiguity_flags",
        "ambiguity_note",
        "pollen_sources",
        "supporting_pollen_names",
        "supporting_source_records",
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
            writer.writerow(
                {
                    "lake_name": candidate.lake_name,
                    "lake_label": candidate.lake_label,
                    "lake_token": candidate.lake_token,
                    "name_key": candidate.name_key,
                    "latitude": round(candidate.latitude, 6),
                    "longitude": round(candidate.longitude, 6),
                    "aggregate_rank": assessment.aggregate_rank,
                    "aggregate_score": assessment.aggregate_score,
                    "duplicate_name_count": candidate.duplicate_name_count,
                    "coordinate_spread_km": candidate.coordinate_spread_km,
                    "ambiguity_flags": "; ".join(candidate.ambiguity_flags),
                    "ambiguity_note": candidate.ambiguity_note,
                    "pollen_sources": "; ".join(candidate.pollen_sources),
                    "supporting_pollen_names": "; ".join(
                        candidate.supporting_pollen_names
                    ),
                    "supporting_source_records": "; ".join(
                        candidate.supporting_source_records
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
        "aggregate_rank",
        "aggregate_score",
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
    overall_rows = "\n".join(
        (
            f"| {assessment.aggregate_rank} | {assessment.candidate.lake_label} | "
            f"{assessment.candidate.latitude:.4f}, {assessment.candidate.longitude:.4f} | "
            f"{assessment.aggregate_score:.4f} | "
            f"{_render_ambiguity_cell(assessment.candidate.ambiguity_flags)} | "
            f"{', '.join(assessment.candidate.pollen_sources)} | "
            f"{_band_score(assessment, 20).human_adna_locality_count} | "
            f"{_band_score(assessment, 20).sead_site_count} | "
            f"{_band_score(assessment, 50).domesticated_animal_locality_count} |"
        )
        for assessment in report.assessments[:20]
    ) or "| - | No lake candidates | - | 0.0000 | - | - | 0 | 0 | 0 |"
    band_sections = "\n\n".join(
        _render_band_table(report, radius_km=radius) for radius in report.radii_km
    )
    return f"""# Sweden lake evidence richness

This report ranks Sweden lake candidates by the richness of tracked pollen, archaeology, human aDNA, and domesticated-animal aDNA evidence around each lake. The ranking now keeps lake identity diagnostics visible so duplicate names, source coordinate spread, and explicit source-position warnings are not hidden inside one synthetic lake label.

## Methodology

- Candidate derivation: {report.methodology["candidate_derivation"]}
- Distance bands: {", ".join(f"{radius} km" for radius in report.radii_km)}
- Identity diagnostics: cleaned-name matching within {report.methodology["identity_diagnostics"]["name_match_distance_km"]} km, coordinate-spread flag at {report.methodology["identity_diagnostics"]["coordinate_spread_flag_km"]} km, and explicit source-position notes when raw source notes say the lake position is uncertain.
- Archaeology note: {report.methodology["archaeology_note"]}
- Animal note: {report.methodology["animal_note"]}

## Aggregate Ranking

| Rank | Lake | Coordinates | Aggregate score | Identity diagnostics | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: | ---: |
{overall_rows}

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
    rows = "\n".join(
        (
            f"| {_band_score(assessment, radius_km).band_rank} | "
            f"{assessment.candidate.lake_label} | "
            f"{assessment.candidate.latitude:.4f}, {assessment.candidate.longitude:.4f} | "
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
    ) or "| - | No lake candidates | - | 0.0000 | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 |"
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
    rows: list[dict[str, object]] = []
    for assessment in report.assessments:
        candidate = assessment.candidate
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
                "aggregate_rank": assessment.aggregate_rank,
                "aggregate_score": assessment.aggregate_score,
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
                    "aggregate_rank": assessment.aggregate_rank,
                    "aggregate_score": assessment.aggregate_score,
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
            or "Lake candidate derived from Sweden pollen context.",
            "source_url": "",
            "record_count": 1,
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
            "value": f"{candidate.latitude:.4f}, {candidate.longitude:.4f}",
        },
        {
            "label": "Pollen sources",
            "value": ", ".join(candidate.pollen_sources) or "None",
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
    scenarios: list[dict[str, object]] = [
        {
            "key": "lake-evidence-aggregate",
            "label": "Aggregate top 20",
            "rows": sorted(report.assessments, key=lambda item: item.aggregate_rank)[:20],
            "rank_getter": lambda assessment: assessment.aggregate_rank,
            "score_getter": lambda assessment: assessment.aggregate_score,
            "scenario_label": "Aggregate",
        }
    ]
    for radius in report.radii_km:
        scenarios.append(
            {
                "key": f"lake-evidence-{radius}km",
                "label": f"{radius} km top 20",
                "rows": sorted(
                    report.assessments,
                    key=lambda item: _band_score(item, radius).band_rank,
                )[:20],
                "rank_getter": lambda assessment, radius=radius: _band_score(
                    assessment, radius
                ).band_rank,
                "score_getter": lambda assessment, radius=radius: _band_score(
                    assessment, radius
                ).total_score,
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
                    or "Lake candidate ranked for the active scenario.",
                    "source_url": "",
                    "record_count": 1,
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
