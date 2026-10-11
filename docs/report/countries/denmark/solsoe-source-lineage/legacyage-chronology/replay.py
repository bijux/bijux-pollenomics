"""Join Solsø core samples to primary LegacyAge depth and chronology tables."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from statistics import median

SOURCE_SHA = {
    "table-s5-legacyage-chronology.csv": "bbe0e8d5854acf091a11737ddedc10d5656f8a25c8eeb9637b85f9e69a37cb41",
    "table-s6-chronology-comparison.csv": "2a058f08472199b0545e4562e6860371dfaba7ce74140b1e0b4dbdce0ce55300",
}
NEOTOMA_SHA = {
    "samples": "c959e77f7c645b814bffe92a92ff2d8fabcc077b4fc4c894e6315e448d14100c",
    "age_claims": "6b8983b43138ec68895d96070508218d0b7c4f9908bf87860f96b79d2725c558",
}
CORES = {
    "4445": {"name": "SOLSOE81", "unit": "4303", "samples": 66, "s5_depths": 492},
    "4446": {"name": "SOLSOE83", "unit": "4304", "samples": 26, "s5_depths": 185},
}
CHRONOLOGY = "Giesecke et al. 2014 (MADCAP)"
FIELDS = (
    "dataset_id",
    "core",
    "sample_id",
    "depth_cm",
    "neotoma_age_cal_bp",
    "neotoma_age_claim_status",
    "neotoma_age_refusal_reason",
    "legacyage_min_cal_bp",
    "legacyage_max_cal_bp",
    "legacyage_median_cal_bp",
    "legacyage_mean_cal_bp",
    "legacyage_depth_uncertainty_yr",
    "legacyage_record_mean_uncertainty_yr",
    "neotoma_point_inside_s5_95_percent",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _checked(path: Path, digest: str) -> None:
    if _sha(path) != digest:
        raise ValueError(f"source identity changed: {path}")


def _source_rows(repository: Path, surface: str) -> list[dict]:
    path = repository / "data/neotoma/relational/surfaces" / surface / "part-00001.json"
    _checked(path, NEOTOMA_SHA[surface])
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def _write_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def replay(repository: Path, source_dir: Path, output: Path) -> None:
    """Produce an exact native-depth relation without transferring age models."""
    repository = repository.resolve()
    source_dir = source_dir.resolve()
    if output.exists():
        raise ValueError(f"output must be absent: {output}")
    for name, digest in SOURCE_SHA.items():
        _checked(source_dir / name, digest)
    samples = [
        row
        for row in _source_rows(repository, "samples")
        if row["dataset_id"].split(":")[-1] in CORES
    ]
    claims = [
        row
        for row in _source_rows(repository, "age_claims")
        if row["dataset_id"].split(":")[-1] in CORES
        and row["subject_type"] == "sample"
        and row["chronology_name"] == CHRONOLOGY
        and row["source_age_type"] == "Calibrated radiocarbon years BP"
    ]
    ages = {row["subject_id"]: row for row in claims}
    if len(samples) != 92 or len(claims) != 92 or len(ages) != 92:
        raise ValueError("Solsø core sample or calibrated age denominator changed")
    s5: dict[tuple[str, Decimal], dict[str, str]] = {}
    with (source_dir / "table-s5-legacyage-chronology.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            dataset = row["Dataset_ID"]
            if dataset not in CORES:
                continue
            key = (dataset, Decimal(row["Depth (cm)"]))
            if key in s5:
                raise ValueError(f"duplicate S5 core-depth identity: {key}")
            if not (
                Decimal(row["Age_Minimum"])
                <= Decimal(row["Age_Median"])
                <= Decimal(row["Age_Maximum"])
            ):
                raise ValueError(f"S5 age interval order changed: {key}")
            s5[key] = row
    s6: dict[str, dict[str, str]] = {}
    with (source_dir / "table-s6-chronology-comparison.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            dataset = row["Dataset_ID"]
            if dataset in CORES:
                if dataset in s6:
                    raise ValueError(f"duplicate S6 core identity: {dataset}")
                s6[dataset] = row
    if set(s6) != set(CORES) or Counter(dataset for dataset, _ in s5) != {
        key: spec["s5_depths"] for key, spec in CORES.items()
    }:
        raise ValueError("Solsø S5/S6 source denominator changed")
    if any(
        row["Original.chronology_Compared"] != CHRONOLOGY
        or row["LegacyAge 1.0_Source"] != "AWI"
        for row in s6.values()
    ):
        raise ValueError("LegacyAge S6 Solsø chronology identity changed")

    joined: list[dict] = []
    unmatched: list[dict] = []
    for sample in sorted(
        samples, key=lambda row: (row["dataset_id"], Decimal(str(row["source_depth"])))
    ):
        dataset = sample["dataset_id"].split(":")[-1]
        spec = CORES[dataset]
        claim = ages[sample["sample_id"]]
        if (
            sample["site_id"] != "neotoma:site:3432"
            or sample["collection_unit_id"] != f"neotoma:collection-unit:{spec['unit']}"
            or claim["dataset_id"] != sample["dataset_id"]
            or claim["site_id"] != sample["site_id"]
            or claim["collection_unit_id"] != sample["collection_unit_id"]
            or claim["calibration_status"] != "calibrated"
            or claim["source_age_unit"] != "year"
        ):
            raise ValueError(f"Solsø sample-age owner changed: {sample['sample_id']}")
        depth = Decimal(str(sample["source_depth"]))
        estimate = s5.get((dataset, depth))
        if estimate is None:
            unmatched.append(
                {
                    "dataset_id": dataset,
                    "core": spec["name"],
                    "sample_id": sample["sample_id"],
                    "depth_cm": str(depth),
                    "reason": "no_exact_s5_depth",
                }
            )
            continue
        point = Decimal(str(claim["source_age_value"]))
        younger = Decimal(estimate["Age_Minimum"])
        older = Decimal(estimate["Age_Maximum"])
        joined.append(
            {
                "dataset_id": dataset,
                "core": spec["name"],
                "sample_id": sample["sample_id"],
                "depth_cm": str(depth),
                "neotoma_age_cal_bp": str(point),
                "neotoma_age_claim_status": claim["comparability_status"],
                "neotoma_age_refusal_reason": claim["admission_reason"] or "",
                "legacyage_min_cal_bp": estimate["Age_Minimum"],
                "legacyage_max_cal_bp": estimate["Age_Maximum"],
                "legacyage_median_cal_bp": estimate["Age_Median"],
                "legacyage_mean_cal_bp": estimate["Age_Mean"],
                "legacyage_depth_uncertainty_yr": estimate["Uncertainty_Each.depth"],
                "legacyage_record_mean_uncertainty_yr": estimate[
                    "Uncertainty_Record.mean"
                ],
                "neotoma_point_inside_s5_95_percent": younger <= point <= older,
            }
        )
    by_dataset = Counter(row["dataset_id"] for row in joined)
    if by_dataset != {key: spec["samples"] for key, spec in CORES.items()} or unmatched:
        raise ValueError("Solsø exact-depth sample coverage changed")
    refusals = [
        {
            "dataset_id": row["dataset_id"],
            "core": row["core"],
            "sample_id": row["sample_id"],
            "depth_cm": row["depth_cm"],
            "age_claim_status": row["neotoma_age_claim_status"],
            "reason": row["neotoma_age_refusal_reason"],
        }
        for row in joined
        if row["neotoma_age_claim_status"] != "comparable"
    ]
    if refusals != [
        {
            "dataset_id": "4445",
            "core": "SOLSOE81",
            "sample_id": "neotoma:sample:352996",
            "depth_cm": "98",
            "age_claim_status": "refused",
            "reason": "negative_bp",
        }
    ]:
        raise ValueError("Solsø age-claim refusal changed")
    output.mkdir(parents=True)
    _write_csv(output / "sample-depth-join.csv", joined, FIELDS)
    _write_csv(output / "refused-samples.csv", refusals, tuple(refusals[0]))
    datasets = {}
    for key, spec in CORES.items():
        rows = [row for row in joined if row["dataset_id"] == key]
        deltas = [
            Decimal(row["legacyage_mean_cal_bp"]) - Decimal(row["neotoma_age_cal_bp"])
            for row in rows
        ]
        datasets[key] = {
            "core": spec["name"],
            "collection_unit_id": f"neotoma:collection-unit:{spec['unit']}",
            "neotoma_samples": spec["samples"],
            "s5_model_depths": spec["s5_depths"],
            "exact_sample_depth_joins": len(rows),
            "no_exact_depth_samples": 0,
            "comparable_calibrated_age_claims": sum(
                row["neotoma_age_claim_status"] == "comparable" for row in rows
            ),
            "refused_calibrated_age_claims": sum(
                row["neotoma_age_claim_status"] != "comparable" for row in rows
            ),
            "neotoma_points_inside_s5_95_percent": sum(
                row["neotoma_point_inside_s5_95_percent"] for row in rows
            ),
            "neotoma_points_outside_s5_95_percent": sum(
                not row["neotoma_point_inside_s5_95_percent"] for row in rows
            ),
            "legacyage_mean_minus_neotoma_point_years": {
                "minimum": float(min(deltas)),
                "median": float(median(deltas)),
                "maximum": float(max(deltas)),
            },
            "s6_original_chronology_compared": s6[key]["Original.chronology_Compared"],
            "s6_comparison": s6[key][
                "Original.chronology_VS._Newly.chronology"
            ].strip(),
            "s6_selection_reason": s6[key]["Reason"],
            "s6_legacyage_source": s6[key]["LegacyAge 1.0_Source"],
        }
    report = {
        "schema_version": "solsoe-legacyage-exact-depth-join.v1",
        "source_doi": "10.1594/PANGAEA.933132",
        "source_license": "CC-BY-4.0",
        "source_sha256": SOURCE_SHA,
        "neotoma_sha256": NEOTOMA_SHA,
        "source_depth_unit": "cm",
        "age_unit": "calibrated years BP",
        "neotoma_site_id": "neotoma:site:3432",
        "joined_samples": len(joined),
        "unmatched_exact_depth_samples": len(unmatched),
        "refused_age_claim_samples": len(refusals),
        "datasets": datasets,
        "sample_depth_join_sha256": _sha(output / "sample-depth-join.csv"),
        "refused_samples_sha256": _sha(output / "refused-samples.csv"),
        "lra_admitted_samples": 0,
        "interpretation": "Exact sample-depth correspondence to an alternative LegacyAge chronology. The source S6 comparison does not identify historical LandClim age selection, repair a refused Neotoma age, supply sample-age basin geometry, or admit LRA input.",
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    replay(args.repository, args.source_dir, args.output)


if __name__ == "__main__":
    main()
