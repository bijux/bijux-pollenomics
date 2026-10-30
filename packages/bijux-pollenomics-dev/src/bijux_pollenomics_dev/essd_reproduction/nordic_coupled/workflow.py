"""Batch conditional coupled predictions and separately authenticated scoring."""

from __future__ import annotations

import argparse
from collections import Counter
from functools import partial
import hashlib
import json
from pathlib import Path
import stat
from typing import Any

NAMES = tuple(f"cal-bp-{x}-{x + 500}" for x in range(2700, 5700, 500))
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
PROTOCOL_SHA256 = "835a1c9342ee086cdf6a755c6e6b450c1933d9f3b50625f9895349d9636990a6"
MAX_OUTPUT = 134217728


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def physical(path: Path) -> None:
    require(
        path.is_absolute() and ".." not in path.parts, "Absolute physical path required"
    )
    require(not any(p.is_symlink() for p in (path, *path.parents)), "Alias refused")


def read(path: Path, checksum: str, maximum: int) -> tuple[bytes, Any]:
    physical(path)
    before = path.stat()
    require(
        stat.S_ISREG(before.st_mode)
        and before.st_nlink == 1
        and before.st_size <= maximum,
        "Bounded single-link regular input required",
    )
    raw = path.read_bytes()
    after = path.stat()
    stable_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    require(
        all(getattr(after, key) == getattr(before, key) for key in stable_fields)
        and len(raw) == before.st_size
        and hashlib.sha256(raw).hexdigest() == checksum,
        "Input buffer identity differs",
    )

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value = {}
        for key, item in items:
            require(key not in value, "Duplicate JSON key")
            value[key] = item
        return value

    def nonfinite(token: str) -> Any:
        raise ValueError("Nonfinite JSON token: " + token)

    return raw, json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def write(root: Path, value: object) -> None:
    raw = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= 2097152, "Batch index exceeds bound")
    # The owned ledger is refreshed as each bin terminates; native products stay immutable.
    (root / "batch.json").write_bytes(raw)


