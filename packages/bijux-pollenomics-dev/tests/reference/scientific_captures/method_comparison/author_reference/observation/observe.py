"""Independently authenticate retained numerics and exact prepared request identities."""

import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def exact_typed(expected, observed):
    assert json.dumps(expected, separators=(",", ":"), allow_nan=False) == json.dumps(
        observed, separators=(",", ":"), allow_nan=False
    ), "scientific values, types or order differ"


def source_inputs(directory, original_count, taxa_count):
    report = read(directory / "source-report.json")
    experiment = read(directory / "experiment.json")
    assert (
        report["source_manifest_sha256"]
        == "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
    )
    assert report["experiment_sha256"] == sha(directory / "experiment.json")
    assert len(report["eligible_sites"]) == len(experiment["sites"]) == 15
    assert len(set(report["eligible_sites"])) == 15
    assert len(report["zero_count_sites"]) == 2
    assert report["total_count"] == original_count == 20732
    assert report["selected_window"] == 5 and report["age_support_bp"] == [1250, 1750]
    assert len(experiment["request_template"]["taxa"]) == taxa_count
    assert len(experiment["request_template"]["parameters"]) == taxa_count
    total = 0
    for site in experiment["sites"]:
        for field in ("raw", "geometry"):
            row = site[field]
            name = Path(row["path"])
            assert not name.is_absolute() and ".." not in name.parts
            assert sha(directory / name) == row["sha256"]
        raw = read(directory / site["raw"]["path"])
        assert raw["taxa"] == experiment["request_template"]["taxa"]
        assert all(type(n) is int and n >= 0 for n in raw["sample"]["counts"])
        assert len(raw["sample"]["counts"]) == taxa_count
        total += sum(raw["sample"]["counts"])
    assert total == (20732 if taxa_count == 31 else 20573)
    for row in experiment["request_template"]["evidence"]:
        name = Path(row["path"])
        assert not name.is_absolute() and ".." not in name.parts
        assert sha(directory / name) == row["sha256"]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.plan)
    root, out = Path(plan["repository"]), Path(plan["output"])
    progress = read(out / "stage-progress.json")
    assert len(progress) == 4 and all(row["actual_exit"] == 0 for row in progress)
    expected = (
        root
        / "docs/report/method-certification/petrkunes-r-comparison/native-report.json"
    )
    actual = out / "comparison/native-report.json"
    exact_typed(read(expected), read(actual))
    assert expected.read_bytes() == actual.read_bytes()
    original = source_inputs(out / "source-inputs", 20732, 31)
    constrained = source_inputs(out / "constrained-inputs", 20732, 30)
    original_constrained = read(
        root / "docs/report/pollen-reconstruction/author-lra-constrained/report.json"
    )
    assert (
        constrained["experiment_sha256"]
        == original_constrained["source_experiment_sha256"]
    )
    assert (
        constrained["excluded_taxon"] == "Filipendula"
        and constrained["excluded_taxon_nisp"] == 159
    )
    source_inputs(out / "feasibility/source-inputs", 20732, 31)
    retained = read(
        root
        / "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/report.json"
    )
    requests = []
    for label, record in zip(
        ("initial", "extended"), retained["attempts"], strict=True
    ):
        path = out / "feasibility" / label / "inputs/request.json"
        request = read(path)
        assert sha(path) == record["request_sha256"]
        assert len(request["taxa"]) == len(request["parameters"]) == 30
        assert "Filipendula" not in request["taxa"]
        requests.append({"label": label, "path": str(path), "sha256": sha(path)})
    for row in plan["input_pins"]:
        path = Path(row["path"])
        assert path.is_file() and not path.is_symlink()
        assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"]
    products = []
    for path in sorted(out.rglob("*")):
        assert not path.is_symlink()
        if path.is_file():
            products.append(
                {
                    "path": str(path.relative_to(out)),
                    "sha256": sha(path),
                    "bytes": path.stat().st_size,
                }
            )
    receipt = {
        "candidate": plan["candidate"],
        "actual_exit": 0,
        "historical_native_comparison_byte_exact": True,
        "source_preparation": original,
        "constrained_preparation": constrained,
        "exact_original_requests": requests,
        "products_before_observer": products,
        "optimizer_R_or_new_prediction_executed": False,
        "scope": plan["scope"],
    }
    path = out / "independent-author-development-input-review.json"
    assert not path.exists()
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {"native_exit": 0, "receipt_sha256": sha(path), "products": len(products)}
        )
    )


if __name__ == "__main__":
    main()
