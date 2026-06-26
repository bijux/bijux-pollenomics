from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean

from ..lake_evidence_richness import (
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)
from .lake_fieldwork_priority import (
    band_score,
    fieldwork_rows,
    fieldwork_shortlist_score,
    human_context_posture,
)

__all__ = [
    "build_lake_fieldwork_preparation_payload",
    "render_lake_fieldwork_preparation_markdown",
    "render_lake_fieldwork_preparation_section",
    "write_lake_fieldwork_preparation_csv",
    "write_lake_fieldwork_preparation_json",
]


def build_lake_fieldwork_preparation_payload(
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int = 20,
) -> dict[str, object]:
    """Build a refusal-prone Sweden lake fieldwork-preparation packet."""
    ordered_assessments = fieldwork_rows(report, top_n=top_n)
    rows = [
        _build_fieldwork_preparation_row(assessment, fieldwork_rank=index)
        for index, assessment in enumerate(ordered_assessments, start=1)
    ]
    return {
        "schema_version": "sweden-lake-fieldwork-preparation.v2",
        "country": report.country,
        "row_count": len(rows),
        "methodology": {
            "scope": "fieldwork-priority Sweden lake candidates only",
            "identity_rule": (
                "identity resolution remains required when duplicate names, "
                "non-official registry names, source coordinate spread, or "
                "source name variants remain visible"
            ),
            "sampling_rule": (
                "sampling fit stays separate from evidence density so very small "
                "basins remain review-first and engineered or wetland-style names "
                "never read as ordinary lake targets"
            ),
            "human_context_rule": (
                "near-lake human aDNA remains decisive for fieldwork ordering: "
                "10 km support is strongest, 20 km support remains shortlist-grade, "
                "and lakes with human support only beyond 20 km stay review-first "
                "even when their broader context is rich"
            ),
            "scenario_consistency_rule": (
                "scenario consistency is high when a lake appears in at least four "
                "top-20 scenario lists across aggregate and 10-50 km bands, medium "
                "at two to three lists, else low"
            ),
            "fieldwork_ordering_rule": (
                "fieldwork ordering sorts first by near-lake human aDNA posture, "
                "then by sampling posture, then by a human-weighted shortlist score; "
                "aggregate evidence score remains visible for traceability"
            ),
            "sead_context_rule": "SEAD 20 km context fit is high at >=20 sites, medium at >=5 sites, else low",
            "palaeopen_alignment_rule": (
                "PalaeOpen alignment fit is high when the lake already carries "
                ">=2 direct pollen sources and >=4 evidence families within 20 km"
            ),
            "warning": (
                "This is a fieldwork-preparation surface, not a final sampling "
                "recommendation."
            ),
        },
        "rows": rows,
    }


def write_lake_fieldwork_preparation_json(
    path: Path,
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int = 20,
) -> None:
    """Write one JSON payload for Sweden lake fieldwork preparation."""
    path.write_text(
        json.dumps(
            build_lake_fieldwork_preparation_payload(report, top_n=top_n),
            indent=2,
        ),
        encoding="utf-8",
    )


