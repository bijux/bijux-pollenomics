from __future__ import annotations

import csv
import json
from pathlib import Path

from ..publication_policy import build_site_ranking_policy
from .ranking import CandidateSensitivityReport
from .site_candidates import CandidateSiteScore, resolve_ranking_profile

__all__ = [
    "build_candidate_site_sensitivity_payload",
    "build_candidate_sites_json_payload",
    "render_candidate_site_sensitivity_markdown",
    "render_candidate_site_markdown",
    "write_candidate_site_sensitivity_json",
    "write_candidate_sites_csv",
    "write_candidate_sites_json",
]


def write_candidate_sites_csv(path: Path, scores: list[CandidateSiteScore]) -> None:
    """Write candidate-site rankings as CSV."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "locality",
                "locality_token",
                "profile_name",
                "ranking_status",
                "total_score",
                "evidence_density_signal",
                "chronology_alignment_signal",
                "species_diversity_signal",
                "contextual_support_signal",
                "missingness_penalty",
                "direct_sample_count",
                "distinct_species_count",
                "nearby_context_points",
                "nearby_context_layer_count",
                "temporal_overlap_points",
                "sampling_recommendation_ready",
                "recommendation_posture",
                "ranking_blockers",
                "recommendation_blockers",
                "warning_flags",
                "rationale",
            ],
        )
        writer.writeheader()
        for score in scores:
            writer.writerow(
                {
                    "locality": score.locality,
                    "locality_token": score.locality_token,
                    "profile_name": score.profile_name,
                    "ranking_status": score.ranking_status,
                    "total_score": score.total_score,
                    "evidence_density_signal": score.evidence_density_signal,
                    "chronology_alignment_signal": score.chronology_alignment_signal,
                    "species_diversity_signal": score.species_diversity_signal,
                    "contextual_support_signal": score.contextual_support_signal,
                    "missingness_penalty": score.missingness_penalty,
                    "direct_sample_count": score.direct_sample_count,
                    "distinct_species_count": score.distinct_species_count,
                    "nearby_context_points": score.nearby_context_points,
                    "nearby_context_layer_count": score.nearby_context_layer_count,
                    "temporal_overlap_points": score.temporal_overlap_points,
                    "sampling_recommendation_ready": str(
                        score.sampling_recommendation_ready
                    ).lower(),
                    "recommendation_posture": score.recommendation_posture,
                    "ranking_blockers": " | ".join(score.ranking_blockers),
                    "recommendation_blockers": " | ".join(
                        score.recommendation_blockers
                    ),
                    "warning_flags": " | ".join(score.warning_flags),
                    "rationale": " | ".join(score.rationale),
                }
            )


def write_candidate_sites_json(path: Path, scores: list[CandidateSiteScore]) -> None:
    """Write candidate-site rankings as JSON."""
    path.write_text(
        json.dumps(build_candidate_sites_json_payload(scores), indent=2),
        encoding="utf-8",
    )


def write_candidate_site_sensitivity_json(
    path: Path,
    report: CandidateSensitivityReport,
) -> None:
    """Write candidate-site sensitivity comparisons as JSON."""
    path.write_text(
        json.dumps(build_candidate_site_sensitivity_payload(report), indent=2),
        encoding="utf-8",
    )


def build_candidate_sites_json_payload(
    scores: list[CandidateSiteScore], *, title: str = "Atlas"
) -> dict[str, object]:
    """Build the machine-readable ranking payload with explicit score families."""
    profile_name = scores[0].profile_name if scores else "atlas_exploration"
    policy = build_site_ranking_policy(title=title, profile_name=profile_name)
    profile = resolve_ranking_profile(profile_name)
    return {
        "schema_version": "candidate-site-ranking.v2",
        "profile": profile.as_dict(),
        "evidence_boundary": f'{policy["intro"]} {policy["boundary"]}',
        "species_evidence_boundary": {
            "human_adna": (
                "Mapped Homo sapiens ancient-DNA localities are direct atlas evidence, "
                "but they remain metadata-only until genotype-aware runtime support exists."
            ),
            "animal_adna": (
                "Non-human ancient-DNA support is contextual review evidence until the "
                "runtime owns species-specific sample or locality rows."
            ),
            "cross_species_interpretation": (
                "Cross-species locality anchors can strengthen heuristic ranking signals, "
                "but they do not erase source asymmetry between mapped human records and "
                "unmapped animal project curation."
            ),
            "proximity_refusal": (
                "Animal aDNA plus atlas proximity is not enough to claim shared locality "
                "support or fieldwork readiness."
            ),
            "country_profile_caution": (
                "Country-facing atlas outputs must distinguish mapped human direct evidence "
                "from unmapped animal context."
            ),
        },
        "recommendation_gate": policy["recommendation_gate"],
        "rows": [
            {
                "locality": score.locality,
                "locality_token": score.locality_token,
                "ranking_status": score.ranking_status,
                "total_score": score.total_score,
                "score_families": {
                    "evidence_density": score.evidence_density_signal,
                    "chronology_alignment": score.chronology_alignment_signal,
                    "species_diversity": score.species_diversity_signal,
                    "contextual_support": score.contextual_support_signal,
                },
                "missingness_penalty": score.missingness_penalty,
                "direct_sample_count": score.direct_sample_count,
                "distinct_species_count": score.distinct_species_count,
                "nearby_context_points": score.nearby_context_points,
                "nearby_context_layer_count": score.nearby_context_layer_count,
                "time_aware_context_points": score.time_aware_context_points,
                "temporal_overlap_points": score.temporal_overlap_points,
                "sampling_recommendation_ready": score.sampling_recommendation_ready,
                "recommendation_posture": score.recommendation_posture,
                "ranking_blockers": list(score.ranking_blockers),
                "recommendation_blockers": list(score.recommendation_blockers),
                "warning_flags": list(score.warning_flags),
                "rationale": list(score.rationale),
            }
            for score in scores
        ],
    }


def build_candidate_site_sensitivity_payload(
    report: CandidateSensitivityReport,
) -> dict[str, object]:
    """Build the machine-readable sensitivity comparison payload."""
    return report.as_dict()


def render_candidate_site_markdown(
    scores: list[CandidateSiteScore], *, title: str
) -> str:
    """Render candidate-site rankings as markdown."""
    profile_name = scores[0].profile_name if scores else "atlas_exploration"
    policy = build_site_ranking_policy(title=title, profile_name=profile_name)
    rows = "\n".join(
        (
            f"| {score.locality} | {score.ranking_status} | {score.total_score:.4f} | "
            f"{score.evidence_density_signal:.4f} | {score.chronology_alignment_signal:.4f} | "
            f"{score.species_diversity_signal:.4f} | {score.contextual_support_signal:.4f} | "
            f"{score.missingness_penalty:.4f} | {score.recommendation_posture} | "
            f"{'; '.join(score.rationale)} |"
        )
        for score in scores
    )
    if not rows:
        rows = (
            "| No ranked localities | refused | 0.0000 | 0.0000 | 0.0000 | 0.0000 | "
            "0.0000 | 0.0000 | exploratory_only | No localities were available for ranking |"
        )
    return f"""# {policy["title"]}

