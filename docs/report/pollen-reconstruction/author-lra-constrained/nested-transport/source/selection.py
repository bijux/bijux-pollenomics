"""Train-only transport choice and separately frozen outer target evaluation."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def eligible_metric(row: dict[str, Any]) -> bool:
    if row["status"] not in {"scored", "refused"}:
        raise ValueError("Unknown inner prediction disposition")
    metrics = row["metrics"]
    if row["status"] == "refused":
        if metrics is not None:
            raise ValueError("Refused prediction cannot carry scores")
        return False
    if (
        not isinstance(metrics, dict)
        or metrics.get("status") != "scored"
        or metrics.get("target") != "pollen_composition"
    ):
        raise ValueError("Complete scored inner pollen metrics required")
    for key in ("mae_fraction", "rmse_fraction", "bias_fraction", "total_variation"):
        number = metrics[key]
        if type(number) not in (float, int) or not math.isfinite(number):
            raise ValueError("Finite inner metrics required")
    if not 0 <= metrics["total_variation"] <= 1:
        raise ValueError("Training-only TV must be a fraction")
    impossible = metrics["zero_probability_positive_count"]
    deviance = metrics["count_conditioned_deviance"]
    if (
        type(impossible) is not bool
        or (impossible and deviance is not None)
        or (
            not impossible
            and (
                type(deviance) not in (float, int)
                or not math.isfinite(deviance)
                or deviance < 0
            )
        )
    ):
        raise ValueError(
            "Explicit impossible-prediction deviance qualification required"
        )
    if any(
        type(value) not in (float, int) or not math.isfinite(value)
        for _taxon, value in metrics["signed_error_by_taxon"]
    ):
        raise ValueError("Finite per-taxon signed errors required")
    return True


def expected_forward_refusal(error: Exception) -> bool:
    from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
    from bijux_pollenomics_lra.models.errors import ValidationError

    return (
        isinstance(error, ValidationRefusal)
        and error.reason_code == "forward_model_refused"
        and isinstance(error.__cause__, ValidationError)
        and str(error.__cause__)
        == "Forward deposition has nonfinite or zero total mass"
        and str(error) == str(error.__cause__)
    )


def choose(
    outer: Any,
    baseline: str,
    rows: list[dict[str, Any]],
    methods: tuple[str, ...],
    groups: dict[str, str],
) -> dict[str, Any]:
    expected = set(outer.train_record_ids)
    target = outer.test_record_ids[0]
    fields = {
        "method",
        "outer_target",
        "inner_target",
        "inner_train_record_ids",
        "inner_train_group_ids",
        "baseline",
        "bin_id",
        "status",
        "metrics",
        "prediction_sha256",
    }
    seen = set()
    by_method: dict[str, list[dict[str, Any]]] = {method: [] for method in methods}
    for row in rows:
        key = (row["method"], row["inner_target"])
        if (
            set(row) != fields
            or row["outer_target"] != target
            or row["baseline"] != baseline
            or row["bin_id"] != "author-TW5"
            or row["method"] not in methods
            or row["inner_target"] not in expected
            or key in seen
        ):
            raise ValueError(
                "Exact training-only candidate/inner target score grid required"
            )
        inner = set(row["inner_train_record_ids"])
        inner_groups = set(row["inner_train_group_ids"])
        if (
            inner != expected - {row["inner_target"]}
            or inner_groups != {groups[x] for x in inner}
            or groups[target] in inner_groups
        ):
            raise ValueError("Outer site/core identity leaked into candidate choice")
        seen.add(key)
        by_method[row["method"]].append(row)
    if seen != {(method, record) for method in methods for record in expected}:
        raise ValueError("Complete fourteen inner targets per candidate required")
    ranking = []
    for method, values in by_method.items():
        eligible = [row for row in values if eligible_metric(row)]
        score = None
        if len(eligible) == 14:
            numbers = [row["metrics"]["total_variation"] for row in eligible]
            if any(
                type(n) not in (float, int) or not math.isfinite(n) or not 0 <= n <= 1
                for n in numbers
            ):
                raise ValueError("Finite training-only TV values required")
            score = math.fsum(numbers) / 14
        ranking.append(
            {
                "method": method,
                "complete_inner_predictions": len(eligible),
                "mean_inner_total_variation": score,
            }
        )
    complete = [row for row in ranking if row["complete_inner_predictions"] == 14]
    selected = (
        min(
            complete, key=lambda row: (row["mean_inner_total_variation"], row["method"])
        )["method"]
        if complete
        else None
    )
    return {
        "outer_target": target,
        "baseline": baseline,
        "selected_method": selected,
        "ranking": ranking,
        "status": "selected" if selected is not None else "refused",
        "selection_scope": "Only fourteen inner targets from this outer training set; no outer target count/score or alternate-window label argument.",
    }


def refused_slots(
    header: dict[str, Any], baselines: tuple[str, ...], reason: str, code: str
) -> list[dict[str, Any]]:
    return [
        {
            **header,
            "baseline": baseline,
            "status": "refused",
            "reason": reason,
            "reason_code": code,
        }
        for baseline in baselines
    ]


def predictions(
    common: dict[str, Any],
    original: dict[str, Any],
    spec: Any,
    experiment: dict[str, Any],
    contexts: list[dict[str, Any]],
    groups: dict[str, str],
    numeric: dict[str, Any],
    records: dict[str, Any],
    prepared: Path,
    method: str,
    training_ref: dict[str, Any],
) -> list[dict[str, Any]]:
    import numpy as np

    from bijux_pollenomics.analysis.lra_validation.experiments.prediction import (
        predict_fold,
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.reconstruction import (
        FoldFits,
    )

    by_record = {site.record.record_id: site for site in spec.sites}
    # Source record IDs remain separate from native site_id fields in requests.
    pair_hash = {}
    for key, item in numeric.items():
        anchor = next(
            site.record.record_id
            for site in spec.sites
            if site.record.site_id
            == item.payload()["regional"]["samples"][0]["site_id"]
        )
        pair_hash[(item.item_id, anchor)] = key
    slots = []
    for context in contexts:
        fold = context["fold"]
        target = context["target"]
        anchor = context["anchor"]
        selected = [
            records[pair_hash[(record, anchor)]] for record in context["predictors"]
        ]
        header = {
            "kind": context["kind"],
            "outer_target": context["outer"].test_record_ids[0],
            "target": target,
            "method": method,
            "fold": fold.as_dict(),
        }
        if any(any(choice is None for choice in row["selections"]) for row in selected):
            slots.extend(
                refused_slots(
                    header,
                    spec.baselines,
                    "Training ring has no accepted fixed start",
                    "no_accepted_training_start",
                )
            )
            continue
        regional = np.asarray(selected[0]["regional_cover"])
        if any(not np.array_equal(row["regional_cover"], regional) for row in selected):
            raise ValueError("Shared raw regional handoff differs")
        compositions = {
            groups[row["item_id"]]: row["selections"][-1]["composition"]
            for row in selected
        }
        identities = tuple(
            {
                "record_id": row["item_id"],
                "group_id": groups[row["item_id"]],
                "request_sha256": row["request_sha256"],
                "diagnostic_ring_evidence": row["selections"],
                "host_LRAProduct_claimed": False,
            }
            for row in selected
        )
        fits = FoldFits(
            by_record[anchor],
            tuple(by_record[x] for x in context["predictors"]),
            compositions,
            tuple(regional),
            identities,
            {
                "profile": "fixed-start-nested-transport-diagnostic",
                "host_LRAProduct_claimed": False,
                "training_evidence": training_ref,
            },
        )
        for baseline in spec.baselines:
            projected = original["SourceExperimentSpec"](
                {**experiment, "baselines": [baseline]}
            )
            try:
                rows, geometry = predict_fold(
                    projected,
                    fold,
                    by_record[target],
                    fits,
                    groups,
                    input_root=prepared,
                )
            except ValueError as error:
                if not expected_forward_refusal(error):
                    raise
                slots.extend(
                    refused_slots(
                        header, (baseline,), str(error), "forward_model_refused"
                    )
                )
                continue
            if len(rows) != 1 or rows[0]["baseline"] != baseline:
                raise ValueError("Exact independent baseline prediction required")
            slots.append(
                {
                    **header,
                    "baseline": baseline,
                    "status": "predicted",
                    "prediction": rows[0],
                    "geometry": geometry,
                }
            )
    if len(slots) != 675:
        raise ValueError("Complete45outer/630inner slots per method required")
    return slots


def evaluate(
    common: dict[str, Any],
    libraries: dict[str, dict[str, Any]],
    experiment: dict[str, Any],
    contexts: list[dict[str, Any]],
    groups: dict[str, str],
    all_slots: list[dict[str, Any]],
    prepared: Path,
    inputs: list[dict[str, Any]],
    output: Path,
    candidate_ref: dict[str, Any],
) -> dict[str, Any]:
    from bijux_pollenomics.analysis.lra_validation.metrics import score_pollen

    spec = libraries["original"]["SourceExperimentSpec"](experiment)
    sites = {s.record.record_id: s for s in spec.sites}
    methods = common["METHODS"]
    baselines = spec.baselines
    inner = [row for row in all_slots if row["kind"] == "inner"]
    outer = [row for row in all_slots if row["kind"] == "outer"]
    if len(inner) != 3150 or len(outer) != 225:
        raise ValueError("Complete3150inner/225outer dispositions required")
    inner_scores = []
    with (output / "inner-label-access.jsonl").open("x") as access:
        for slot in inner:
            fold = slot["fold"]
            header = {
                "method": slot["method"],
                "outer_target": slot["outer_target"],
                "inner_target": slot["target"],
                "inner_train_record_ids": fold["train_record_ids"],
                "inner_train_group_ids": fold["train_group_ids"],
                "baseline": slot["baseline"],
                "bin_id": "author-TW5",
                "prediction_sha256": common["digest"](slot),
                "status": "refused",
                "metrics": None,
            }
            if (
                slot["target"] == slot["outer_target"]
                or slot["outer_target"] in fold["train_record_ids"]
            ):
                raise ValueError("Outer target reached inner label access")
            if slot["status"] == "predicted":
                access.write(
                    json.dumps(
                        {
                            "outer_target": slot["outer_target"],
                            "inner_target": slot["target"],
                            "candidate_freeze": candidate_ref,
                            "purpose": "inner training-only score",
                        }
                    )
                    + "\n"
                )
                access.flush()
                counts = libraries["cohort"]["outcome_counts"](
                    prepared, sites[slot["target"]], spec, slot["prediction"], inputs
                )
                header.update(
                    status="scored",
                    metrics=score_pollen(
                        slot["prediction"]["pollen_fraction"], counts
                    ).as_dict(),
                )
            inner_scores.append(header)
    inner_ref = common["write"](output / "inner-scores.json", inner_scores)
    choices = []
    selected = []
    for context in contexts:
        if context["kind"] != "outer":
            continue
        fold = context["fold"]
        target = context["target"]
        for baseline in baselines:
            rows = [
                row
                for row in inner_scores
                if row["outer_target"] == target and row["baseline"] == baseline
            ]
            choice = choose(fold, baseline, rows, methods, groups)
            choices.append(choice)
            if choice["selected_method"] is None:
                selected.append(
                    {
                        "outer_target": target,
                        "baseline": baseline,
                        "status": "refused",
                        "reason": "No candidate has complete fourteen-inner-fold predictions",
                    }
                )
            else:
                selected.append(
                    next(
                        row
                        for row in outer
                        if row["outer_target"] == target
                        and row["baseline"] == baseline
                        and row["method"] == choice["selected_method"]
                    )
                )
    choice_ref = common["write"](
        output / "transport-selection.json",
        {"inner_scores": inner_ref, "choices": choices},
    )
    frozen = common["write"](
        output / "selected-prediction-freeze.json",
        {
            "candidate_freeze": candidate_ref,
            "selection": choice_ref,
            "slots": selected,
            "ordering": "All45 selected prediction/refusal slots frozen before new outer evaluation. Every site is already exposed development data.",
        },
    )
    reopened = common["decode"](
        common["checked"](
            output,
            {
                "path": "selected-prediction-freeze.json",
                "sha256": frozen["sha256"],
                "bytes": frozen["bytes"],
            },
        )
    )
    if len(reopened["slots"]) != 45:
        raise ValueError("Complete45 selected slots required")
    scores = []
    selected_scores = []
    with (output / "outer-label-access.jsonl").open("x") as access:
        for slot in outer:
            if slot["status"] != "predicted":
                continue
            access.write(
                json.dumps(
                    {
                        "outer_target": slot["target"],
                        "baseline": slot["baseline"],
                        "method": slot["method"],
                        "candidate_freeze": candidate_ref,
                        "selected_freeze": frozen,
                    }
                )
                + "\n"
            )
            access.flush()
            counts = libraries["cohort"]["outcome_counts"](
                prepared, sites[slot["target"]], spec, slot["prediction"], inputs
            )
            score = {
                "outer_target": slot["target"],
                "baseline": slot["baseline"],
                "method": slot["method"],
                **score_pollen(slot["prediction"]["pollen_fraction"], counts).as_dict(),
            }
            scores.append(score)
            if any(
                row.get("method") == slot["method"]
                and row["outer_target"] == slot["target"]
                and row["baseline"] == slot["baseline"]
                for row in reopened["slots"]
            ):
                selected_scores.append(score)
    return {
        "candidate_freeze": candidate_ref,
        "selection": choice_ref,
        "selected_freeze": frozen,
        "candidate_scores": scores,
        "candidate_dispositions": [
            {
                key: row[key]
                for key in (
                    "outer_target",
                    "method",
                    "baseline",
                    "status",
                    "reason",
                    "reason_code",
                )
                if key in row
            }
            for row in outer
        ],
        "inner_prediction_dispositions": {
            method: {
                "expected": 630,
                "predicted": sum(
                    row["method"] == method and row["status"] == "predicted"
                    for row in inner
                ),
                "refused": sum(
                    row["method"] == method and row["status"] == "refused"
                    for row in inner
                ),
            }
            for method in methods
        },
        "selected_scores": selected_scores,
        "selected_refusals": [row for row in selected if row["status"] == "refused"],
        "exposure": "Retrospective prior-exposed development. Structural train-only setting choice is not untouched or unbiased test accuracy.",
        "scientific_acceptance": "not_evaluated",
    }
