from __future__ import annotations

from dataclasses import replace
from collections.abc import Mapping
from pathlib import Path

from bijux_pollenomics.reporting.context.points import build_external_point_layer
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy
from bijux_pollenomics.reporting.rendering.artifacts import copy_map_assets
from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessReport,
)

from ..lake_fieldwork_priority import band_score as _band_score

from .methodology import (
    _is_registry_backed_report,
    _lake_ranking_summary_paragraph,
    _render_coordinate_targeting,
    _render_human_weighting,
    _render_identity_methodology,
    _render_optional_methodology_note,
    _render_ranking_decision_rule,
    _render_source_temporal_coverage,
    _render_temporal_alignment_rule,
    _render_temporal_navigation,
)

from .presentation import (
    _render_ambiguity_cell,
    _render_coordinate_link,
)

from .ranking_tables import (
    _render_consensus_table,
    _render_fieldwork_shortlist_table,
    _render_lake_identity_cell,
)

from .scenario_features import (
    _build_scenario_feature_collection,
    _lake_bounds,
    _map_scenarios,
)
from .scenario_metrics import scenario_metric_map as _scenario_metric_map


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
    if report.methodology.get("availability_status") == "blocked":
        return _render_blocked_lake_evidence_richness(report)
    scenario_metrics = _scenario_metric_map(report)
    registry_backed = _is_registry_backed_report(report)
    sampling_note = _render_optional_methodology_note(report, "sampling_note")
    sampling_note_row = f"- Sampling note: {sampling_note}" if sampling_note else ""
    temporal_navigation = _render_temporal_navigation(report)
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
- Time-navigation coverage: {temporal_navigation}
- Source temporal coverage: {_render_source_temporal_coverage(report)}
{sampling_note_row}
- Archaeology note: {report.methodology["archaeology_note"]}
- Pollen note: {_render_optional_methodology_note(report, "pollen_note")}
- Animal note: {report.methodology["animal_note"]}

## Interpretation guardrails

- Human aDNA remains the gatekeeper layer: lakes without at least one nearby human locality inside 50 km do not stay in the ranked candidate set.
- Spatial context is not the same as chronology support: source layers with zero numeric intervals remain visible for surrounding evidence density, but they do not contribute chronology-overlap strength.
- Nearby time context is not lake chronology: map windows summarize numeric pollen, SEAD, or aDNA records within 50 km and label that role explicitly. Direct lake pollen chronology remains a separate field in the CSV and JSON.
- Partial chronology remains explicit: Neotoma records with BP intervals can strengthen time-aware comparisons, while unresolved or label-only records stay visible without being promoted to same-period evidence.

## Aggregate Ranking

| Rank | Lake | Coordinates | Lake registry id | Name status | Aggregate score | Top-20 scenario presence | Identity diagnostics | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
{overall_rows}

{consensus_section}

{fieldwork_section}

{band_sections}
"""


def _render_blocked_lake_evidence_richness(
    report: LakeEvidenceRichnessReport,
) -> str:
    methodology = report.methodology
    return f"""# Sweden lake evidence richness

The lake-ranking surface is blocked and contains `{report.candidate_count}` admitted candidates.

- Availability status: `{methodology.get("availability_status", "blocked")}`
- Refusal reason: `{methodology.get("refusal_reason", "not recorded")}`
- Governing surface: `{methodology.get("governing_surface", "not recorded")}`
- Candidate derivation: {methodology.get("candidate_derivation", "Not recorded.")}

No derived review subset is promoted to a scientific ranking while its governing registry is unavailable.
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
            "archaeology, human aDNA, and domesticated-animal aDNA evidence. Time "
            "navigation uses explicitly labeled nearby context windows and does not "
            "present them as chronology measured from the lake."
        ),
        bounds_summary=(
            "The opening extent follows the Sweden candidate registry rather than the "
            "broader Nordic map scope so ranking differences stay legible."
        ),
        minimum_bounds=minimum_bounds,
    )
    point_layers: list[Mapping[str, object]] = [
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
- Chronology caveat: the linked markdown report keeps source-by-source temporal guardrails explicit; zero-interval context layers remain spatial evidence only.
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
