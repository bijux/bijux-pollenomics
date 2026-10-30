"""Check full-support means and literal signed comparison populations independently."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

from .verification_math import SCORE_BOUND, ZERO, require
from .verification_sources import METHODS, METRICS, RADII

D = Decimal
Scores = dict[tuple[int, str, str], list[tuple[str, str, Decimal, Decimal]]]
Contrasts = dict[tuple[int, str, str], dict[str, int]]
Compare = Callable[[str, Decimal, Decimal, str], Decimal]


def summarize_verification(
    grouped_scores: Scores,
    contrast_counts: Contrasts,
    summary_path: Path | None,
    compare: Compare,
) -> tuple[list[dict[str, Any]], int]:
    """Preserve absent full-support means rather than averaging surviving sites."""
    summaries: list[dict[str, Any]] = []
    for radius in RADII:
        for method in METHODS:
            for metric in METRICS:
                grouped_scores.setdefault((radius, method, metric), [])
    for (radius, method, metric), values in sorted(grouped_scores.items()):
        groups = {g for _, g, _, _ in values}
        full_support = len(values) == 10 and len(groups) == 9
        for weighting in ("site", "group"):
            if not full_support:
                expected_mean = observed_mean = None
            elif weighting == "site":
                expected_mean = sum((v for _, _, v, _ in values), ZERO) / len(values)
                observed_mean = sum((v for _, _, _, v in values), ZERO) / len(values)
            else:
                expected_mean = sum(
                    (
                        sum((v for _, h, v, _ in values if g == h), ZERO)
                        / sum(h == g for _, h, _, _ in values)
                        for g in groups
                    ),
                    ZERO,
                ) / len(groups)
                observed_mean = sum(
                    (
                        sum((v for _, h, _, v in values if g == h), ZERO)
                        / sum(h == g for _, h, _, _ in values)
                        for g in groups
                    ),
                    ZERO,
                ) / len(groups)
            if full_support:
                assert expected_mean is not None
                compare(str(observed_mean), expected_mean, SCORE_BOUND, "score")
            summaries.append(
                {
                    "radius": radius,
                    "method": method,
                    "metric": metric,
                    "weighting": weighting,
                    "sites": len(values),
                    "groups": len(groups),
                    "full_support": full_support,
                    "value": str(expected_mean) if expected_mean is not None else None,
                }
            )
    summary_values_compared = 0
    if summary_path is not None:
        native_summary = json.loads(summary_path.read_text())
        require(
            set(native_summary) == set(map(str, RADII)),
            "native summary radius population",
        )
        for entry in summaries:
            native = native_summary[str(entry["radius"])]["methods"][entry["method"]]
            require(
                native["scored_sites"] == entry["sites"]
                and native["full_support"] == entry["full_support"],
                "native summary coverage",
            )
            key = f"{entry['weighting']}_mean_{entry['metric']}"
            if entry["value"] is None:
                require(
                    native[key] is None,
                    "incomplete-support native means must remain null",
                )
            else:
                compare(str(native[key]), D(entry["value"]), SCORE_BOUND, "score")
                summary_values_compared += 1
        for radius in RADII:
            require(
                native_summary[str(radius)]["sites"] == 10,
                "native summary all held sites retained",
            )
            for baseline in METHODS[1:]:
                for metric in METRICS:
                    expected_counts = contrast_counts.get(
                        (radius, baseline, metric), {"poorer": 0, "better": 0, "tie": 0}
                    )
                    require(
                        native_summary[str(radius)]["contrasts"][baseline][metric]
                        == {
                            "paired_sites": sum(expected_counts.values()),
                            **expected_counts,
                        },
                        "native paired contrast/tie populations",
                    )
    return summaries, summary_values_compared
