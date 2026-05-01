from __future__ import annotations

import csv
import json
from pathlib import Path

from .site_candidates import CandidateSiteScore

__all__ = [
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
    payload = [
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
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def render_candidate_site_markdown(
    scores: list[CandidateSiteScore], *, title: str
) -> str:
    """Render candidate-site rankings as markdown."""
    rows = "\n".join(
        f"| {score.locality} | {score.total_score:.4f} | {score.sample_signal:.4f} | {score.context_signal:.4f} | {score.temporal_signal:.4f} | {score.distance_signal:.4f} | {'; '.join(score.rationale)} |"
        for score in scores
    )
    if not rows:
        rows = "| No ranked localities | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | No localities were available for ranking |"
    return f"""# {title} Candidate Site Ranking

This ranking is an atlas-adjacent heuristic for comparing current AADR
localities against nearby contextual layers. It is not yet a lake-selection or
sampling recommendation engine.

| Locality | Total score | Sample signal | Context signal | Temporal signal | Distance signal | Rationale |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{rows}
"""
