from __future__ import annotations

import csv
import json
from pathlib import Path

from ..publication_policy import build_site_ranking_policy
from .site_candidates import CandidateSiteScore

__all__ = [
    "build_candidate_sites_json_payload",
    "render_candidate_site_markdown",
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
                "total_score",
                "sample_signal",
                "context_signal",
                "temporal_signal",
                "distance_signal",
                "rationale",
            ],
        )
        writer.writeheader()
        for score in scores:
            writer.writerow(
                {
                    "locality": score.locality,
                    "total_score": score.total_score,
                    "sample_signal": score.sample_signal,
                    "context_signal": score.context_signal,
                    "temporal_signal": score.temporal_signal,
                    "distance_signal": score.distance_signal,
                    "rationale": " | ".join(score.rationale),
                }
            )


def write_candidate_sites_json(path: Path, scores: list[CandidateSiteScore]) -> None:
    """Write candidate-site rankings as JSON."""
    path.write_text(
        json.dumps(build_candidate_sites_json_payload(scores), indent=2),
        encoding="utf-8",
    )


def build_candidate_sites_json_payload(
    scores: list[CandidateSiteScore], *, title: str = "Atlas"
) -> dict[str, object]:
    """Build the machine-readable ranking payload with provenance boundaries."""
    policy = build_site_ranking_policy(title=title)
    return {
        "schema_version": "candidate-site-ranking.v1",
        "evidence_boundary": f'{policy["intro"]} {policy["boundary"]}',
        "rows": [
            {
                "locality": score.locality,
                "total_score": score.total_score,
                "sample_signal": score.sample_signal,
                "context_signal": score.context_signal,
                "temporal_signal": score.temporal_signal,
                "distance_signal": score.distance_signal,
                "rationale": list(score.rationale),
            }
            for score in scores
        ],
    }


def render_candidate_site_markdown(
    scores: list[CandidateSiteScore], *, title: str
) -> str:
    """Render candidate-site rankings as markdown."""
    policy = build_site_ranking_policy(title=title)
    rows = "\n".join(
        f"| {score.locality} | {score.total_score:.4f} | {score.sample_signal:.4f} | {score.context_signal:.4f} | {score.temporal_signal:.4f} | {score.distance_signal:.4f} | {'; '.join(score.rationale)} |"
        for score in scores
    )
    if not rows:
        rows = "| No ranked localities | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | No localities were available for ranking |"
    return f"""# {policy["title"]}

{policy["intro"]} {policy["boundary"]}

| Locality | Total score | Sample signal | Context signal | Temporal signal | Distance signal | Rationale |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{rows}
"""
