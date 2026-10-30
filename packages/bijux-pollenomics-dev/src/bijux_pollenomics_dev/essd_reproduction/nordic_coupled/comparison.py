"""Compare stored coupled and direct pollen scores on exactly matched inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    read_experiment_product,
    read_member,
)

from . import workflow as shared

read, require, physical = shared.read, shared.require, shared.physical
AXIS = ("Betula", "Ulmus")
CORES = {
    "BOKE": (28872, 54001, 39241),
    "BUS": (28869, 53995, 39238),
    "SOLSOE83": (3432, 4446, 4304),
}
OLD_FREEZE = "2591edeb9ebc73168ea278f422e7ccb0963e592b1db1961783079a068653c24b"
OLD_SCORES = "dc8881e216aa1bc27d4eb2c46307b9501d6ffd0a0c0d06be4b15191dd55e6dc5"
INPUTS = "8738dbe8c7fcf29795c9bfde58fd6d26345ed3e367bdd26e42182b5867d8e05f"


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def product(directory: Path, checksum: str) -> dict[str, Any]:
    """Use the maintained reader for complete, including nested, native products."""
    native, manifest = read_experiment_product(
        directory, expected_manifest_sha256=checksum
    )
    require(
        manifest["profile"] == "source-observations-withheld-site-baselines-v1"
        and manifest["phase"] in {"predictions", "scores"},
        "Wrong native product profile/phase",
    )
    scientific = cast(dict[str, Any], manifest["scientific_payload"])
    key = "scores" if manifest["phase"] == "scores" else "training"
    actual_rows = read_member(native, key + ".json")
    require(actual_rows == scientific[key], "Native member/scientific rows differ")
    return cast(dict[str, Any], manifest)


def count_identity(axis: list[str], values: list[int]) -> str:
    require(
        axis == list(AXIS)
        and len(values) == 2
        and all(type(v) is int and v >= 0 for v in values)
        and sum(values) > 0,
        "Exact positive two-taxon count axis required",
    )
    return digest({"axis": axis, "counts": values})


def joined(
    target: str,
    scope: str,
    window: list[float],
    current: dict[str, Any],
    context: dict[str, Any],
    direct: dict[str, Any],
    cells: dict[str, Any],
    originals: dict[str, Any],
    training: dict[str, Any],
) -> dict[str, Any]:
    """Return a pair only after exact identities, inputs and eligibility agree."""
    result: dict[str, Any] = {
        "core": target,
        "window_cal_bp": window,
        "direct_scope": scope,
        "coupled_method": "training_mean",
        "status": "unmatched",
    }
    try:
        require(
            current["score"]["status"] == "scored" and direct["status"] == "scored",
            "Unscored outcome",
        )
        identity = direct["identity"]
        require(
            context["identity"] == identity
            and identity["core"] == target
            and identity["window_cal_bp"] == window
            and identity["axis"] == list(AXIS)
            and identity["scope"] == scope,
            "Target identity/axis/window differs",
        )
        require(
            tuple(identity[k] for k in ("physical_site", "dataset", "collection_unit"))
            == CORES[target],
            "Native target identity differs",
        )
        for field in ("mae_fraction", "total_variation"):
            require(
                all(
                    type(x) in (int, float) and math.isfinite(x)
                    for x in (current["score"][field], direct[field])
                ),
                "Finite stored score required",
            )
        target_cell = cells[target]
        observed = current["observation"]["pollen_count"]
        require(
            observed
            == direct["target_counts"]
            == dict(zip(AXIS, target_cell["counts"], strict=True)),
            "Target count vector differs",
        )
        require(
            direct["target_panel_N"] == sum(target_cell["counts"])
            and direct["target_source_support_sha256"] == target_cell["support"],
            "Target N/support differs",
        )
        require(
            count_identity(list(AXIS), target_cell["counts"])
            == count_identity(list(AXIS), originals[target]["counts"])
            and target_cell["support"] == originals[target]["support"],
            "Original/current target source differs",
        )
        training_cores = set(CORES) - {target}
        anchor = min(training_cores, key=lambda c: CORES[c][0])
        local = next(c for c in training_cores if c != anchor)
        expected_records = {cells[c]["record"] for c in training_cores}
        require(
            set(training["outer_fold"]["train_record_ids"]) == expected_records
            and training["outer_fold"]["test_record_ids"] == [target_cell["record"]],
            "Fold/source exclusion differs",
        )
        require(
            training["regional_anchor_record_id"] == cells[anchor]["record"]
            and [x["record_id"] for x in training["training_products"]]
            == [cells[local]["record"]],
            "Regional/local source roles differ",
        )
        expected = training_cores if scope == "pooled_eligible_nordic" else {local}
        require(
            scope in {"pooled_eligible_nordic", "swedish_only"}, "Unknown direct scope"
        )
        sources = context["training_sources"]
        require(
            len(sources) == len(expected) and {x["core"] for x in sources} == expected,
            "Old source eligibility differs",
        )
        for source in sources:
            core = source["core"]
            require(
                tuple(
                    source[k] for k in ("physical_site", "dataset", "collection_unit")
                )
                == CORES[core]
                and source["window_cal_bp"] == window,
                "Training native/window identity differs",
            )
            new, old = cells[core], originals[core]
            require(
                count_identity(list(AXIS), new["counts"])
                == count_identity(list(AXIS), old["counts"]),
                "Training count hash differs",
            )
            require(
                source["source_support_sha256"] == new["support"] == old["support"]
                and source["projected_panel_N"] == sum(new["counts"]),
                "Training support/N differs",
            )
        require(
            context["families"]["direct_panel_mean"]["status"] == "predicted",
            "Old direct prediction unavailable",
        )
        result.update(
            status="paired",
            coupled={
                k: current["score"][k] for k in ("mae_fraction", "total_variation")
            },
            direct={k: direct[k] for k in ("mae_fraction", "total_variation")},
            target_count_sha256=count_identity(list(AXIS), target_cell["counts"]),
            target_panel_N=sum(target_cell["counts"]),
            training_roles={
                "regional_proxy": anchor,
                "local_predictor": local,
                "direct_sources": sorted(expected),
            },
            training_count_sha256={
                c: count_identity(list(AXIS), cells[c]["counts"]) for c in expected
            },
            old_source_refusals=context["source_refusals"],
        )
    except (ValueError, KeyError, TypeError) as exc:
        result.update(
            reason=str(exc), current_score_status=current.get("score", {}).get("status")
        )
    return result


def execute(args: argparse.Namespace) -> dict[str, Any]:
    require(not args.output.exists(), "Absent output required")
    physical(args.output)
    _, observed = read(args.input_inventory, INPUTS, 65536)
    rows, pins = shared.input_scope(
        args.input_root,
        args.numerical_input_manifest,
        args.numerical_input_manifest_sha256,
    )
    observed_members = {
        str(Path(x["path"]).relative_to(args.input_root)): (x["sha256"], x["bytes"])
        for x in observed["members"]
    }
    require(
        observed_members == {p["path"]: (p["sha256"], p["bytes"]) for p in pins},
        "Original80/current numerical input map differs",
    )
    physical(args.repository)
    public = (
        args.repository / "reports/science/pollen-reconstruction/matched-pollen-forward"
    )
    _, freeze = read(public / "prediction-freeze.json", OLD_FREEZE, 1048576)
    _, old_scores = read(public / "scores.json", OLD_SCORES, 1048576)
    require(
        old_scores["prediction_freeze"]["sha256"] == OLD_FREEZE,
        "Old score/freeze join differs",
    )
    originals = {}
    for pin in freeze["input_pins"]:
        _, value = read(Path(pin["path"]), pin["sha256"], 4194304)
        if "/swedish-static-basin-scenarios/report.json" in pin["path"]:
            originals.update(
                {
                    x["metadata_code"]: x
                    for x in value["cores"]
                    if x["metadata_code"] in {"BOKE", "BUS"}
                }
            )
        elif "/nordic-static-basin-scenarios/report.json" in pin["path"]:
            originals["SOLSOE83"] = next(
                x
                for x in value["cases"]
                if x["case_id"] == "4446.metadata_static_radius"
            )
    _, prepared = read(args.prediction_batch, args.prediction_batch_sha256, 2097152)
    _, scored = read(args.score_batch, args.score_batch_sha256, 2097152)
    require(
        prepared["phase"] == "prepare"
        and scored["phase"] == "score"
        and prepared["all_bins_accounted"] is True
        and scored["all_bins_accounted"] is True,
        "Incomplete native batch",
    )
    require(
        prepared["input_manifest_sha256"]
        == scored["input_manifest_sha256"]
        == args.numerical_input_manifest_sha256
        and scored["prediction_index_sha256"] == args.prediction_batch_sha256,
        "Prediction/score/input batch lineage differs",
    )
    output = []
    for index, input_row in enumerate(rows):
        name = input_row["directory"]
        window = [float(x) for x in name.removeprefix("cal-bp-").split("-")]
        directory = args.input_root / name
        cells = {}
        provenance = json.loads((directory / "projection.json").read_bytes())
        for core in CORES:
            raw = json.loads((directory / (core + "-raw.json")).read_bytes())
            original = next(x for x in provenance if x["native_site"] == CORES[core][0])
            require(raw["taxa"] == list(AXIS), "Current raw axis differs")
            cells[core] = {
                "record": original["record_id"],
                "counts": raw["sample"]["counts"],
                "support": original["source_support_sha256"],
            }
        old_cells = {}
        for core, original in originals.items():
            candidates = [
                x
                for x in original["results"]
                if [x["younger_cal_bp"], x["older_cal_bp_exclusive"]] == window
                and (core == "SOLSOE83" or x["profile"] == "metadata_radius_wind_3")
            ]
            require(len(candidates) == 1, "Exact original window required")
            cell = candidates[0]
            old_cells[core] = {
                "counts": [
                    cell["counts"][0][original["parameter_taxa"].index(t)] for t in AXIS
                ],
                "support": cell[
                    "local_actual_source_support_sha256"
                    if core == "SOLSOE83"
                    else "local_native_sample_support_sha256"
                ],
            }
        prior, current = prepared["bins"][index], scored["bins"][index]
        require(prior["bin"] == current["bin"] == name, "Batch bin differs")
        training, scores = [], []
        if "prediction" in prior and "scoring" in current:
            prediction = product(
                Path(prior["prediction"]["directory"]),
                prior["prediction"]["manifest_sha256"],
            )
            native_scores = product(
                Path(current["scoring"]["directory"]),
                current["scoring"]["manifest_sha256"],
            )
            require(
                native_scores["scientific_payload"]["prediction_manifest_sha256"]
                == prior["prediction"]["manifest_sha256"],
                "Native score/prediction join differs",
            )
            training, scores = (
                prediction["scientific_payload"]["training"],
                native_scores["scientific_payload"]["scores"],
            )
        for core in CORES:
            for scope in ("pooled_eligible_nordic", "swedish_only"):
                base = {
                    "core": core,
                    "window_cal_bp": window,
                    "direct_scope": scope,
                    "status": "unmatched",
                    "reason": "No existing Swedish-target S2 row"
                    if core == "SOLSOE83"
                    else "Current prediction/score unavailable",
                    "current_bin_disposition": current,
                }
                candidates = [
                    x
                    for x in scores
                    if x["record_id"] == cells[core]["record"]
                    and x["baseline"] == "training_mean"
                    and x["target"] == "pollen_composition"
                ]
                if core != "SOLSOE83" and len(candidates) == 1:
                    ctx = [
                        x
                        for x in freeze["contexts"]
                        if x["identity"]["core"] == core
                        and x["identity"]["scope"] == scope
                        and x["identity"]["window_cal_bp"] == window
                    ]
                    direct = [
                        x
                        for x in old_scores["outcomes"]
                        if x["identity"]["core"] == core
                        and x["identity"]["scope"] == scope
                        and x["identity"]["window_cal_bp"] == window
                        and x["family"] == "direct_panel_mean"
                    ]
                    fits = [
                        x for x in training if x["fold_id"] == candidates[0]["fold_id"]
                    ]
                    if len(ctx) == len(direct) == len(fits) == 1:
                        base = joined(
                            core,
                            scope,
                            window,
                            candidates[0],
                            ctx[0],
                            direct[0],
                            cells,
                            old_cells,
                            fits[0],
                        )
                output.append(base)
    # Reauthenticate source buffers and both batch indexes after the read-only join.
    shared.input_scope(
        args.input_root,
        args.numerical_input_manifest,
        args.numerical_input_manifest_sha256,
    )
    read(args.prediction_batch, args.prediction_batch_sha256, 2097152)
    read(args.score_batch, args.score_batch_sha256, 2097152)
    read(args.input_inventory, INPUTS, 65536)
    read(public / "prediction-freeze.json", OLD_FREEZE, 1048576)
    read(public / "scores.json", OLD_SCORES, 1048576)
    for pin in freeze["input_pins"]:
        read(Path(pin["path"]), pin["sha256"], 4194304)
    result = {
        "schema_version": "nordic-coupled-direct-comparison.v1",
        "input_execution_epoch": observed["candidate"],
        "prediction_epoch": prepared["execution_epoch"],
        "score_epoch": scored["execution_epoch"],
        "old_S2_epoch": freeze["candidate"],
        "comparisons": output,
        "paired_rows": sum(x["status"] == "paired" for x in output),
        "current_method_dispositions": [
            x.get("prediction", {}).get("method_dispositions", [])
            for x in prepared["bins"]
        ],
        "scope": "Training_mean physical outcome only; other two physical baselines are dependent one-predictor variants retained in native products. Two separately labeled direct comparators, not36independent target windows. No new scores/fits or untouched/field/vegetation/uncertainty acceptance.",
    }
    payload = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    require(len(payload) <= 2097152, "Comparison output exceeds2MiB")
    with args.output.open("xb") as stream:
        stream.write(payload)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in (
        "repository",
        "input-root",
        "input-inventory",
        "numerical-input-manifest",
        "prediction-batch",
        "score-batch",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("numerical-input-manifest", "prediction-batch", "score-batch"):
        parser.add_argument("--" + name + "-sha256", required=True)
    execute(parser.parse_args())


if __name__ == "__main__":
    main()
