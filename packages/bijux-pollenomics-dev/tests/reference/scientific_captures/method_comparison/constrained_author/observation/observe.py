"""Verify all eleven products and the actual current native provenance chain."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

from contracts import compare, original_denominator


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def csv_rows(path):
    with Path(path).open(newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.plan)
    root, output, work, products = map(
        Path,
        (
            plan["repository"],
            plan["output"],
            plan["retained_work"],
            plan["source_products"],
        ),
    )
    sys.path[:0] = [str(root / "packages" / name / "src") for name in plan["packages"]]
    from bijux_pollenomics.analysis.lra.engine.discovery import load_engine
    from bijux_pollenomics.analysis.lra.outputs.identity import capture_code_identity
    from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product
    from bijux_pollenomics.analysis.lra_validation.contracts import manifest_sha256
    from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
        read_experiment_product,
    )

    binding = load_engine()
    code = capture_code_identity(binding).payload()
    engine_identity = manifest_sha256(binding.as_dict())
    prediction_sha = sha(work / "predictions/manifest.json")
    score_sha = sha(work / "scores/manifest.json")
    read_experiment_product(
        work / "predictions", expected_manifest_sha256=prediction_sha
    )
    read_experiment_product(work / "scores", expected_manifest_sha256=score_sha)
    expected_inputs = Path(plan["qualified_input_epoch"]["observer"]["path"])
    witness = read(expected_inputs)
    original_inputs_root = Path(plan["qualified_input_epoch"]["plan"]["path"]).parent
    for record in witness["products_before_observer"]:
        if record["path"].startswith("constrained-inputs/"):
            current = work / record["path"]
            assert (
                current.stat().st_size == record["bytes"]
                and sha(current) == record["sha256"]
            )
            assert (
                current.read_bytes()
                == (original_inputs_root / record["path"]).read_bytes()
            )
    native = []
    receipts = sorted(
        (work / "predictions").glob("batches/fold-*/items/*/receipt.json")
    )
    assert len(receipts) == 195
    counts = Counter()
    failed = []
    for path in receipts:
        item = read(path)
        counts[item["item_status"]] += 1
        attempt = read(path.parents[2] / "receipt.json")
        declared = next(
            row for row in attempt["items"] if row["item_id"] == item["item_id"]
        )
        assert (
            item["request_sha256"]
            == declared["request_sha256"]
            == manifest_sha256(declared["request"])
        )
        assert item["scientific_acceptance"] == "not_evaluated"
        if item["item_status"] == "completed":
            record = item["product"]
            directory = Path(record["directory"])
            assert directory.is_relative_to(output) and directory.resolve() == directory
            verified = read_lra_product(
                directory, expected_manifest_sha256=record["manifest_sha256"]
            )
            manifest = verified.manifest()
            assert (
                manifest["scientific_content_sha256"]
                == record["scientific_content_sha256"]
                and manifest["request_sha256"] == item["request_sha256"]
            )
            assert manifest["engine"] == binding.as_dict()
            for key, value in code.items():
                compare(manifest["scientific_identity"][key], value, {})
            native.append(
                {
                    "item": item["item_id"],
                    "request_sha256": item["request_sha256"],
                    "product_manifest_sha256": record["manifest_sha256"],
                    "scientific_content_sha256": record["scientific_content_sha256"],
                }
            )
        elif item["item_status"] == "refused":
            assert "product" not in item and isinstance(item["error"], dict)
            failed.append(item["item_id"])
        else:
            raise ValueError(("unobserved/failed training item", item))
    assert counts == {"completed": 192, "refused": 3} and sorted(failed) == [
        "author:CUTHILL2",
        "author:HANGINGS",
        "author:LONGBREACH",
    ]
    predictions = read(work / "predictions/predictions.json")
    assert len(predictions) == 42
    identities = {}
    for row in predictions:
        manifest = row["prediction_manifest"]
        assert manifest_sha256(manifest) == row["prediction_manifest_sha256"]
        assert manifest["forward_inputs"]["engine_build_id"] == engine_identity
        assert manifest["scientific_acceptance"] == "not_evaluated_by_prediction"
        assert row["record_id"] not in manifest["allowed_input_closure"]
        compare(manifest["vegetation_fraction"], row["vegetation_fraction"], {})
        compare(manifest["pollen_fraction"], row["pollen_fraction"], {})
        key = (row["fold_id"], row["record_id"], row["baseline"])
        assert key not in identities
        identities[key] = row["prediction_manifest_sha256"]
    original_denominator(read(products / "report.json"))
    current_facts = {
        "report.json": {
            ("prediction_manifest_sha256",): prediction_sha,
            ("score_manifest_sha256",): score_sha,
        },
        "direct-pollen/comparison.json": {
            ("lra_score_csv_sha256",): sha(work / "report/scores.csv")
        },
        "direct-pollen/site-sensitivity.json": {
            ("comparison_sha256",): sha(work / "direct-comparison/comparison.json"),
            ("matched_scores_sha256",): sha(
                work / "direct-comparison/matched-scores.csv"
            ),
        },
        "direct-pollen/paired-hellinger.json": {
            ("lra_prediction_manifest_sha256",): prediction_sha,
            ("lra_prediction_csv_sha256",): sha(work / "report/predictions.csv"),
            ("lra_score_csv_sha256",): sha(work / "report/scores.csv"),
        },
        "direct-pollen/paired-hellinger-sensitivity.json": {
            ("paired_hellinger_sha256",): sha(work / "paired-hellinger.json")
        },
    }
    by_target_method = {(key[1], key[2]): value for key, value in identities.items()}
    hellinger = read(products / "direct-pollen/paired-hellinger.json")
    for index, row in enumerate(hellinger["site_method_rows"]):
        current_facts["direct-pollen/paired-hellinger.json"][
            ("site_method_rows", str(index), "lra_prediction_identity")
        ] = by_target_method[row["target_record_id"], row["method"]]
    result_rows = []
    for source, relative in plan["products"].items():
        actual, original = (
            products / relative,
            Path(plan["original_reports"][relative]["path"]),
        )
        assert actual.read_bytes() == (work / source).read_bytes()
        assert sha(original) == plan["original_reports"][relative]["sha256"]
        differences = []
        if actual.suffix == ".csv":
            a_fields, a_rows = csv_rows(actual)
            b_fields, b_rows = csv_rows(original)
            compare(a_fields, b_fields, {})
            permitted = {}
            for index, row in enumerate(a_rows):
                if (
                    relative in ("predictions.csv", "scores.csv")
                    and row["prediction_identity"]
                ):
                    permitted[str(index), "prediction_identity"] = identities[
                        row["fold_id"], row["target_record_id"], row["method"]
                    ]
                elif relative == "direct-pollen/matched-scores.csv":
                    permitted[str(index), "lra_prediction_identity"] = by_target_method[
                        row["target_record_id"], row["method"]
                    ]
            differences = compare(a_rows, b_rows, permitted)
        else:
            differences = compare(
                read(actual), read(original), current_facts.get(relative, {})
            )
        result_rows.append(
            {
                "path": relative,
                "original_sha256": sha(original),
                "actual_sha256": sha(actual),
                "byte_equal": actual.read_bytes() == original.read_bytes(),
                "all_scientific_typed_values_and_ordered_membership_equal": True,
                "declared_chain_differences": differences,
            }
        )
    assert len(result_rows) == 11
    assert {
        path.relative_to(products).as_posix()
        for path in products.rglob("*")
        if path.is_file()
    } == set(plan["products"].values())
    for row in plan["input_pins"]:
        path = Path(row["path"])
        assert (
            path.is_file()
            and not path.is_symlink()
            and path.stat().st_size == row["bytes"]
            and sha(path) == row["sha256"]
        )
    report = {
        "candidate": plan["candidate"],
        "all_eleven_products_scientific_values_equal": True,
        "products": result_rows,
        "current_binding": binding.as_dict(),
        "current_code_identity": code,
        "native_training_items": 195,
        "native_completed": 192,
        "native_refused": 3,
        "refused_training_sites": sorted(failed),
        "completed_native_products_current_code_and_inventory_verified": native,
        "target_exclusion_and_prediction_chain_verified": 42,
        "retained_full_work": str(work),
        "source_input_epoch": plan["qualified_input_epoch"],
        "current_diagnostic_reference": plan["current_diagnostic_reference"],
        "historical_3d6_terminal_available": False,
        "R_or_new_solver_or_ecological_or_official_release_acceptance": False,
        "scope": plan["scope"],
    }
    target = output / "independent-constrained-author-review.json"
    with target.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "native_exit": 0,
                "products": 11,
                "native_items": 195,
                "report_sha256": sha(target),
            }
        )
    )


if __name__ == "__main__":
    main()