def write_lake_fieldwork_preparation_csv(
    path: Path,
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int = 20,
) -> None:
    """Write one CSV row per reviewed Sweden lake candidate."""
    payload = build_lake_fieldwork_preparation_payload(report, top_n=top_n)
    fieldnames = (
        "fieldwork_rank",
        "fieldwork_shortlist_score",
        "aggregate_rank",
        "lake_label",
        "latitude",
        "longitude",
        "aggregate_score",
        "preparation_posture",
        "identity_posture",
        "sampling_posture",
        "sampling_fit",
        "lake_area_km2",
        "human_context_posture",
        "scenario_consistency_posture",
        "sead_context_posture",
        "palaeopen_alignment_posture",
        "scenario_top20_presence_count",
        "scenario_best_rank",
        "scenario_mean_rank",
        "rank_10km",
        "rank_20km",
        "rank_30km",
        "rank_40km",
        "rank_50km",
        "google_maps_url",
        "representative_source_record",
        "lake_registry_id",
        "lake_name_status",
        "coordinate_resolution_method",
        "direct_pollen_source_count",
        "time_aware_direct_pollen_records",
        "evidence_families_20km",
        "sead_sites_20km",
        "human_localities_10km",
        "human_samples_10km",
        "human_localities_20km",
        "human_samples_20km",
        "domesticated_animal_localities_50km",
        "ambiguity_flags",
        "required_actions",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow(
                {
                    "fieldwork_rank": row["fieldwork_rank"],
                    "fieldwork_shortlist_score": row["fieldwork_shortlist_score"],
                    "aggregate_rank": row["aggregate_rank"],
                    "lake_label": row["lake_label"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "aggregate_score": row["aggregate_score"],
                    "preparation_posture": row["preparation_posture"],
                    "identity_posture": row["identity_posture"],
                    "sampling_posture": row["sampling_posture"],
                    "sampling_fit": row["sampling_fit"],
                    "lake_area_km2": row["lake_area_km2"],
                    "human_context_posture": row["human_context_posture"],
                    "scenario_consistency_posture": row["scenario_consistency_posture"],
                    "sead_context_posture": row["sead_context_posture"],
                    "palaeopen_alignment_posture": row["palaeopen_alignment_posture"],
                    "scenario_top20_presence_count": row[
                        "scenario_top20_presence_count"
                    ],
                    "scenario_best_rank": row["scenario_best_rank"],
                    "scenario_mean_rank": row["scenario_mean_rank"],
                    "rank_10km": row["scenario_ranks"]["10km"],
                    "rank_20km": row["scenario_ranks"]["20km"],
                    "rank_30km": row["scenario_ranks"]["30km"],
                    "rank_40km": row["scenario_ranks"]["40km"],
                    "rank_50km": row["scenario_ranks"]["50km"],
                    "google_maps_url": row["google_maps_url"],
                    "representative_source_record": row["representative_source_record"],
                    "lake_registry_id": row["lake_registry_id"],
                    "lake_name_status": row["lake_name_status"],
                    "coordinate_resolution_method": row["coordinate_resolution_method"],
                    "direct_pollen_source_count": row["direct_pollen_source_count"],
                    "time_aware_direct_pollen_records": row[
                        "time_aware_direct_pollen_records"
                    ],
                    "evidence_families_20km": row["evidence_families_20km"],
                    "sead_sites_20km": row["sead_sites_20km"],
                    "human_localities_10km": row["human_localities_10km"],
                    "human_samples_10km": row["human_samples_10km"],
                    "human_localities_20km": row["human_localities_20km"],
                    "human_samples_20km": row["human_samples_20km"],
                    "domesticated_animal_localities_50km": row[
                        "domesticated_animal_localities_50km"
                    ],
                    "ambiguity_flags": "; ".join(row["ambiguity_flags"]),
                    "required_actions": "; ".join(row["required_actions"]),
                }
            )


def render_lake_fieldwork_preparation_markdown(
    payload: dict[str, object],
) -> str:
    """Render the Sweden lake fieldwork-preparation packet as markdown."""
    rows = (
        "\n".join(
            (
                f"| {row['fieldwork_rank']} | {row['aggregate_rank']} | {row['lake_label']} | "
                f"[{row['latitude']:.6f}, {row['longitude']:.6f}]({row['google_maps_url']}) | "
                f"{row['lake_registry_id'] or 'not_available'} | "
                f"{row['lake_name_status'] or 'not_available'} | "
                f"{row['fieldwork_shortlist_score']:.4f} | "
                f"{row['preparation_posture']} | {row['identity_posture']} | "
                f"{row['sampling_posture']} | {row['human_context_posture']} | "
                f"{row['sampling_fit']:.4f} | "
                f"{row['scenario_consistency_posture']} | "
                f"{row['sead_context_posture']} | {row['palaeopen_alignment_posture']} | "
                f"{row['evidence_families_20km']} | {row['scenario_top20_presence_count']} | "
                f"{row['scenario_ranks']['20km']} | "
                f"{', '.join(row['required_actions']) or 'none'} |"
            )
            for row in payload["rows"]
        )
        or "| - | - | No reviewed lakes | - | not_available | not_available | - | - | - | - | - | - | - | - | - | 0 | 0 | - | none |"
    )
    return f"""# Sweden lake fieldwork preparation

This packet turns the Sweden lake richness ranking into a stricter
fieldwork-preparation screen. It keeps identity ambiguity, archaeology-context
depth, and interoperability fit visible before any stronger sampling language is
used.

## Methodology

- Scope: {payload["methodology"]["scope"]}
- Identity rule: {payload["methodology"]["identity_rule"]}
- Sampling rule: {payload["methodology"]["sampling_rule"]}
- Human context rule: {payload["methodology"]["human_context_rule"]}
- Scenario consistency rule: {payload["methodology"]["scenario_consistency_rule"]}
- Fieldwork ordering rule: {payload["methodology"]["fieldwork_ordering_rule"]}
- SEAD context rule: {payload["methodology"]["sead_context_rule"]}
- PalaeOpen alignment rule: {payload["methodology"]["palaeopen_alignment_rule"]}
- Warning: {payload["methodology"]["warning"]}

## Top Lake Preparation Rows

| Fieldwork rank | Aggregate rank | Lake | Coordinates | Lake registry id | Name status | Fieldwork shortlist score | Preparation posture | Identity posture | Sampling posture | Human context | Sampling fit | Scenario consistency | SEAD context | PalaeOpen alignment | Evidence families within 20 km | Top-20 scenario presence | 20 km rank | Required actions |
| ---: | ---: | --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
{rows}
"""


def render_lake_fieldwork_preparation_section(
    *,
    json_name: str,
    csv_name: str,
    markdown_name: str,
) -> str:
    """Render the README section that links the fieldwork-preparation outputs."""
    return f"""

## Lake Fieldwork Preparation

- Sweden lake fieldwork preparation JSON: [`{json_name}`](./{json_name})
- Sweden lake fieldwork preparation CSV: [`{csv_name}`](./{csv_name})
- Sweden lake fieldwork preparation markdown: [`{markdown_name}`](./{markdown_name})
"""


def _build_fieldwork_preparation_row(
    assessment: LakeEvidenceRichnessAssessment,
    *,
    fieldwork_rank: int,
) -> dict[str, object]:
    candidate = assessment.candidate
    band_10 = band_score(assessment, 10)
    band_20 = band_score(assessment, 20)
    band_50 = band_score(assessment, 50)
    identity_posture = _identity_posture(candidate.ambiguity_flags)
    lake_human_context_posture = human_context_posture(assessment)
    scenario_ranks = {
        f"{score.radius_km}km": score.band_rank for score in assessment.band_scores
    }
    scenario_top20_presence_count = _scenario_top20_presence_count(
        aggregate_rank=assessment.aggregate_rank,
        scenario_ranks=scenario_ranks,
    )
    scenario_best_rank = min((assessment.aggregate_rank, *scenario_ranks.values()))
    scenario_mean_rank = round(
        mean((assessment.aggregate_rank, *scenario_ranks.values())),
        2,
    )
    sampling_posture = candidate.lake_sampling_posture or "sampling_not_scored"
    scenario_consistency_posture = _scenario_consistency_posture(
        scenario_top20_presence_count
    )
    sead_context_posture = _sead_context_posture(band_20.sead_site_count)
    palaeopen_alignment_posture = _palaeopen_alignment_posture(
        direct_pollen_source_count=candidate.direct_pollen_source_count,
        evidence_family_count=band_20.evidence_family_count,
    )
    preparation_posture = _preparation_posture(
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
        "fieldwork_shortlist_score": fieldwork_shortlist_score(assessment),
        "aggregate_rank": assessment.aggregate_rank,
        "lake_label": candidate.lake_label,
        "latitude": candidate.latitude,
        "longitude": candidate.longitude,
        "google_maps_url": _google_maps_url(candidate.latitude, candidate.longitude),
        "aggregate_score": assessment.aggregate_score,
        "preparation_posture": preparation_posture,
        "identity_posture": identity_posture,
        "sampling_posture": sampling_posture,
        "human_context_posture": lake_human_context_posture,
        "sampling_fit": candidate.lake_sampling_fit,
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
        "required_actions": _required_actions(
            ambiguity_flags=candidate.ambiguity_flags,
            sampling_posture=sampling_posture,
            human_context_posture=lake_human_context_posture,
            scenario_consistency_posture=scenario_consistency_posture,
            sead_context_posture=sead_context_posture,
            palaeopen_alignment_posture=palaeopen_alignment_posture,
            preparation_posture=preparation_posture,
        ),
    }


def _identity_posture(ambiguity_flags: tuple[str, ...]) -> str:
    flags = set(ambiguity_flags)
    if "duplicate_sweden_name" in flags:
        return "duplicate_name_resolution_required"
    if "non_official_registry_name" in flags:
        return "registry_name_review_required"
    if "source_coordinate_spread" in flags or "source_name_variants" in flags:
        return "registry_cross_check_required"
    return "registry_clear"


def _sead_context_posture(sead_site_count: int) -> str:
    if sead_site_count >= 20:
        return "high"
    if sead_site_count >= 5:
        return "medium"
    return "low"


def _palaeopen_alignment_posture(
    *,
    direct_pollen_source_count: int,
    evidence_family_count: int,
) -> str:
    if direct_pollen_source_count >= 2 and evidence_family_count >= 4:
        return "high"
    if direct_pollen_source_count >= 2 and evidence_family_count >= 3:
        return "medium"
    return "low"


def _preparation_posture(
    *,
    ambiguity_flags: tuple[str, ...],
    sampling_posture: str,
    sampling_fit: float,
    human_context_posture: str,
    direct_pollen_source_count: int,
    evidence_family_count: int,
    sead_site_count: int,
    human_locality_count: int,
    scenario_consistency_posture: str,
) -> str:
    if ambiguity_flags:
        return "identity_resolution_required"
    if sampling_posture == "small_lake_review" or sampling_fit < 0.5:
        return "sampling_fit_review_required"
    if human_context_posture in {
        "extended_human_adna_context",
        "outer_human_adna_context",
        "human_adna_context_absent",
    }:
        return "human_context_review_required"
    if (
        human_context_posture in {"core_human_adna_context", "near_human_adna_context"}
        and scenario_consistency_posture == "high"
        and direct_pollen_source_count >= 2
        and evidence_family_count >= 4
        and sead_site_count >= 10
    ):
        return "fieldwork_preparation_ready"
    if (
        human_context_posture in {"core_human_adna_context", "near_human_adna_context"}
        and direct_pollen_source_count >= 2
        and scenario_consistency_posture in {"high", "medium"}
        and evidence_family_count >= 4
    ):
        return "context_review_ready"
    if evidence_family_count >= 3 and (
        sead_site_count >= 1 or human_locality_count >= 1
    ):
        return "context_review_ready"
    return "evidence_screen_only"


def _required_actions(
    *,
    ambiguity_flags: tuple[str, ...],
    sampling_posture: str,
    human_context_posture: str,
    scenario_consistency_posture: str,
    sead_context_posture: str,
    palaeopen_alignment_posture: str,
    preparation_posture: str,
) -> list[str]:
    actions: list[str] = []
    flags = set(ambiguity_flags)
    if "duplicate_sweden_name" in flags:
        actions.append(
            "confirm the exact Swedish lake registry match before field planning"
        )
    if "source_coordinate_spread" in flags:
        actions.append(
            "reconcile source coordinates against the basin description and lake outline"
        )
    if "source_name_variants" in flags:
        actions.append(
            "normalize source name variants against the lake registry and tracked source records"
        )
    if "non_official_registry_name" in flags:
        actions.append(
            "confirm the official Swedish lake registry name before field planning"
        )
    if sampling_posture == "small_lake_review":
        actions.append(
            "verify basin depth, access, and sediment suitability before treating this small lake as a field target"
        )
    if human_context_posture in {
        "extended_human_adna_context",
        "outer_human_adna_context",
    }:
        actions.append(
            "treat this lake as context-rich but aDNA-distant until a nearer human aDNA locality supports field planning"
        )
    if human_context_posture == "human_adna_context_absent":
        actions.append(
            "do not promote this lake for field planning until human aDNA support is present in the checked-in context"
        )
    if scenario_consistency_posture == "low":
        actions.append(
            "stress-test this candidate against alternative distance-band scenarios before field planning"
        )
    if sead_context_posture in {"high", "medium"}:
        actions.append(
            "inspect linked SEAD records before narrowing the archaeology-context interpretation"
        )
    if palaeopen_alignment_posture == "high":
        actions.append(
            "prepare interoperable metadata notes for wider palaeoecological comparison"
        )
    if not actions and preparation_posture == "fieldwork_preparation_ready":
        actions.append(
            "prepare a site-specific fieldwork review with access, coring, and basin constraints"
        )
    return actions


def _scenario_top20_presence_count(
    *,
    aggregate_rank: int,
    scenario_ranks: dict[str, int],
) -> int:
    return int(aggregate_rank <= 20) + sum(
        1 for rank in scenario_ranks.values() if rank <= 20
    )


def _scenario_consistency_posture(top20_presence_count: int) -> str:
    if top20_presence_count >= 4:
        return "high"
    if top20_presence_count >= 2:
        return "medium"
    return "low"


def _google_maps_url(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={latitude:.6f},{longitude:.6f}"
