from __future__ import annotations

import csv
import json
from pathlib import Path

from ..lake_evidence_richness import LakeEvidenceRichnessReport

__all__ = [
    "build_lake_archaeology_sensitivity_payload",
    "render_lake_archaeology_sensitivity_markdown",
    "write_lake_archaeology_sensitivity_csv",
    "write_lake_archaeology_sensitivity_json",
]

_BASELINE_WEIGHTS = {
    "human": 0.59,
    "direct_pollen": 0.14,
    "nearby_pollen": 0.07,
    "sampling": 0.07,
    "archaeology": 0.07,
    "animal": 0.04,
    "diversity": 0.02,
}
_ARCHAEOLOGY_PROFILES = (
    ("context_conservative", 0.03),
    ("baseline", 0.07),
    ("context_emphasis", 0.15),
)
_RADIUS_WEIGHTS = {10: 0.35, 20: 0.27, 30: 0.18, 40: 0.12, 50: 0.08}


def build_lake_archaeology_sensitivity_payload(
    report: LakeEvidenceRichnessReport,
) -> dict[str, object]:
    """Re-rank lakes under bounded archaeology-context weight profiles."""
    profile_rows: dict[str, list[dict[str, object]]] = {}
    for profile_key, archaeology_weight in _ARCHAEOLOGY_PROFILES:
        weights = _profile_weights(archaeology_weight)
        rows = []
        for assessment in report.assessments:
            temporal_context = assessment.candidate.temporal_context_points
            sead_temporal_context = tuple(
                point
                for point in temporal_context
                if point.source_layer_key.startswith("sead")
            )
            band_scores = [
                _reweighted_band_score(
                    band=band,
                    sampling_fit=assessment.candidate.lake_sampling_fit,
                    weights=weights,
                )
                for band in assessment.band_scores
            ]
            aggregate_score = round(
                sum(
                    score * _RADIUS_WEIGHTS.get(band.radius_km, 0.0)
                    for band, score in zip(assessment.band_scores, band_scores)
                ),
                4,
            )
            rows.append(
                {
                    "lake_token": assessment.candidate.lake_token,
                    "lake_label": assessment.candidate.lake_label,
                    "baseline_engine_rank": assessment.aggregate_rank,
                    "aggregate_score": aggregate_score,
                    "archaeology_weight": archaeology_weight,
                    "archaeology_signal_20km": _band_20(
                        assessment.band_scores
                    ).archaeology_signal,
                    "temporal_context_window_count": len(temporal_context),
                    "temporal_context_windows": "; ".join(
                        sorted(
                            {
                                str(
                                    (point.temporal_semantics or {}).get(
                                        "temporal_window_key", "unresolved"
                                    )
                                )
                                for point in temporal_context
                            }
                        )
                    ),
                    "sead_temporal_context_window_count": len(sead_temporal_context),
                    "sead_temporal_context_record_count": sum(
                        point.record_count for point in sead_temporal_context
                    ),
                }
            )
        rows.sort(key=lambda row: (-float(row["aggregate_score"]), row["lake_label"]))
        for rank, row in enumerate(rows, start=1):
            row["sensitivity_rank"] = rank
        profile_rows[profile_key] = rows

    baseline_ranks = {
        str(row["lake_token"]): int(row["sensitivity_rank"])
        for row in profile_rows["baseline"]
    }
    output_rows = []
    for profile_key, archaeology_weight in _ARCHAEOLOGY_PROFILES:
        for row in profile_rows[profile_key]:
            baseline_rank = baseline_ranks[str(row["lake_token"])]
            output_rows.append(
                {
                    "profile_key": profile_key,
                    **row,
                    "baseline_sensitivity_rank": baseline_rank,
                    "rank_shift_from_baseline": baseline_rank
                    - int(row["sensitivity_rank"]),
                }
            )

    maximum_shift = max(
        (abs(int(row["rank_shift_from_baseline"])) for row in output_rows),
        default=0,
    )
    return {
        "schema_version": "sweden-lake-archaeology-sensitivity.v1",
        "country": report.country,
        "candidate_count": report.candidate_count,
        "profiles": [
            {
                "profile_key": profile_key,
                "archaeology_weight": archaeology_weight,
                "weights": _profile_weights(archaeology_weight),
            }
            for profile_key, archaeology_weight in _ARCHAEOLOGY_PROFILES
        ],
        "methodology": {
            "baseline_justification": (
                "Archaeology receives 0.07 because it is contextual rather than direct "
                "lake or sampling evidence. It equals nearby-pollen and area-screen "
                "weight, remains below direct pollen, and remains far below human aDNA."
            ),
            "archaeology_signal_contract": (
                "SEAD site density contributes 0.40 inside the archaeology signal, "
                "numeric SEAD chronology 0.20, SEAD chronology overlapping nearby human "
                "aDNA 0.20, and coarse RAÄ density 0.20."
            ),
            "renormalization_rule": (
                "When archaeology weight changes, every non-archaeology component is "
                "scaled proportionally so profile weights continue to sum to 1.00."
            ),
            "decision_rule": (
                "A lake should move upward on archaeology grounds only when linked SEAD "
                "records are inspected and temporally compatible. RAÄ density alone is "
                "a discovery prompt, never sufficient promotion evidence."
            ),
            "temporal_qualification_rule": (
                "Each sensitivity row publishes the candidate's available temporal "
                "context windows and the count of nearby numeric SEAD records. A "
                "weight change remains a static robustness check; interpretation in "
                "a particular period requires a matching SEAD context window."
            ),
            "ranking_note": (
                "Sensitivity rank is score-ordered for isolating weight effects; the "
                "published engine rank separately applies direct-evidence tie-breakers."
            ),
        },
        "maximum_absolute_rank_shift": maximum_shift,
        "rows": output_rows,
    }


