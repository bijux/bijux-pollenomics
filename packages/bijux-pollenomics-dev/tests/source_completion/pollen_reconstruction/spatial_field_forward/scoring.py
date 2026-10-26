"""Independent positive composition arithmetic and numerical score resolution."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

Pair = tuple[float, float]


def close(values: Sequence[float]) -> Pair:
    if len(values) != 2:
        raise ValueError("Independent composition requires exactly two taxa")
    total = math.fsum(values)
    if total <= 0 or not all(math.isfinite(value) and value >= 0 for value in values):
        raise ValueError("Independent composition requires finite positive total mass")
    return values[0] / total, values[1] / total


def source_cover(counts: Pair, own_factors: Pair, ppe: Pair) -> Pair:
    return close(tuple(counts[i] / (own_factors[i] * ppe[i]) for i in range(2)))


def reconstruct_predictions(
    counts: tuple[Pair, Pair],
    source_factors: tuple[Pair, Pair],
    ppe: Pair,
    target_factors: Pair,
    centre_first_weight: float,
    spatial_factors: tuple[Pair, Pair] | None,
) -> tuple[dict[str, Pair], tuple[Pair, Pair]]:
    """Rebuild three saved predictions from counts and independently checked factors."""
    pollen = (close(counts[0]), close(counts[1]))
    cover = (
        source_cover(counts[0], source_factors[0], ppe),
        source_cover(counts[1], source_factors[1], ppe),
    )
    weights = centre_first_weight, 1 - centre_first_weight
    centre_cover = tuple(
        math.fsum(weights[s] * cover[s][i] for s in range(2)) for i in range(2)
    )
    direct = tuple(
        math.fsum(weights[s] * pollen[s][i] for s in range(2)) for i in range(2)
    )
    centre_forward = close(
        tuple(ppe[i] * target_factors[i] * centre_cover[i] for i in range(2))
    )
    predictions = {
        "direct_pollen_idw": (direct[0], direct[1]),
        "centre_cover_idw_forward": centre_forward,
    }
    if spatial_factors is not None:
        predictions["spatial_cover_idw_forward"] = close(
            tuple(
                ppe[i]
                * math.fsum(spatial_factors[i][s] * cover[s][i] for s in range(2))
                for i in range(2)
            )
        )
    return predictions, cover


@dataclass(frozen=True)
class Scores:
    signed_fraction_errors: Pair
    mae: float
    total_variation: float
    hellinger: float

    def metrics(self) -> dict[str, float]:
        return {
            "mae": self.mae,
            "total_variation": self.total_variation,
            "hellinger": self.hellinger,
        }


def scores(predicted: Pair, observed: Pair) -> Scores:
    """Score the two-taxon closed panel; no pooled-count or vegetation accuracy claim."""
    truth = close(observed)
    errors = tuple(predicted[i] - truth[i] for i in range(2))
    absolute = math.fsum(abs(value) for value in errors)
    return Scores(
        (errors[0], errors[1]),
        absolute / 2,
        absolute / 2,
        math.sqrt(
            math.fsum(
                (math.sqrt(predicted[i]) - math.sqrt(truth[i])) ** 2 for i in range(2)
            )
            / 2
        ),
    )


def metric_ranges(observed: Pair, first_fraction_bounds: Pair) -> dict[str, Pair]:
    """Map a numerical prediction interval to descriptive score ranges, not CIs."""
    low, high = first_fraction_bounds
    if not 0 <= low <= high <= 1:
        raise ValueError("Independent closed-fraction bounds are invalid")
    truth = close(observed)[0]
    endpoint_scores = [scores((p, 1 - p), observed) for p in (low, high)]
    contains_truth = low <= truth <= high
    result = {}
    for metric in ("mae", "total_variation", "hellinger"):
        endpoints = [row.metrics()[metric] for row in endpoint_scores]
        result[metric] = (0.0 if contains_truth else min(endpoints), max(endpoints))
    return result


def verify_score_ledger(
    result: dict[str, object],
    predictions: dict[tuple[str, str], Pair],
    bounds: dict[tuple[str, str], Pair],
    observations: dict[str, Pair],
) -> dict[str, object]:
    """Reconstruct all score rows and equal-place summaries with fixed denominators."""
    from itertools import combinations
    from typing import Any, cast

    import pytest

    saved = cast(dict[str, Any], result)
    labels = (
        "direct_pollen_idw",
        "centre_cover_idw_forward",
        "spatial_cover_idw_forward",
    )
    metrics = {
        "mean_absolute_fraction_error": "mae",
        "total_variation": "total_variation",
        "hellinger_distance": "hellinger",
    }
    rows = {(row["context_id"], row["family"]): row for row in saved["scores"]}
    assert len(rows) == len(saved["scores"]) == 54
    assert set(rows) == {
        (context, family) for context in observations for family in labels
    }
    support = {
        f"{row['core']}:{row['window'][0]}:{row['window'][1]}": row
        for row in saved["observations"]
    }
    expected: dict[tuple[str, str], dict[str, Any]] = {}
    for identity, row in rows.items():
        context, family = identity
        assert row["prediction_file_sha256"] == saved["prediction_file"]["sha256"]
        assert row["observed_fraction"] == pytest.approx(
            close(observations[context]), abs=2e-12, rel=0
        )
        assert row["core"] == context.split(":")[0]
        assert row["window"] == support[context]["window"]
        assert row["sample_ids"] == support[context]["sample_ids"]
        if identity not in predictions:
            assert row["status"] == "refused_prediction" and row["reason"]
            continue
        assert row["status"] == "scored"
        predicted = predictions[identity]
        expected_score = scores(predicted, observations[context])
        assert row["predicted_fraction"] == pytest.approx(predicted, abs=2e-12, rel=0)
        assert row["signed_fraction_error"] == pytest.approx(
            expected_score.signed_fraction_errors, abs=2e-12, rel=0
        )
        intervals = metric_ranges(observations[context], bounds[identity])
        values = {}
        for key, oracle_key in metrics.items():
            value = expected_score.metrics()[oracle_key]
            assert row[key] == pytest.approx(value, abs=2e-12, rel=0)
            assert row["numerical_ranges"][key] == pytest.approx(
                intervals[oracle_key], abs=2e-12, rel=0
            )
            values[key] = value
        expected[identity] = {
            "metrics": values,
            "ranges": {
                key: intervals[oracle_key] for key, oracle_key in metrics.items()
            },
        }
    summaries = {row["family"]: row for row in saved["summaries"]["families"]}
    assert len(saved["summaries"]["families"]) == len(summaries) == 3
    assert set(summaries) == set(labels)
    aggregate: dict[str, dict[str, Any]] = {}
    for family in labels:
        row = summaries[family]
        eligible = [
            record for (context, label), record in expected.items() if label == family
        ]
        assert row["requested_contexts"] == 18 and row["scored_contexts"] == len(
            eligible
        )
        if len(eligible) != 18:
            assert row["status"] == "refused_incomplete_cohort"
            assert "equal_place" not in row and "places" not in row
            continue
        assert row["status"] == "complete_cohort"
        places = {place["core"]: place for place in row["places"]}
        assert len(row["places"]) == len(places) == 3
        place_expected: list[dict[str, Any]] = []
        for core in ("BOKE", "BUS", "SOLSOE83"):
            group = [
                record
                for (context, label), record in expected.items()
                if label == family and context.startswith(core + ":")
            ]
            assert len(group) == 6
            values = {
                key: math.fsum(record["metrics"][key] for record in group) / 6
                for key in metrics
            }
            intervals = {
                key: (
                    math.fsum(record["ranges"][key][0] for record in group) / 6,
                    math.fsum(record["ranges"][key][1] for record in group) / 6,
                )
                for key in metrics
            }
            for key in metrics:
                assert places[core]["metrics"][key] == pytest.approx(
                    values[key], abs=2e-12, rel=0
                )
                assert places[core]["numerical_ranges"][key] == pytest.approx(
                    intervals[key], abs=2e-12, rel=0
                )
            place_expected.append({"metrics": values, "ranges": intervals})
        values = {
            key: math.fsum(place["metrics"][key] for place in place_expected) / 3
            for key in metrics
        }
        intervals = {
            key: (
                math.fsum(place["ranges"][key][0] for place in place_expected) / 3,
                math.fsum(place["ranges"][key][1] for place in place_expected) / 3,
            )
            for key in metrics
        }
        for key in metrics:
            assert row["equal_place"]["metrics"][key] == pytest.approx(
                values[key], abs=2e-12, rel=0
            )
            assert row["equal_place"]["numerical_ranges"][key] == pytest.approx(
                intervals[key], abs=2e-12, rel=0
            )
        aggregate[family] = {"metrics": values, "ranges": intervals}
    pairs = {
        (row["first_family"], row["second_family"]): row
        for row in saved["summaries"]["pairwise"]
    }
    assert len(saved["summaries"]["pairwise"]) == len(pairs) == 3
    assert set(pairs) == set(combinations(labels, 2))
    unresolved = 0
    for (first, second), row in pairs.items():
        if first not in aggregate or second not in aggregate:
            assert row["status"] == "refused_incomplete_cohort"
            continue
        assert row["status"] == "matched_complete_cohort"
        for key in metrics:
            a, b = aggregate[first], aggregate[second]
            expected_range = (
                a["ranges"][key][0] - b["ranges"][key][1],
                a["ranges"][key][1] - b["ranges"][key][0],
            )
            reported = row["metrics"][key]
            assert reported["point_difference"] == pytest.approx(
                a["metrics"][key] - b["metrics"][key], abs=2e-12, rel=0
            )
            assert reported["numerical_difference_range"] == pytest.approx(
                expected_range, abs=2e-12, rel=0
            )
            lo, hi = reported["numerical_difference_range"]
            resolution = (
                "numerically_unresolved"
                if lo <= 0 <= hi
                else "separated_conditional_numerical_ranges"
            )
            assert reported["resolution"] == resolution
            unresolved += resolution == "numerically_unresolved"
    return {
        "scored_rows": len(expected),
        "refused_rows": 54 - len(expected),
        "numerically_unresolved_pair_metrics": unresolved,
        "aggregate": aggregate,
    }
