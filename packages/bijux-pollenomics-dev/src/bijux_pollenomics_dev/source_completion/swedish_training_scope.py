"""Compare Swedish-only and four-country training on identical Swedish pollen targets."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)

from .nordic_author_target_pollen import _compressed_read, _compressed_write, predict
from .nordic_direct_pollen import BASELINE_METHODS, _json_write, _sha

NORDIC = Path("docs/report/regions/nordic/author-target-pollen")
SWEDISH = Path("docs/report/regions/nordic/swedish-author-target-pollen")
SCOPES = ("sweden_only", "four_country")


def _checked_input(root: Path, manifest: dict[str, Any], relative: str) -> Path:
    path = root / relative
    if _sha(path) != manifest["produced_file_sha256"][relative]:
        raise ValueError(f"retained author-target input changed: {relative}")
    return path


def prepare(repository: Path, output: Path) -> None:
    """Publish target-excluded predictor inputs without opening sealed outcomes."""
    repository = repository.resolve()
    swedish_root = repository / SWEDISH
    nordic_root = repository / NORDIC
    swedish_manifest_path = swedish_root / "input-manifest.json"
    nordic_manifest_path = nordic_root / "input-manifest.json"
    swedish_manifest = json.loads(swedish_manifest_path.read_text())
    nordic_manifest = json.loads(nordic_manifest_path.read_text())
    if (
        swedish_manifest["axis"] != nordic_manifest["axis"]
        or len(swedish_manifest["axis"]) != 31
    ):
        raise ValueError("Swedish and Nordic author target axes differ")
    nordic_path = _checked_input(
        swedish_root, swedish_manifest, "inputs/training-SE.json.gz"
    )
    metadata_path = _checked_input(
        swedish_root, swedish_manifest, "inputs/metadata-SE.json.gz"
    )
    source_path = _checked_input(
        nordic_root, nordic_manifest, "inputs/training-DK.json.gz"
    )
    # The outcomes path is bound but intentionally unopened until score().
    outcome_hash = swedish_manifest["produced_file_sha256"][
        "sealed-outcomes/outcomes-SE.json.gz"
    ]
    metadata = _compressed_read(metadata_path)
    nordic = _compressed_read(nordic_path)
    swedish = {
        key: value
        for key, value in _compressed_read(source_path).items()
        if value["country"] == "SE"
    }
    if len(metadata["sites"]) != 3 or len(swedish) != 3 or len(nordic) != 81:
        raise ValueError("expected 3 Swedish and 81 other Nordic physical sites")
    if any(value["country"] == "SE" for value in nordic.values()):
        raise ValueError("Nordic training includes Swedish pollen")
    if set(nordic) & set(swedish):
        raise ValueError("Swedish and Nordic training record IDs overlap")
    output.mkdir(parents=True, exist_ok=False)
    folds: list[dict[str, str]] = []
    for site in sorted(metadata["sites"], key=lambda item: item["site_id"]):
        target_id = site["site_id"]
        target_group = site["group_id"]
        target_key = f"SE:{target_id}"
        if target_key not in swedish:
            raise ValueError("target Swedish site is absent from retained profiles")
        local_training = {
            key: profile
            for key, profile in swedish.items()
            if profile["group_id"] != target_group
        }
        if len(local_training) != 2:
            raise ValueError("Swedish whole-site exclusion did not leave two sites")
        for scope in SCOPES:
            training = (
                local_training
                if scope == "sweden_only"
                else {**nordic, **local_training}
            )
            if any(
                profile["group_id"] == target_group for profile in training.values()
            ):
                raise ValueError("target physical site leaked into training")
            fold_dir = output / scope / target_id
            training_rel = "inputs/training-SE.json.gz"
            metadata_rel = "inputs/metadata-SE.json.gz"
            _compressed_write(fold_dir / training_rel, training)
            _compressed_write(
                fold_dir / metadata_rel, {"country": "SE", "sites": [site]}
            )
            _json_write(
                fold_dir / "input-manifest.json",
                {
                    "schema_version": "swedish-training-scope-inputs.v1",
                    "axis": swedish_manifest["axis"],
                    "scope": scope,
                    "target_site_id": target_id,
                    "target_group_id": target_group,
                    "training_site_count": len(training),
                    "target_outcomes_in_prediction_inputs": False,
                    "produced_file_sha256": {
                        training_rel: _sha(fold_dir / training_rel),
                        metadata_rel: _sha(fold_dir / metadata_rel),
                    },
                },
            )
            folds.append(
                {
                    "scope": scope,
                    "site_id": target_id,
                    "input_manifest_sha256": _sha(fold_dir / "input-manifest.json"),
                }
            )
    _json_write(
        output / "prepare.json",
        {
            "schema_version": "swedish-training-scope-preparation.v1",
            "swedish_input_manifest_sha256": _sha(swedish_manifest_path),
            "nordic_input_manifest_sha256": _sha(nordic_manifest_path),
            "swedish_training_sha256": _sha(source_path),
            "nordic_training_sha256": _sha(nordic_path),
            "target_metadata_sha256": _sha(metadata_path),
            "sealed_outcome_sha256": outcome_hash,
            "folds": folds,
            "interpretation": "Previously exposed pollen outcomes; predictor files exclude each entire Swedish target site.",
        },
    )


def freeze(prepared: Path, output: Path) -> None:
    """Publish all six scope/site prediction products before scoring."""
    receipt = json.loads((prepared / "prepare.json").read_text())
    output.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, str]] = []
    for fold in receipt["folds"]:
        relative = Path(fold["scope"]) / fold["site_id"]
        source = prepared / relative
        if _sha(source / "input-manifest.json") != fold["input_manifest_sha256"]:
            raise ValueError("prepared fold identity changed")
        predict(source, output / relative, countries=("SE",))
        prediction = output / relative / "predictions-SE.json.gz"
        rows.append({**fold, "prediction_sha256": _sha(prediction)})
    _json_write(
        output / "freeze.json",
        {
            "schema_version": "swedish-training-scope-freeze.v1",
            "prepare_sha256": _sha(prepared / "prepare.json"),
            "folds": rows,
        },
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"empty scientific output: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def score(
    prepared: Path, frozen: Path, expected_sha256: str, repository: Path, output: Path
) -> None:
    """Open exact retained outcomes only after authenticating the freeze."""
    freeze_path = frozen / "freeze.json"
    if _sha(freeze_path) != expected_sha256:
        raise ValueError("prediction freeze digest changed")
    receipt = json.loads((prepared / "prepare.json").read_text())
    frozen_receipt = json.loads(freeze_path.read_text())
    if frozen_receipt["prepare_sha256"] != _sha(prepared / "prepare.json"):
        raise ValueError("prepared input identity changed after prediction")
    if len(frozen_receipt["folds"]) != 6 or len(receipt["folds"]) != 6:
        raise ValueError("scope/site fold denominator changed")
    for fold, sealed in zip(receipt["folds"], frozen_receipt["folds"], strict=True):
        if any(fold[key] != sealed[key] for key in fold):
            raise ValueError("prediction fold identity changed")
        relative = Path(fold["scope"]) / fold["site_id"]
        if (
            _sha(prepared / relative / "input-manifest.json")
            != fold["input_manifest_sha256"]
        ):
            raise ValueError("prepared fold changed")
        if (
            _sha(frozen / relative / "predictions-SE.json.gz")
            != sealed["prediction_sha256"]
        ):
            raise ValueError("frozen prediction changed")
    outcome_path = (
        repository.resolve() / SWEDISH / "sealed-outcomes/outcomes-SE.json.gz"
    )
    if _sha(outcome_path) != receipt["sealed_outcome_sha256"]:
        raise ValueError("target outcome source changed")
    outcomes = _compressed_read(outcome_path)
    rows: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for fold in frozen_receipt["folds"]:
        relative = Path(fold["scope"]) / fold["site_id"]
        manifest = json.loads((prepared / relative / "input-manifest.json").read_text())
        metadata = _compressed_read(prepared / relative / "inputs/metadata-SE.json.gz")
        if (
            _sha(prepared / relative / "inputs/metadata-SE.json.gz")
            != manifest["produced_file_sha256"]["inputs/metadata-SE.json.gz"]
        ):
            raise ValueError("target metadata changed")
        payload = _compressed_read(frozen / relative / "predictions-SE.json.gz")
        if payload["axis"] != manifest["axis"] or payload["country"] != "SE":
            raise ValueError("frozen prediction response changed")
        site = metadata["sites"][0]
        if site["site_id"] != fold["site_id"]:
            raise ValueError("frozen site identity changed")
        candidate = {
            (site["site_id"], int(bin_id)) for bin_id in site["candidate_bin_ids"]
        }
        predicted = {(row["site_id"], row["bin_id"]) for row in payload["predictions"]}
        refused = {(row["site_id"], row["bin_id"]) for row in payload["refusals"]}
        if predicted & refused or predicted | refused != candidate:
            raise ValueError("prediction and refusal support does not close")
        methods_by_bin: dict[tuple[str, int], set[str]] = defaultdict(set)
        for prediction in payload["predictions"]:
            bin_key = (prediction["site_id"], prediction["bin_id"])
            method = prediction["method"]
            if method in methods_by_bin[bin_key]:
                raise ValueError("duplicate method prediction")
            methods_by_bin[bin_key].add(method)
            if (
                fold["site_id"] in prediction["training_site_ids"]
                or prediction["target_pollen_counts_read"]
            ):
                raise ValueError("target pollen leaked into prediction")
            observed = outcomes[f"SE:{fold['site_id']}"][str(prediction["bin_id"])]
            if observed["closed_nisp"] <= 0:
                continue
            composition = {
                name: count / observed["closed_nisp"]
                for name, count in observed["counts"].items()
            }
            result = score_pollen(prediction["fractions"], observed["counts"])
            rows.append(
                {
                    "scope": fold["scope"],
                    "site_id": fold["site_id"],
                    "bin_id": prediction["bin_id"],
                    "method": method,
                    "mae_fraction": result.mae_fraction,
                    "hellinger_distance": hellinger_distance(
                        prediction["fractions"], composition
                    ),
                    "target_assigned_nisp": observed["closed_nisp"],
                    "target_native_nisp": observed["all_pollen_nisp"],
                    "prediction_sha256": fold["prediction_sha256"],
                }
            )
        if set(methods_by_bin) != predicted or any(
            methods != set(BASELINE_METHODS) for methods in methods_by_bin.values()
        ):
            raise ValueError("method coverage differs across predicted bins")
        coverage.append(
            {
                "scope": fold["scope"],
                "site_id": fold["site_id"],
                "candidate_bins": len(candidate),
                "predicted_bins": len(predicted),
                "refused_bins": len(refused),
            }
        )
    matched: dict[tuple[str, int, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        matched[(row["site_id"], row["bin_id"], row["method"])][row["scope"]] = row
    paired = []
    for (site_id, bin_id, method), by_scope in sorted(matched.items()):
        if set(by_scope) != set(SCOPES):
            continue
        local, nordic = (by_scope[scope] for scope in SCOPES)
        if (local["target_assigned_nisp"], local["target_native_nisp"]) != (
            nordic["target_assigned_nisp"],
            nordic["target_native_nisp"],
        ):
            raise ValueError("paired response denominator changed")
        paired.append(
            {
                "site_id": site_id,
                "bin_id": bin_id,
                "method": method,
                "sweden_only_mae_fraction": local["mae_fraction"],
                "four_country_mae_fraction": nordic["mae_fraction"],
                "four_country_minus_sweden_mae_fraction": nordic["mae_fraction"]
                - local["mae_fraction"],
                "sweden_only_hellinger_distance": local["hellinger_distance"],
                "four_country_hellinger_distance": nordic["hellinger_distance"],
                "target_assigned_nisp": local["target_assigned_nisp"],
            }
        )
    if len(paired) != 39 * len(BASELINE_METHODS):
        raise ValueError("expected 39 shared Swedish site-bins for each fixed method")
    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "scores.csv", rows)
    _write_csv(output / "coverage.csv", coverage)
    _write_csv(output / "paired-scores.csv", paired)
    paired_sites = sorted({row["site_id"] for row in paired})
    coverage_by_scope = {
        scope: {
            "training_sites_per_fold": 2 if scope == "sweden_only" else 83,
            "candidate_bins": sum(
                row["candidate_bins"] for row in coverage if row["scope"] == scope
            ),
            "predicted_bins": sum(
                row["predicted_bins"] for row in coverage if row["scope"] == scope
            ),
            "refused_bins": sum(
                row["refused_bins"] for row in coverage if row["scope"] == scope
            ),
        }
        for scope in SCOPES
    }
    site_macro = {
        method: {
            scope: mean(
                mean(
                    row[f"{scope}_mae_fraction"]
                    for row in paired
                    if row["method"] == method and row["site_id"] == site_id
                )
                for site_id in paired_sites
            )
            for scope in SCOPES
        }
        for method in BASELINE_METHODS
    }
    site_macro_hellinger = {
        method: {
            scope: mean(
                mean(
                    row[f"{scope}_hellinger_distance"]
                    for row in paired
                    if row["method"] == method and row["site_id"] == site_id
                )
                for site_id in paired_sites
            )
            for scope in SCOPES
        }
        for method in BASELINE_METHODS
    }
    _json_write(
        output / "report.json",
        {
            "schema_version": "swedish-training-scope-study.v1",
            "prepare_sha256": _sha(prepared / "prepare.json"),
            "prediction_freeze_sha256": expected_sha256,
            "source_outcome_sha256": _sha(outcome_path),
            "score_rows": len(rows),
            "paired_score_rows": len(paired),
            "paired_site_bins": len(
                {(row["site_id"], row["bin_id"]) for row in paired}
            ),
            "target_sites": len(paired_sites),
            "coverage_rows": len(coverage),
            "scope_coverage": coverage_by_scope,
            "site_macro_mae_fraction_on_common_support": site_macro,
            "site_macro_hellinger_distance_on_common_support": site_macro_hellinger,
            "scores_sha256": _sha(output / "scores.csv"),
            "coverage_sha256": _sha(output / "coverage.csv"),
            "paired_scores_sha256": _sha(output / "paired-scores.csv"),
            "interpretation": "Prior-exposed Swedish whole-site observed-pollen comparison on 31 author targets; four-country training adds DK/FI/NO sites and does not supply LRA or vegetation truth.",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "predict", "score"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--frozen", type=Path)
    parser.add_argument("--freeze-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "prepare":
        if args.repository is None:
            parser.error("prepare requires --repository")
        prepare(args.repository, args.output)
    elif args.stage == "predict":
        if args.prepared is None:
            parser.error("predict requires --prepared")
        freeze(args.prepared, args.output)
    else:
        if (
            args.repository is None
            or args.prepared is None
            or args.frozen is None
            or args.freeze_sha256 is None
        ):
            parser.error(
                "score requires --repository, --prepared, --frozen and --freeze-sha256"
            )
        score(
            args.prepared, args.frozen, args.freeze_sha256, args.repository, args.output
        )


if __name__ == "__main__":
    main()