def write_lake_archaeology_sensitivity_json(
    path: Path,
    payload: dict[str, object],
) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_lake_archaeology_sensitivity_csv(
    path: Path,
    payload: dict[str, object],
) -> None:
    fieldnames = (
        "profile_key",
        "archaeology_weight",
        "lake_token",
        "lake_label",
        "baseline_engine_rank",
        "baseline_sensitivity_rank",
        "sensitivity_rank",
        "rank_shift_from_baseline",
        "aggregate_score",
        "archaeology_signal_20km",
        "temporal_context_window_count",
        "temporal_context_windows",
        "sead_temporal_context_window_count",
        "sead_temporal_context_record_count",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(payload["rows"])


def render_lake_archaeology_sensitivity_markdown(
    payload: dict[str, object],
) -> str:
    methodology = payload["methodology"]
    emphasized = sorted(
        (row for row in payload["rows"] if row["profile_key"] == "context_emphasis"),
        key=lambda row: int(row["sensitivity_rank"]),
    )[:20]
    rows = "\n".join(
        f"| {row['sensitivity_rank']} | {row['lake_label']} | "
        f"{row['aggregate_score']:.4f} | {row['archaeology_signal_20km']:.4f} | "
        f"{row['sead_temporal_context_window_count']} | "
        f"{row['sead_temporal_context_record_count']} | "
        f"{int(row['rank_shift_from_baseline']):+d} |"
        for row in emphasized
    )
    return f"""# Sweden lake archaeology-weight sensitivity

This report isolates how much the lake shortlist changes when archaeology is
treated conservatively, at the published baseline, or with added contextual
emphasis. It does not turn nearby archaeology into proof of lake suitability.

## Why The Baseline Is 0.07

{methodology["baseline_justification"]}

The archaeology component is itself bounded: {methodology["archaeology_signal_contract"]}
{methodology["renormalization_rule"]}

## Decision Rule

{methodology["decision_rule"]}

{methodology["temporal_qualification_rule"]}

{methodology["ranking_note"]}

The maximum absolute movement across the tested profiles is
**{payload["maximum_absolute_rank_shift"]} ranks**.

## Archaeology-Emphasis Top 20

| Rank | Lake | Score | Archaeology signal at 20 km | SEAD time windows | Numeric SEAD records | Shift from baseline |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
{rows}
"""


def _profile_weights(archaeology_weight: float) -> dict[str, float]:
    non_archaeology_scale = (1.0 - archaeology_weight) / (
        1.0 - _BASELINE_WEIGHTS["archaeology"]
    )
    return {
        key: (
            archaeology_weight
            if key == "archaeology"
            else round(weight * non_archaeology_scale, 8)
        )
        for key, weight in _BASELINE_WEIGHTS.items()
    }


def _reweighted_band_score(*, band, sampling_fit: float, weights) -> float:
    return round(
        band.human_signal * weights["human"]
        + band.nearby_pollen_signal * weights["nearby_pollen"]
        + band.archaeology_signal * weights["archaeology"]
        + band.animal_signal * weights["animal"]
        + band.diversity_signal * weights["diversity"]
        + sampling_fit * weights["sampling"]
        + _direct_pollen_signal_from_band(band, sampling_fit=sampling_fit)
        * weights["direct_pollen"],
        4,
    )


def _direct_pollen_signal_from_band(band, *, sampling_fit: float) -> float:
    total_weighted = (
        band.total_score
        - band.human_signal * _BASELINE_WEIGHTS["human"]
        - band.nearby_pollen_signal * _BASELINE_WEIGHTS["nearby_pollen"]
        - band.archaeology_signal * _BASELINE_WEIGHTS["archaeology"]
        - band.animal_signal * _BASELINE_WEIGHTS["animal"]
        - band.diversity_signal * _BASELINE_WEIGHTS["diversity"]
        - sampling_fit * _BASELINE_WEIGHTS["sampling"]
    )
    return max(0.0, total_weighted / _BASELINE_WEIGHTS["direct_pollen"])


def _band_20(bands):
    return next(band for band in bands if band.radius_km == 20)
