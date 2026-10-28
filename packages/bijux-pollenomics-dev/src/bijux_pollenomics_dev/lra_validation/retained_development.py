"""Freeze and audit exposed English development scores through the local ledger.

Fresh audit attempts evaluate retained predictions. They neither rerun historical
fits nor retroactively supply a prospective protocol for the original search.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
from importlib import metadata
import json
import math
from pathlib import Path
from statistics import mean
import sys
import sysconfig
from typing import Any, cast

from .development_cohort import PROFILE
from .development_design import canonical_json, validate_development_design
from .experiment_ledger import read_development_attempts
from .trial_runner import run_development_trial

_SOURCE_FILES = {
    "historical-design.json": "docs/report/pollen-reconstruction/author-development-design.json",
    "scores.csv": "docs/report/pollen-reconstruction/scores.csv",
    "predictions.csv.gz": "docs/report/pollen-reconstruction/author-development-predictions.csv.gz",
    "source-custody.json": "docs/report/pollen-reconstruction/author-source-custody.json",
}
_THREADS = dict.fromkeys(
    (
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ),
    "1",
)
_METRICS = ["pollen_mae", "pollen_hellinger", "coverage_fraction"]
_MODULE = "bijux_pollenomics_dev.lra_validation.retained_development"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2, allow_nan=False) + "\n")


def _canonical_digest(payload: object) -> tuple[str, str]:
    value = canonical_json(payload)
    return value, hashlib.sha256(value.encode()).hexdigest()


def _inputs(root: Path) -> dict[str, Any]:
    manifest = cast(
        dict[str, Any], json.loads((root / "input-manifest.json").read_text())
    )
    for member in manifest["files"]:
        path = root / member["name"]
        if path.is_symlink() or not path.is_file() or _hash(path) != member["sha256"]:
            raise ValueError("retained_development_input_changed")
    return manifest


def prepare(
    repository: Path,
    output: Path,
    *,
    python_entry: Path,
    source_candidate: str,
    module_environment: dict[str, str] | None = None,
) -> dict[str, object]:
    """Declare a new retained-score audit before reserving any fresh attempt."""
    if output.exists() or output.is_symlink():
        raise ValueError("retained_development_output_exists")
    if not output.is_absolute() or not output.resolve().is_relative_to(
        repository / "artifacts"
    ):
        raise ValueError("retained_development_output_not_owned")
    if len(source_candidate) != 40 or any(
        c not in "0123456789abcdef" for c in source_candidate
    ):
        raise ValueError("invalid_source_candidate")
    historical = cast(
        dict[str, Any],
        json.loads((repository / _SOURCE_FILES["historical-design.json"]).read_text()),
    )
    if (
        historical["status"] != "completed_development_evidence"
        or historical["target_outcomes_used_for_selection"] is not True
    ):
        raise ValueError("historical_exposure_boundary_changed")
    if historical["candidate_count"] != 12 or len(historical["folds"]) != 3:
        raise ValueError("historical_search_space_changed")
    output.mkdir(parents=True)
    frozen = output / "frozen"
    frozen.mkdir()
    files = []
    for name, relative in _SOURCE_FILES.items():
        original = repository / relative
        if original.is_symlink() or not original.is_file():
            raise ValueError("retained_development_source_not_regular")
        content = original.read_bytes()
        (frozen / name).write_bytes(content)
        files.append(
            {
                "name": name,
                "source_path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
            }
        )
    source_manifest = {
        "schema_version": "english-retained-development-inputs.v1",
        "source_candidate": source_candidate,
        "files": files,
        "original_source_manifest_sha256": historical["source_manifest_sha256"],
        "fresh_operation": "retained_score_audit_without_refitting",
        "original_outcomes_previously_exposed": True,
    }
    _write(frozen / "input-manifest.json", source_manifest)
    _, source_sha = _canonical_digest(source_manifest)
    split = {
        "schema_version": "english-author-development-splits.v1",
        "folds": historical["folds"],
        "grouping": historical["grouping"],
        "source_manifest_sha256": historical["source_manifest_sha256"],
    }
    _write(frozen / "split-manifest.json", split)
    _, split_sha = _canonical_digest(split)
    with gzip.open(frozen / "predictions.csv.gz", "rt", newline="") as stream:
        prediction_rows = csv.DictReader(stream)
        first_prediction = [next(prediction_rows) for _ in range(31)]
    taxon_names = sorted(row["taxon"] for row in first_prediction)
    if len(set(taxon_names)) != 31 or any(
        _key(row) != _key(first_prediction[0]) for row in first_prediction
    ):
        raise ValueError("retained_prediction_taxon_axis_changed")
    scope = {
        "schema_version": "pollenomics-prior-exposed-development-scope.v1",
        "experiment": "all_target_pollen_withheld",
        "target": "pollen_composition",
        "split_manifest_sha256": split_sha,
        "support": {
            "response": "closed_original_31_author_prepared_taxon_counts",
            "taxon_names": taxon_names,
            "spatial": "three_grid_stratified_whole_site_folds_17_author_site_ids",
            "temporal": "same_retained_author_TW_bin_label_per_target_and_training",
            "consumer": "retained_prediction_scoring_without_training",
            "source_manifest_sha256": historical["source_manifest_sha256"],
            "split_manifest_sha256": split_sha,
            "original_target_outcomes_previously_exposed": True,
            "independent_vegetation_truth": False,
        },
    }
    scope_json, scope_sha = _canonical_digest(scope)
    _write(frozen / "scope.json", scope)
    cohort = {
        "profile": PROFILE,
        "admission_class": "prior_exposed_development_only",
        "outcome_access_status": "previously_exposed",
        "scientific_acceptance": "not_evaluated",
        "confirmatory_result": False,
        "canonical_scope_json": scope_json,
        "scope_sha256": scope_sha,
        "source_manifest_sha256": source_sha,
        "admitted_record_ids": sorted(
            f"author:{site}" for sites in historical["folds"].values() for site in sites
        ),
    }
    cohort_json, cohort_sha = _canonical_digest(cohort)
    _write(frozen / "development-cohort.json", cohort)
    if module_environment is None:
        module_environment = {
            "PYTHONPATH": ":".join(
                str(repository / path)
                for path in (
                    "packages/bijux-pollenomics-dev/src",
                    "packages/bijux-pollenomics/src",
                )
            )
        }
    # A copied interpreter no longer discovers the original venv's libraries.
    # Keep its dependency roots explicit in the immutable invocation environment.
    module_environment = dict(module_environment)
    package_paths = list(
        dict.fromkeys(
            [
                *module_environment.get("PYTHONPATH", "").split(":"),
                sysconfig.get_path("purelib"),
                sysconfig.get_path("platlib"),
            ]
        )
    )
    module_environment["PYTHONPATH"] = ":".join(path for path in package_paths if path)
    dependency_roots = sorted(
        {sysconfig.get_path("purelib"), sysconfig.get_path("platlib")}
    )
    distribution_records = []
    for distribution in metadata.distributions(path=dependency_roots):
        for member in distribution.files or []:
            if member.name in {"METADATA", "WHEEL", "RECORD"} and ".dist-info" in str(
                member
            ):
                path = Path(str(distribution.locate_file(member)))
                if path.is_symlink() or not path.is_file():
                    raise ValueError("runtime_distribution_record_not_regular")
                distribution_records.append(
                    {
                        "distribution": distribution.metadata["Name"],
                        "version": distribution.version,
                        "path": str(path),
                        "sha256": _hash(path),
                    }
                )
    runtime = {
        "schema_version": "retained-development-runtime-context.v1",
        "python_version": sys.version,
        "interpreter_entry": str(python_entry),
        "interpreter_sha256": _hash(python_entry),
        "dependency_roots": dependency_roots,
        "distribution_records": sorted(
            distribution_records, key=lambda row: row["path"]
        ),
    }
    _write(frozen / "runtime-manifest.json", runtime)
    _, runtime_sha = _canonical_digest(runtime)
    environment = {
        **_THREADS,
        "PYTHONDONTWRITEBYTECODE": "1",
        **module_environment,
    }
    candidates = []
    attempts = []
    for old in historical["candidates"]:
        for fold_id in historical["folds"]:
            runtime_identity = hashlib.sha256(
                canonical_json(environment).encode()
            ).hexdigest()[:12]
            identity = f"{old['candidate_id']}.{fold_id}.{runtime_identity}"
            result_path = output / "results" / f"{identity}.json"
            argv = [
                str(python_entry),
                "-m",
                _MODULE,
                "audit",
                "--frozen",
                str(frozen),
                "--candidate",
                old["candidate_id"],
                "--fold",
                fold_id,
                "--result",
                str(result_path),
                "--attempt-id",
                identity,
            ]
            configuration = {
                "method": old["model"],
                "transport": "direct-pollen-no-transport",
                "taxon_profile": "author-prepared-31-taxon-count-subcomposition",
                "ppe_profile": "none-direct-pollen",
                "basin_scenario": "none-direct-pollen",
                "spatial_support": "three-whole-author-site-folds",
                "temporal_support": "same-author-TW-bin-label",
                "uncertainty": "none-retained-point-predictions",
            }
            candidate = {
                "candidate_id": identity,
                "model": old["model"],
                "configuration": configuration,
                "hyperparameters": {
                    "historical_candidate_id": old["candidate_id"],
                    "historical_parameters": old["configuration"],
                    "fold_id": fold_id,
                },
                "backend": "python-stdlib-retained-score-audit",
                "invocation": {
                    "argv": argv,
                    "cwd": str(repository),
                    "environment": environment,
                    "executable_sha256": _hash(python_entry),
                },
            }
            candidates.append(candidate)
            attempts.append(
                {
                    "candidate": candidate,
                    "fold_id": fold_id,
                    "result_path": str(result_path),
                }
            )
    design = {
        "schema_version": "lra-development-design.v1",
        "status": "frozen",
        "cohort_admission_sha256": cohort_sha,
        "scope_sha256": scope_sha,
        "split_manifest_sha256": split_sha,
        "experiment_targets": [
            {"experiment": "all_target_pollen_withheld", "target": "pollen_composition"}
        ],
        "fold_ids": list(historical["folds"]),
        "candidates": candidates,
        "seeds": [0],
        "metric_ids": {"pollen_composition": _METRICS},
        "selection_rule": {
            "primary_metric_by_target": {"pollen_composition": "pollen_mae"},
            "direction_by_metric": {
                "pollen_mae": "minimize",
                "pollen_hellinger": "minimize",
                "coverage_fraction": "maximize",
            },
            "tie_breakers": ["greater_own_coverage", "historical_candidate_id"],
            "minimum_completed_folds": 3,
        },
        "resource_budget": {
            "maximum_trials": 36,
            "maximum_seconds_per_trial": 15,
            "maximum_declared_threads_per_trial": 1,
            "maximum_total_declared_cpu_seconds": 540,
        },
    }
    design_json, design_sha = _canonical_digest(design)
    validate_development_design(design_json, design_sha)
    _write(frozen / "design.json", design)
    _write(
        frozen / "selection-policy.json",
        {
            "minimum_own_scored_bin_coverage": 0.8,
            "support": "intersection_of_scored_fold_site_bin_keys_across_all_12_candidates",
            "aggregation": "equal_weight_site_mean_then_equal_weight_site_macro_across_all_three_folds",
            "primary": "minimum_common_support_site_macro_mae",
            "ties": ["greater_own_coverage", "historical_candidate_id"],
            "purpose": "reconcile_retained_exposed_selection_not_new_model_selection",
        },
    )
    binding = {
        "canonical_cohort_admission_json": cohort_json,
        "cohort_admission_sha256": cohort_sha,
        "scope_sha256": scope_sha,
        "split_manifest_sha256": split_sha,
        "split_kind": "predefined_block",
        "experiment": "all_target_pollen_withheld",
        "target": "pollen_composition",
    }
    plans = output / "plans"
    plans.mkdir()
    for attempt in attempts:
        candidate = attempt["candidate"]
        spec = {
            "schema_version": "lra-development-attempt.v3",
            "run_id": candidate["candidate_id"],
            "development_design": {
                "canonical_design_json": design_json,
                "design_sha256": design_sha,
            },
            "input_hashes": {
                "development_source_manifest": source_sha,
                "target_support": scope_sha,
                "split_manifest": split_sha,
                "runtime_context": runtime_sha,
            },
            "evaluation_binding": binding,
            "fold_id": attempt["fold_id"],
            **{
                key: candidate[key]
                for key in (
                    "candidate_id",
                    "model",
                    "configuration",
                    "hyperparameters",
                    "backend",
                )
            },
            "seed": 0,
            "budget": {"seconds": 15, "threads": 1},
            "invocation": {
                **{
                    key: candidate["invocation"][key]
                    for key in ("argv", "cwd", "environment")
                },
                "result_path": attempt["result_path"],
            },
        }
        _write(
            plans / f"{candidate['candidate_id']}.json",
            {
                "schema_version": "lra-development-trial.v2",
                "ledger_root": str(output / "ledger"),
                "spec": spec,
                "timeout_seconds": 15,
            },
        )
    return {
        "design_sha256": design_sha,
        "scope_sha256": scope_sha,
        "source_manifest_sha256": source_sha,
        "fresh_audit_attempts": 36,
    }


def _key(row: dict[str, str]) -> tuple[str, str, str]:
    return row["fold_id"], row["target_site_id"], row["bin_id_bp"]


def audit(
    frozen: Path, candidate_id: str, fold_id: str, result_path: Path, *, attempt_id: str
) -> None:
    """Reconcile each retained bin and publish one fresh audit terminal payload."""
    run_id = attempt_id
    start_path = frozen.parent / "ledger" / run_id / "start.json"
    if not start_path.is_file() or start_path.is_symlink():
        raise ValueError("audit_not_reserved_before_source_consumption")
    start = next(
        row["start"]
        for row in read_development_attempts(frozen.parent / "ledger")
        if row["start"]["run_id"] == run_id
    )
    manifest = _inputs(frozen)
    if (
        _canonical_digest(manifest)[1]
        != start["input_hashes"]["development_source_manifest"]
    ):
        raise ValueError("retained_development_source_manifest_changed")
    for filename, input_key in (
        ("scope.json", "target_support"),
        ("split-manifest.json", "split_manifest"),
    ):
        path = frozen / filename
        if (
            path.is_symlink()
            or _canonical_digest(json.loads(path.read_text()))[1]
            != start["input_hashes"][input_key]
        ):
            raise ValueError("retained_development_support_changed")
    if (
        canonical_json(json.loads((frozen / "design.json").read_text()))
        != start["development_design"]["canonical_design_json"]
    ):
        raise ValueError("retained_development_design_changed")
    if (
        canonical_json(json.loads((frozen / "development-cohort.json").read_text()))
        != start["evaluation_binding"]["canonical_cohort_admission_json"]
    ):
        raise ValueError("retained_development_admission_class_changed")
    scope = json.loads((frozen / "scope.json").read_text())
    taxon_names = scope["support"]["taxon_names"]
    runtime = json.loads((frozen / "runtime-manifest.json").read_text())
    if _canonical_digest(runtime)[1] != start["input_hashes"]["runtime_context"]:
        raise ValueError("retained_development_runtime_context_changed")
    if _hash(Path(runtime["interpreter_entry"])) != runtime["interpreter_sha256"]:
        raise ValueError("retained_development_runtime_interpreter_changed")
    if any(
        _hash(Path(row["path"])) != row["sha256"]
        for row in runtime["distribution_records"]
    ):
        raise ValueError("retained_development_runtime_distribution_changed")
    historical = json.loads((frozen / "historical-design.json").read_text())
    if fold_id not in historical["folds"] or candidate_id not in {
        row["candidate_id"] for row in historical["candidates"]
    }:
        raise ValueError("audit_choice_not_declared")
    with (frozen / "scores.csv").open(newline="") as stream:
        all_rows = list(csv.DictReader(stream))
    rows = [
        row
        for row in all_rows
        if row["candidate_id"] == candidate_id and row["fold_id"] == fold_id
    ]
    common: set[tuple[str, str, str]] | None = None
    for old in historical["candidates"]:
        keys = {
            _key(row)
            for row in all_rows
            if row["candidate_id"] == old["candidate_id"] and row["status"] == "scored"
        }
        common = keys if common is None else common & keys
    common = common or set()
    predictions: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    with gzip.open(frozen / "predictions.csv.gz", "rt", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["candidate_id"] == candidate_id and row["fold_id"] == fold_id:
                predictions.setdefault(_key(row), []).append(row)
    retained: list[dict[str, str]] = []
    scored: dict[tuple[str, str, str], tuple[float, float]] = {}
    max_mae_error = max_hellinger_error = 0.0
    for row in rows:
        if row["target_site_id"] not in historical["folds"][fold_id]:
            raise ValueError("target_outside_declared_fold")
        key = _key(row)
        if key in {_key(item) for item in retained}:
            raise ValueError("duplicate_retained_attempt")
        if row["status"] == "refused":
            if (
                key in predictions
                or not row["reason"]
                or row["mae_fraction"]
                or row["hellinger_distance"]
            ):
                raise ValueError("refusal_has_score_or_prediction")
        elif row["status"] == "scored":
            values = predictions.get(key, [])
            if (
                len(values) != 31
                or sorted(item["taxon"] for item in values) != taxon_names
            ):
                raise ValueError("retained_prediction_taxon_axis_changed")
            if any(
                item["training_manifest_sha256"] != row["training_manifest_sha256"]
                for item in values
            ):
                raise ValueError("retained_training_identity_changed")
            counts = [int(item["observed_count"]) for item in values]
            fractions = [float(item["predicted_fraction"]) for item in values]
            total = sum(counts)
            if (
                total != int(row["observed_total_count"])
                or total <= 0
                or any(n < 0 for n in counts)
                or any(not math.isfinite(p) or p < 0 for p in fractions)
                or abs(sum(fractions) - 1.0) > 1e-12
            ):
                raise ValueError("retained_prediction_denominator_changed")
            mae = (
                sum(abs(p - n / total) for p, n in zip(fractions, counts, strict=True))
                / 31
            )
            hellinger = math.sqrt(
                0.5
                * sum(
                    (math.sqrt(p) - math.sqrt(n / total)) ** 2
                    for p, n in zip(fractions, counts, strict=True)
                )
            )
            mae_error = abs(mae - float(row["mae_fraction"]))
            hellinger_error = abs(hellinger - float(row["hellinger_distance"]))
            max_mae_error = max(max_mae_error, mae_error)
            max_hellinger_error = max(max_hellinger_error, hellinger_error)
            if mae_error > 1e-14 or hellinger_error > 1e-14:
                raise ValueError("retained_score_disagrees_with_counts_and_predictions")
            scored[key] = mae, hellinger
        else:
            raise ValueError("unknown_retained_attempt_status")
        retained.append(row)
    if len(scored) != len(predictions):
        raise ValueError("unaccounted_retained_predictions")
    common_values = {key: value for key, value in scored.items() if key in common}
    sites = sorted({key[1] for key in common_values})
    metrics = (
        {
            "pollen_mae": mean(
                mean(value[0] for key, value in common_values.items() if key[1] == site)
                for site in sites
            ),
            "pollen_hellinger": mean(
                mean(value[1] for key, value in common_values.items() if key[1] == site)
                for site in sites
            ),
            "coverage_fraction": len(scored) / len(rows),
        }
        if sites and rows
        else {}
    )
    diagnostics = {
        "schema_version": "english-retained-development-audit.v1",
        "fresh_attempt_id": run_id,
        "historical_candidate_id": candidate_id,
        "fold_id": fold_id,
        "fresh_operation": "retained_score_audit_without_refitting",
        "original_outcomes_previously_exposed": True,
        "confirmatory_result": False,
        "original_attempts": retained,
        "original_attempt_count": len(rows),
        "original_status_counts": dict(Counter(row["status"] for row in rows)),
        "original_refusal_reason_counts": dict(
            Counter(row["reason"] for row in rows if row["status"] == "refused")
        ),
        "common_scored_bins": len(common_values),
        "common_scored_sites": len(sites),
        "independent_score_check": {
            "taxon_cells": sum(len(value) for value in predictions.values()),
            "maximum_mae_difference": max_mae_error,
            "maximum_hellinger_difference": max_hellinger_error,
            "absolute_tolerance": 1e-14,
        },
        "metrics": metrics,
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    _write(result_path.with_suffix(".diagnostics.json"), diagnostics)
    _write(
        result_path,
        {
            "status": "completed" if metrics else "refused",
            "metrics": metrics,
            "reason_code": None if metrics else "no_common_scored_support",
        },
    )


def run(output: Path) -> dict[str, object]:
    """Execute all declared audit runs; preserve every native terminal status."""
    terminals = []
    for path in sorted((output / "plans").glob("*.json")):
        plan = json.loads(path.read_text())
        code = run_development_trial(plan)
        terminals.append({"run_id": plan["spec"]["run_id"], "native_exit": code})
    rows = read_development_attempts(output / "ledger")
    report = {
        "schema_version": "english-retained-development-ledger-account.v1",
        "fresh_operation": "retained_score_audit_without_refitting",
        "fresh_attempt_count": len(rows),
        "fresh_native_terminals": terminals,
        "original_outcomes_previously_exposed": True,
        "confirmatory_result": False,
        "fresh_attempts": rows,
    }
    _write(output / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    """Prepare a declaration, audit one candidate/fold, or run its frozen ledger."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    declaration = sub.add_parser("prepare")
    declaration.add_argument("--repository", type=Path, required=True)
    declaration.add_argument("--output", type=Path, required=True)
    declaration.add_argument("--python-entry", type=Path, default=Path(sys.executable))
    declaration.add_argument("--source-candidate", required=True)
    execution = sub.add_parser("run")
    execution.add_argument("--output", type=Path, required=True)
    consumer = sub.add_parser("audit")
    consumer.add_argument("--frozen", type=Path, required=True)
    consumer.add_argument("--candidate", required=True)
    consumer.add_argument("--fold", required=True)
    consumer.add_argument("--result", type=Path, required=True)
    consumer.add_argument("--attempt-id", required=True)
    args = parser.parse_args(argv)
    if args.operation == "prepare":
        print(
            json.dumps(
                prepare(
                    args.repository,
                    args.output,
                    python_entry=args.python_entry,
                    source_candidate=args.source_candidate,
                )
            )
        )
    elif args.operation == "run":
        report = run(args.output)
        terminals = cast(list[dict[str, object]], report["fresh_native_terminals"])
        return (
            0
            if len(terminals) == 36
            and all(row["native_exit"] == 0 for row in terminals)
            else 1
        )
    else:
        audit(
            args.frozen,
            args.candidate,
            args.fold,
            args.result,
            attempt_id=args.attempt_id,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