{policy["intro"]} {policy["boundary"]}

Profile warning: {policy["profile_warning"]}

Recommendation gate: {policy["recommendation_gate"]}

Species-aware evidence boundary: mapped Homo sapiens localities are direct atlas evidence; non-human aDNA remains contextual review support until species-owned locality rows exist. Animal aDNA plus atlas proximity is not enough for locality claims.

| Locality | Status | Total score | Evidence density | Chronology alignment | Species diversity | Contextual support | Missingness penalty | Recommendation posture | Rationale |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
{rows}
"""


def render_candidate_site_sensitivity_markdown(
    report: CandidateSensitivityReport,
    *,
    title: str,
) -> str:
    """Render the rank-shift comparison across alternate profiles."""
    rows = "\n".join(
        (
            f"| {row.locality} | {row.baseline_rank} | "
            f"{row.profile_ranks.get('fieldwork_triage', '-')} | "
            f"{row.profile_ranks.get('chronology_first', '-')} | "
            f"{row.profile_ranks.get('context_first', '-')} | "
            f"{row.max_rank_shift} | "
            f"{', '.join(row.recommendation_ready_profiles) or 'none'} |"
        )
        for row in report.rows
    )
    if not rows:
        rows = "| No ranked localities | - | - | - | - | 0 | none |"
    return f"""# {title} Candidate Site Sensitivity

This comparison shows how locality order changes when the ranking engine shifts
from exploratory atlas weighting toward chronology-heavy, context-heavy, or
fieldwork-triage weighting.

| Locality | Atlas rank | Fieldwork rank | Chronology-first rank | Context-first rank | Max shift | Recommendation-ready profiles |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{rows}
"""
