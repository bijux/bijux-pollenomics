"""Bind Neotoma dataset identities to the bounded Nordic pollen study."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


DATASETS = Path("data/neotoma/relational/surfaces/datasets/part-00001.json")
MANIFEST = Path("data/neotoma/relational/manifest.json")
RAW_MANIFEST = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json")
SCREEN = Path("docs/report/source-relations/neotoma/pollen-screen/report.json")
COHORT = Path("docs/report/regions/nordic/direct-pollen/cohort.csv")
TRAINING = Path("docs/report/regions/nordic/direct-pollen/training-sources.csv")


def _read(repository: Path, path: Path) -> tuple[bytes, str]:
    data = (repository / path).read_bytes()
    return data, sha256(data).hexdigest()


def _dataset_id(value: str) -> str:
    return value if value.startswith("neotoma:dataset:") else f"neotoma:dataset:{value}"


def build(repository: Path) -> dict[str, Any]:
    """Keep source prerequisites and actual study membership distinct."""
    inputs = {
        path.as_posix(): _read(repository, path)[1]
        for path in (DATASETS, MANIFEST, RAW_MANIFEST, SCREEN, COHORT, TRAINING)
    }
    manifest = json.loads((repository / MANIFEST).read_bytes())
    screen = json.loads((repository / SCREEN).read_bytes())
    part = manifest["surfaces"]["datasets"]["parts"]
    if len(part) != 1 or part[0]["path"] != "surfaces/datasets/part-00001.json":
        raise ValueError("Neotoma dataset parts changed")
    if part[0]["sha256"] != inputs[DATASETS.as_posix()]:
        raise ValueError("Neotoma dataset part differs from relational manifest")
    if screen["normalized_manifest_sha256"] != inputs[MANIFEST.as_posix()] or (
        screen["raw_manifest_sha256"] != inputs[RAW_MANIFEST.as_posix()]
    ):
        raise ValueError("Neotoma screen no longer binds the current source manifests")
    datasets = json.loads((repository / DATASETS).read_bytes())["rows"]
    if len(datasets) != part[0]["row_count"]:
        raise ValueError("Neotoma dataset denominator changed")
    by_id = {row["dataset_id"]: row for row in datasets}
    if len(by_id) != len(datasets):
        raise ValueError("Duplicate Neotoma dataset identity")

    samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in screen["sample_decisions"]:
        if row["dataset_id"] not in by_id:
            raise ValueError("Screen sample has no source dataset")
        samples[row["dataset_id"]].append(row)
    if (
        sum(map(len, samples.values()))
        != screen["source_denominators"]["available_samples"]
    ):
        raise ValueError("Screen sample denominator changed")
    if (
        sum(
            row["screen_status"] == "necessary_candidate"
            for rows in samples.values()
            for row in rows
        )
        != screen["screen_denominators"]["necessary_candidate_samples"]
    ):
        raise ValueError("Screen candidate denominator changed")

    targets: dict[str, set[str]] = defaultdict(set)
    with (repository / COHORT).open(newline="") as stream:
        for row in csv.DictReader(stream):
            for dataset_id in row["dataset_ids"].split(";"):
                dataset_id = _dataset_id(dataset_id)
                source = by_id.get(dataset_id)
                if (
                    source is None
                    or source["site_id"] != row["site_id"]
                    or source["country_code"] != row["country"]
                ):
                    raise ValueError(
                        "Target cohort dataset identity differs from source"
                    )
                targets[dataset_id].add(row["country"])

    training: dict[str, set[str]] = defaultdict(set)
    with (repository / TRAINING).open(newline="") as stream:
        for row in csv.DictReader(stream):
            dataset_id = _dataset_id(row["dataset_id"])
            source = by_id.get(dataset_id)
            site_id = row["site_id"]
            if not site_id.startswith("neotoma:site:"):
                site_id = f"neotoma:site:{site_id}"
            if (
                source is None
                or source["site_id"] != site_id
                or source["country_code"] != row["training_country"]
            ):
                raise ValueError("Training dataset identity differs from source")
            training[dataset_id].add(row["held_out_country"])
    if set(targets) - set(training):
        raise ValueError("Target-linked dataset absent from other-country training")

    decisions = []
    for dataset_id, source in sorted(by_id.items()):
        records = samples[dataset_id]
        candidate = sum(
            row["screen_status"] == "necessary_candidate" for row in records
        )
        refused = len(records) - candidate
        if any(row["lra_admission_status"] != "refused" for row in records):
            raise ValueError("Unexpected LRA admission in prerequisite screen")
        selected = dataset_id in training
        decisions.append(
            {
                "dataset_id": dataset_id,
                "site_id": source["site_id"],
                "country_code": source["country_code"],
                "source_dataset_row_sha256": sha256(
                    json.dumps(source, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "sample_count": len(records),
                "count_and_comparable_age_candidate_samples": candidate,
                "prerequisite_refused_samples": refused,
                "direct_pollen_study_disposition": "included"
                if selected
                else "excluded_from_selected_study",
                "direct_pollen_target_country": sorted(targets[dataset_id]),
                "direct_pollen_training_for_held_out_countries": sorted(
                    training[dataset_id]
                ),
                "lra_disposition": "unresolved_source_requirements",
                "measured_vegetation_disposition": "unresolved_no_matched_observation",
            }
        )
    by_country = {}
    for country in ("SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE"):
        rows = [row for row in decisions if row["country_code"] == country]
        if rows:
            by_country[country] = {
                "datasets": len(rows),
                "direct_pollen_included": sum(
                    row["direct_pollen_study_disposition"] == "included" for row in rows
                ),
                "direct_pollen_excluded": sum(
                    row["direct_pollen_study_disposition"]
                    == "excluded_from_selected_study"
                    for row in rows
                ),
                "count_age_candidate_samples": sum(
                    row["count_and_comparable_age_candidate_samples"] for row in rows
                ),
            }
    return {
        "schema_version": "neotoma-nordic-entity-decisions.v1",
        "source_family": "neotoma",
        "entity_type": "dataset",
        "scope": "Captured Neotoma/EPD datasets; inclusion applies only to the retained 16-label direct observed-pollen study. Candidate ages/counts do not establish LRA admission or measured vegetation truth.",
        "inputs": inputs,
        "dataset_count": len(decisions),
        "sample_count": sum(row["sample_count"] for row in decisions),
        "direct_pollen_included_datasets": sum(
            row["direct_pollen_study_disposition"] == "included" for row in decisions
        ),
        "direct_pollen_excluded_datasets": sum(
            row["direct_pollen_study_disposition"] == "excluded_from_selected_study"
            for row in decisions
        ),
        "country_denominators": by_country,
        "decisions": decisions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build(args.repository), indent=2) + "\n")


if __name__ == "__main__":
    main()
