"""Exercise current grouped splitting and fitted-input isolation on known fixtures."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
from typing import Any

Json = dict[str, Any]


def operations() -> Json:
    from bijux_pollenomics.analysis.lra_validation.experiments import (
        prepare_experiment_predictions,
        prepare_fitted_spatial_predictions,
        read_withheld_predictions,
        score_experiment_predictions,
    )
    from bijux_pollenomics_dev.lra_validation.split_guard import (
        SplitGuardError,
        build_candidate_split,
    )

    return {
        "baselines": prepare_experiment_predictions,
        "fitted": prepare_fitted_spatial_predictions,
        "read": read_withheld_predictions,
        "score": score_experiment_predictions,
        "split": build_candidate_split,
        "split_error": SplitGuardError,
    }


def identity_witness(api: Json) -> Json:
    rows: list[Json] = []
    for name in "abcdefghi":
        rows.append(
            {
                "record_id": name,
                "site_id": "site-" + name,
                "core_id": None,
                "publication_id": None,
                "alias_ids": [],
                "country": "Sweden",
                "spatial_block_id": "block-target"
                if name in "abcdei"
                else "block-" + name,
                "kind": "pollen",
                "dependency_ids": [],
            }
        )
    by_id = {row["record_id"]: row for row in rows}
    by_id["a"]["core_id"] = by_id["b"]["core_id"] = "core-shared"
    by_id["a"]["publication_id"] = by_id["c"]["publication_id"] = "publication-shared"
    by_id["d"]["alias_ids"] = ["a"]
    by_id["e"]["alias_ids"] = ["b"]
    by_id["i"].update(kind="derived", alias_ids=["e"], dependency_ids=["e"])
    split = api["split"](rows, test_record_id="a", target="withheld_pollen_prediction")
    if split["test_record_ids"] != list("abcdei") or split["train_record_ids"] != list(
        "fgh"
    ):
        raise ValueError(
            "Explicit site/core/publication/chronology/derived group differs"
        )
    contaminated = [
        *rows,
        {
            **by_id["f"],
            "record_id": "unowned-derived",
            "site_id": "unowned",
            "kind": "derived",
            "dependency_ids": ["i"],
        },
    ]
    try:
        api["split"](
            contaminated, test_record_id="a", target="withheld_pollen_prediction"
        )
    except api["split_error"] as error:
        if error.reason_code != "contaminated_train_input":
            raise
    else:
        raise ValueError("Target-derived training source was admitted")
    return {
        "records": rows,
        "split": split,
        "contaminated_derived_refusal": "contaminated_train_input",
    }


def outcome_inventory(inputs: Path, payload: Json, variant: str, helper: Json) -> Json:
    references = {}
    for site in payload["sites"]:
        record = site["record_id"]
        raw = json.loads((inputs / site["raw"]["path"]).read_text())
        target = record == "p01"
        vegetation = (
            [0.9, 0.1] if target and variant == "target-perturbed" else [0.25, 0.75]
        )
        value = {
            "schema_version": "lra-experiment-observation.v1",
            "data_kind": "synthetic",
            "record_id": record,
            "bin_id": "test-bin",
            "vegetation_unit": "fraction",
            "pollen_unit": "count",
            "vegetation_fraction": dict(
                zip(["Alnus", "Betula"], vegetation, strict=True)
            ),
            "pollen_count": dict(
                zip(["Alnus", "Betula"], raw["sample"]["counts"], strict=True)
            ),
        }
        path = inputs / (record + "-outcome.json")
        helper["write"](path, value)
        references[record] = {
            "path": path.name,
            "sha256": helper["pin"](path)["sha256"],
        }
    return {
        "schema_version": "lra-experiment-outcomes.v1",
        "data_kind": "synthetic",
        "records": references,
    }


def target_evidence(
    lane: str, variant: str, product: Any, journal: Any, api: Json, helper: Json
) -> Json:
    _, manifest, folds, predictions, methods = api["read"](
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    target_fold = next(
        key for key, value in folds.items() if value["test_record_ids"] == ["p01"]
    )
    selected = [row for (fold, _), row in predictions.items() if fold == target_fold]
    training = [
        row
        for row in journal.rows
        if row["kind"] == "reconstruction_completed"
        and row["lane"] == lane
        and row["variant"] == variant
        and tuple(row["fold"]["test_record_ids"]) == ("p01",)
    ]
    failures = [
        row
        for row in manifest["scientific_payload"]["failures"]
        if row["fold_id"] == target_fold
    ]
    dispositions = []
    for method in methods:
        predicted = [
            row for row in selected if row.get("method", row.get("baseline")) == method
        ]
        refused = [
            row for row in failures if "method" not in row or row["method"] == method
        ]
        if len(predicted) + len(refused) != 1:
            raise ValueError("Complete unique target method disposition required")
        dispositions.append(
            {
                "method": method,
                "status": "predicted"
                if predicted
                else refused[0].get("status", "refused"),
                "prediction": predicted[0] if predicted else None,
                "failure": refused[0] if refused else None,
            }
        )
    if len(training) > 1 or (selected and len(training) != 1):
        raise ValueError(
            "Complete target-fold training and method predictions required"
        )
    training_payload = (
        {
            key: value
            for key, value in training[0].items()
            if key not in {"index", "lane", "variant", "kind"}
        }
        if training
        else None
    )
    return {
        "lane": lane,
        "variant": variant,
        "target_fold": target_fold,
        "training": training_payload,
        "training_observed": bool(training),
        "training_sha256": helper["digest"](training_payload),
        "predictions": sorted(
            selected, key=lambda row: str(row.get("method", row.get("baseline")))
        ),
        "methods": list(methods),
        "method_dispositions": dispositions,
        "scientific_payload": manifest["scientific_payload"],
    }


def run(
    repository: Path,
    output: Path,
    protocol: Json,
    helper: Json,
    api: Json | None = None,
) -> Json:
    """Publish the complete controlled witness; any unexpected fault stays fatal."""
    api = operations() if api is None else api
    if (
        not output.is_absolute()
        or output.exists()
        or output.is_symlink()
        or ".." in output.parts
    ):
        raise ValueError("Fresh normalized output directory required")
    output.resolve().relative_to(repository.resolve() / "artifacts")
    for row in protocol["source_inputs"]:
        helper["checked"](repository, row)
    output.mkdir(parents=True)
    seed = helper["seed_cache"](
        repository, output / "cache", protocol["saved_cache_seed"]
    )
    journal = helper["Journal"](output / "read-journal.jsonl")
    identity = identity_witness(api)
    fixture_source = helper["checked"](repository, protocol["fixture_source"])
    payloads, inputs = {}, {}
    for variant in ("reference", "target-perturbed"):
        directory = output / (variant + "-inputs")
        payload = helper["fixture"](directory, fixture_source)
        if variant == "target-perturbed":
            raw = directory / payload["sites"][0]["raw"]["path"]
            value = json.loads(raw.read_text())
            value["sample"]["counts"] = [100, 900]
            raw.write_text(json.dumps(value, sort_keys=True) + "\n")
            payload["sites"][0]["raw"]["sha256"] = helper["pin"](raw)["sha256"]
        payloads[variant], inputs[variant] = payload, directory
    products, target_rows, score_rows = {}, [], []
    with helper["instrument"](journal):
        for lane in ("baselines", "fitted"):
            for variant in ("reference", "target-perturbed"):
                journal.lane, journal.variant = lane, variant
                payload = json.loads(json.dumps(payloads[variant]))
                if lane == "fitted":
                    payload.pop("baselines")
                    payload.update(
                        profile="synthetic-withheld-site-fitted-spatial-v1",
                        method={
                            "profile": "clr-wgs84-rbf-ridge-v1",
                            "length_scale_km": 20,
                            "ridge_penalty": 0.2,
                        },
                    )
                product = api[lane](
                    payload,
                    input_root=inputs[variant],
                    cache_root=output / "cache",
                    destination=output / (lane + "-" + variant + "-predictions"),
                    workers=1,
                )
                products[lane, variant] = product
                journal.record(
                    "predictions_published",
                    directory=str(product.directory),
                    manifest_sha256=product.manifest_sha256,
                )
                target_rows.append(
                    target_evidence(lane, variant, product, journal, api, helper)
                )
        for variant in ("reference", "target-perturbed"):
            inventory = outcome_inventory(
                inputs[variant], payloads[variant], variant, helper
            )
            for lane in ("baselines", "fitted"):
                journal.lane, journal.variant = lane, variant
                product = products[lane, variant]
                scored = api["score"](
                    product.directory,
                    expected_manifest_sha256=product.manifest_sha256,
                    outcome_root=inputs[variant],
                    outcome_inventory=inventory,
                    destination=output / (lane + "-" + variant + "-scores"),
                )
                rows = json.loads((scored.directory / "scores.json").read_text())
                score_rows.append(
                    {
                        "lane": lane,
                        "variant": variant,
                        "rows": rows,
                        "manifest_sha256": scored.manifest_sha256,
                        "directory": str(scored.directory),
                    }
                )
    for lane in ("baselines", "fitted"):
        left, right = [row for row in target_rows if row["lane"] == lane]
        if (
            left["training_sha256"] != right["training_sha256"]
            or left["predictions"] != right["predictions"]
            or left["method_dispositions"] != right["method_dispositions"]
        ):
            raise ValueError(
                "Target-only labels altered training inputs or predictions"
            )
    batches = [row for row in journal.rows if row["kind"] == "batch_completed"]
    items = [item for row in batches for item in row["result"]["items"]]
    report = {
        "schema_version": "development-input-isolation-current.v1",
        "scope": protocol["scope"],
        "identity_witness": identity,
        "target_evidence": target_rows,
        "score_products": score_rows,
        "actual_batch_items": len(items),
        "actual_unique_requests": len({item["request_sha256"] for item in items}),
        "saved_cache_seed": seed,
        "engine_call_observation_scope": "Parent hooks do not propagate into spawned cache workers; this counter reports only directly observed parent events, not child stage calls.",
        "actual_cache_misses": sum(item.get("cache_hit") is False for item in items),
        "actual_cache_hits": sum(item.get("cache_hit") is True for item in items),
        "actual_engine_calls": dict(
            Counter(
                row["operation"]
                for row in journal.rows
                if row["kind"] == "engine_before"
            )
        ),
        "actual_spatial_fit_operations": sum(
            row["kind"] == "spatial_fit_before" for row in journal.rows
        ),
        "journal": helper["pin"](journal.path),
        "protocol_canonical_sha256": helper["digest"](protocol),
        "scientific_acceptance": "not_evaluated",
        "historical_receipt_restored": False,
    }
    helper["write"](output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.protocol.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.protocol_sha256:
        raise ValueError("Frozen protocol differs")
    protocol = json.loads(raw)
    row = protocol["source_files"]["evidence.py"]
    path = args.repository / row["path"]
    if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError("Regular single-link helper required")
    content = path.read_bytes()
    if (
        len(content) != row["bytes"]
        or hashlib.sha256(content).hexdigest() != row["sha256"]
    ):
        raise ValueError("Helper differs from frozen source")
    if set(protocol["source_files"]) != {"replay.py", "evidence.py"}:
        raise ValueError("Exact two-source scientific namespace required")
    declared = protocol["source_files"]["replay.py"]
    current = Path(__file__).read_bytes()
    if (
        len(current) != declared["bytes"]
        or hashlib.sha256(current).hexdigest() != declared["sha256"]
    ):
        raise ValueError("Scientific caller differs from frozen source")
    if {p.name for p in path.parent.iterdir() if p.suffix == ".py"} != set(
        protocol["source_files"]
    ):
        raise ValueError("Undeclared scientific source member")
    helper = runpy.run_path(str(path), run_name="development_input_isolation_evidence")
    run(args.repository, args.output, protocol, helper)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
