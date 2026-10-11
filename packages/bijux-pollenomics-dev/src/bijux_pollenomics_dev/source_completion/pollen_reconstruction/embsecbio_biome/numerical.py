"""Evaluate the published saved-parameter distance without ecological inference."""

from __future__ import annotations

import math

ORDER = ("TUND", "DESE", "GRAM", "XSHB", "ENWD", "WTSFS", "CENF", "CMIX", "TEDE")


def evaluate(
    percentages: list[float], means: dict[str, list[float]], sd: dict[str, list[float]]
) -> tuple[dict[str, float], dict[str, float], str]:
    """Keep literal percentage units, sample SD plus 0.5, and source class ties."""
    if not percentages or any(
        not math.isfinite(p) or not 0 <= p <= 100 for p in percentages
    ):
        raise ValueError("pollen percentages must be finite in [0,100]")
    if set(means) != set(ORDER) or set(sd) != set(ORDER):
        raise ValueError("saved model class support differs")
    for biome in ORDER:
        if len(means[biome]) != len(percentages) or len(sd[biome]) != len(percentages):
            raise ValueError("saved model taxon dimensions differ")
        if any(not math.isfinite(m) for m in means[biome]):
            raise ValueError("saved means must be finite")
        if any(not math.isfinite(s) or s < 0 for s in sd[biome]):
            raise ValueError("saved sample SD must be finite and nonnegative")
    distances = {
        b: math.sqrt(
            math.fsum(
                ((p - m) / (s + 0.5)) ** 2
                for p, m, s in zip(percentages, means[b], sd[b], strict=True)
            )
        )
        for b in ORDER
    }
    scores = {b: math.exp(-distances[b] / 100) for b in ORDER}
    return distances, scores, max(ORDER, key=scores.__getitem__)


def matrix(rows: list[dict[str, str]], target: str) -> dict[tuple[str, str], int]:
    """Compare MLmetrics source uses reference rows and prediction columns."""
    from collections import Counter

    pairs = []
    for row in rows:
        prediction = row["prediction"]
        observed = row["subdominant"] if target == "Subdominant" else row["dominant"]
        if target == "Composit" and prediction in (row["dominant"], row["subdominant"]):
            observed = prediction
        if observed in ORDER and prediction in ORDER:
            pairs.append((observed, prediction))
    return dict(Counter(pairs))
