"""Evaluate fifteen prior-exposed folds using exact fixed-start request reuse."""

from __future__ import annotations

import argparse
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
from bijux_pollenomics.analysis.lra_validation.metrics import score_pollen

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/"


def write(path: Path, value: Any) -> dict[str, Any]:
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


def pin(root: Path, row: dict[str, Any]) -> bytes:
    path: Path = root / row["path"]
    if path.is_symlink() or not path.is_file():
        raise ValueError("Physical declared input required")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["bytes"]:
        raise ValueError("Declared scientific input changed")
    return raw


def outcome_counts(
    prepared: Path,
    site: Any,
    spec: Any,
    prediction: dict[str, Any],
    input_rows: list[dict[str, Any]],
) -> dict[str, int]:
    """Decode scoring labels only after the complete prediction inventory is frozen."""
    outcome = json.loads(
        pin(
            prepared,
            next(
                row
                for row in input_rows
                if row["path"] == site.raw.path and row["sha256"] == site.raw.sha256
            ),
        )
    )
    sample = outcome["sample"]
    metadata = read_geometry(prepared, site, spec)["sample_metadata"]
    if not isinstance(metadata, dict) or any(
        sample.get(field) != metadata[field] for field in SAMPLE_FIELDS
    ):
        raise ValueError("Exact sample, chronology and support metadata required")
    if (
        set(outcome) != {"data_kind", "taxa", "sample"}
        or outcome["data_kind"] != "source_observations"
        or outcome["taxa"] != spec.template()["taxa"]
        or set(sample) != SAMPLE_FIELDS | {"counts"}
        or sample["site_id"] != site.record.site_id
        or sample["bin_id"] != prediction["bin_id"]
        or len(sample["counts"]) != 30
        or any(type(count) is not int or count < 0 for count in sample["counts"])
        or not 0 < sum(sample["counts"]) <= 2**53
    ):
        raise ValueError("Exact named30-axis integer observations required")
    return dict(zip(outcome["taxa"], sample["counts"], strict=True))


