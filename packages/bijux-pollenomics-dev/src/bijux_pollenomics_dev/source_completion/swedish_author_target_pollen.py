"""Hold out Swedish lakes on the retained Nordic 31-target pollen response."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from .nordic_author_target_pollen import (
    _compressed_read,
    _compressed_write,
    _sha,
    predict,
    score,
)
from .nordic_direct_pollen import _json_write, _swedish_training


NORDIC = Path("docs/report/regions/nordic/author-target-pollen")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
SWEDISH_CONFIG = Path(
    "docs/report/pollen-reconstruction/swedish-direct-pollen/config.json"
)
SWEDISH_MASS = Path(
    "docs/report/source-relations/neotoma/author-taxonomy-mass/report.json"
)


def prepare(repository: Path, output: Path) -> None:
    repository = repository.resolve()
    retained = repository / NORDIC
    original_path = retained / "input-manifest.json"
    original = json.loads(original_path.read_text(encoding="utf-8"))
    axis = original["axis"]
    if len(axis) != 31:
        raise ValueError("retained author target axis changed")
    all_profiles: dict[str, dict[str, Any]] = {}
    swedish_views: list[dict[str, dict[str, Any]]] = []
    input_hashes: dict[str, str] = {}
    for country in ("DK", "FI", "NO"):
        path = retained / "inputs" / f"training-{country}.json.gz"
        relative = str(path.relative_to(retained))
        digest = _sha(path)
        if digest != original["produced_file_sha256"][relative]:
            raise ValueError("retained Nordic training input changed")
        input_hashes[relative] = digest
        profiles = _compressed_read(path)
        swedish_views.append(
            {key: value for key, value in profiles.items() if value["country"] == "SE"}
        )
        for key, profile in profiles.items():
            if profile["country"] == "SE":
                continue
            if key in all_profiles and all_profiles[key] != profile:
                raise ValueError(
                    "Nordic training profile differs across retained folds"
                )
            all_profiles[key] = profile
    swedish = swedish_views[0]
    if any(view != swedish for view in swedish_views[1:]) or len(swedish) != 3:
        raise ValueError("Swedish target profiles differ across retained folds")
    if Counter(value["country"] for value in all_profiles.values()) != {
        "DK": 1,
        "FI": 28,
        "NO": 52,
    }:
        raise ValueError("Nordic country training site denominator changed")

    source, source_hashes = _swedish_training(repository / RAW)
    if source_hashes != original["swedish_source_sha256"]:
        raise ValueError("Swedish original source bytes changed")
    sites: list[dict[str, Any]] = []
    outcomes: dict[str, dict[str, Any]] = {}
    for key, target in sorted(swedish.items()):
        dataset_id = target["dataset_id"]
        native = source[dataset_id]
        if target["site_id"] != native["site_id"] or set(target["bins"]) != set(
            native["bins"]
        ):
            raise ValueError("Swedish target source identity or bin support changed")
        sample_ids = [
            sample_id
            for cell in native["bins"].values()
            for sample_id in cell["sample_ids"]
        ]
        if (
            len(sample_ids) != len(set(sample_ids))
            or len(sample_ids) != target["sample_count"]
        ):
            raise ValueError("Swedish native sample denominator changed")
        for bin_id, cell in target["bins"].items():
            if (
                cell["all_pollen_nisp"] != native["bins"][bin_id]["all_pollen_nisp"]
                or cell["closed_nisp"]
                + cell["author_excluded_nisp"]
                + cell["unmapped_nisp"]
                != cell["all_pollen_nisp"]
                or set(cell["counts"]) != set(axis)
            ):
                raise ValueError("Swedish author target native count closure changed")
        sites.append(
            {
                "country": "SE",
                "site_id": target["site_id"],
                "site_name": target["site_name"],
                "group_id": target["group_id"],
                "coordinate": target["coordinate"],
                "candidate_bin_ids": sorted(target["bins"], key=int),
                "candidate_sample_ids": sorted(sample_ids),
            }
        )
        outcomes[key] = target["bins"]
    if sum(len(site["candidate_sample_ids"]) for site in sites) != 228:
        raise ValueError("Swedish source sample count changed")
    common_bins = set(
        json.loads((repository / SWEDISH_CONFIG).read_text(encoding="utf-8"))[
            "common_age_bin_ids"
        ]
    )
    common_cells = [
        cell
        for bins in outcomes.values()
        for bin_id, cell in bins.items()
        if int(bin_id) in common_bins
    ]
    mass_path = repository / SWEDISH_MASS
    mass = json.loads(mass_path.read_text(encoding="utf-8"))
    if (
        len(common_cells) != mass["common_bin_count"]
        or sum(cell["all_pollen_nisp"] for cell in common_cells)
        != sum(site["all_native_nisp"] for site in mass["sites"])
        or sum(cell["closed_nisp"] for cell in common_cells)
        != sum(site["author_assigned_nisp"] for site in mass["sites"])
    ):
        raise ValueError("Swedish common-bin author taxonomy mass changed")

    output.mkdir(parents=True, exist_ok=False)
    prepared_files = {
        "inputs/training-SE.json.gz": all_profiles,
        "inputs/metadata-SE.json.gz": {"country": "SE", "sites": sites},
        "sealed-outcomes/outcomes-SE.json.gz": outcomes,
    }
    produced: dict[str, str] = {}
    for relative, value in prepared_files.items():
        path = output / relative
        _compressed_write(path, value)
        produced[relative] = _sha(path)
    _json_write(
        output / "input-manifest.json",
        {
            "schema_version": "swedish-author-target-pollen-inputs.v1",
            "axis": axis,
            "parent_input_manifest_sha256": _sha(original_path),
            "parent_training_sha256": input_hashes,
            "swedish_source_sha256": source_hashes,
            "swedish_common_bin_mass_sha256": _sha(mass_path),
            "swedish_common_bin_config_sha256": _sha(repository / SWEDISH_CONFIG),
            "produced_file_sha256": produced,
            "target_outcomes_in_prediction_inputs": False,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "predict", "score"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "prepare":
        if args.repository is None:
            parser.error("prepare requires --repository")
        prepare(args.repository, args.output)
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
