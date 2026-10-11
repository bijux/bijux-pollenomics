"""Allocate the published LegacyAge depth summaries to DALMUT's 4.5 cm sample."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path


SOURCE_SHA256 = {
    "table-s4-original-chronology.csv": "943d6151d05cfc47df65b5a3ccedc683393fe6e8e24d14733ba7c58dcd071bb2",
    "table-s5-legacyage-chronology.csv": "bbe0e8d5854acf091a11737ddedc10d5656f8a25c8eeb9637b85f9e69a37cb41",
}
SAMPLES_SHA256 = "c959e77f7c645b814bffe92a92ff2d8fabcc077b4fc4c894e6315e448d14100c"
DATASET_ID = "20034"
SITE_ID = "13388"
SAMPLE_ID = "neotoma:sample:175354"
AUTHOR_R_COMMIT = "9ae54335e61a7a93426530141ef057dc85412e42"
AGE_COLUMNS = ("Age_Minimum", "Age_Maximum", "Age_Median", "Age_Mean")


def checked(path: Path, expected: str) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"source hash changed: {path}: {actual}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def depth_rows(path: Path, *, dataset: str) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle, delimiter="\t")
            if row["Dataset_ID"] == dataset
        ]


def number(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(f"output must be absent: {args.output}")

    manifest = json.loads((args.source_dir / "source-manifest.json").read_text())
    require(
        manifest["source_doi"] == "10.1594/PANGAEA.933132",
        "LegacyAge source DOI changed",
    )
    require(manifest["license"] == "CC-BY-4.0", "LegacyAge source rights changed")
    manifest_files = {entry["file"]: entry for entry in manifest["files"]}
    for filename, digest in SOURCE_SHA256.items():
        require(
            manifest_files[filename]["sha256"] == digest,
            f"LegacyAge source receipt changed: {filename}",
        )
        checked(args.source_dir / filename, digest)

    s4 = depth_rows(args.source_dir / "table-s4-original-chronology.csv", dataset=DATASET_ID)
    require(len(s4) == 72, "DALMUT S4 pollen-record count changed")
    require(
        all(row["Site_ID"] == SITE_ID and row["Event"] == "DALMUT" for row in s4),
        "DALMUT S4 site identity changed",
    )
    s4_by_depth = {Decimal(row["Depth_Pollen"]): row for row in s4}
    require(len(s4_by_depth) == len(s4), "DALMUT S4 pollen depths are not unique")

    samples_path = args.repository / "data/neotoma/relational/surfaces/samples/part-00001.json"
    checked(samples_path, SAMPLES_SHA256)
    samples = [
        row
        for row in json.loads(samples_path.read_text(encoding="utf-8"))["rows"]
        if row["dataset_id"] == f"neotoma:dataset:{DATASET_ID}"
    ]
    require(len(samples) == 72, "DALMUT Neotoma pollen-sample count changed")
    require(
        all(row["site_id"] == f"neotoma:site:{SITE_ID}" for row in samples),
        "DALMUT Neotoma site identity changed",
    )
    samples_by_depth = {Decimal(str(row["source_depth"])): row for row in samples}
    require(len(samples_by_depth) == len(samples), "DALMUT Neotoma depths are not unique")
    require(
        samples_by_depth.keys() == s4_by_depth.keys(),
        "DALMUT S4 and Neotoma depth datums differ",
    )
    require(
        samples_by_depth[Decimal("4.5")]["sample_id"] == SAMPLE_ID,
        "DALMUT 4.5 cm sample identity changed",
    )

    s5 = depth_rows(args.source_dir / "table-s5-legacyage-chronology.csv", dataset=DATASET_ID)
    require(len(s5) == 289, "DALMUT S5 model-grid row count changed")
    s5_by_depth = {Decimal(row["Depth (cm)"]): row for row in s5}
    require(len(s5_by_depth) == len(s5), "DALMUT S5 model depths are not unique")
    require(
        set(s5_by_depth) == {Decimal(depth) for depth in range(289)},
        "DALMUT S5 model grid is not 0–288 cm in 1 cm steps",
    )
    lower, upper = s5_by_depth[Decimal(4)], s5_by_depth[Decimal(5)]
    require(
        Decimal(lower["Depth (cm)"]) < Decimal("4.5") < Decimal(upper["Depth (cm)"]),
        "DALMUT 4.5 cm sample is not bracketed by the S5 rows",
    )
    fraction = (Decimal("4.5") - Decimal(lower["Depth (cm)"])) / (
        Decimal(upper["Depth (cm)"]) - Decimal(lower["Depth (cm)"])
    )
    require(fraction == Decimal("0.5"), "DALMUT Case II interpolation fraction changed")
    for row in (lower, upper):
        require(
            Decimal(row["Age_Minimum"])
            <= Decimal(row["Age_Median"])
            <= Decimal(row["Age_Maximum"]),
            f"DALMUT S5 age-summary order invalid at {row['Depth (cm)']} cm",
        )

    bracket = {
        str(depth): {column: number(Decimal(row[column])) for column in AGE_COLUMNS}
        for depth, row in ((4, lower), (5, upper))
    }
    allocated = {
        column: number(
            Decimal(lower[column]) * (1 - fraction) + Decimal(upper[column]) * fraction
        )
        for column in AGE_COLUMNS
    }
    report = {
        "schema_version": "legacyage-depth-summary-allocation.v1",
        "source_doi": manifest["source_doi"],
        "source_license": manifest["license"],
        "source_sha256": SOURCE_SHA256,
        "neotoma_samples_sha256": SAMPLES_SHA256,
        "author_r_commit": AUTHOR_R_COMMIT,
        "dataset_id": DATASET_ID,
        "site_id": SITE_ID,
        "core": "DALMUT",
        "sample_id": SAMPLE_ID,
        "sample_depth_cm": 4.5,
        "s4_pollen_record_depths_matching_neotoma": len(samples_by_depth),
        "s5_model_grid_cm": {"minimum": 0, "maximum": 288, "step": 1},
        "s5_bracketing_rows_cal_bp": bracket,
        "allocation_rule": "author Case II: lower * (1 - fraction) + upper * fraction",
        "fraction": number(fraction),
        "allocated_published_summary_cal_bp": allocated,
        "allocated_min_max_width_years": number(
            Decimal(str(allocated["Age_Maximum"]))
            - Decimal(str(allocated["Age_Minimum"]))
        ),
        "interpretation": "derived interpolation of published rounded age summaries; not an exact S5 row, joint posterior, historical LandClim age, or LRA admission",
    }
    args.output.mkdir(parents=True)
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
