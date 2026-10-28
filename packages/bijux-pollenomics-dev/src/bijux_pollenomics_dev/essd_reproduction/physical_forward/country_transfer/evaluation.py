"""Score closed forecasts and retain common-support descriptive denominators."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from copy import deepcopy
from itertools import combinations
import math
from pathlib import Path
from typing import Any, cast

from ...author_lra_spatial.products import reopen
from ..inputs import require
from .inputs import AXIS, METHODS, METRICS, counts, semantic_sha
from .prediction import context_specs


def native_score(prediction: list[float], vector: tuple[int, int]) -> dict[str, Any]:
    from bijux_pollenomics.analysis.lra_validation.metrics import (
        hellinger_distance,
        score_pollen,
    )

    predicted = dict(zip(AXIS, prediction, strict=True))
    observed = dict(zip(AXIS, vector, strict=True))
    result = score_pollen(predicted, observed)
    require(
        result.status == "scored"
        and result.observed_total_count == sum(vector)
        and result.taxon_count == 2,
        "Native score count denominator differs",
    )
    return {
        "mae_fraction": result.mae_fraction,
        "total_variation": result.total_variation,
        "hellinger_stable": hellinger_distance(
            predicted,
            {k: v / sum(vector) for k, v in observed.items()},
            arithmetic_profile="stable",
        ),
        "signed_error_by_taxon": [
            prediction[i] - vector[i] / sum(vector) for i in range(2)
        ],
    }


def score_closed(
    directory: Path,
    prediction_pin: dict[str, Any],
    response_pin: dict[str, Any],
    packet: dict[str, Any],
    protocol: dict[str, Any],
    *,
    score: Callable[[list[float], tuple[int, int]], dict[str, Any]] = native_score,
) -> list[dict[str, Any]]:
    # Every byte/member is authenticated before the first target score call.
    response = reopen(directory, response_pin)
    prediction = reopen(directory, prediction_pin)
    require(
        response["schema_version"] == "nordic-physical-responses.v1"
        and prediction["schema_version"] == "nordic-physical-predictions.v1"
        and prediction["response_file"] == response_pin,
        "Closed forecast/response identity differs",
    )
    expected = {
        f"{p['id']}/{e}/{t}/{w[0]}-{w[1]}/{s}"
        for p, e, t, w, s in context_specs(protocol)
    }
    contexts = prediction["contexts"]
    require(
        len(contexts) == 216
        and len({r["context_id"] for r in contexts}) == 216
        and {r["context_id"] for r in contexts} == expected
        and all(set(r["families"]) == set(METHODS) for r in contexts),
        "Complete closed forecast inventory required",
    )
    rows = []
    for context in contexts:
        identity = context["identity"]
        require(identity["axis"] == list(AXIS), "Forecast score axis differs")
        key = identity["target_core"]
        index = protocol["windows"].index(identity["window_cal_bp"])
        cell = packet["cores"][key]["windows"][index]
        available = cell["status"] == "supported"
        vector = None
        if available:
            vector = counts(cell["panel_counts"])
            require(
                sum(vector) == cell["panel_N"], "Observed panel denominator differs"
            )
        for method in METHODS:
            family = context["families"][method]
            row = {
                "context_id": context["context_id"],
                "identity": deepcopy(identity),
                "method": method,
                "status": "unavailable_target_observation",
                "reason": cell["status"],
                "target_counts": list(vector) if vector is not None else None,
                "target_panel_N": cell["panel_N"],
                "target_sample_ids": deepcopy(cell["sample_ids"]),
                "target_owner_count": len(cell["sample_ids"]),
                "target_source_ref": {
                    "ledger": key,
                    "window_index": index,
                    "window_sha256": semantic_sha(cell),
                },
                "pollen_fraction": deepcopy(family["pollen_fraction"]),
                "metrics": None,
            }
            if available and family["status"] != "predicted":
                row.update(status="prediction_refused", reason=family["reason"])
            elif available:
                require(vector is not None, "Defined observed vector required")
                values = score(family["pollen_fraction"], cast(tuple[int, int], vector))
                require(
                    set(values) == {*METRICS, "signed_error_by_taxon"}
                    and all(
                        type(values[k]) in (int, float)
                        and math.isfinite(values[k])
                        and 0 <= values[k] <= 1
                        for k in METRICS
                    )
                    and len(values["signed_error_by_taxon"]) == 2
                    and all(
                        type(v) in (int, float) and math.isfinite(v)
                        for v in values["signed_error_by_taxon"]
                    ),
                    "Finite complete native score required",
                )
                row.update(status="scored", reason=None, metrics=values)
            rows.append(row)
    require(len(rows) == 432, "All432 method score dispositions required")
    return rows


def _macro(rows: list[dict[str, Any]]) -> dict[str, float] | None:
    return (
        {k: math.fsum(r["metrics"][k] for r in rows) / len(rows) for k in METRICS}
        if rows
        else None
    )


def _owner_weighted(rows: list[dict[str, Any]]) -> dict[str, Any]:
    denominator = sum(r["target_owner_count"] for r in rows)
    require(
        all(
            type(r["target_owner_count"]) is int
            and r["target_owner_count"] == len(r["target_sample_ids"])
            and r["target_owner_count"] > 0
            for r in rows
        ),
        "Exact native target-owner denominator required",
    )
    return {
        "owner_denominator": denominator,
        "metrics": {
            k: math.fsum(r["metrics"][k] * r["target_owner_count"] for r in rows)
            / denominator
            for k in METRICS
        }
        if denominator
        else None,
    }


def _group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        targets[row["identity"]["target_core"]].append(row)
    per_target = []
    for key, items in sorted(targets.items()):
        scored = [r for r in items if r["status"] == "scored"]
        predicted = sum(r["pollen_fraction"] is not None for r in items)
        per_target.append(
            {
                "target_core": key,
                "physical_family": items[0]["identity"]["physical_family"],
                "requested": len(items),
                "predicted": predicted,
                "refused": len(items) - predicted,
                "scored": len(scored),
                "macro": _macro(scored),
            }
        )
    defined = [r["macro"] for r in per_target if r["macro"] is not None]
    predicted = sum(r["pollen_fraction"] is not None for r in rows)
    scored = [r for r in rows if r["status"] == "scored"]
    return {
        "requested": len(rows),
        "predicted": predicted,
        "refused": len(rows) - predicted,
        "unavailable_targets": sum(
            r["status"] == "unavailable_target_observation" for r in rows
        ),
        "scored": len(scored),
        "target_count": len(targets),
        "per_target": per_target,
        "macro": {k: math.fsum(v[k] for v in defined) / len(defined) for k in METRICS}
        if defined
        else None,
        "native_owner_weighted": _owner_weighted(scored),
    }


def _channel(profile: str, scope: str, method: str) -> dict[str, str]:
    return {
        "profile": profile,
        "experiment": "swedish_training_scope",
        "scope": scope,
        "method": method,
    }


def _matched(
    rows: list[dict[str, Any]], protocol: dict[str, Any]
) -> list[dict[str, Any]]:
    profiles = [p["id"] for p in protocol["profiles"]]
    configurations = [("swedish_scope_methods:" + p, [p]) for p in profiles]
    configurations += [
        ("density_sensitivity_swedish", profiles[:2]),
        ("core_sensitivity_swedish", [profiles[0], profiles[2]]),
    ]
    results = []
    for name, selected in configurations:
        channels = [
            _channel(p, s, m)
            for p in selected
            for s in ("swedish_only", "pooled_nordic")
            for m in METHODS
        ]
        channel_rows = []
        for channel in channels:
            subset = [
                r
                for r in rows
                if all(
                    (r["method"] if k == "method" else r["identity"][k]) == v
                    for k, v in channel.items()
                )
            ]
            indexed = {
                (r["identity"]["target_core"], tuple(r["identity"]["window_cal_bp"])): r
                for r in subset
            }
            require(
                len(indexed) == len(subset) == 18,
                "Full Swedish comparison population required",
            )
            channel_rows.append(indexed)
        keys = list(channel_rows[0])
        matched = []
        unmatched = []
        for key in keys:
            items = [indexed[key] for indexed in channel_rows]
            if all(r["status"] == "scored" for r in items):
                first = items[0]
                require(
                    all(
                        r["identity"]["physical_family"]
                        == first["identity"]["physical_family"]
                        and r["identity"]["axis"] == first["identity"]["axis"]
                        and r["target_counts"] == first["target_counts"]
                        and r["target_panel_N"] == first["target_panel_N"]
                        and r["target_sample_ids"] == first["target_sample_ids"]
                        for r in items
                    ),
                    "Matched target source response differs",
                )
                matched.append(key)
            else:
                unmatched.append(
                    {
                        "target_core": key[0],
                        "physical_family": items[0]["identity"]["physical_family"],
                        "window_cal_bp": list(key[1]),
                        "reason": "incomplete_common_support",
                    }
                )
        summaries = []
        for channel, indexed in zip(channels, channel_rows, strict=True):
            selected_rows = [indexed[k] for k in matched]
            group = _group(selected_rows)
            summaries.append(
                {
                    "channel": channel,
                    "physical_targets": group["target_count"],
                    "matched_windows": len(matched),
                    "per_target": [
                        {
                            "target_core": r["target_core"],
                            "physical_family": r["physical_family"],
                            "matched_windows": r["scored"],
                            "macro": r["macro"],
                        }
                        for r in group["per_target"]
                    ],
                    "macro": group["macro"],
                    "native_owner_weighted": group["native_owner_weighted"],
                }
            )
        pairwise = []
        for first, second in combinations(summaries, 2):
            difference = (
                {k: first["macro"][k] - second["macro"][k] for k in METRICS}
                if first["macro"] is not None
                else None
            )
            pairwise.append(
                {
                    "first": first["channel"],
                    "second": second["channel"],
                    "mean_difference": difference,
                }
            )
        results.append(
            {
                "comparison_id": name,
                "channels": channels,
                "requested_target_windows": 18,
                "matched_target_windows": len(matched),
                "unmatched": unmatched,
                "channels_summary": summaries,
                "pairwise": pairwise,
            }
        )
    return results


def summarize(rows: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    require(
        len(rows) == 432 and len({(r["context_id"], r["method"]) for r in rows}) == 432,
        "Complete unique score population required",
    )
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        identity = row["identity"]
        for country in (identity["country"], "ALL"):
            grouped[
                (
                    identity["profile"],
                    identity["experiment"],
                    identity["scope"],
                    row["method"],
                    country,
                )
            ].append(row)
    return {
        "schema_version": "nordic-physical-summary.v1",
        "groups": [
            {
                **dict(
                    zip(
                        ("profile", "experiment", "scope", "method", "country"),
                        key,
                        strict=True,
                    )
                ),
                **_group(items),
            }
            for key, items in sorted(grouped.items())
        ],
        "matched": _matched(rows, protocol),
    }
