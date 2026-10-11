"""Pair fixed-radius LRA forward pollen with the published direct baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any


EXPECTED = {
    "radius_report": "d2c10a128acb00425c5c785ce195ad245bcf1b428f0f4a4d75d0f7aa95f11129",
    "radius_scores": "60bf6b4cc25bf94a9afbb241370d55e7be17239c20e25881b4cc862e452eb494",
    "direct_mae": "623b0eb20e46e86fccbd48e840fa20e1882b89bf17ef3ef81c89e63c3a2c6f50",
    "direct_hellinger": "91255eda5f958f7072ea489dfc36201360b7aaa5f019e5f0c91f3e2a59830950",
}
FACTORS = (0.8, 1.0, 1.2)
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def produce(study: Path, output: Path) -> None:
    """Compare paired development results without reopening raw target counts."""
    if output.exists():
        raise FileExistsError(output)
    parent = study.parent
    sources = {
        "radius_report": study / "scored/report.json",
        "radius_scores": study / "scored/scores.csv",
        "direct_mae": parent / "direct-pollen/matched-scores.csv",
        "direct_hellinger": parent / "direct-pollen/paired-hellinger.json",
    }
    for name, path in sources.items():
        if _sha(path) != EXPECTED[name]:
            raise ValueError(f"published comparison source changed: {name}")
    report = json.loads(sources["radius_report"].read_text())
    hellinger = json.loads(sources["direct_hellinger"].read_text())
    if (
        report["scored_sites"] != 14
        or report["scored_rows"] != 126
        or hellinger["matched_sites"] != 14
        or hellinger["matched_method_rows"] != 42
        or report["source"]["prediction_manifest_sha256"]
        != hellinger["lra_prediction_manifest_sha256"]
    ):
        raise ValueError("published paired-study support changed")
    direct_mae = {
        (row["target_record_id"], row["method"]): row
        for row in _csv(sources["direct_mae"])
    }
    direct_hellinger = {
        (row["target_record_id"], row["method"]): row
        for row in hellinger["site_method_rows"]
    }
    radius = _csv(sources["radius_scores"])
    if len(direct_mae) != 42 or len(direct_hellinger) != 42 or len(radius) != 126:
        raise ValueError("paired row identities changed")
    paired: list[dict[str, Any]] = []
    for source in radius:
        key = source["record_id"], source["method"]
        original = direct_mae[key]
        distance = direct_hellinger[key]
        if (
            source["observation_sha256"]
            != original["target_raw_sha256"]
            != distance["target_raw_sha256"]
            or int(source["observed_count"]) != distance["observed_total_count"]
            or original["lra_prediction_identity"]
            != distance["lra_prediction_identity"]
        ):
            raise ValueError("paired target or LRA prediction identity changed")
        factor = float(source["radius_factor"])
        lra_mae = float(source["mae_fraction"])
        lra_hellinger = float(source["hellinger_distance"])
        direct_pollen_mae = float(original["direct_pollen_mae_fraction"])
        direct_pollen_hellinger = float(distance["direct_pollen_hellinger"])
        if factor == 1.0 and (
            abs(lra_mae - float(original["lra_forward_pollen_mae_fraction"])) > 1e-15
            or abs(lra_hellinger - float(distance["lra_forward_pollen_hellinger"]))
            > 1e-15
        ):
            raise ValueError("declared-radius paired baseline changed")
        paired.append(
            {
                "record_id": key[0],
                "method": key[1],
                "radius_factor": factor,
                "direct_mae_fraction": direct_pollen_mae,
                "lra_mae_fraction": lra_mae,
                "direct_minus_lra_mae_fraction": direct_pollen_mae - lra_mae,
                "direct_hellinger_distance": direct_pollen_hellinger,
                "lra_hellinger_distance": lra_hellinger,
                "direct_minus_lra_hellinger_distance": (
                    direct_pollen_hellinger - lra_hellinger
                ),
                "observation_sha256": source["observation_sha256"],
            }
        )
    summary: list[dict[str, Any]] = []
    for method in METHODS:
        for factor in FACTORS:
            rows = [
                row
                for row in paired
                if row["method"] == method and row["radius_factor"] == factor
            ]
            if len(rows) != 14:
                raise ValueError("radius comparison lost a matched site")
            summary.append(
                {
                    "method": method,
                    "radius_factor": factor,
                    "paired_sites": len(rows),
                    "direct_mae_fraction": mean(
                        row["direct_mae_fraction"] for row in rows
                    ),
                    "lra_mae_fraction": mean(row["lra_mae_fraction"] for row in rows),
                    "direct_minus_lra_mae_fraction": mean(
                        row["direct_minus_lra_mae_fraction"] for row in rows
                    ),
                    "direct_lower_mae_sites": sum(
                        row["direct_minus_lra_mae_fraction"] < 0 for row in rows
                    ),
                    "direct_hellinger_distance": mean(
                        row["direct_hellinger_distance"] for row in rows
                    ),
                    "lra_hellinger_distance": mean(
                        row["lra_hellinger_distance"] for row in rows
                    ),
                    "direct_minus_lra_hellinger_distance": mean(
                        row["direct_minus_lra_hellinger_distance"] for row in rows
                    ),
                    "direct_lower_hellinger_sites": sum(
                        row["direct_minus_lra_hellinger_distance"] < 0 for row in rows
                    ),
                }
            )
    output.mkdir(parents=True)
    with (output / "paired-scores.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(paired[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(paired)
    (output / "report.json").write_text(
        json.dumps(
            {
                "schema_version": "author-lra-radius-direct-paired.v1",
                "source_sha256": EXPECTED,
                "producer_sha256": _sha(Path(__file__)),
                "matched_sites": 14,
                "paired_rows": len(paired),
                "summary": summary,
                "interpretation": "Prior-exposed English 30-target development comparison. Direct pollen and fixed-vegetation LRA forward pollen share target observations, but not training information. Radius variants are modeled geometry assumptions, not calibrated basins or refitted LOVE.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    produce(args.study.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
