"""Prepare a metadata-selected Swedish lake cohort for fixed pollen transfer."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
from hashlib import sha256
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
from .swedish_neotoma_holdout import RELATIONAL, _rows


PROTOCOL = Path("docs/report/regions/nordic/swedish-lake-transfer/protocol.json")


def _selected_claims(ages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in ages:
        if not (
            row["subject_type"] == "sample"
            and row["country_code"] == "SE"
            and row["source_age_type"] == "Calibrated radiocarbon years BP"
            and row["is_default_chronology"]
            and row["comparability_status"] == "comparable"
            and row["calibration_status"] == "calibrated"
        ):
            continue
        sample_id = row["subject_id"]
        age = row["source_age_value"]
        if not isinstance(age, (float, int)) or not math.isfinite(age) or age < 0:
            raise ValueError(
                f"Selected source age is not finite nonnegative BP: {sample_id}"
            )
        if sample_id in selected:
            raise ValueError(f"Multiple source-default calibrated ages: {sample_id}")
        selected[sample_id] = row
    return selected


def prepare(repository: Path, author_source_root: Path, output: Path) -> None:
    """Pin source membership and seal outcomes apart from prediction inputs."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    protocol_path = repository / PROTOCOL
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if (
        protocol["schema_version"] != "swedish-lake-pollen-transfer-protocol.v1"
        or protocol["decision_stage"] != "fixed_before_target_observation_read"
        or tuple(BASELINE_METHODS) != tuple(protocol["fixed_methods"])
        or AGE_WIDTH != protocol["response"]["age_bin_width_bp"]
    ):
        raise ValueError("Locked lake transfer design changed")
    manifest_path = repository / RELATIONAL / "manifest.json"
    source = protocol["source_identity"]
    if _sha(manifest_path) != source["relational_manifest_sha256"]:
        raise ValueError("Neotoma relational manifest differs from locked protocol")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest["source_snapshot_id"] != source["source_snapshot_id"]
        or manifest["build_id"] != source["relational_build_id"]
    ):
        raise ValueError("Neotoma source identity changed")

    sites, site_digests = _rows(repository, manifest, "sites")
    units, unit_digests = _rows(repository, manifest, "collection_units")
    datasets, dataset_digests = _rows(repository, manifest, "datasets")
    samples, sample_digests = _rows(repository, manifest, "samples")
    ages, age_digests = _rows(repository, manifest, "age_claims")
    sites_by_id = {row["site_id"]: row for row in sites}
    units_by_id = {row["collection_unit_id"]: row for row in units}
    datasets_by_id = {row["dataset_id"]: row for row in datasets}
    samples_by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in samples:
        if row["country_code"] == "SE":
            samples_by_site[row["site_id"]].append(row)
    claims = _selected_claims(ages)
    claims_by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sample_id, claim in claims.items():
        claims_by_site[claim["site_id"]].append(claim)
    excluded = set(protocol["previous_swedish_target_site_ids"])
    eligible = {
        site_id
        for site_id, sample_rows in samples_by_site.items()
        if site_id not in excluded
        and len({row["dataset_id"] for row in sample_rows}) == 1
        and len({row["collection_unit_id"] for row in sample_rows}) == 1
        and (sites_by_id[site_id]["source_payload"].get("sitedescription") or "")
        .lower()
        .startswith(("lake", "small lake"))
        and len(claims_by_site[site_id]) >= 50
        and datasets_by_id[sample_rows[0]["dataset_id"]]["source_payload"].get(
            "datasettype"
        )
        == "pollen"
        and datasets_by_id[sample_rows[0]["dataset_id"]]["source_payload"].get(
            "database"
        )
        == "European Pollen Database"
    }
    if eligible != {row["site_id"] for row in protocol["targets"]}:
        raise ValueError("Metadata-selected Swedish lake cohort changed")

    training_path = repository / protocol["training"]["input_path"]
    if _sha(training_path) != protocol["training"]["input_sha256"]:
        raise ValueError("Frozen DK/FI/NO training profile changed")
    training = json.loads(gzip.decompress(training_path.read_bytes()))
    if (
        len(training) != protocol["training"]["site_groups"]
        or {row["country"] for row in training.values()}
        != set(protocol["training"]["country_codes"])
        or any(row["site_id"] in eligible for row in training.values())
    ):
        raise ValueError("Training site exclusion or country profile changed")
    mapping, lookup_rows = _lookup(author_source_root.resolve() / LOOKUP)
    axis = tuple(sorted(set(mapping.values()) - {"zz.do not use", "aage.cal.BP"}))
    if len(axis) != 31:
        raise ValueError("Author target axis changed")

    metadata_sites: list[dict[str, Any]] = []
    selected_sample_bins: dict[str, tuple[str, str]] = {}
    outcomes: dict[str, dict[str, dict[str, Any]]] = {}
    for target in protocol["targets"]:
        site_id = target["site_id"]
        site = sites_by_id[site_id]
        selected = claims_by_site[site_id]
        selected_ids = sorted(claim["subject_id"] for claim in selected)
        digest = sha256(("\n".join(selected_ids) + "\n").encode()).hexdigest()
        sample_rows = samples_by_site[site_id]
        if (
            site["source_payload"]["sitename"] != target["site_name"]
            or len(sample_rows) != target["source_samples"]
            or len(selected) != target["selected_samples"]
            or len(set(selected_ids)) != len(selected_ids)
            or digest != target["selected_sample_ids_sha256_newline_utf8"]
            or {row["dataset_id"] for row in sample_rows} != {target["dataset_id"]}
            or {row["collection_unit_id"] for row in sample_rows}
            != {target["collection_unit_id"]}
            or units_by_id[target["collection_unit_id"]]["source_payload"]["handle"]
            != target["source_handle"]
            or min(claim["source_age_value"] for claim in selected)
            != target["selected_age_min_bp"]
            or max(claim["source_age_value"] for claim in selected)
            != target["selected_age_max_bp"]
        ):
            raise ValueError(
                f"Locked Swedish lake source identities changed: {site_id}"
            )
        bins: dict[str, list[str]] = defaultdict(list)
        for claim in selected:
            sample_id = claim["subject_id"]
            bin_id = str(math.floor(claim["source_age_value"] / AGE_WIDTH))
            bins[bin_id].append(sample_id)
            if sample_id in selected_sample_bins:
                raise ValueError("Swedish sample belongs to multiple site bins")
            selected_sample_bins[sample_id] = (site_id, bin_id)
        metadata_sites.append(
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
        )
        outcomes[f"SE:{site_id}"] = {
            bin_id: {"sample_count": len(ids), "native_counts": Counter()}
            for bin_id, ids in bins.items()
        }

    output.mkdir(parents=True, exist_ok=False)
    training_copy = output / "inputs/training-SE.json.gz"
    training_copy.parent.mkdir(parents=True)
    training_copy.write_bytes(training_path.read_bytes())
    metadata_path = output / "inputs/metadata-SE.json.gz"
    _compressed_write(metadata_path, {"country": "SE", "sites": metadata_sites})
    observation_digests: dict[str, str] = {}
    seen_observations: set[str] = set()
    samples_with_counts: set[str] = set()
    for part in manifest["surfaces"]["observations"]["parts"]:
        relative = RELATIONAL / part["path"]
        path = repository / relative
        digest = _sha(path)
        if digest != part["sha256"]:
            raise ValueError(f"Neotoma observation part changed: {relative}")
        observation_digests[relative.as_posix()] = digest
        for row in _read_rows(path):
            owner = selected_sample_bins.get(row["sample_id"])
            if owner is None or not _is_direct_pollen_count(row):
                continue
            site_id, bin_id = owner
            if row["site_id"] != site_id or row["observation_id"] in seen_observations:
                raise ValueError("Selected Swedish observation identity changed")
            seen_observations.add(row["observation_id"])
            samples_with_counts.add(row["sample_id"])
            outcomes[f"SE:{site_id}"][bin_id]["native_counts"][
                row["source_reported_name"]
            ] += row["source_value"]
    if samples_with_counts != set(selected_sample_bins):
        raise ValueError("Selected lake sample lacks source pollen NISP")
    for site_outcomes in outcomes.values():
        for bin_id, cell in site_outcomes.items():
            native = cell.pop("native_counts")
            target_counts, mass = _native_to_target(native, mapping, axis)
            if sum(native.values()) <= 0:
                raise ValueError(f"No native pollen NISP in selected bin {bin_id}")
            cell.update(
                {
                    "counts": target_counts,
                    "closed_nisp": mass["author_assigned_nisp"],
                    "all_pollen_nisp": sum(native.values()),
                    "author_excluded_nisp": mass["author_excluded_nisp"],
                    "unmapped_nisp": mass["unmapped_nisp"],
                }
            )
    outcome_path = output / "sealed-outcomes/outcomes-SE.json.gz"
    _compressed_write(outcome_path, outcomes)
    produced = {
        path.relative_to(output).as_posix(): _sha(path)
        for path in (training_copy, metadata_path, outcome_path)
    }
    _json_write(
        output / "input-manifest.json",
        {
            "schema_version": "swedish-lake-pollen-transfer-inputs.v1",
            "axis": axis,
            "protocol_sha256": _sha(protocol_path),
            "source_manifest_sha256": _sha(manifest_path),
            "source_surface_sha256": dict(
                sorted(
                    {
                        **site_digests,
                        **unit_digests,
                        **dataset_digests,
                        **sample_digests,
                        **age_digests,
                        **observation_digests,
                    }.items()
                )
            ),
            "author_lookup_sha256": LOOKUP_SHA256,
            "author_lookup_rows": lookup_rows,
            "selected_sites": len(metadata_sites),
            "selected_samples": len(selected_sample_bins),
            "excluded_source_samples": sum(
                target["source_samples"] - target["selected_samples"]
                for target in protocol["targets"]
            ),
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
