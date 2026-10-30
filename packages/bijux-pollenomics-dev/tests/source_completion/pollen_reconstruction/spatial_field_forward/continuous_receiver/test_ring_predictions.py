"""Portable count-free fixtures and complete continuous prediction consumers."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward import (
    radial_envelope as exact,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    ring_predictions as consumer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.ring_bounds import (
    RingCaseResult,
    coefficient_bounds,
    deposition_bounds,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.study_inputs import (
    AXIS,
    CORES,
)


def prediction_packets() -> tuple[dict[str, Any], dict[str, Any]]:
    """Complete fake inputs; no actual source artifacts, counts or fits are read."""
    radii = (80, 69, 89)
    covers = ([0.8, 0.2], [0.25, 0.75], [0.4, 0.6])
    prediction: dict[str, Any] = {
        "source_commit": "old-fixed-source",
        "axis": list(AXIS),
        "ppe": [2.0, 1.0],
        "fall": [0.024, 0.032],
        "geometry": [],
        "contexts": [],
    }
    scores: list[dict[str, Any]] = []
    point_vectors = ([0.4, 0.6000000000001], [0.55, 0.45], [0.56, 0.44])

    def owner(index: int, window_index: int) -> dict[str, Any]:
        return {
            "core": CORES[index],
            "site_id": 100 + index,
            "dataset_id": 200 + index,
            "collection_unit_id": 300 + index,
            "radius_m": radii[index],
            "window": [window_index * 500, (window_index + 1) * 500],
            "sample_ids": [
                index * 10000 + window_index * 10 + j + 1 for j in range(index + 1)
            ],
        }

    for index, core in enumerate(CORES):
        anchors = [name for name in CORES if name != core]
        prediction["geometry"].append(
            {
                "core": core,
                "anchor_order": anchors,
                "anchor_xy_m": [[1.0, 0.0], [2.0, 0.0]],
                "radius_m": radii[index],
                "centre_weights": [0.01, 0.99],
            }
        )
        for window_index in range(6):
            target = owner(index, window_index)
            key = f"{core}:{window_index * 500}:{(window_index + 1) * 500}"
            training = [
                {
                    **owner(j, window_index),
                    "cover": covers[j],
                    "counts": "unused source field",
                    "homogeneous_factors": [999.0, 999.0],
                }
                for j in range(3)
                if j != index
            ]
            families = {
                family: {"status": "predicted", "pollen_fraction": point_vectors[k]}
                for k, family in enumerate(consumer.FAMILIES)
            }
            prediction["contexts"].append(
                {
                    "context_id": key,
                    "target": target,
                    "training": training,
                    "geometry_core": core,
                    "families": families,
                }
            )
            for k, family in enumerate(consumer.FAMILIES):
                metric = 0.2 + k * 0.1
                scores.append(
                    {
                        "context_id": key,
                        "core": core,
                        "window": target["window"],
                        "sample_ids": target["sample_ids"],
                        "family": family,
                        "status": "scored",
                        "predicted_fraction": point_vectors[k],
                        "observed_fraction": [0.2, 0.80000000000001],
                        **dict.fromkeys(exact.METRICS, metric),
                    }
                )
    old = {
        "source_commit": prediction["source_commit"],
        "scores": scores,
        "summaries": {
            "families": [
                {
                    "family": family,
                    "equal_place": {
                        "metrics": dict.fromkeys(exact.METRICS, 0.2 + k * 0.1)
                    },
                }
                for k, family in enumerate(consumer.FAMILIES)
            ],
            "pairwise": [
                {
                    "first_family": first,
                    "second_family": second,
                    "metrics": {
                        metric: {"point_difference": -0.1} for metric in exact.METRICS
                    },
                }
                for first, second in combinations(consumer.FAMILIES, 2)
            ],
        },
    }
    return prediction, old


def case_results(
    prediction: dict[str, Any], *, width: Fraction = Fraction(0)
) -> tuple[RingCaseResult, ...]:
    results = []
    for row in prediction["geometry"]:
        points = row["anchor_xy_m"]
        for index in range(2):
            model = Geometry(
                Fraction(3 + index, 5),
                Fraction(row["radius_m"]),
                Fraction(100000),
                (Fraction(points[0][0]), Fraction(points[0][1])),
                (Fraction(points[1][0]), Fraction(points[1][1])),
            )
            left, right = (
                (Fraction(4, 5), Fraction(1, 5))
                if index == 0
                else (Fraction(7, 10), Fraction(2, 5))
            )
            bounds = coefficient_bounds(
                model,
                (model.receiver, model.outer),
                (
                    Interval(left - width, left + width),
                    Interval(right - width, right + width),
                ),
            )
            results.append(RingCaseResult((None, None), (None, None), bounds, None))
    return tuple(results)


def close_packet(
    path: Path, prediction: dict[str, Any], rows: list[dict[str, Any]]
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": consumer.PREDICTION_SCHEMA,
                "source_prediction_commit": prediction["source_commit"],
                "contexts": rows,
            }
        ),
        encoding="utf-8",
    )


def test_same_continuous_k_and_exact_centre_weights_ignore_old_point_factors() -> None:
    prediction, _ = prediction_packets()
    cases = case_results(prediction)
    rows = consumer.prediction_contexts(prediction, cases)
    assert len(rows) == 18
    first = rows[0]["families"][consumer.FAMILIES[1]]
    for index in range(2):
        bounds = cases[index].bounds
        assert bounds is not None
        c1, c2 = (
            Fraction(row["cover"][index])
            for row in prediction["contexts"][0]["training"]
        )
        expected = (
            bounds.homogeneous
            * ((4 * c1 + c2) / 5)
            * Fraction(prediction["ppe"][index])
        )
        assert exact.decoded(first["deposition_bounds_exact"][index]) == (
            expected.lower,
            expected.upper,
        )
    assert first["status"] == consumer.ENCLOSED
    assert rows[0]["families"][consumer.FAMILIES[2]]["status"] == consumer.ENCLOSED


@pytest.mark.parametrize("covers", [([0.9, 0.1], [0.2, 0.8]), ([0.1, 0.9], [0.8, 0.2])])
def test_signed_affine_spatial_deposition_uses_shared_q(
    covers: tuple[list[float], list[float]],
) -> None:
    prediction, _ = prediction_packets()
    context = prediction["contexts"][0]
    for row, cover in zip(context["training"], covers, strict=True):
        row["cover"] = cover
    cases = case_results(prediction, width=Fraction(1, 100))
    result = consumer.prediction_contexts(prediction, cases)[0]["families"][
        consumer.FAMILIES[2]
    ]
    for index in range(2):
        bounds = cases[index].bounds
        assert bounds is not None
        expected = deposition_bounds(
            bounds, Fraction(covers[0][index]), Fraction(covers[1][index])
        ) * Fraction(prediction["ppe"][index])
        assert exact.decoded(result["deposition_bounds_exact"][index]) == (
            expected.lower,
            expected.upper,
        )
    assert (
        result["status"] == consumer.ENCLOSED
        and result["coefficient_precision_pass"] is False
    )


def test_refused_geometry_keeps_all_context_and_family_slots(tmp_path: Path) -> None:
    prediction, old = prediction_packets()
    cases = tuple(
        RingCaseResult((None,), ("not_executed",), None, "not_executed")
        for _ in range(6)
    )
    rows = consumer.prediction_contexts(prediction, cases)
    path = tmp_path / "closed.json"
    close_packet(path, prediction, rows)
    scores = consumer.score_closed(path, old, prediction)
    assert len(rows) == 18 and len(scores) == 54
    assert sum(row["status"] == consumer.DIRECT for row in scores) == 18
    assert sum(row["status"] == consumer.UNRESOLVED for row in scores) == 36
    summary = consumer.summarize(scores, old)
    assert summary["families"][0]["status"] == consumer.DIRECT
    assert all(row["status"] == consumer.UNRESOLVED for row in summary["families"][1:])
    assert all(row["status"] == consumer.UNRESOLVED for row in summary["pairwise"])


def test_closed_scores_preserve_nonclosed_finite_observations_and_direct_metrics(
    tmp_path: Path,
) -> None:
    prediction, old = prediction_packets()
    rows = consumer.prediction_contexts(prediction, case_results(prediction))
    path = tmp_path / "closed.json"
    close_packet(path, prediction, rows)
    scores = consumer.score_closed(path, old, prediction)
    assert scores[0]["observed_fraction"] == [0.2, 0.80000000000001]
    assert scores[0]["conditional_metric_ranges_exact"][
        exact.METRICS[0]
    ] == exact.encoded((Fraction(0.2), Fraction(0.2)))
    assert rows[0]["families"][consumer.FAMILIES[0]]["prediction_bounds_exact"][
        1
    ] == exact.encoded((Fraction(0.6000000000001), Fraction(0.6000000000001)))
    for score in scores:
        if score["family"] != consumer.FAMILIES[0]:
            context = next(
                row for row in rows if row["context_id"] == score["context_id"]
            )
            probability = exact.decoded(
                context["families"][score["family"]]["prediction_bounds_exact"][0]
            )
            assert score["conditional_metric_ranges_exact"] == exact.metric_ranges(
                probability, score["observed_fraction"]
            )
    summary = consumer.summarize(scores, old)
    assert len(summary["families"]) == len(summary["pairwise"]) == 3
    assert all(len(row["places"]) == 3 for row in summary["families"])


@pytest.mark.parametrize(
    "damage",
    [
        "closed_owner",
        "direct_vector",
        "observed",
        "duplicate_score",
        "missing_context",
        "source",
    ],
)
def test_closed_packet_and_original_owner_drift_refuse(
    tmp_path: Path, damage: str
) -> None:
    prediction, old = prediction_packets()
    rows = consumer.prediction_contexts(prediction, case_results(prediction))
    if damage == "closed_owner":
        rows[0] = deepcopy(rows[0])
        rows[0]["sample_ids"] = [99999]
    elif damage == "direct_vector":
        rows[0]["families"][consumer.FAMILIES[0]]["prediction_bounds_exact"][1] = [
            "3/5",
            "3/5",
        ]
    elif damage == "observed":
        old["scores"][1]["observed_fraction"] = [0.3, 0.7]
    elif damage == "duplicate_score":
        old["scores"][-1] = old["scores"][0]
    elif damage == "missing_context":
        rows.pop()
    else:
        old["source_commit"] = "foreign"
    path = tmp_path / "closed.json"
    close_packet(path, prediction, rows)
    with pytest.raises(ValueError):
        consumer.score_closed(path, old, prediction)


def test_no_score_reads_occur_before_closed_packet_and_no_summary_reweighting(
    tmp_path: Path,
) -> None:
    prediction, old = prediction_packets()
    with pytest.raises(FileNotFoundError):
        consumer.score_closed(tmp_path / "absent.json", {}, prediction)
    rows = consumer.prediction_contexts(prediction, case_results(prediction))
    path = tmp_path / "closed.json"
    close_packet(path, prediction, rows)
    scores = consumer.score_closed(path, old, prediction)
    with pytest.raises(ValueError, match="population"):
        consumer.summarize(scores[:-1], old)
    damaged = deepcopy(scores)
    damaged[0]["core"] = "FOREIGN"
    with pytest.raises(ValueError, match="ownership"):
        consumer.summarize(damaged, old)


def test_geometry_anchor_drift_and_incomplete_case_tuple_refuse() -> None:
    prediction, _ = prediction_packets()
    cases = case_results(prediction)
    with pytest.raises(ValueError, match="six"):
        consumer.prediction_contexts(prediction, cases[:-1])
    bad = deepcopy(prediction)
    bad["geometry"][0]["anchor_xy_m"][0][0] = 123.0
    with pytest.raises(ValueError, match="foreign"):
        consumer.prediction_contexts(bad, cases)
    bad = deepcopy(prediction)
    bad["contexts"][0]["training"].reverse()
    with pytest.raises(ValueError, match="anchor"):
        consumer.prediction_contexts(bad, cases)


def test_equal_place_mean_ignores_sample_count_and_pairwise_zero_is_unresolved(
    tmp_path: Path,
) -> None:
    prediction, old = prediction_packets()
    for row in old["scores"]:
        if row["family"] == consumer.FAMILIES[0]:
            for metric in exact.METRICS:
                row[metric] = CORES.index(row["core"]) / 2
    rows = consumer.prediction_contexts(prediction, case_results(prediction))
    path = tmp_path / "closed.json"
    close_packet(path, prediction, rows)
    scores = consumer.score_closed(path, old, prediction)
    for row in scores:
        if row["family"] != consumer.FAMILIES[0]:
            row["conditional_metric_ranges_exact"] = {
                metric: ["0", "1"] for metric in exact.METRICS
            }
    result = consumer.summarize(scores, old)
    for interval in result["families"][0]["equal_place"][
        "conditional_metric_ranges_exact"
    ].values():
        assert exact.decoded(interval) == (Fraction(1, 2), Fraction(1, 2))
    pair = result["pairwise"][-1]
    for metric in exact.METRICS:
        assert pair["metrics"][metric]["conditional_difference_range_exact"] == [
            "-1",
            "1",
        ]
        assert (
            pair["metrics"][metric]["conditional_resolution"]
            == "unresolved_continuous_law"
        )
