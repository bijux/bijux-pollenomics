"""Replay the ABBO LegacyAge interval-contained direct-pollen sensitivity."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.source_completion import swedish_direct_pollen as direct


HERE = Path(__file__).resolve().parent
ORIGINAL = Path("docs/report/pollen-reconstruction/swedish-direct-pollen")
JOIN = Path(
    "docs/report/source-relations/neotoma/legacyage-chronology/sample-depth-join.csv"
)
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json")
SOURCE_HASHES = {
    str(JOIN): "00fb70fc6201b07873d2ec13ea59ec6018c656ae5f680f881c055d1a0a4b4ac6",
    str(RAW): "d96046c88b497ba07082120e446fecacad0d9b5533d8960bdbc03811976ea435",
    str(
        ORIGINAL / "prepared/dataset-19913.json"
    ): "fad881f64fae9fcf632854068274375f4f842398cfe2255ba71b68e9a6335d79",
    str(
        ORIGINAL / "prepared/dataset-53995.json"
    ): "7ff0ce9286983ab726e6fb9bcd95df3cf393ef0df7efde81a79b78d2c3fd92e5",
    str(
        ORIGINAL / "prepared/dataset-54001.json"
    ): "3231eb8ca83f99b3ecdeca8eb8aacc7f60c4bbf2547dca2c0e2c23a98e98b520",
}
SUPPORT_FIELDS = (
    "sample_id",
    "depth_cm",
    "neotoma_age_cal_bp",
    "legacyage_min_cal_bp",
    "legacyage_max_cal_bp",
    "possible_common_bins",
    "contained_common_bin",
    "admission",
    "all_nisp_count",
    "closed_nisp_count",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_inputs(repository: Path) -> None:
    for relative, expected in SOURCE_HASHES.items():
        if sha(repository / relative) != expected:
            raise ValueError(f"source bytes changed: {relative}")


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def prepare(repository: Path, output: Path) -> None:
    """Prepare outcomes without mixing an ABBO target into any prediction fold."""
    if output.exists():
        raise ValueError(f"output must be absent: {output}")
    checked_inputs(repository)
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    parent_config = json.loads(
        (repository / ORIGINAL / "config.json").read_text(encoding="utf-8")
    )
    bins = config["common_age_bin_ids"]
    if bins != [3, 4, 5, 9] or config["closed_taxa"] != parent_config["closed_taxa"]:
        raise ValueError("declared common support or taxon denominator changed")
    if config["sites"] != parent_config["sites"]:
        raise ValueError("site identity or coordinates changed")

    source_rows = [
        row
        for row in csv.DictReader(
            (repository / JOIN).open(encoding="utf-8", newline="")
        )
        if row["dataset_id"] == "19913"
    ]
    join_rows = {row["sample_id"]: row for row in source_rows}
    if len(source_rows) != 107 or len(join_rows) != 107:
        raise ValueError("ABBO LegacyAge join is incomplete or duplicated")
    raw = json.loads((repository / RAW).read_text(encoding="utf-8"))
    matched_sites = [
        row["site"]
        for row in raw["rows"]
        if str(row["site"].get("dataset", {}).get("datasetid")) == "19913"
    ]
    if len(matched_sites) != 1 or str(matched_sites[0]["siteid"]) != "13338":
        raise ValueError("ABBO raw dataset/site identity changed")
    samples = matched_sites[0]["collectionunit"]["dataset"]["samples"]
    prior = json.loads(
        (repository / ORIGINAL / "prepared/dataset-19913.json").read_text(
            encoding="utf-8"
        )
    )
    taxa = tuple(config["closed_taxa"])
    profile = {**prior, "bins": {}}
    support: list[dict[str, Any]] = []
    seen: set[str] = set()
    for sample in samples:
        sample_id = f"neotoma:sample:{sample['sampleid']}"
        row = join_rows.get(sample_id)
        if row is None or sample_id in seen:
            raise ValueError(f"unmatched or duplicate ABBO sample: {sample_id}")
        seen.add(sample_id)
        native_age = sample["ages"]
        if len(native_age) != 1 or float(native_age[0]["age"]) != float(
            row["neotoma_age_cal_bp"]
        ):
            raise ValueError(f"native sample age differs: {sample_id}")
        if float(sample["depth"]) != float(row["depth_cm"]):
            raise ValueError(f"sample depth differs: {sample_id}")
        low, high = (
            float(row["legacyage_min_cal_bp"]),
            float(row["legacyage_max_cal_bp"]),
        )
        if not low <= high:
            raise ValueError(f"invalid S5 interval: {sample_id}")
        # S5 endpoints are closed; the study bins are [lower, upper).
        possible = [
            bin_id
            for bin_id in bins
            if low < (bin_id + 1) * 500 and high >= bin_id * 500
        ]
        contained = [
            bin_id
            for bin_id in bins
            if low >= bin_id * 500 and high < (bin_id + 1) * 500
        ]
        if len(contained) > 1:
            raise ValueError(f"sample wholly contained in multiple bins: {sample_id}")
        counts = dict.fromkeys(taxa, 0)
        all_nisp = 0
        names: set[str] = set()
        for datum in sample["datum"]:
            if datum.get("units") != "NISP" or datum.get("elementtype") != "pollen":
                continue
            name, value = datum.get("variablename"), datum.get("value")
            if (
                not isinstance(name, str)
                or type(value) is not int
                or value < 0
                or name in names
            ):
                raise ValueError(f"invalid or duplicate ABBO datum: {sample_id}")
            names.add(name)
            all_nisp += value
            if name in counts:
                counts[name] += value
        if all_nisp <= 0:
            raise ValueError(f"empty ABBO sample: {sample_id}")
        selected = contained[0] if contained else None
        support.append(
            {
                "sample_id": sample_id,
                "depth_cm": row["depth_cm"],
                "neotoma_age_cal_bp": row["neotoma_age_cal_bp"],
                "legacyage_min_cal_bp": row["legacyage_min_cal_bp"],
                "legacyage_max_cal_bp": row["legacyage_max_cal_bp"],
                "possible_common_bins": ";".join(map(str, possible)),
                "contained_common_bin": "" if selected is None else selected,
                "admission": "contained"
                if selected is not None
                else "unresolved_in_common_bins"
                if possible
                else "outside_common_bins",
                "all_nisp_count": all_nisp,
                "closed_nisp_count": sum(counts.values()),
            }
        )
        if selected is not None:
            bucket = profile["bins"].setdefault(
                str(selected),
                {
                    "counts": dict.fromkeys(taxa, 0),
                    "all_nisp_count": 0,
                    "closed_nisp_count": 0,
                    "sample_count": 0,
                },
            )
            for name, value in counts.items():
                bucket["counts"][name] += value
            bucket["all_nisp_count"] += all_nisp
            bucket["closed_nisp_count"] += sum(counts.values())
            bucket["sample_count"] += 1
    if seen != set(join_rows) or set(map(int, profile["bins"])) != set(bins):
        raise ValueError("ABBO sample or selected bin coverage changed")
    if any(x["closed_nisp_count"] <= 0 for x in profile["bins"].values()):
        raise ValueError("selected bin has no closed pollen counts")
    selected_rows = [row for row in support if row["admission"] == "contained"]
    profile.update(
        chronology_id="PANGAEA.933132/S5",
        chronology_name="LegacyAge 1.0 AWI Bacon",
        sample_age_bounds_present=True,
        sample_count=len(selected_rows),
        all_nisp_count=sum(int(row["all_nisp_count"]) for row in selected_rows),
        closed_nisp_count=sum(int(row["closed_nisp_count"]) for row in selected_rows),
        age_min_cal_bp=min(float(row["legacyage_min_cal_bp"]) for row in selected_rows),
        age_max_cal_bp=max(float(row["legacyage_max_cal_bp"]) for row in selected_rows),
        age_support_policy="full S5 reported 95% interval inside one half-open 500-cal-BP bin",
    )
    output.mkdir(parents=True)
    dump(output / "prepared/dataset-19913.json", profile)
    for dataset_id in ("53995", "54001"):
        source = repository / ORIGINAL / f"prepared/dataset-{dataset_id}.json"
        destination = output / "prepared" / source.name
        destination.write_bytes(source.read_bytes())
    with (output / "age-bin-support.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=SUPPORT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(support)
    dump(
        output / "input-manifest.json",
        {
            "schema_version": "abbo-interval-contained-pollen.v1",
            "source_sha256": SOURCE_HASHES,
            "config_sha256": sha(HERE / "config.json"),
            "producer_sha256": sha(HERE / "replay.py"),
            "age_source": "LegacyAge 1.0 S5 reported 95% bounds, DOI 10.1594/PANGAEA.933132",
            "admitted_abbo_samples": sum(
                row["admission"] == "contained" for row in support
            ),
            "abbo_bins": {
                key: value["sample_count"] for key, value in profile["bins"].items()
            },
        },
    )


def score(repository: Path, output: Path) -> None:
    """Score only after three whole-site prediction files have been sealed."""
    prediction_files = [
        output / "predictions" / f"site-{site}.json"
        for site in ("13338", "28869", "28872")
    ]
    if any(not path.is_file() for path in prediction_files):
        raise ValueError("all three saved site predictions are required before scoring")
    prior_hashes = {path.name: sha(path) for path in prediction_files}
    direct.score(output)
    # The shared scorer emits prose for its original 13-bin design.
    (output / "REPORT.md").unlink()
    if prior_hashes != {path.name: sha(path) for path in prediction_files}:
        raise ValueError("a saved prediction changed during scoring")
    original_rows = list(
        csv.DictReader(
            (repository / ORIGINAL / "scores.csv").open(encoding="utf-8", newline="")
        )
    )
    new_rows = list(
        csv.DictReader((output / "scores.csv").open(encoding="utf-8", newline=""))
    )
    common = {
        int(value)
        for value in json.loads((HERE / "config.json").read_text(encoding="utf-8"))[
            "common_age_bin_ids"
        ]
    }
    reference = {
        (r["candidate_id"], r["target_dataset_id"], int(r["bin_id"])): r
        for r in original_rows
        if int(r["bin_id"]) in common
    }
    if len(reference) != 48 or len(new_rows) != 48:
        raise ValueError(
            "paired score denominator differs from four methods x twelve site-bins"
        )
    by_method: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in new_rows:
        key = (row["candidate_id"], row["target_dataset_id"], int(row["bin_id"]))
        if (
            key not in reference
            or row["status"] != "scored"
            or reference[key]["status"] != "scored"
        ):
            raise ValueError(f"unpaired or unscored prediction: {key}")
        by_method[row["candidate_id"]].append(row)
    comparison: dict[str, Any] = {}
    for method, rows in by_method.items():
        site_scores: list[dict[str, float]] = []
        for site in ("19913", "53995", "54001"):
            selected = [r for r in rows if r["target_dataset_id"] == site]
            if len(selected) != 4:
                raise ValueError(f"missing paired site bins: {method}, {site}")
            site_scores.append(
                {
                    name: sum(float(r[name]) for r in selected) / 4
                    for name in ("mae_fraction", "hellinger_distance")
                }
            )
        old_site_scores = []
        for site in ("19913", "53995", "54001"):
            selected = [reference[(method, site, bin_id)] for bin_id in sorted(common)]
            old_site_scores.append(
                {
                    name: sum(float(r[name]) for r in selected) / 4
                    for name in ("mae_fraction", "hellinger_distance")
                }
            )
        comparison[method] = {
            "paired_site_bin_targets": 12,
            "original_same_support_site_macro_mae": sum(
                x["mae_fraction"] for x in old_site_scores
            )
            / 3,
            "interval_contained_site_macro_mae": sum(
                x["mae_fraction"] for x in site_scores
            )
            / 3,
            "original_same_support_site_macro_hellinger": sum(
                x["hellinger_distance"] for x in old_site_scores
            )
            / 3,
            "interval_contained_site_macro_hellinger": sum(
                x["hellinger_distance"] for x in site_scores
            )
            / 3,
        }
        comparison[method]["delta_mae"] = (
            comparison[method]["interval_contained_site_macro_mae"]
            - comparison[method]["original_same_support_site_macro_mae"]
        )
        comparison[method]["delta_hellinger"] = (
            comparison[method]["interval_contained_site_macro_hellinger"]
            - comparison[method]["original_same_support_site_macro_hellinger"]
        )
    dump(
        output / "comparison.json",
        {
            "schema_version": "abbo-interval-contained-paired-comparison.v1",
            "prediction_sha256_before_target_scoring": prior_hashes,
            "methods": comparison,
            "interpretation": "prior-exposed development sensitivity; S5 bounds select ABBO samples; no joint chronology posterior or LRA",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "predict", "score"))
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-dataset-id", choices=("19913", "53995", "54001"))
    args = parser.parse_args()
    repository = args.repository.resolve()
    output = args.output.resolve()
    if args.stage == "prepare":
        prepare(repository, output)
    elif args.stage == "predict":
        if args.target_dataset_id is None:
            parser.error("predict requires --target-dataset-id")
        direct.predict(args.target_dataset_id, output, HERE / "config.json")
    else:
        score(repository, output)


if __name__ == "__main__":
    main()
