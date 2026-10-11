"""Compare parallel EPD datasets from the same Storasjö collection unit."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from .nordic_direct_pollen import _is_direct_pollen_count, _json_write, _read_rows, _sha
from .swedish_neotoma_holdout import PROTOCOL, RELATIONAL, _rows


def review(repository: Path, output: Path) -> dict[str, Any]:
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    protocol = json.loads((repository / PROTOCOL).read_text(encoding="utf-8"))
    target = protocol["target"]
    manifest_path = repository / RELATIONAL / "manifest.json"
    if _sha(manifest_path) != protocol["source_identity"]["relational_manifest_sha256"]:
        raise ValueError("Storasjö source manifest changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    samples, sample_digests = _rows(repository, manifest, "samples")
    selected = {
        row["sample_id"]: row
        for row in samples
        if row["dataset_id"] == target["selected_dataset_id"]
    }
    parallel = {
        row["sample_id"]: row
        for row in samples
        if row["dataset_id"] == target["excluded_parallel_dataset_id"]
    }
    if len(selected) != 77 or len(parallel) != 77:
        raise ValueError("Storasjö parallel dataset sample denominator changed")
    depth_by_sample = {
        row["sample_id"]: row["source_depth"]
        for row in (*selected.values(), *parallel.values())
    }
    if {row["source_depth"] for row in selected.values()} != {
        row["source_depth"] for row in parallel.values()
    } or len(set(depth_by_sample.values())) != 77:
        raise ValueError("Storasjö parallel dataset depths changed")
    counts: dict[tuple[str, float], Counter[str]] = defaultdict(Counter)
    observation_digests: dict[str, str] = {}
    for part in manifest["surfaces"]["observations"]["parts"]:
        relative = RELATIONAL / part["path"]
        path = repository / relative
        digest = _sha(path)
        if digest != part["sha256"]:
            raise ValueError(f"Neotoma observation part changed: {relative}")
        observation_digests[relative.as_posix()] = digest
        for row in _read_rows(path):
            sample_id = row["sample_id"]
            if sample_id in depth_by_sample and _is_direct_pollen_count(row):
                counts[(row["dataset_id"], depth_by_sample[sample_id])][
                    row["source_reported_name"]
                ] += row["source_value"]
    first = target["selected_dataset_id"]
    second = target["excluded_parallel_dataset_id"]
    depths = sorted({row["source_depth"] for row in selected.values()})
    matched = sum(counts[first, depth] == counts[second, depth] for depth in depths)
    mass = {
        dataset: sum(sum(counts[dataset, depth].values()) for depth in depths)
        for dataset in (first, second)
    }
    taxa = {
        dataset: len(set().union(*(counts[dataset, depth] for depth in depths)))
        for dataset in (first, second)
    }
    if matched != 77 or mass[first] <= 0 or mass[first] != mass[second]:
        raise ValueError("Storasjö parallel pollen count vectors differ")
    report = {
        "schema_version": "storasjo-parallel-epd-pollen-review.v1",
        "site_id": target["site_id"],
        "collection_unit_id": target["collection_unit_id"],
        "selected_dataset_id": first,
        "excluded_parallel_dataset_id": second,
        "shared_depth_count": len(depths),
        "exact_matching_pollen_count_vectors": matched,
        "native_pollen_nisp_by_dataset": mass,
        "distinct_source_names_by_dataset": taxa,
        "counting_decision": "use one physical-core pollen count vector per depth",
        "source_manifest_sha256": _sha(manifest_path),
        "source_part_sha256": dict(
            sorted({**sample_digests, **observation_digests}.items())
        ),
    }
    output.mkdir(parents=True, exist_ok=False)
    _json_write(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review(args.repository, args.output)


if __name__ == "__main__":
    main()
