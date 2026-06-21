from __future__ import annotations

import csv
import json
from pathlib import Path

from ..lake_evidence_richness import LakeEvidenceRichnessReport

__all__ = [
    "build_lake_evidence_richness_payload",
    "render_lake_evidence_richness_markdown",
    "render_lake_evidence_richness_section",
    "write_lake_evidence_richness_band_csv",
    "write_lake_evidence_richness_json",
]


def build_lake_evidence_richness_payload(
    report: LakeEvidenceRichnessReport,
) -> dict[str, object]:
    """Build the machine-readable lake evidence richness payload."""
    return report.as_dict()


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
    """Write one long-form CSV row per lake and distance band."""
    fieldnames = (
        "lake_name",
        "lake_token",
        "latitude",
        "longitude",
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
                        "lake_token": candidate.lake_token,
                        "latitude": round(candidate.latitude, 6),
                        "longitude": round(candidate.longitude, 6),
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


def render_lake_evidence_richness_markdown(
    report: LakeEvidenceRichnessReport,
) -> str:
    """Render the Sweden lake evidence richness report as markdown."""
    overall_rows = "\n".join(
        (
            f"| {assessment.aggregate_rank} | {assessment.candidate.lake_name} | "
            f"{assessment.aggregate_score:.4f} | {assessment.candidate.direct_pollen_signal:.4f} | "
            f"{', '.join(assessment.candidate.pollen_sources)} | "
            f"{_band_score(assessment, 20).human_adna_locality_count} | "
            f"{_band_score(assessment, 20).sead_site_count} | "
            f"{_band_score(assessment, 50).domesticated_animal_locality_count} |"
        )
        for assessment in report.assessments[:20]
    ) or "| - | No lake candidates | 0.0000 | 0.0000 | - | 0 | 0 | 0 |"
    band_sections = "\n\n".join(
        _render_band_table(report, radius_km=radius) for radius in report.radii_km
    )
    return f"""# Sweden lake evidence richness

This report ranks Sweden lake candidates by the richness of tracked pollen, archaeology, human aDNA, and domesticated-animal aDNA evidence around each lake.

## Methodology

- Candidate derivation: {report.methodology["candidate_derivation"]}
- Distance bands: {", ".join(f"{radius} km" for radius in report.radii_km)}
- Archaeology note: {report.methodology["archaeology_note"]}
- Animal note: {report.methodology["animal_note"]}

## Aggregate Ranking

| Rank | Lake | Aggregate score | Direct pollen | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: |
{overall_rows}

{band_sections}
"""


def render_lake_evidence_richness_section(
    *,
    json_name: str,
    band_csv_name: str,
    markdown_name: str,
) -> str:
    """Render the README section that links the Sweden lake evidence richness outputs."""
    return f"""

## Lake Evidence Richness

- Sweden lake evidence richness JSON: [`{json_name}`](./{json_name})
- Sweden lake evidence richness distance-band CSV: [`{band_csv_name}`](./{band_csv_name})
- Sweden lake evidence richness markdown: [`{markdown_name}`](./{markdown_name})
"""


def _render_band_table(report: LakeEvidenceRichnessReport, *, radius_km: int) -> str:
    ordered = sorted(
        report.assessments,
        key=lambda assessment: _band_score(assessment, radius_km).band_rank,
    )[:15]
    rows = "\n".join(
        (
            f"| {_band_score(assessment, radius_km).band_rank} | "
            f"{assessment.candidate.lake_name} | "
            f"{_band_score(assessment, radius_km).total_score:.4f} | "
            f"{_band_score(assessment, radius_km).human_adna_locality_count} | "
            f"{_band_score(assessment, radius_km).human_adna_sample_count} | "
            f"{_band_score(assessment, radius_km).domesticated_animal_locality_count} | "
            f"{_band_score(assessment, radius_km).sead_site_count} | "
            f"{_band_score(assessment, radius_km).raa_density_site_count} | "
            f"{_band_score(assessment, radius_km).nearby_pollen_lake_count} | "
            f"{_band_score(assessment, radius_km).evidence_family_count} |"
        )
        for assessment in ordered
    ) or "| - | No lake candidates | 0.0000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |"
    return f"""## {radius_km} km Ranking

| Rank | Lake | Score | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{rows}"""


def _band_score(assessment, radius_km: int):
    for score in assessment.band_scores:
        if score.radius_km == radius_km:
            return score
    raise ValueError(f"Missing band score for radius {radius_km}")