def input_scope(
    root: Path, manifest: Path, checksum: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Authenticate the exact root-owned80-member namespace before package entry."""
    physical(root)
    _, pins = read(manifest, checksum, 65536)
    require(
        type(pins) is list and len(pins) == 80,
        "Exact80-member input inventory required",
    )
    members = set()
    total = 0
    for pin in pins:
        require(set(pin) == {"path", "sha256", "bytes"}, "Closed input pin required")
        relative = Path(pin["path"])
        require(
            not relative.is_absolute()
            and ".." not in relative.parts
            and relative.as_posix() == pin["path"],
            "Confined relative input required",
        )
        require(pin["path"] not in members, "Duplicate input pin")
        members.add(pin["path"])
        raw, _ = read(root / relative, pin["sha256"], 65536)
        require(len(raw) == pin["bytes"], "Input size differs")
        total += len(raw)
    expected = {"inputs.json", "source-pins.json"}
    for name in NAMES:
        expected.update(
            f"{name}/{member}.json"
            for member in (
                "chronology",
                "taxa",
                "parameters",
                "dependency_lock",
                "decision",
                "BOKE-raw",
                "BUS-raw",
                "SOLSOE83-raw",
                "BOKE-geometry",
                "BUS-geometry",
                "SOLSOE83-geometry",
                "experiment",
                "projection",
            )
        )
    require(
        members == expected and total <= 2097152,
        "Input namespace or total bound differs",
    )
    actual = set()
    for path in root.rglob("*"):
        physical(path)
        require(path.is_dir() or path.is_file(), "Special input refused")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    require(actual == expected, "Unlisted input member")
    by_name = {p["path"]: p for p in pins}
    _, index = read(root / "inputs.json", by_name["inputs.json"]["sha256"], 65536)
    require(
        [r["directory"] for r in index["experiments"]] == list(NAMES),
        "Six ordered input bins required",
    )
    for row in index["experiments"]:
        require(
            row["experiment"]["path"] == "experiment.json"
            and row["experiment"]["sha256"]
            == by_name[row["directory"] + "/experiment.json"]["sha256"],
            "Experiment/index binding differs",
        )
    return index["experiments"], pins


def apis() -> dict[str, Any]:
    from bijux_pollenomics.analysis.lra.api import LRARefusal
    from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
    from bijux_pollenomics.analysis.lra_validation.experiments import (
        SourceExperimentSpec,
        prepare_experiment_predictions,
        read_withheld_predictions,
        score_experiment_predictions,
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
        read_experiment_product,
    )

    return {
        "spec": SourceExperimentSpec,
        "prepare": prepare_experiment_predictions,
        "reopen": read_withheld_predictions,
        "score": score_experiment_predictions,
        "product": read_experiment_product,
        "refusals": (ValidationRefusal, LRARefusal),
    }


def prediction_receipt(
    directory: Path, checksum: str, api: dict[str, Any]
) -> dict[str, Any]:
    product, manifest, folds, predictions, methods = api["reopen"](
        directory, expected_manifest_sha256=checksum
    )
    require(
        len(folds) == 3 and tuple(methods) == METHODS,
        "Prediction fold/method population differs",
    )
    scientific = manifest["scientific_payload"]
    failures = scientific["failures"]
    require(
        len(predictions) + len(failures) * 3 == 9, "Nine method dispositions required"
    )
    dispositions = []
    failure_by_fold = {r["fold_id"]: r for r in failures}
    for fold_id in folds:
        for method in methods:
            if (fold_id, method) in predictions:
                dispositions.append(
                    {"fold_id": fold_id, "method": method, "status": "predicted"}
                )
            else:
                failure = failure_by_fold[fold_id]
                require(
                    failure["status"] in {"refused", "not_run"},
                    "Unknown fold failure status",
                )
                dispositions.append(
                    {
                        "fold_id": fold_id,
                        "method": method,
                        **{
                            k: failure[k]
                            for k in (
                                "status",
                                "reason_code",
                                "detail",
                                "exception_type",
                            )
                            if k in failure
                        },
                    }
                )
    return {
        "directory": str(product.directory),
        "manifest_sha256": product.manifest_sha256,
        "scientific_content_sha256": product.scientific_content_sha256,
        "failures": failures,
        "interrupted": scientific.get("interrupted", False),
        "retained_tables": {
            name: manifest["files"][name]
            for name in (
                "training.json",
                "preparations.json",
                "operations.json",
                "failures.json",
                "predictions.json",
            )
        },
        "method_dispositions": dispositions,
        "status_counts": dict(Counter(r["status"] for r in dispositions)),
    }


def batch(
    input_root: Path,
    manifest: Path,
    manifest_sha256: str,
    output: Path,
    *,
    phase: str,
    execution_epoch: str,
    prediction_index: Path | None = None,
    prediction_index_sha256: str | None = None,
    protocol_binding: dict[str, Any] | None = None,
    cohort: str | None = None,
) -> dict[str, Any]:
    require(
        len(execution_epoch) == 40
        and all(c in "0123456789abcdef" for c in execution_epoch),
        "Explicit actual execution epoch required",
    )
    scope_reader = input_scope
    receipt_reader = prediction_receipt
    score_rows = 9
    experiment_member = "experiment.json"
    score_message = "Nine explicit score dispositions required"
    if cohort is None:
        protocol_sha256 = PROTOCOL_SHA256
        if protocol_binding is not None:
            require(
                set(protocol_binding) == {"path", "sha256", "bytes"}
                and type(protocol_binding["bytes"]) is int
                and 0 < protocol_binding["bytes"] <= 65536,
                "Closed bounded protocol identity required",
            )
            protocol_raw, declaration = read(
                Path(protocol_binding["path"]), protocol_binding["sha256"], 65536
            )
            require(
                len(protocol_raw) == protocol_binding["bytes"]
                and declaration["schema_version"] == "nordic-coupled-ppe-sensitivity.v1"
                and declaration["baseline_protocol_sha256"] == PROTOCOL_SHA256,
                "Sensitivity protocol authority differs",
            )
            protocol_sha256 = protocol_binding["sha256"]
    else:
        require(
            cohort == "flink_nordic" and protocol_binding is not None,
            "Unknown or unbound cohort",
        )
        from .cohorts import workflow as cohort_workflow

        assert protocol_binding is not None
        cohort_workflow.protocol(protocol_binding)
        protocol_sha256 = protocol_binding["sha256"]
        scope_reader = partial(cohort_workflow.input_scope, binding=protocol_binding)
        receipt_reader = cohort_workflow.prediction_receipt
        score_rows = 12
        experiment_member = "cohort-experiment.json"
        score_message = "Twelve explicit score dispositions required"
    rows, pins = scope_reader(input_root, manifest, manifest_sha256)
    physical(output)
    require(not output.exists(), "Fresh absent output required")
    api = apis()
    prior = None
    if phase == "score":
        if prediction_index is None or prediction_index_sha256 is None:
            raise ValueError("Frozen prediction batch identity required")
        _, prior = read(prediction_index, prediction_index_sha256, 2097152)
        require(
            prior.get("schema_version") == "nordic-coupled-batch.v1"
            and prior.get("all_bins_accounted") is True
            and prior.get("protocol_sha256") == protocol_sha256
            and prior.get("protocol_binding") == protocol_binding,
            "Incomplete prediction batch cannot authorize scores",
        )
        require(
            prior["phase"] == "prepare"
            and prior["input_manifest_sha256"] == manifest_sha256
            and [r["bin"] for r in prior["bins"]] == list(NAMES),
            "Prediction batch/source identity differs",
        )
        if cohort is not None:
            require(prior.get("cohort") == cohort, "Prediction cohort differs")
        # Authenticate every available prediction before any score API/outcome access.
        for row in prior["bins"]:
            if "prediction" in row:
                require(
                    Path(row["prediction"]["directory"])
                    == prediction_index.parent / row["bin"],
                    "Prediction directory/owned batch differs",
                )
                receipt_reader(
                    Path(row["prediction"]["directory"]),
                    row["prediction"]["manifest_sha256"],
                    api,
                )
    require(phase in {"prepare", "score"}, "Unknown operation")
    output.mkdir(parents=True)
    result: dict[str, Any] = {
        "schema_version": "nordic-coupled-batch.v1",
        "phase": phase,
        "execution_epoch": execution_epoch,
        "input_manifest_sha256": manifest_sha256,
        "protocol_sha256": protocol_sha256,
        "bins": [{"bin": name, "status": "not_run"} for name in NAMES],
        "scope": "Prior-exposed conditional point predictions; small-lake regional proxies, no measured vegetation or calibrated uncertainty. Three baselines share one local predictor.",
    }
    if cohort is not None:
        result["cohort"] = cohort
        result["scope"] = (
            "Four conditional physical places, six separate bins,24 requested folds and72 dependent method dispositions; one regional anchor plus two local training places per fold. Existing fold-atomic success/refusal/notrun semantics; no independent models, measured vegetation, calibrated uncertainty or geometry/source-rights admission."
        )
    if protocol_binding is not None:
        result["protocol_binding"] = dict(protocol_binding)
    if prior is not None:
        result["prediction_execution_epoch"] = prior["execution_epoch"]
        result["prediction_index_sha256"] = prediction_index_sha256
    write(output, result)
    try:
        for position, row in enumerate(rows):
            current = result["bins"][position]
            current["status"] = "attempted"
            directory = input_root / row["directory"]
            try:
                _, payload = read(
                    directory / experiment_member, row["experiment"]["sha256"], 65536
                )
                spec = api["spec"](payload)
                if phase == "prepare":
                    product = api["prepare"](
                        spec,
                        input_root=directory,
                        cache_root=output / "cache" / row["directory"],
                        destination=output / row["directory"],
                        workers=1,
                    )
                    current["prediction"] = receipt_reader(
                        product.directory, product.manifest_sha256, api
                    )
                    current["status"] = "completed"
                    if current["prediction"]["interrupted"]:
                        raise KeyboardInterrupt(
                            "Maintained workflow interrupted; later bins remain unrun"
                        )
                else:
                    assert prior is not None
                    previous = prior["bins"][position]
                    if "prediction" not in previous:
                        current.update(
                            status="prediction_unavailable",
                            previous_disposition=previous,
                        )
                        continue
                    prediction = previous["prediction"]
                    receipt_reader(
                        Path(prediction["directory"]),
                        prediction["manifest_sha256"],
                        api,
                    )
                    inventory = {
                        "schema_version": "lra-source-pollen-outcomes.v1",
                        "data_kind": "source_observations",
                        "records": {
                            site["record_id"]: site["raw"] for site in payload["sites"]
                        },
                    }
                    product = api["score"](
                        Path(prediction["directory"]),
                        expected_manifest_sha256=prediction["manifest_sha256"],
                        outcome_root=directory,
                        outcome_inventory=inventory,
                        destination=output / row["directory"],
                    )
                    _, scored = api["product"](
                        product.directory,
                        expected_manifest_sha256=product.manifest_sha256,
                    )
                    require(
                        scored["phase"] == "scores"
                        and scored["scientific_payload"]["prediction_manifest_sha256"]
                        == prediction["manifest_sha256"],
                        "Score/prediction identity differs",
                    )
                    scores = scored["scientific_payload"]["scores"]
                    require(len(scores) == score_rows, score_message)
                    current.update(
                        status="completed",
                        scoring={
                            "directory": str(product.directory),
                            "manifest_sha256": product.manifest_sha256,
                            "scientific_content_sha256": product.scientific_content_sha256,
                            "prediction_manifest_sha256": prediction["manifest_sha256"],
                            "status_counts": dict(
                                Counter(x["score"]["status"] for x in scores)
                            ),
                        },
                    )
            except api["refusals"] as exc:
                current.update(
                    status="refused",
                    reason_code=exc.reason_code,
                    detail=str(exc),
                    exception_type=type(exc).__name__,
                )
            except BaseException as exc:
                current.update(
                    status="fatal", detail=str(exc), exception_type=type(exc).__name__
                )
                raise
            finally:
                write(output, result)
        _, after = scope_reader(input_root, manifest, manifest_sha256)
        require(after == pins, "Input manifest changed after batch")
        total = 0
        for member in output.rglob("*"):
            physical(member)
            info = member.lstat()
            require(
                stat.S_ISDIR(info.st_mode)
                or (stat.S_ISREG(info.st_mode) and info.st_nlink == 1),
                "Unsafe output namespace retained/refused",
            )
            if stat.S_ISREG(info.st_mode):
                total += info.st_size
        require(
            total <= MAX_OUTPUT - 2097152,
            "Owned numerical output exceeds reserved128MiB bound",
        )
        if phase == "score":
            assert prediction_index is not None and prediction_index_sha256 is not None
            read(prediction_index, prediction_index_sha256, 2097152)
        if protocol_binding is not None:
            final_protocol, _ = read(
                Path(protocol_binding["path"]), protocol_sha256, 65536
            )
            require(
                len(final_protocol) == protocol_binding["bytes"],
                "Protocol size changed",
            )
        result["all_bins_accounted"] = True
        result["bin_status_counts"] = dict(Counter(x["status"] for x in result["bins"]))
        write(output, result)
    finally:
        write(output, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("phase", choices=("prepare", "score"))
    parser.add_argument("--execution-epoch", required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--input-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prediction-index", type=Path)
    parser.add_argument("--prediction-index-sha256")
    args = parser.parse_args()
    result = batch(
        args.input_root,
        args.input_manifest,
        args.input_manifest_sha256,
        args.output,
        phase=args.phase,
        execution_epoch=args.execution_epoch,
        prediction_index=args.prediction_index,
        prediction_index_sha256=args.prediction_index_sha256,
    )
    print(
        json.dumps(
            {"phase": result["phase"], "bin_status_counts": result["bin_status_counts"]}
        )
    )


if __name__ == "__main__":
    main()
