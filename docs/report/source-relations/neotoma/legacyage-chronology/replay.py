"""Join primary LegacyAge depth estimates to named Neotoma pollen samples."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median


SOURCES = {
    "table-s5-legacyage-chronology.csv": "bbe0e8d5854acf091a11737ddedc10d5656f8a25c8eeb9637b85f9e69a37cb41",
    "table-s6-chronology-comparison.csv": "2a058f08472199b0545e4562e6860371dfaba7ce74140b1e0b4dbdce0ce55300",
}
NEOTOMA = {
    "samples": "c959e77f7c645b814bffe92a92ff2d8fabcc077b4fc4c894e6315e448d14100c",
    "age_claims": "6b8983b43138ec68895d96070508218d0b7c4f9908bf87860f96b79d2725c558",
}
DATASETS = {
    "19913": {
        "site": "13338",
        "core": "ABBO",
        "native_chronology": "EPD 1",
        "samples": 107,
        "model_depths": 249,
    },
    "20034": {
        "site": "13388",
        "core": "DALMUT",
        "native_chronology": "author preferred",
        "samples": 72,
        "model_depths": 289,
    },
}
FIELDS = (
    "dataset_id",
    "site_id",
    "core",
    "sample_id",
    "depth_cm",
    "neotoma_age_cal_bp",
    "legacyage_min_cal_bp",
    "legacyage_max_cal_bp",
    "legacyage_median_cal_bp",
    "legacyage_mean_cal_bp",
    "legacyage_depth_uncertainty_yr",
    "legacyage_record_mean_uncertainty_yr",
)


def checked(path: Path, expected: str) -> str:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"source hash changed: {path}: {actual}")
    return actual


def surface(repository: Path, name: str) -> list[dict]:
    path = repository / "data/neotoma/relational/surfaces" / name / "part-00001.json"
    checked(path, NEOTOMA[name])
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(f"output must be absent: {args.output}")
    for name, digest in SOURCES.items():
        checked(args.source_dir / name, digest)

    samples = [
        r
        for r in surface(args.repository, "samples")
        if r["dataset_id"].split(":")[-1] in DATASETS
    ]
    ages = [
        r
        for r in surface(args.repository, "age_claims")
        if r["dataset_id"].split(":")[-1] in DATASETS
    ]
    selected_ages = {}
    for row in ages:
        dataset = row["dataset_id"].split(":")[-1]
        if row["chronology_name"] == DATASETS[dataset]["native_chronology"]:
            assert row["calibration_status"] == "calibrated"
            assert row["source_age_type"] == "Calibrated radiocarbon years BP"
            key = (dataset, row["subject_id"])
            assert key not in selected_ages
            selected_ages[key] = row["source_age_value"]

    s5 = {}
    with (args.source_dir / "table-s5-legacyage-chronology.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            dataset = row["Dataset_ID"]
            if dataset not in DATASETS:
                continue
            key = (dataset, row["Depth (cm)"])
            assert key not in s5
            assert (
                float(row["Age_Minimum"])
                <= float(row["Age_Median"])
                <= float(row["Age_Maximum"])
            )
            s5[key] = row

    s6 = {}
    with (args.source_dir / "table-s6-chronology-comparison.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            dataset = row["Dataset_ID"]
            if dataset in DATASETS:
                assert dataset not in s6
                s6[dataset] = row

    joined, unmatched = [], []
    for sample in sorted(
        samples, key=lambda r: (r["dataset_id"], float(r["source_depth"]))
    ):
        dataset = sample["dataset_id"].split(":")[-1]
        spec = DATASETS[dataset]
        assert sample["site_id"] == f"neotoma:site:{spec['site']}"
        assert (dataset, sample["sample_id"]) in selected_ages
        # Native depth has independent centimetre support for these cores; do not round a fractional depth.
        depth = str(sample["source_depth"])
        estimate = s5.get((dataset, depth))
        if estimate is None:
            unmatched.append(
                {
                    "dataset_id": dataset,
                    "sample_id": sample["sample_id"],
                    "depth_cm": depth,
                    "reason": "no exact LegacyAge S5 depth",
                }
            )
            continue
        joined.append(
            {
                "dataset_id": dataset,
                "site_id": spec["site"],
                "core": spec["core"],
                "sample_id": sample["sample_id"],
                "depth_cm": depth,
                "neotoma_age_cal_bp": selected_ages[(dataset, sample["sample_id"])],
                "legacyage_min_cal_bp": estimate["Age_Minimum"],
                "legacyage_max_cal_bp": estimate["Age_Maximum"],
                "legacyage_median_cal_bp": estimate["Age_Median"],
                "legacyage_mean_cal_bp": estimate["Age_Mean"],
                "legacyage_depth_uncertainty_yr": estimate["Uncertainty_Each.depth"],
                "legacyage_record_mean_uncertainty_yr": estimate[
                    "Uncertainty_Record.mean"
                ],
            }
        )

    sample_counts = Counter(r["dataset_id"].split(":")[-1] for r in samples)
    model_counts = Counter(dataset for dataset, _ in s5)
    assert all(
        sample_counts[key] == spec["samples"]
        and model_counts[key] == spec["model_depths"]
        for key, spec in DATASETS.items()
    )
    assert len(joined) == 178 and unmatched == [
        {
            "dataset_id": "20034",
            "sample_id": "neotoma:sample:175354",
            "depth_cm": "4.5",
            "reason": "no exact LegacyAge S5 depth",
        }
    ]
    assert all(
        float(row["legacyage_min_cal_bp"])
        <= float(row["neotoma_age_cal_bp"])
        <= float(row["legacyage_max_cal_bp"])
        for row in joined
    )
    assert all(s6[key]["LegacyAge 1.0_Source"] == "AWI" for key in DATASETS)

    args.output.mkdir(parents=True)
    with (args.output / "sample-depth-join.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(joined)
    with (args.output / "unmatched-samples.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("dataset_id", "sample_id", "depth_cm", "reason"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(unmatched)
    age_deltas = {
        key: [
            float(row["legacyage_mean_cal_bp"]) - float(row["neotoma_age_cal_bp"])
            for row in joined
            if row["dataset_id"] == key
        ]
        for key in DATASETS
    }
    report = {
        "schema_version": "legacyage-neotoma-depth-join.v1",
        "source_doi": "10.1594/PANGAEA.933132",
        "source_license": "CC-BY-4.0",
        "source_sha256": SOURCES,
        "neotoma_sha256": NEOTOMA,
        "depth_unit": "cm",
        "age_unit": "calibrated years BP",
        "datasets": {
            key: {
                "site_id": spec["site"],
                "core": spec["core"],
                "samples": sample_counts[key],
                "s5_model_depths": model_counts[key],
                "exact_sample_depth_joins": sum(r["dataset_id"] == key for r in joined),
                "unmatched_sample_depths": [
                    r["depth_cm"] for r in unmatched if r["dataset_id"] == key
                ],
                "legacyage_mean_minus_neotoma_point_years": {
                    "minimum": min(age_deltas[key]),
                    "median": median(age_deltas[key]),
                    "maximum": max(age_deltas[key]),
                },
                "original_chronology_compared": s6[key]["Original.chronology_Compared"],
                "comparison": s6[key][
                    "Original.chronology_VS._Newly.chronology"
                ].strip(),
                "selection_reason": s6[key]["Reason"],
                "legacyage_source": s6[key]["LegacyAge 1.0_Source"],
            }
            for key, spec in DATASETS.items()
        },
        "exact_joins_with_neotoma_point_age_inside_s5_95_percent_range": len(joined),
        "lra_admitted_samples": 0,
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
