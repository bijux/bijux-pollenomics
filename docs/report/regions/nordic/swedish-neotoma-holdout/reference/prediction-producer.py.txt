"""Prepare one source-selected Swedish core for fixed Nordic pollen transfer."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .landclim_taxonomy_mass import LOOKUP, LOOKUP_SHA256, _lookup
from .nordic_author_target_pollen import (
    _compressed_write,
    _native_to_target,
    predict,
    score,
)
from .nordic_direct_pollen import (
    AGE_WIDTH,
    BASELINE_METHODS,
    _is_direct_pollen_count,
    _json_write,
    _read_rows,
    _sha,
    _site_coordinate,
)

PROTOCOL = Path("docs/report/regions/nordic/swedish-neotoma-holdout/protocol.json")
RELATIONAL = Path("data/neotoma/relational")


def _rows(
    repository: Path, manifest: dict[str, Any], surface: str
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    result: list[dict[str, Any]] = []
    digests: dict[str, str] = {}
    entry = manifest["surfaces"][surface]
    for part in entry["parts"]:
        relative = RELATIONAL / part["path"]
        path = repository / relative
        digest = _sha(path)
        if digest != part["sha256"]:
            raise ValueError(f"Neotoma relational part changed: {relative}")
        rows = _read_rows(path)
        if len(rows) != part["row_count"]:
            raise ValueError(f"Neotoma relational row count changed: {relative}")
        result.extend(rows)
        digests[relative.as_posix()] = digest
    if len(result) != entry["row_count"]:
        raise ValueError(f"Neotoma relational surface changed: {surface}")
    return result, digests


def _claims_for_samples(
    ages: list[dict[str, Any]], samples: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    claims: dict[str, dict[str, Any]] = {}
    for row in ages:
        sample_id = row["subject_id"]
        if sample_id not in samples or row["subject_type"] != "sample":
            continue
        if not (
            row["is_default_chronology"]
            and row["comparability_status"] == "comparable"
            and row["calibration_status"] == "calibrated"
            and row["source_age_type"] == "Calibrated radiocarbon years BP"
        ):
            continue
        age = row["source_age_value"]
        if not isinstance(age, (int, float)) or not math.isfinite(float(age)):
            raise ValueError(f"Selected age is not finite: {sample_id}")
        if sample_id in claims:
            raise ValueError(f"Multiple selected ages: {sample_id}")
        claims[sample_id] = row
    if set(claims) != set(samples):
        raise ValueError(
            "Selected Storasjö samples lack unique default calibrated ages"
        )
    return claims


def prepare(repository: Path, author_source_root: Path, output: Path) -> None:
    """Freeze target metadata and training before reading selected observations."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    protocol_path = repository / PROTOCOL
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["schema_version"] != "swedish-neotoma-pollen-holdout-protocol.v1":
        raise ValueError("Storasjö protocol changed")
    target = protocol["target"]
    source = protocol["source_identity"]
    manifest_path = repository / RELATIONAL / "manifest.json"
    if _sha(manifest_path) != source["relational_manifest_sha256"]:
        raise ValueError("Neotoma source manifest differs from locked protocol")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest["source_snapshot_id"] != source["source_snapshot_id"]
        or manifest["build_id"] != source["relational_build_id"]
    ):
        raise ValueError("Neotoma source identity differs from locked protocol")
    training_path = repository / protocol["training"]["input_path"]
    if _sha(training_path) != protocol["training"]["input_sha256"]:
        raise ValueError("Nordic training profile differs from locked protocol")
    sites, site_digests = _rows(repository, manifest, "sites")
    datasets, dataset_digests = _rows(repository, manifest, "datasets")
    sample_rows, sample_digests = _rows(repository, manifest, "samples")
    ages, age_digests = _rows(repository, manifest, "age_claims")
    site = next((row for row in sites if row["site_id"] == target["site_id"]), None)
    if site is None or site["country_code"] != "SE":
        raise ValueError("Selected Storasjö site is unavailable")
    relevant_datasets = {
        row["dataset_id"]: row
        for row in datasets
        if row["site_id"] == target["site_id"]
    }
    if set(relevant_datasets) != {
        target["selected_dataset_id"],
        target["excluded_parallel_dataset_id"],
    } or any(
        row["collection_unit_id"] != target["collection_unit_id"]
        or row["source_payload"].get("datasettype") != "pollen"
        or row["source_payload"].get("database") != "European Pollen Database"
        for row in relevant_datasets.values()
    ):
        raise ValueError("Storasjö source datasets or physical core changed")
    selected = {
        row["sample_id"]: row
        for row in sample_rows
        if row["dataset_id"] == target["selected_dataset_id"]
    }
    parallel = {
        row["sample_id"]: row
        for row in sample_rows
        if row["dataset_id"] == target["excluded_parallel_dataset_id"]
    }
    selected_ids = sorted(selected)
    digest = hashlib.sha256(("\n".join(selected_ids) + "\n").encode()).hexdigest()
    if (
        len(selected) != target["selected_sample_count"]
        or len(parallel) != target["parallel_dataset_sample_count"]
        or digest != target["selected_sample_ids_sha256_newline_utf8"]
        or any(
            row["site_id"] != target["site_id"]
            for row in (*selected.values(), *parallel.values())
        )
    ):
        raise ValueError("Storasjö sample identities changed")
    selected_claims = _claims_for_samples(ages, selected)
    parallel_claims = _claims_for_samples(ages, parallel)
    selected_by_depth = {
        row["source_depth"]: selected_claims[sample_id]["source_age_value"]
        for sample_id, row in selected.items()
    }
    parallel_by_depth = {
        row["source_depth"]: parallel_claims[sample_id]["source_age_value"]
        for sample_id, row in parallel.items()
    }
    if (
        len(selected_by_depth) != target["shared_depths_with_equal_calibrated_age"]
        or selected_by_depth != parallel_by_depth
        or min(selected_by_depth.values()) != target["source_age_min_bp"]
        or max(selected_by_depth.values()) != target["source_age_max_bp"]
    ):
        raise ValueError("Storasjö parallel dataset depth or age relation changed")
    bins: dict[str, list[str]] = defaultdict(list)
    for sample_id in selected_ids:
        age = selected_claims[sample_id]["source_age_value"]
        bins[str(math.floor(age / AGE_WIDTH))].append(sample_id)
    training = json.loads(gzip.decompress(training_path.read_bytes()))
    if (
        len(training) != protocol["training"]["site_groups"]
        or {row["country"] for row in training.values()}
        != set(protocol["training"]["country_codes"])
        or any(row["site_id"] == target["site_id"] for row in training.values())
        or tuple(BASELINE_METHODS) != tuple(protocol["fixed_methods"])
        or AGE_WIDTH != protocol["response"]["age_bin_width_bp"]
    ):
        raise ValueError("Locked Nordic prediction design changed")
    mapping, lookup_rows = _lookup(author_source_root.resolve() / LOOKUP)
    axis = tuple(sorted(set(mapping.values()) - {"zz.do not use", "aage.cal.BP"}))
    if len(axis) != 31:
        raise ValueError("Author target axis changed")
    site_id = target["site_id"]
    metadata = {
        "country": "SE",
        "sites": [
            {
                "site_id": site_id,
                "site_name": target["site_name"],
                "group_id": site_id,
                "coordinate": _site_coordinate(
                    site["source_payload"]["geography"]
                ).as_dict(),
                "candidate_bin_ids": sorted(bins, key=int),
                "candidate_sample_ids": selected_ids,
            }
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    training_copy = output / "inputs/training-SE.json.gz"
    training_copy.parent.mkdir(parents=True)
    training_copy.write_bytes(training_path.read_bytes())
    metadata_path = output / "inputs/metadata-SE.json.gz"
    _compressed_write(metadata_path, metadata)

    counts: dict[str, Counter[str]] = {bin_id: Counter() for bin_id in bins}
    sample_bin = {
        sample_id: bin_id for bin_id, ids in bins.items() for sample_id in ids
    }
    sample_mass: Counter[str] = Counter()
    observation_digests: dict[str, str] = {}
    seen_observations: set[str] = set()
    for part in manifest["surfaces"]["observations"]["parts"]:
        relative = RELATIONAL / part["path"]
        path = repository / relative
        digest = _sha(path)
        if digest != part["sha256"]:
            raise ValueError(f"Neotoma observation part changed: {relative}")
        observation_digests[relative.as_posix()] = digest
        for row in _read_rows(path):
            sample_id = row["sample_id"]
            if sample_id not in selected or not _is_direct_pollen_count(row):
                continue
            if (
                row["dataset_id"] != target["selected_dataset_id"]
                or row["site_id"] != site_id
                or row["observation_id"] in seen_observations
            ):
                raise ValueError("Selected Storasjö observation identity changed")
            seen_observations.add(row["observation_id"])
            counts[sample_bin[sample_id]][row["source_reported_name"]] += row[
                "source_value"
            ]
            sample_mass[sample_id] += row["source_value"]
    if set(sample_mass) != set(selected) or any(
        value <= 0 for value in sample_mass.values()
    ):
        raise ValueError("Selected Storasjö samples lack positive pollen NISP")
    outcomes: dict[str, dict[str, Any]] = {}
    for bin_id in sorted(bins, key=int):
        target_counts, mass = _native_to_target(counts[bin_id], mapping, axis)
        outcomes[bin_id] = {
            "counts": target_counts,
            "closed_nisp": mass["author_assigned_nisp"],
            "all_pollen_nisp": sum(counts[bin_id].values()),
            "sample_count": len(bins[bin_id]),
            "author_excluded_nisp": mass["author_excluded_nisp"],
            "unmapped_nisp": mass["unmapped_nisp"],
        }
    outcome_path = output / "sealed-outcomes/outcomes-SE.json.gz"
    _compressed_write(outcome_path, {f"SE:{site_id}": outcomes})
    produced = {
        path.relative_to(output).as_posix(): _sha(path)
        for path in (training_copy, metadata_path, outcome_path)
    }
    _json_write(
        output / "input-manifest.json",
        {
            "schema_version": "swedish-neotoma-pollen-holdout-inputs.v1",
            "axis": axis,
            "protocol_sha256": _sha(protocol_path),
            "source_manifest_sha256": _sha(manifest_path),
            "source_surface_sha256": dict(
                sorted(
                    {
                        **site_digests,
                        **dataset_digests,
                        **sample_digests,
                        **age_digests,
                        **observation_digests,
                    }.items()
                )
            ),
            "author_lookup_sha256": LOOKUP_SHA256,
            "author_lookup_rows": lookup_rows,
            "target_sample_count": len(selected),
            "parallel_dataset_excluded_sample_count": len(parallel),
            "target_outcomes_in_prediction_inputs": False,
            "produced_file_sha256": produced,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "predict", "score"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--author-source-root", type=Path)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "prepare":
        if args.repository is None or args.author_source_root is None:
            parser.error("prepare requires --repository and --author-source-root")
        prepare(args.repository, args.author_source_root, args.output)
    elif args.stage == "predict":
        if args.prepared is None:
            parser.error("predict requires --prepared")
        predict(args.prepared, args.output, countries=("SE",))
    else:
        if args.prepared is None or args.predictions is None:
            parser.error("score requires --prepared and --predictions")
        score(args.prepared, args.predictions, args.output, countries=("SE",))


if __name__ == "__main__":
    main()