def run(
    repository: Path, prepared: Path, protocol: dict[str, Any], output: Path
) -> dict[str, Any]:
    if (
        protocol["schema_version"] != "author-love-cohort-development-protocol.v1"
        or protocol["counts"]
        != {
            "folds": 15,
            "logical_requests": 195,
            "unique_requests": 27,
            "new_attempts": 896,
            "reused_attempts": 832,
            "unique_attempts": 1728,
            "logical_attempt_references": 12480,
            "prediction_slots": 45,
        }
        or protocol["optimizer"]
        != {
            "maxiter": 300,
            "max_search_evaluations": 16000,
            "ftol": 1e-8,
            "rings": 2,
            "starts_per_ring": 32,
        }
    ):
        raise ValueError("Declared fixed scientific execution differs")
    for name, expected in protocol["versions"].items():
        if version(name) != expected:
            raise ValueError("Numerical or source-engine version differs")
    for row in protocol["source_pins"]:
        pin(repository, row)
    for row in protocol["inputs"]:
        pin(prepared, row)
    if len(protocol["inputs"]) != 37 or {path.name for path in prepared.iterdir()} != {
        row["path"] for row in protocol["inputs"]
    }:
        raise ValueError("Exact37 retained scientific input namespace required")
    references = {
        name: pin(repository, row) for name, row in protocol["prior_evidence"].items()
    }
    previous_protocol = json.loads(references["development_protocol"])
    authority = json.loads(references["development_receipt"])
    if (
        previous_protocol["source_pins"] != protocol["reused_source_pins"]
        or authority["runtime"]["plan"]["sha256"]
        != protocol["runtime_reference_sha256"]
        or authority["execution"]["common_exit"] != 0
        or authority["execution"]["outer_exit"] != 0
        or authority["execution"]["native_exit"] != 0
    ):
        raise ValueError("Prior computational/runtime source qualification differs")
    if (
        protocol["inputs"]
        != sorted(
            previous_protocol["before_prediction_freeze"]
            + [previous_protocol["outcome"]],
            key=lambda row: row["path"],
        )
        or protocol["versions"] != previous_protocol["versions"]
        or protocol["runtime_reference_sha256"]
        != previous_protocol["runtime_reference_sha256"]
        or protocol["baselines"] != previous_protocol["baselines"]
    ):
        raise ValueError(
            "Prior input, runtime or scientific comparison contract differs"
        )
    helper = runpy.run_path(
        str(repository / PREFIX / "optimizer-start-sensitivity/replay.py")
    )
    original = runpy.run_path(str(repository / PREFIX / "optimizer-gradient/replay.py"))
    math = runpy.run_path(str(repository / PREFIX / "development-fold/training.py"))
    pool_path = Path(__file__).absolute().with_name("pool.py")
    pin(pool_path.parent, protocol["pool_helper"])
    pool_math = runpy.run_path(str(pool_path))
    prior_training = json.loads(references["development_training"])
    reused = pool_math["prior_attempts"](
        math,
        prior_training,
        references["development_trials"],
        json.loads(references["start_report"]),
        references["start_trials"],
    )
    experiment = json.loads((prepared / "experiment.json").read_bytes())
    spec = original["SourceExperimentSpec"](experiment)
    folds = original["grouped_leave_one_out"]([site.record for site in spec.sites])
    by_record = {site.record.record_id: site for site in spec.sites}
    groups = {
        record: fold.test_group_ids[0]
        for fold in folds
        for record in fold.test_record_ids
    }
    expected = {
        (row["fold_id"], row["local_record_id"]): row
        for row in protocol["logical_requests"]
    }
    numerical: dict[str, Any] = {}
    logical, contexts = [], []
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    for fold in folds:
        anchor = next(
            record
            for record in spec.regional_priority
            if record in fold.train_record_ids
        )
        predictors = tuple(
            by_record[record]
            for record in fold.train_record_ids
            if groups[record] != groups[anchor]
        )
        if len(predictors) != 13 or len(fold.test_record_ids) != 1:
            raise ValueError("Exact fifteen original whole-site folds required")
        contexts.append((fold, anchor, predictors))
        local_pollen: set[str] = set()
        local_geometry: set[str] = set()
        for site in predictors:
            request = original["make_request"](
                spec,
                site,
                by_record[anchor],
                fold,
                prepared,
                consumed_pollen=local_pollen,
                consumed_geometry=local_geometry,
            )
            item = original["LRABatchItem"](site.record.record_id, request)
            row = {
                "fold_id": fold.fold_id,
                "local_record_id": item.item_id,
                "regional_anchor_record_id": anchor,
                "request_sha256": item.request_sha256,
                "target_record_id": fold.test_record_ids[0],
            }
            if (
                row != expected.get((fold.fold_id, item.item_id))
                or not {item.item_id, anchor}.issubset(fold.train_record_ids)
                or set(fold.test_record_ids) & local_pollen
            ):
                raise ValueError(
                    "Exact request equivalence or per-fold training ancestry differs"
                )
            logical.append(row)
            prior_item = numerical.setdefault(item.request_sha256, item)
            if prior_item.payload() != item.payload():
                raise ValueError(
                    "Equal request identity has distinct numerical payload"
                )
        consumed_pollen.update(local_pollen)
        consumed_geometry.update(local_geometry)
    if (
        len(logical) != 195
        or len(expected) != 195
        or len(numerical) != 27
        or {key[0] for key in reused}
        != {
            row["request_sha256"]
            for row in logical
            if row["regional_anchor_record_id"] == "author:BROADOWN"
        }
    ):
        raise ValueError(
            "Exact27 numeric requests and13 admitted prior requests required"
        )
    pool, new_attempts = {}, []
    with (output / "trials.jsonl").open("x") as ledger:

        def emit(row: dict[str, Any]) -> None:
            ledger.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())

        for checksum, item in sorted(numerical.items()):
            record, attempts = pool_math["fit_request"](
                original, helper, math, item, prepared, reused, prior_training, emit
            )
            pool[checksum] = record
            new_attempts.extend(attempts)
    if (
        len(new_attempts) != 896
        or sum(row["execution"] == "reused" for row in pool.values()) != 13
    ):
        raise ValueError("Exact896 new and832 prior unique attempts required")
    pool_pin = write(
        output / "training.json",
        {
            "numerical_requests": pool,
            "new_attempts": new_attempts,
            "prior_evidence": protocol["prior_evidence"],
            "logical_requests": logical,
            "counts": protocol["counts"],
        },
    )
    slots: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for fold, anchor, predictors in contexts:
        records = [
            pool[expected[(fold.fold_id, site.record.record_id)]["request_sha256"]]
            for site in predictors
        ]
        missing = [
            {"request_sha256": row["request_sha256"], "ring_index": ring}
            for row in records
            for ring, choice in enumerate(row["selections"])
            if choice is None
        ]
        if missing:
            failures.append(
                {
                    "fold_id": fold.fold_id,
                    "reason": "training_ring_has_no_accepted_fixed_start",
                    "missing": missing,
                }
            )
            slots.extend(
                {
                    "fold_id": fold.fold_id,
                    "record_id": fold.test_record_ids[0],
                    "baseline": baseline,
                    "status": "refused",
                    "reason": "training_ring_has_no_accepted_fixed_start",
                }
                for baseline in spec.baselines
            )
            continue
        regional = np.asarray(records[0]["regional_cover"])
        if any(not np.array_equal(row["regional_cover"], regional) for row in records):
            raise ValueError("Per-fold shared raw regional handoff differs")
        compositions = {
            groups[row["item_id"]]: row["selections"][-1]["composition"]
            for row in records
        }
        identities = tuple(
            {
                "record_id": row["item_id"],
                "group_id": groups[row["item_id"]],
                "request_sha256": row["request_sha256"],
                "diagnostic_ring_evidence": row["selections"],
                "host_LRAProduct_claimed": False,
            }
            for row in records
        )
        fits = FoldFits(
            by_record[anchor],
            predictors,
            compositions,
            tuple(regional),
            identities,
            {
                "profile": protocol["profile"],
                "host_LRAProduct_claimed": False,
                "training_evidence": pool_pin,
            },
        )
        predictions, geometry = predict_fold(
            spec,
            fold,
            by_record[fold.test_record_ids[0]],
            fits,
            groups,
            input_root=prepared,
            consumed_geometry=consumed_geometry,
        )
        if len(predictions) != 3 or {row["baseline"] for row in predictions} != set(
            spec.baselines
        ):
            raise ValueError("Exact three maintained forward predictions required")
        slots.extend(
            {
                "fold_id": fold.fold_id,
                "record_id": fold.test_record_ids[0],
                "baseline": row["baseline"],
                "status": "predicted",
                "prediction": row,
                "geometry": geometry,
            }
            for row in predictions
        )
    if (
        len(slots) != 45
        or len({(row["fold_id"], row["baseline"]) for row in slots}) != 45
    ):
        raise ValueError("Complete45-slot inventory required before new cohort scoring")
    verify_consumed_sources(
        spec,
        prepared,
        pollen_record_ids=consumed_pollen,
        geometry_record_ids=consumed_geometry,
        template_used=True,
    )
    frozen = write(
        output / "prediction-freeze.json",
        {
            "profile": protocol["profile"],
            "training": pool_pin,
            "folds": [fold.as_dict() for fold in folds],
            "slots": slots,
            "ordering": "All45 prediction or refusal slots frozen before any new cohort scoring; source pollen is legitimately training in other folds.",
        },
    )
    reopened = json.loads(
        pin(
            output,
            {
                "path": "prediction-freeze.json",
                **{key: frozen[key] for key in ("sha256", "bytes")},
            },
        )
    )
    scores = []
    with (output / "outcome-access.jsonl").open("x") as access:
        for fold, _, _ in contexts:
            rows = [
                row
                for row in reopened["slots"]
                if row["fold_id"] == fold.fold_id and row["status"] == "predicted"
            ]
            if not rows:
                continue
            site = by_record[fold.test_record_ids[0]]
            event = {
                "record_id": site.record.record_id,
                "fold_id": fold.fold_id,
                "prediction_freeze": frozen,
                "ordering": "complete45_slot_freeze_reopened_before_new_cohort_scoring",
                "exposure": "Source may already be training in other folds; all sites previously exposed.",
            }
            access.write(json.dumps(event, sort_keys=True) + "\n")
            access.flush()
            os.fsync(access.fileno())
            counts = outcome_counts(
                prepared, site, spec, rows[0]["prediction"], protocol["inputs"]
            )
            for row in rows:
                scores.append(
                    {
                        "fold_id": fold.fold_id,
                        "record_id": site.record.record_id,
                        "baseline": row["baseline"],
                        **score_pollen(
                            row["prediction"]["pollen_fraction"], counts
                        ).as_dict(),
                    }
                )
    for row in protocol["inputs"]:
        pin(prepared, row)
    for row in protocol["source_pins"]:
        pin(repository, row)
    for row in protocol["prior_evidence"].values():
        pin(repository, row)
    pin(pool_path.parent, protocol["pool_helper"])
    pin(
        output,
        {
            "path": "prediction-freeze.json",
            **{key: frozen[key] for key in ("sha256", "bytes")},
        },
    )
    return {
        "schema_version": "author-love-cohort-development.v1",
        "profile": protocol["profile"],
        "counts": protocol["counts"],
        "training": pool_pin,
        "prediction_freeze": frozen,
        "failures": failures,
        "predicted_folds": len(scores) // 3,
        "refused_folds": len(failures),
        "scores": scores,
        "exposure": "Homogeneous retrospective prior-exposed fifteen-site diagnostic; original uniform evaluations remain separate.",
        "scientific_acceptance": "not_evaluated",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "prepared", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    raw = args.protocol.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.protocol_sha256:
        raise ValueError("Frozen cohort protocol changed")
    repository, output = args.repository.absolute(), args.output.absolute()
    if (
        ".." in output.parts
        or not output.is_relative_to(repository / "artifacts")
        or output.exists()
        or any(path.is_symlink() for path in (output, *output.parents))
    ):
        raise ValueError("Absent physical artifact output required")
    output.mkdir(parents=True)
    report = run(repository, args.prepared.absolute(), json.loads(raw), output)
    write(output / "report.json", report)


if __name__ == "__main__":
    main()
