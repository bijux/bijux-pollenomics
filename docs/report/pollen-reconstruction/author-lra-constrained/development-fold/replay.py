"""Evaluate one prior-exposed BECKHAM fold with train-only fixed-start LOVE."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import runpy
from typing import Any

import numpy as np

from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    SAMPLE_FIELDS,
    read_geometry,
    verify_consumed_sources,
)
from bijux_pollenomics.analysis.lra_validation.experiments.prediction import (
    predict_fold,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reconstruction import (
    FoldFits,
)
from bijux_pollenomics.analysis.lra_validation.metrics import (
    score_pollen,
)

DIAGNOSTIC = "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/replay.py"
REFERENCE = "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/replay.py"
TARGET = "author:BECKHAM"
REUSED = ("author:CUTHILL2", "author:LONGBREACH")


def _write(path: Path, value: Any) -> dict[str, Any]:
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def run(
    repository: Path, prepared: Path, protocol: dict[str, Any], output: Path
) -> dict[str, Any]:
    numeric = protocol["numerical_protocol"]
    if protocol[
        "schema_version"
    ] != "author-love-development-fold-protocol.v1" or tuple(
        numeric[key]
        for key in (
            "maxiter",
            "max_search_evaluations",
            "ftol",
            "new_attempts",
            "reused_attempts",
            "total_attempts",
            "rings",
            "starts_per_ring",
        )
    ) != (300, 16000, 1e-8, 704, 128, 832, 2, 32):
        raise ValueError("Declared scientific protocol differs from fixed execution")
    for row in protocol["source_pins"]:
        raw = Path(repository / row["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["bytes"]:
            raise ValueError("Declared computational source changed")
    helper = runpy.run_path(str(repository / DIAGNOSTIC))
    original = runpy.run_path(str(repository / REFERENCE))
    pin, decode = helper["_pin"], helper["_json"]
    training_path = Path(__file__).absolute().with_name("training.py")
    training_source = protocol["training_helper"]
    pin(training_path, training_source["sha256"], training_source["bytes"])
    training_math = runpy.run_path(str(training_path))
    _reuse = training_math["_reuse"]
    _new_attempts = training_math["_new_attempts"]
    _composition = training_math["_composition"]
    before = protocol["before_prediction_freeze"]
    outcome_pin = protocol["outcome"]
    if len(before) != 36 or Path(outcome_pin["path"]).name in {
        Path(row["path"]).name for row in before
    }:
        raise ValueError(
            "Exact36 training/geometry metadata files and separate outcome required"
        )
    for row in before:
        pin(prepared / Path(row["path"]).name, row["sha256"], row["bytes"])
    experiment_row = next(
        row for row in before if Path(row["path"]).name == "experiment.json"
    )
    experiment = decode(
        pin(
            prepared / "experiment.json",
            experiment_row["sha256"],
            experiment_row["bytes"],
        )
    )
    spec = original["SourceExperimentSpec"](experiment)
    folds = original["grouped_leave_one_out"]([site.record for site in spec.sites])
    fold = next(row for row in folds if row.test_record_ids == (TARGET,))
    if (
        fold.fold_id != protocol["fold_id"]
        or list(fold.train_record_ids) != protocol["training_records"]
        or list(spec.baselines) != protocol["baselines"]
    ):
        raise ValueError("Exact declared whole-group fold and three baselines required")
    groups = {
        record: row.test_group_ids[0] for row in folds for record in row.test_record_ids
    }
    by_record = {site.record.record_id: site for site in spec.sites}
    anchor_id = next(
        record for record in spec.regional_priority if record in fold.train_record_ids
    )
    predictors = tuple(
        by_record[record]
        for record in fold.train_record_ids
        if groups[record] != groups[anchor_id]
    )
    if (
        anchor_id != protocol["regional_anchor"]
        or len(predictors) != 13
        or [site.record.record_id for site in predictors]
        != protocol["local_predictors"]
    ):
        raise ValueError("Exact anchor and13 local predictor groups required")
    prior_refs = protocol["prior_evidence"]
    prior_bodies = {
        name: pin(repository / row["path"], row["sha256"], row["bytes"])
        for name, row in prior_refs.items()
    }
    prior = decode(prior_bodies["report"])
    previous_protocol = decode(prior_bodies["protocol"])
    authority = decode(prior_bodies["receipt"])
    if (
        prior["fold_id"] != fold.fold_id
        or prior["experiment_sha256"] != experiment_row["sha256"]
        or prior["optimizer_contract"] != previous_protocol["protocol"]
        or authority["runtime"]["reference_sha256"]
        != protocol["runtime_reference_sha256"]
    ):
        raise ValueError("Prior scientific/runtime identity mismatch")
    if (
        any(
            version(name) != expected for name, expected in protocol["versions"].items()
        )
        or version("bijux-pollenomics-lra")
        != authority["runtime"]["source_metadata_projection"]["version"]
    ):
        raise ValueError("Prior engine and numerical dependency versions differ")
    reused = _reuse(prior, prior_bodies["trials"])
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    compositions, identities, training, attempts = {}, [], [], []
    common_regional = None
    failures = []
    with (output / "trials.jsonl").open("x") as ledger:

        def emit(row: dict[str, Any]) -> None:
            ledger.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())

        for site in predictors:
            request = original["make_request"](
                spec,
                site,
                by_record[anchor_id],
                fold,
                prepared,
                consumed_pollen=consumed_pollen,
                consumed_geometry=consumed_geometry,
            )
            item = original["LRABatchItem"](site.record.record_id, request)
            validated = original["validate_lra_inputs"](
                item.payload(), input_root=prepared
            )
            payload = validated.payload()
            binding = original["load_engine"](
                required_capability=original["required_capability_for_profile"](
                    payload["method_profile"]
                )
            )
            reveals, love, paired = original["_configuration"](binding, payload)
            if (
                len(payload["taxa"]),
                len(payload["rings"]),
                love.max_ring,
                love.repeats,
                love.optimizer_iterations,
                love.optimizer_max_evaluations,
                love.optimizer_tolerance,
            ) != (30, 3, 2, 1, 300, 16000, 1e-8):
                raise ValueError("Original dimensions and numerical bounds changed")
            regional_seed, local_seed = np.random.SeedSequence(paired.seed).spawn(2)
            reveals = replace(
                reveals,
                seed=int(regional_seed.generate_state(1, dtype=np.uint32)[0]),
                retain_samples=True,
            )
            love = replace(
                love, seed=int(local_seed.generate_state(1, dtype=np.uint32)[0])
            )
            pollen, parameters, rings = original["_tables"](payload)
            regional_result = original["run_reveals"](
                pollen["regional"], parameters, reveals
            )
            if regional_result.samples is None or regional_result.samples.shape[0] != 1:
                raise ValueError("Original single regional sample required")
            regional = regional_result.samples[0, 0, :] / 100
            if common_regional is not None and not np.array_equal(
                common_regional, regional
            ):
                raise ValueError("Shared raw rounded regional handoff differs")
            common_regional = regional.copy()
            params = original["_prepare_love_params"](parameters, payload["taxa"], love)
            kernels = original["calK"](rings, params).to_numpy(dtype=float)
            terrestrial = (rings["terrestrial"] / rings["ring"]).to_numpy(dtype=float)
            ppe = parameters["ppe"].to_numpy(dtype=float)
            counts = np.asarray(payload["local"]["samples"][0]["counts"], dtype=float)
            observed = counts / counts.sum()
            selections: list[dict[str, Any] | None] = []
            for ring in range(2):
                if site.record.record_id in REUSED:
                    rows = reused[(site.record.record_id, ring)]
                    handoff = next(
                        row
                        for row in prior["regional_handoffs"]
                        if row["item_id"] == site.record.record_id
                    )
                    if handoff["taxa"] != payload["taxa"] or not np.array_equal(
                        handoff["fractional_cover"], regional
                    ):
                        raise ValueError("Reused taxon/regional source differs")
                    starts = helper["_starts"](observed, regional)
                    for row, (name, start) in zip(rows, starts, strict=True):
                        if (
                            row["request_sha256"] != item.request_sha256
                            or row["start_id"] != name
                            or not np.array_equal(row["start"], start)
                            or row["outer_m"] != payload["rings"][ring]["outer_m"]
                        ):
                            raise ValueError(
                                "Reused request/start/ring identity differs"
                            )
                        if row["accepted"]:
                            fraction, local_k = (
                                terrestrial[: ring + 1],
                                kernels[: ring + 1],
                            )
                            background = np.sum(
                                kernels[ring + 1 :]
                                * (regional * ppe)[None, :]
                                * terrestrial[ring + 1 :, None],
                                axis=0,
                            )
                            value = original["tf"](
                                np.asarray(row["result"]["x"]),
                                background,
                                local_k,
                                fraction,
                                observed,
                                ppe,
                            )
                            if not np.isclose(
                                value, row["result"]["fun"], rtol=1e-12, atol=1e-12
                            ):
                                raise ValueError(
                                    "Reused accepted objective no longer certifies"
                                )
                else:
                    rows = _new_attempts(
                        helper,
                        original,
                        item,
                        payload,
                        regional,
                        ppe,
                        kernels,
                        terrestrial,
                        observed,
                        love.seed,
                        ring,
                        emit,
                    )
                    attempts.extend(rows)
                accepted = [row for row in rows if row["accepted"]]
                if not accepted:
                    failures.append(
                        {
                            "item_id": site.record.record_id,
                            "ring_index": ring,
                            "reason": "all_declared_starts_refused",
                        }
                    )
                    selections.append(None)
                    continue
                chosen = min(
                    accepted, key=lambda row: (row["result"]["fun"], row["start_id"])
                )
                composition, transformed = _composition(chosen, payload["taxa"])
                evidence = {
                    "item_id": site.record.record_id,
                    "request_sha256": item.request_sha256,
                    "ring_index": ring,
                    "attempted": 32,
                    "accepted": len(accepted),
                    "refused": 32 - len(accepted),
                    "selected_start_id": chosen["start_id"],
                    "selected_objective": chosen["result"]["fun"],
                    "selected_attempt_sha256": hashlib.sha256(
                        json.dumps(
                            chosen,
                            sort_keys=True,
                            separators=(",", ":"),
                            allow_nan=False,
                        ).encode()
                    ).hexdigest(),
                    "execution": "reused" if site.record.record_id in REUSED else "new",
                    **transformed,
                }
                selections.append(evidence)
            training.append(
                {
                    "item_id": site.record.record_id,
                    "request_sha256": item.request_sha256,
                    "regional_cover": regional.tolist(),
                    "selections": selections,
                }
            )
            outer = selections[-1]
            if all(row is not None for row in selections) and outer is not None:
                compositions[groups[site.record.record_id]] = outer["composition"]
                identities.append(
                    {
                        "record_id": site.record.record_id,
                        "group_id": groups[site.record.record_id],
                        "request_sha256": item.request_sha256,
                        "diagnostic_ring_evidence": selections,
                        "host_LRAProduct_claimed": False,
                    }
                )
    if len(attempts) != 704 or len(training) != 13 or TARGET in consumed_pollen:
        raise ValueError(
            "Exact704 new attempts and13 training predictors required without target pollen"
        )
    verify_consumed_sources(
        spec,
        prepared,
        pollen_record_ids=consumed_pollen,
        geometry_record_ids=consumed_geometry,
        template_used=True,
    )
    training_pin = _write(
        output / "training.json",
        {
            "profile": protocol["profile"],
            "fold": fold.as_dict(),
            "new_attempts": attempts,
            "reused_report": prior_refs["report"],
            "reused_trials": prior_refs["trials"],
            "reused_attempts": 128,
            "new_attempt_count": 704,
            "total_attempts": 832,
            "training": training,
            "failures": failures,
        },
    )
    report: dict[str, Any] = {
        "schema_version": "author-love-development-fold.v1",
        "profile": protocol["profile"],
        "fold": fold.as_dict(),
        "training": training_pin,
        "training_predictors": 13,
        "new_attempts": 704,
        "reused_attempts": 128,
        "total_attempts": 832,
        "failures": failures,
        "predictions": [],
        "scores": [],
        "target_opened_for_scoring": False,
        "scientific_acceptance": "not_evaluated",
        "exposure": "retrospective prior-exposed English development; no new untouched cohort or measured vegetation accuracy",
    }
    if not failures:
        if (
            common_regional is None
            or len(compositions) != 13
            or set(compositions)
            != {groups[site.record.record_id] for site in predictors}
        ):
            raise ValueError("All13 exact predictor compositions required")
        fits = FoldFits(
            by_record[anchor_id],
            predictors,
            compositions,
            tuple(common_regional),
            tuple(identities),
            {
                "profile": protocol["profile"],
                "host_LRAProduct_claimed": False,
                "training_evidence": training_pin,
            },
        )
        predictions, geometry = predict_fold(
            spec,
            fold,
            by_record[TARGET],
            fits,
            groups,
            input_root=prepared,
            consumed_geometry=consumed_geometry,
        )
        if (
            len(predictions) != 3
            or {row["baseline"] for row in predictions} != set(spec.baselines)
            or TARGET in consumed_pollen
        ):
            raise ValueError("Exact three target-free predictions required")
        frozen = _write(
            output / "prediction-freeze.json",
            {
                "profile": protocol["profile"],
                "fold": fold.as_dict(),
                "training": training_pin,
                "predictions": predictions,
                "geometry": geometry,
            },
        )
        reopened = decode(pin(Path(frozen["path"]), frozen["sha256"], frozen["bytes"]))
        _write(
            output / "outcome-access.json",
            {
                "record_id": TARGET,
                "prediction_freeze": frozen,
                "outcome": {
                    "path": Path(outcome_pin["path"]).name,
                    "sha256": outcome_pin["sha256"],
                },
                "ordering": "exclusive_prediction_freeze_reopened_before_target_decode",
                "exposure": report["exposure"],
            },
        )
        outcome = decode(
            pin(
                prepared / Path(outcome_pin["path"]).name,
                outcome_pin["sha256"],
                outcome_pin["bytes"],
            )
        )
        site = by_record[TARGET]
        sample = outcome["sample"]
        target_metadata = read_geometry(prepared, site, spec)["sample_metadata"]
        if not isinstance(target_metadata, dict):
            raise ValueError(
                "Outcome-free target sample metadata must remain an object"
            )
        if any(sample.get(field) != target_metadata[field] for field in SAMPLE_FIELDS):
            raise ValueError(
                "Target sample/coordinate/age/support/chronology identity differs"
            )
        if (
            set(outcome) != {"data_kind", "taxa", "sample"}
            or outcome["data_kind"] != "source_observations"
            or outcome["taxa"] != spec.template()["taxa"]
            or set(sample) != SAMPLE_FIELDS | {"counts"}
            or sample["site_id"] != site.record.site_id
            or sample["bin_id"] != predictions[0]["bin_id"]
            or len(sample["counts"]) != 30
            or any(type(count) is not int or count < 0 for count in sample["counts"])
            or not 0 < sum(sample["counts"]) <= 2**53
        ):
            raise ValueError(
                "Exact source target record/bin/30-axis integer-count observation required"
            )
        if (
            site.raw.sha256 != outcome_pin["sha256"]
            or site.raw.path != Path(outcome_pin["path"]).name
        ):
            raise ValueError("Declared target source identity differs")
        observed_counts = dict(zip(outcome["taxa"], sample["counts"], strict=True))
        report.update(
            predictions=reopened["predictions"],
            prediction_freeze=frozen,
            target_opened_for_scoring=True,
            observed_total_count=sum(sample["counts"]),
        )
        for row in reopened["predictions"]:
            report["scores"].append(
                {
                    "baseline": row["baseline"],
                    "record_id": TARGET,
                    **score_pollen(row["pollen_fraction"], observed_counts).as_dict(),
                }
            )
        pin(Path(frozen["path"]), frozen["sha256"], frozen["bytes"])
    for row in before:
        pin(prepared / Path(row["path"]).name, row["sha256"], row["bytes"])
    for row in prior_refs.values():
        pin(repository / row["path"], row["sha256"], row["bytes"])
    for row in protocol["source_pins"]:
        pin(repository / row["path"], row["sha256"], row["bytes"])
    pin(training_path, training_source["sha256"], training_source["bytes"])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.protocol.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.protocol_sha256:
        raise ValueError("Frozen development-fold protocol changed")
    protocol = json.loads(raw)
    output = args.output.absolute()
    if (
        ".." in output.parts
        or not output.is_relative_to(args.repository.absolute() / "artifacts")
        or output.exists()
        or any(path.is_symlink() for path in (output, *output.parents))
    ):
        raise ValueError("Absent physical output required")
    output.mkdir(parents=True)
    result = run(args.repository.absolute(), args.prepared.absolute(), protocol, output)
    _write(output / "report.json", result)


if __name__ == "__main__":
    main()
