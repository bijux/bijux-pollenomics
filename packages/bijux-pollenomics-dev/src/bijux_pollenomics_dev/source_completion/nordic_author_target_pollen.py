"""Predict held-out Nordic pollen on the authors' 31-target count axis."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.lra_validation.baselines import (
    predict_spatial_baseline,
)
from bijux_pollenomics.analysis.lra_validation.contracts import Fold
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km

from .landclim_taxonomy_mass import EXCLUDED_TARGETS, LOOKUP, _lookup
from .nordic_direct_pollen import (
    AGE_WIDTH,
    BASELINE_METHODS,
    COUNTRIES,
    RELATIONAL_BUILD,
    SOURCE_SNAPSHOT,
    _coordinate,
    _is_direct_pollen_count,
    _json_write,
    _neotoma_candidates,
    _read_rows,
    _sha,
    _swedish_training,
)

RELATIONAL = Path("data/neotoma/relational")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
SWEDISH = Path("docs/report/pollen-reconstruction/swedish-direct-pollen")
NORDIC = Path("docs/report/regions/nordic/direct-pollen")
AUTHOR_MASS = Path("docs/report/regions/nordic/author-taxonomy-mass/report.json")


def _native_to_target(
    native: Counter[str], mapping: dict[str, str], axis: tuple[str, ...]
) -> tuple[dict[str, int], Counter[str]]:
    target = dict.fromkeys(axis, 0)
    mass: Counter[str] = Counter()
    for name, count in native.items():
        if count < 0:
            raise ValueError("negative source pollen count")
        label = mapping.get(name)
        if label is None:
            mass["unmapped_nisp"] += count
        elif label in EXCLUDED_TARGETS:
            mass["author_excluded_nisp"] += count
        else:
            target[label] += count
            mass["author_assigned_nisp"] += count
    if sum(target.values()) != mass["author_assigned_nisp"] or sum(
        mass.values()
    ) != sum(native.values()):
        raise ValueError("author pollen target denominator does not close")
    return target, mass


def _compressed_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    path.write_bytes(gzip.compress(payload, mtime=0))


def _compressed_read(path: Path) -> Any:
    return json.loads(gzip.decompress(path.read_bytes()))


def _swedish_profiles(
    repository: Path,
    source_profiles: dict[str, dict[str, Any]],
    mapping: dict[str, str],
    axis: tuple[str, ...],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    exclusions_path = repository / SWEDISH / "exclusions.csv"
    excluded: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    with exclusions_path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            excluded[(row["dataset_id"], row["age_bin_index"])][
                row["taxon_native"]
            ] += int(row["excluded_nisp_count"])
    hashes = {str(SWEDISH / "exclusions.csv"): _sha(exclusions_path)}
    result: dict[str, dict[str, Any]] = {}
    for dataset_id, source in sorted(source_profiles.items()):
        relative = SWEDISH / "prepared" / f"dataset-{dataset_id}.json"
        path = repository / relative
        hashes[str(relative)] = _sha(path)
        prepared = json.loads(path.read_text(encoding="utf-8"))
        if str(prepared["dataset_id"]) != dataset_id or set(prepared["bins"]) != set(
            source["bins"]
        ):
            raise ValueError("Swedish prepared source bins changed")
        profile = {**source, "bins": {}}
        for bin_id, source_bin in source["bins"].items():
            prepared_bin = prepared["bins"][bin_id]
            native = Counter(prepared_bin["counts"])
            native.update(excluded[(dataset_id, bin_id)])
            if (
                sum(native.values()) != source_bin["all_pollen_nisp"]
                or sum(native.values()) != prepared_bin["all_nisp_count"]
                or len(set(source_bin["sample_ids"])) != prepared_bin["sample_count"]
            ):
                raise ValueError("Swedish native and prepared bin denominators differ")
            counts, mass = _native_to_target(native, mapping, axis)
            profile["bins"][bin_id] = {
                "counts": counts,
                "closed_nisp": mass["author_assigned_nisp"],
                "all_pollen_nisp": sum(native.values()),
                "sample_count": prepared_bin["sample_count"],
                "author_excluded_nisp": mass["author_excluded_nisp"],
                "unmapped_nisp": mass["unmapped_nisp"],
            }
        result[f"SE:{source['site_id']}"] = profile
    if len(result) != 3:
        raise ValueError("Swedish author-target training site count changed")
    return result, hashes


def _nordic_profiles(
    repository: Path,
    source_profiles: dict[str, dict[str, Any]],
    metadata: dict[str, dict[str, Any]],
    mapping: dict[str, str],
    axis: tuple[str, ...],
    expected_mass: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    selected: dict[str, tuple[str, str, str]] = {}
    result: dict[str, dict[str, Any]] = {}
    for country in COUNTRIES:
        for site in metadata[country]["sites"]:
            key = f"{country}:{site['site_id']}"
            source = source_profiles[key]
            profile = {**source, "bins": {}}
            for bin_id, source_bin in source["bins"].items():
                profile["bins"][bin_id] = {
                    "counts": dict.fromkeys(axis, 0),
                    "closed_nisp": 0,
                    "all_pollen_nisp": 0,
                    "sample_ids": set(),
                    "author_excluded_nisp": 0,
                    "unmapped_nisp": 0,
                }
                for sample_id in set(source_bin["sample_ids"]):
                    owner = (country, site["site_id"], bin_id)
                    if sample_id in selected and selected[sample_id] != owner:
                        raise ValueError(
                            "Nordic sample belongs to multiple source bins"
                        )
                    selected[sample_id] = owner
            if {
                sample_id
                for sample_id, owner in selected.items()
                if owner[:2] == (country, site["site_id"])
            } != set(site["candidate_sample_ids"]):
                raise ValueError("Nordic selected samples differ from source bins")
            result[key] = profile
    hashes: dict[str, str] = {}
    manifest = json.loads((repository / RELATIONAL / "manifest.json").read_text())
    for part in manifest["surfaces"]["observations"]["parts"]:
        relative = RELATIONAL / part["path"]
        path = repository / relative
        digest = _sha(path)
        if digest != part["sha256"]:
            raise ValueError("Nordic source observation part changed")
        hashes[str(relative)] = digest
        rows = _read_rows(path)
        if len(rows) != part["row_count"]:
            raise ValueError("Nordic source observation count changed")
        for row in rows:
            selected_owner = selected.get(row["sample_id"])
            if selected_owner is None or not _is_direct_pollen_count(row):
                continue
            country, site_id, bin_id = selected_owner
            cell = result[f"{country}:{site_id}"]["bins"][bin_id]
            count = row["source_value"]
            cell["all_pollen_nisp"] += count
            cell["sample_ids"].add(row["sample_id"])
            label = mapping.get(row["source_reported_name"])
            if label is None:
                cell["unmapped_nisp"] += count
            elif label in EXCLUDED_TARGETS:
                cell["author_excluded_nisp"] += count
            else:
                cell["counts"][label] += count
                cell["closed_nisp"] += count
    for key, profile in result.items():
        country, site_id = key.split(":", 1)
        source = source_profiles[key]
        site_mass: Counter[str] = Counter()
        for bin_id, cell in profile["bins"].items():
            source_bin = source["bins"][bin_id]
            if (
                cell["all_pollen_nisp"] != source_bin["all_pollen_nisp"]
                or cell["closed_nisp"] != sum(cell["counts"].values())
                or cell["closed_nisp"]
                + cell["author_excluded_nisp"]
                + cell["unmapped_nisp"]
                != cell["all_pollen_nisp"]
            ):
                raise ValueError("Nordic author-target bin mass does not close")
            site_mass.update(
                {
                    "all_native_nisp": cell["all_pollen_nisp"],
                    "author_assigned_nisp": cell["closed_nisp"],
                    "author_excluded_nisp": cell["author_excluded_nisp"],
                    "unmapped_nisp": cell["unmapped_nisp"],
                }
            )
            cell["sample_count"] = len(cell.pop("sample_ids"))
        expected = expected_mass[(country, site_id)]
        for field in site_mass:
            if site_mass[field] != expected[field]:
                raise ValueError(f"Nordic author taxonomy mass changed: {key} {field}")
    return result, hashes


def prepare(repository: Path, author_source_root: Path, output: Path) -> None:
    repository = repository.resolve()
    mapping, lookup_rows = _lookup(author_source_root.resolve() / LOOKUP)
    axis = tuple(sorted(set(mapping.values()) - EXCLUDED_TARGETS))
    if len(axis) != 31:
        raise ValueError("author target axis changed")
    direct_path = repository / NORDIC / "manifest.json"
    direct = json.loads(direct_path.read_text(encoding="utf-8"))
    swedish_source, raw_hashes = _swedish_training(repository / RAW)
    nordic_source, metadata, hashes, screen_hash, denominators = _neotoma_candidates(
        repository / RELATIONAL, repository / RAW
    )
    identity = direct["input_identity"]
    if (
        hashes != identity["relational_file_sha256"]
        or raw_hashes != identity["swedish_raw_file_sha256"]
        or screen_hash != identity["pollen_screen_sha256"]
        or denominators != identity["source_screen_country_denominators"]
    ):
        raise ValueError(
            "Nordic source identity differs from frozen direct-pollen cohort"
        )
    mass_path = repository / AUTHOR_MASS
    mass_report = json.loads(mass_path.read_text(encoding="utf-8"))
    expected_mass = {
        (row["country"], row["site_id"]): row for row in mass_report["sites"]
    }
    swedish, swedish_hashes = _swedish_profiles(
        repository, swedish_source, mapping, axis
    )
    nordic, observation_hashes = _nordic_profiles(
        repository, nordic_source, metadata, mapping, axis, expected_mass
    )
    all_profiles = {**swedish, **nordic}
    output.mkdir(parents=True, exist_ok=False)
    input_dir = output / "inputs"
    input_dir.mkdir()
    outcome_dir = output / "sealed-outcomes"
    outcome_dir.mkdir()
    produced: dict[str, str] = {}
    for country in COUNTRIES:
        training = {
            key: profile
            for key, profile in all_profiles.items()
            if profile["country"] != country
        }
        outcomes = {
            key: profile["bins"]
            for key, profile in nordic.items()
            if profile["country"] == country
        }
        training_path = input_dir / f"training-{country}.json.gz"
        metadata_path = input_dir / f"metadata-{country}.json.gz"
        outcome_path = outcome_dir / f"outcomes-{country}.json.gz"
        _compressed_write(training_path, training)
        _compressed_write(metadata_path, metadata[country])
        _compressed_write(outcome_path, outcomes)
        for path in (training_path, metadata_path, outcome_path):
            produced[str(path.relative_to(output))] = _sha(path)
    receipt = {
        "schema_version": "nordic-author-target-pollen-inputs.v1",
        "axis": axis,
        "lookup_rows": lookup_rows,
        "age_bin_width_bp": AGE_WIDTH,
        "source_snapshot_id": SOURCE_SNAPSHOT,
        "relational_build_id": RELATIONAL_BUILD,
        "direct_manifest_sha256": _sha(direct_path),
        "author_mass_report_sha256": _sha(mass_path),
        "author_lookup_sha256": _sha(author_source_root.resolve() / LOOKUP),
        "swedish_source_sha256": raw_hashes,
        "swedish_prepared_sha256": swedish_hashes,
        "neotoma_relational_sha256": hashes,
        "observation_part_sha256": observation_hashes,
        "produced_file_sha256": produced,
        "target_outcomes_in_prediction_inputs": False,
    }
    _json_write(output / "input-manifest.json", receipt)


def predict(
    prepared: Path, output: Path, countries: tuple[str, ...] = COUNTRIES
) -> None:
    manifest = json.loads((prepared / "input-manifest.json").read_text())
    axis = manifest["axis"]
    output.mkdir(parents=True, exist_ok=False)
    for country in countries:
        training_path = prepared / "inputs" / f"training-{country}.json.gz"
        metadata_path = prepared / "inputs" / f"metadata-{country}.json.gz"
        for path in (training_path, metadata_path):
            if (
                _sha(path)
                != manifest["produced_file_sha256"][str(path.relative_to(prepared))]
            ):
                raise ValueError("prediction input changed after preparation")
        training = _compressed_read(training_path)
        metadata = _compressed_read(metadata_path)
        predictions: list[dict[str, Any]] = []
        refusals: list[dict[str, Any]] = []
        for site in metadata["sites"]:
            site_id = site["site_id"]
            target = _coordinate(site["coordinate"])
            for bin_id in site["candidate_bin_ids"]:
                chosen = {
                    key: profile
                    for key, profile in training.items()
                    if bin_id in profile["bins"]
                    and profile["bins"][bin_id]["closed_nisp"] > 0
                }
                groups = {profile["group_id"] for profile in chosen.values()}
                if len(groups) < 2:
                    refusals.append(
                        {
                            "site_id": site_id,
                            "bin_id": int(bin_id),
                            "reason": "fewer_than_two_training_site_groups_with_positive_closed_counts",
                        }
                    )
                    continue
                ordered = [profile for _, profile in sorted(chosen.items())]
                record_ids = tuple(profile["record_id"] for profile in ordered)
                group_ids = tuple(profile["group_id"] for profile in ordered)
                fold = Fold(
                    f"author-target:{country}:{site_id}:{bin_id}",
                    record_ids,
                    (f"neotoma-site:{site_id}:bin:{bin_id}",),
                    group_ids,
                    (site["group_id"],),
                )
                compositions = {
                    profile["group_id"]: {
                        taxon: count / profile["bins"][bin_id]["closed_nisp"]
                        for taxon, count in profile["bins"][bin_id]["counts"].items()
                    }
                    for profile in ordered
                }
                distances = {
                    profile["group_id"]: distance_km(
                        _coordinate(profile["coordinate"]), target
                    )
                    for profile in ordered
                }
                if any(not math.isfinite(value) for value in distances.values()):
                    raise ValueError("nonfinite Nordic training-site distance")
                for method in BASELINE_METHODS:
                    estimated = predict_spatial_baseline(
                        fold,
                        compositions,
                        method=method,
                        input_ids=record_ids,
                        dependency_graph=dict.fromkeys(record_ids, ()),
                        distances_km=distances if method != "training_mean" else None,
                        predictor_group_ids=group_ids,
                    )
                    fractions = dict(estimated.fractions)
                    if set(fractions) != set(axis):
                        raise ValueError("author target prediction axis changed")
                    predictions.append(
                        {
                            "country": country,
                            "site_id": site_id,
                            "bin_id": int(bin_id),
                            "method": method,
                            "fractions": fractions,
                            "training_site_ids": sorted(
                                profile["site_id"] for profile in ordered
                            ),
                            "target_pollen_counts_read": False,
                        }
                    )
        _compressed_write(
            output / f"predictions-{country}.json.gz",
            {
                "schema_version": "nordic-author-target-pollen-predictions.v1",
                "country": country,
                "axis": axis,
                "predictions": predictions,
                "refusals": refusals,
            },
        )


def score(
    prepared: Path,
    predictions: Path,
    output: Path,
    countries: tuple[str, ...] = COUNTRIES,
) -> None:
    manifest_path = prepared / "input-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    axis = manifest["axis"]
    scored: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    country_denominators: dict[str, dict[str, int]] = {}
    taxon_errors: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    prediction_hashes: dict[str, str] = {}
    for country in countries:
        path = predictions / f"predictions-{country}.json.gz"
        payload = _compressed_read(path)
        if payload["country"] != country or payload["axis"] != axis:
            raise ValueError("country prediction identity changed")
        prediction_hashes[country] = _sha(path)
        outcome_path = prepared / "sealed-outcomes" / f"outcomes-{country}.json.gz"
        if (
            _sha(outcome_path)
            != manifest["produced_file_sha256"][str(outcome_path.relative_to(prepared))]
        ):
            raise ValueError("sealed target outcomes changed")
        outcomes = _compressed_read(outcome_path)
        metadata = _compressed_read(prepared / "inputs" / f"metadata-{country}.json.gz")
        if (
            _sha(prepared / "inputs" / f"metadata-{country}.json.gz")
            != manifest["produced_file_sha256"][f"inputs/metadata-{country}.json.gz"]
        ):
            raise ValueError("target metadata changed")
        cells = [cell for bins in outcomes.values() for cell in bins.values()]
        country_denominators[country] = {
            "sites": len(metadata["sites"]),
            "selected_samples": sum(
                len(site["candidate_sample_ids"]) for site in metadata["sites"]
            ),
            "native_nisp": sum(cell["all_pollen_nisp"] for cell in cells),
            "assigned_nisp": sum(cell["closed_nisp"] for cell in cells),
            "author_excluded_nisp": sum(cell["author_excluded_nisp"] for cell in cells),
            "unmapped_nisp": sum(cell["unmapped_nisp"] for cell in cells),
        }
        totals = country_denominators[country]
        if (
            totals["assigned_nisp"]
            + totals["author_excluded_nisp"]
            + totals["unmapped_nisp"]
            != totals["native_nisp"]
        ):
            raise ValueError("target country native NISP denominator does not close")
        candidates = {
            (site["site_id"], int(bin_id))
            for site in metadata["sites"]
            for bin_id in site["candidate_bin_ids"]
        }
        predicted = {(row["site_id"], row["bin_id"]) for row in payload["predictions"]}
        refused = {(row["site_id"], row["bin_id"]) for row in payload["refusals"]}
        if predicted & refused or predicted | refused != candidates:
            raise ValueError("country target prediction denominator does not close")
        methods_by_bin: dict[tuple[str, int], set[str]] = defaultdict(set)
        for row in payload["predictions"]:
            bin_key = (row["site_id"], row["bin_id"])
            if row["method"] in methods_by_bin[bin_key]:
                raise ValueError("duplicate method prediction on a target bin")
            methods_by_bin[bin_key].add(row["method"])
            target = outcomes[f"{country}:{row['site_id']}"][str(row["bin_id"])]
            if target["closed_nisp"] <= 0:
                continue
            estimate = row["fractions"]
            if set(estimate) != set(axis) or set(target["counts"]) != set(axis):
                raise ValueError("author target score axis changed")
            result = score_pollen(estimate, target["counts"])
            observed = {
                name: count / target["closed_nisp"]
                for name, count in target["counts"].items()
            }
            for taxon in axis:
                taxon_errors[(country, row["site_id"], row["method"], taxon)].append(
                    abs(estimate[taxon] - observed[taxon])
                )
            scored.append(
                {
                    "country": country,
                    "site_id": row["site_id"],
                    "bin_id": row["bin_id"],
                    "method": row["method"],
                    "status": result.status,
                    "mae_fraction": result.mae_fraction,
                    "hellinger_distance": hellinger_distance(estimate, observed),
                    "target_sample_count": target["sample_count"],
                    "target_assigned_nisp": target["closed_nisp"],
                    "target_native_nisp": target["all_pollen_nisp"],
                    "prediction_sha256": prediction_hashes[country],
                }
            )
        if set(methods_by_bin) != predicted or any(
            methods != set(BASELINE_METHODS) for methods in methods_by_bin.values()
        ):
            raise ValueError("baseline method coverage differs by target bin")
        coverage.append(
            {
                "country": country,
                "candidate_site_bins": len(candidates),
                "predicted_site_bins": len(predicted),
                "refused_training_support_site_bins": len(refused),
                "positive_target_and_predicted_site_bins": len(
                    {
                        (row["site_id"], row["bin_id"])
                        for row in scored
                        if row["country"] == country
                    }
                ),
            }
        )
    if not scored:
        raise ValueError("no source-owned target pollen bins were scored")
    output.mkdir(parents=True, exist_ok=False)
    score_path = output / "scores.csv"
    with score_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(scored[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(scored)
    coverage_path = output / "coverage.csv"
    with coverage_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(coverage[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(coverage)
    site_method: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        site_method[(row["country"], row["site_id"], row["method"])].append(row)
    site_rows = [
        {
            "country": country,
            "site_id": site_id,
            "method": method,
            "scored_bins": len(rows),
            "site_mae_fraction": mean(row["mae_fraction"] for row in rows),
            "site_hellinger_distance": mean(row["hellinger_distance"] for row in rows),
        }
        for (country, site_id, method), rows in sorted(site_method.items())
    ]
    taxon_rows = [
        {
            "country": country,
            "method": method,
            "taxon": taxon,
            "scored_sites": len(
                [
                    1
                    for (c, _, m, t) in taxon_errors
                    if c == country and m == method and t == taxon
                ]
            ),
            "site_macro_abs_error_fraction": mean(
                mean(values)
                for (c, _, m, t), values in taxon_errors.items()
                if c == country and m == method and t == taxon
            ),
        }
        for country in countries
        for method in BASELINE_METHODS
        for taxon in axis
    ]
    site_path = output / "site-scores.csv"
    with site_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(site_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(site_rows)
    taxon_path = output / "taxon-diagnostics.csv"
    with taxon_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(taxon_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(taxon_rows)
    macro_mae = {
        country: {
            method: mean(
                row["site_mae_fraction"]
                for row in site_rows
                if row["country"] == country and row["method"] == method
            )
            for method in BASELINE_METHODS
        }
        for country in countries
    }
    macro_hellinger = {
        country: {
            method: mean(
                row["site_hellinger_distance"]
                for row in site_rows
                if row["country"] == country and row["method"] == method
            )
            for method in BASELINE_METHODS
        }
        for country in countries
    }
    _json_write(
        output / "report.json",
        {
            "schema_version": "nordic-author-target-pollen-study.v1",
            "axis": axis,
            "methods": BASELINE_METHODS,
            "input_manifest_sha256": _sha(manifest_path),
            "prediction_sha256": prediction_hashes,
            "scores_sha256": _sha(score_path),
            "coverage_sha256": _sha(coverage_path),
            "site_scores_sha256": _sha(site_path),
            "taxon_diagnostics_sha256": _sha(taxon_path),
            "score_rows": len(scored),
            "country_source_denominators": country_denominators,
            "site_score_rows": len(site_rows),
            "taxon_diagnostic_rows": len(taxon_rows),
            "site_macro_mae_fraction": macro_mae,
            "site_macro_hellinger_distance": macro_hellinger,
            "interpretation": "Previously exposed country-held-out observed-pollen subcomposition on 31 author lookup targets; not LRA, measured vegetation validation or independent confirmation.",
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
            parser.error("prepare requires repository and author source root")
        prepare(args.repository, args.author_source_root, args.output)
    elif args.stage == "predict":
        if args.prepared is None:
            parser.error("predict requires prepared inputs")
        predict(args.prepared, args.output)
    else:
        if args.prepared is None or args.predictions is None:
            parser.error("score requires prepared inputs and frozen predictions")
        score(args.prepared, args.predictions, args.output)


if __name__ == "__main__":
    main()
