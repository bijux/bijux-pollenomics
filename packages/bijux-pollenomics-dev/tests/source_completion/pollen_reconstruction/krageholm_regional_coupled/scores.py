"""Reconstruct every method score or refusal from closed predictions and exact counts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .lineage import digest
from .native_fits import near
from .reading import decode, exact, product
from .scalar import AXIS, METHODS, metrics, number, require


def check_scores(
    repository: Path,
    pin: dict[str, Any],
    prediction_pin: dict[str, Any],
    prediction: dict[str, Any],
    context: dict[str, Any],
    tolerance: dict[str, Any],
) -> dict[str, Any]:
    directory = Path(pin["directory"])
    require(
        directory.is_relative_to(repository / "artifacts"),
        "score product escaped artifacts",
    )
    manifest, files = product(directory, pin["manifest_sha256"])
    require(
        manifest["phase"] == "scores"
        and manifest["scientific_content_sha256"] == pin["scientific_content_sha256"]
        and manifest["scientific_acceptance"] == "not_evaluated",
        "score product identity/posture differs",
    )
    scientific = manifest["scientific_payload"]
    require(
        scientific["prediction_manifest_sha256"] == prediction_pin["manifest_sha256"]
        and scientific["prediction_scientific_content_sha256"]
        == prediction_pin["scientific_content_sha256"],
        "score output refers to another prediction publication",
    )
    for name in ("scores", "summaries", "paired_baseline_differences"):
        exact(scientific[name], decode(files[name + ".json"]))
    spec = context["experiment"]
    inventory: dict[str, Any] = {
        "schema_version": "lra-source-pollen-outcomes.v1",
        "data_kind": "source_observations",
        "records": {
            site["record_id"]: site["raw"]
            for site in spec["sites"]
            if site["record_id"] in spec["target_record_ids"]
        },
    }
    require(
        scientific["outcome_inventory_sha256"] == digest(inventory),
        "scoring inventory includes wrong target/source role",
    )
    rows = scientific["scores"]
    keyed = {(row["fold_id"], row["baseline"]): row for row in rows}
    require(
        len(rows) == len(keyed) == 9
        and set(keyed)
        == {
            (fold["fold_id"], method)
            for fold in prediction["folds"]
            for method in METHODS
        },
        "all nine method score dispositions required",
    )
    dispositions = []
    errors: dict[tuple[str, str], float] = {}
    maximum = 0.0
    expected_access = {}
    for row in rows:
        key = row["fold_id"], row["baseline"]
        fold = next(fold for fold in prediction["folds"] if fold["fold_id"] == key[0])
        target = fold["test_record_ids"][0]
        require(
            row["record_id"] == target
            and row["record_ids"] == [target]
            and row["target"] == "pollen_composition"
            and row["error_unit"] == "fraction"
            and row["evaluation_role"] == "heldout_pollen_prediction"
            and row["group_id"] == fold["test_group_ids"][0],
            "score target/population/units differ",
        )
        if key not in prediction["predictions"]:
            require(
                row["score"]["status"] == "prediction_failed"
                and row["score"]["mae_fraction"] is None
                and "prediction" not in row,
                "failed prediction must retain unavailable score",
            )
        else:
            available = prediction["predictions"][key]
            require(
                row["score"]["status"] == "scored",
                "available fixed source target score is missing or refused",
            )
            require(
                row["prediction_manifest_sha256"]
                == available["row"]["prediction_manifest_sha256"],
                "score row differs from closed prediction identity",
            )
            exact(row["prediction"], available["row"]["pollen_fraction"])
            code = next(
                code
                for code, identifier in context["ids"].items()
                if identifier == target
            )
            raw = context["members"][code + "-raw.json"]["sample"]
            counts = raw["counts"]
            exact(
                row["observation"]["pollen_count"], dict(zip(AXIS, counts, strict=True))
            )
            reference = inventory["records"][target]
            exact(row["observation_reference"], reference)
            require(
                row["observation_sha256"]
                == row["observation"]["source_raw_sha256"]
                == reference["sha256"]
                and row["observation"]["record_id"] == target
                and row["observation"]["sample_id"] == raw["sample_id"]
                and row["bin_id"] == raw["bin_id"],
                "observed source/count identity differs",
            )
            expected = metrics(available["pollen"], counts)
            score = row["score"]
            require(
                score["taxon_count"] == score["scored_taxon_count"] == 2
                and score["missing_observed_taxa"] == []
                and score["observed_total_count"] == sum(counts),
                "score taxon/count denominator differs",
            )
            for metric, field in (
                ("mean_absolute_fraction_error", "mae_fraction"),
                ("total_variation", "total_variation"),
            ):
                maximum = max(maximum, near(score[field], expected[metric], tolerance))
            signed = dict(score["signed_error_by_taxon"])
            truth = [number(value) / sum(counts) for value in counts]
            for index, taxon in enumerate(AXIS):
                near(
                    signed[taxon], available["pollen"][index] - truth[index], tolerance
                )
            errors[key] = float(expected["mean_absolute_fraction_error"])
            expected_access[target] = {
                "record_id": target,
                "observation_sha256": reference["sha256"],
                "prediction_manifest_sha256": prediction_pin["manifest_sha256"],
                "ordering": "verified_published_predictions_before_outcome_open",
            }
        dispositions.append(
            {"fold_id": key[0], "method": key[1], "status": row["score"]["status"]}
        )
    actual_access = (
        decode(files["outcome_access.json"]) if "outcome_access.json" in files else []
    )
    require(
        len(actual_access) == len(expected_access),
        "duplicate/missing actual outcome access receipt",
    )
    exact(
        sorted(actual_access, key=lambda row: row["record_id"]),
        sorted(expected_access.values(), key=lambda row: row["record_id"]),
    )
    for summary in scientific["summaries"]:
        method = summary["baseline"]
        require(
            method in METHODS
            and summary["target"] == "pollen_composition"
            and summary["requested"] == 3,
            "fixed per-method summary population differs",
        )
        expected_statuses = dict(
            Counter(row["score"]["status"] for row in rows if row["baseline"] == method)
        )
        exact(summary["by_status"], expected_statuses)
        values = [
            value for (fold_id, label), value in errors.items() if label == method
        ]
        require(summary["scored"] == len(values), "summary drops a scored/refused fold")
        if values:
            near(summary["mean_mae_fraction"], sum(values) / len(values), tolerance)
        else:
            require(
                summary["mean_mae_fraction"] is None,
                "no scored folds cannot have a mean",
            )
    require(len(scientific["summaries"]) == 3, "all three method summaries required")
    expected_pairs = {
        (fold["fold_id"], method)
        for fold in prediction["folds"]
        for method in METHODS[1:]
        if (fold["fold_id"], method) in errors
        and (fold["fold_id"], "training_mean") in errors
    }
    pairs = scientific["paired_baseline_differences"]
    require(
        len(pairs) == len(expected_pairs)
        and {(row["fold_id"], row["baseline"]) for row in pairs} == expected_pairs,
        "matched descriptive method differences drop or add folds",
    )
    for row in pairs:
        key = row["fold_id"], row["baseline"]
        require(
            row["reference_baseline"] == "training_mean"
            and row["target"] == "pollen_composition",
            "descriptive reference method differs",
        )
        near(
            row["mae_improvement_fraction"],
            errors[(key[0], "training_mean")] - errors[key],
            tolerance,
        )
    return {
        "dispositions": dispositions,
        "scored": len(errors),
        "refused": 9 - len(errors),
        "maximum_scalar_difference": maximum,
    }
