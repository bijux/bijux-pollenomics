"""Prepare and run a grouped direct-pollen prediction on three EPD datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Literal

from bijux_pollenomics.analysis.lra_validation.baselines import predict_spatial_baseline
from bijux_pollenomics.analysis.lra_validation.contracts import Fold
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics.analysis.lra_validation.spatial import (
    SiteCoordinate,
    SpatialConfig,
    fit_spatial_model,
    half_count_composition,
)
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km


DATASETS = {
    "19913": {"label": "Abborrtjärnen", "site_id": "13338", "part": "part-004.json"},
    "53995": {"label": "Bussjösjön", "site_id": "28869", "part": "part-008.json"},
    "54001": {"label": "Bökesjön", "site_id": "28872", "part": "part-008.json"},
}
BASELINE_METHODS: tuple[
    Literal["training_mean"],
    Literal["nearest_site"],
    Literal["inverse_distance_squared"],
] = ("training_mean", "nearest_site", "inverse_distance_squared")
METHODS = BASELINE_METHODS + ("clr_rbf_ridge",)
AGE_WIDTH = 500


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _records(data_root: Path) -> dict[str, dict[str, Any]]:
    wanted = set(DATASETS)
    result: dict[str, dict[str, Any]] = {}
    for part in sorted({spec["part"] for spec in DATASETS.values()}):
        payload = json.loads((data_root / part).read_text(encoding="utf-8"))
        for row in payload["rows"]:
            site = row["site"]
            dataset = site.get("dataset", {})
            dataset_id = str(dataset.get("datasetid"))
            if dataset_id not in wanted:
                continue
            if dataset_id in result:
                raise ValueError(f"duplicate Neotoma dataset {dataset_id}")
            result[dataset_id] = {"site": site, "dataset": dataset}
    if set(result) != wanted:
        raise ValueError(f"expected datasets {sorted(wanted)}, got {sorted(result)}")
    return result


def prepare(data_root: Path, workdir: Path, config_path: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    taxa = tuple(config["closed_taxa"])
    if len(taxa) != 16 or len(set(taxa)) != len(taxa):
        raise ValueError(
            "the declared exact-name denominator must contain 16 unique taxa"
        )
    records = _records(data_root)
    inventory_rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    native_taxa_by_dataset: dict[str, set[str]] = {}
    sample_totals: dict[str, int] = defaultdict(int)
    closed_totals: dict[str, int] = defaultdict(int)
    site_profiles: dict[str, dict[str, Any]] = {}
    source_files = sorted({spec["part"] for spec in DATASETS.values()})

    for dataset_id, spec in DATASETS.items():
        record = records[dataset_id]
        site, dataset = record["site"], record["dataset"]
        if (
            dataset.get("datasettype") != "pollen"
            or dataset.get("database") != "European Pollen Database"
        ):
            raise ValueError(f"unexpected source identity for dataset {dataset_id}")
        collection = site["collectionunit"]
        nested = collection["dataset"]
        if str(site["siteid"]) != spec["site_id"]:
            raise ValueError(f"site ID changed for dataset {dataset_id}")
        coordinate_json = json.loads(site["geography"])
        longitude, latitude = coordinate_json["coordinates"]
        bin_counts: dict[str, dict[str, int]] = defaultdict(
            lambda: dict.fromkeys(taxa, 0)
        )
        bin_all: dict[str, int] = defaultdict(int)
        bin_samples: dict[str, int] = defaultdict(int)
        all_taxa: set[str] = set()
        ages: list[float] = []
        chronology: set[tuple[str, str]] = set()
        sample_count = 0
        for sample_index, sample in enumerate(nested["samples"]):
            sample_count += 1
            age_rows = sample.get("ages", [])
            if len(age_rows) != 1:
                raise ValueError(
                    f"dataset {dataset_id} sample {sample_index} has {len(age_rows)} age rows"
                )
            age = age_rows[0]
            if (
                age.get("agetype") != "Calibrated radiocarbon years BP"
                or age.get("age") is None
            ):
                raise ValueError(
                    f"dataset {dataset_id} sample {sample_index} lacks selected calibrated BP age"
                )
            chronology.add((str(age["chronologyid"]), str(age["chronologyname"])))
            ages.append(float(age["age"]))
            if age.get("ageolder") is not None or age.get("ageyounger") is not None:
                raise ValueError(
                    "unexpected sample age bounds; update uncertainty accounting"
                )
            bin_id = str(int(float(age["age"]) // AGE_WIDTH))
            seen: set[str] = set()
            sample_all = 0
            for datum in sample.get("datum", []):
                if datum.get("units") != "NISP" or datum.get("elementtype") != "pollen":
                    continue
                name, value = datum.get("variablename"), datum.get("value")
                if not isinstance(name, str) or type(value) is not int or value < 0:
                    raise ValueError("invalid native NISP pollen datum")
                if name in seen:
                    raise ValueError(f"duplicate taxon datum in one sample: {name}")
                seen.add(name)
                all_taxa.add(name)
                sample_all += value
                if name in taxa:
                    bin_counts[bin_id][name] += value
                else:
                    exclusions.append(
                        {
                            "dataset_id": dataset_id,
                            "site_id": spec["site_id"],
                            "site": spec["label"],
                            "age_bin_index": bin_id,
                            "age_bin_lower_cal_bp": int(bin_id) * AGE_WIDTH,
                            "age_bin_upper_cal_bp_exclusive": (int(bin_id) + 1)
                            * AGE_WIDTH,
                            "taxon_native": name,
                            "excluded_nisp_count": value,
                            "reason": "outside exact-name shared 16-taxon subcomposition",
                        }
                    )
            if sample_all <= 0:
                raise ValueError(
                    f"dataset {dataset_id} sample {sample_index} has no positive pollen NISP"
                )
            bin_all[bin_id] += sample_all
            bin_samples[bin_id] += 1
            sample_totals[dataset_id] += sample_all
            closed_totals[dataset_id] += sum(
                datum["value"]
                for datum in sample.get("datum", [])
                if datum.get("units") == "NISP"
                and datum.get("elementtype") == "pollen"
                and datum.get("variablename") in taxa
            )
        if len(chronology) != 1:
            raise ValueError(f"dataset {dataset_id} has multiple sample chronologies")
        native_taxa_by_dataset[dataset_id] = all_taxa
        chronology_id, chronology_name = next(iter(chronology))
        doi = dataset.get("doi", [])
        citation = dataset.get("datasetpi", [])
        site_profiles[dataset_id] = {
            "dataset_id": dataset_id,
            "site_id": spec["site_id"],
            "site": spec["label"],
            "record_id": f"neotoma-dataset:{dataset_id}",
            "group_id": f"neotoma-site:{spec['site_id']}",
            "latitude": latitude,
            "longitude": longitude,
            "chronology_id": chronology_id,
            "chronology_name": chronology_name,
            "sample_count": sample_count,
            "age_min_cal_bp": min(ages),
            "age_max_cal_bp": max(ages),
            "sample_age_bounds_present": False,
            "collection_date": collection.get("colldate"),
            "collection_unit": collection.get("handle"),
            "dataset_doi": doi,
            "dataset_pi": [
                f"{person.get('firstname', '')} {person.get('familyname', '')}".strip()
                for person in citation
            ],
            "all_taxa_native": sorted(all_taxa),
            "all_nisp_count": sample_totals[dataset_id],
            "closed_nisp_count": closed_totals[dataset_id],
            "bins": {
                key: {
                    "counts": values,
                    "all_nisp_count": bin_all[key],
                    "sample_count": bin_samples[key],
                    "closed_nisp_count": sum(values.values()),
                }
                for key, values in sorted(
                    bin_counts.items(), key=lambda item: int(item[0])
                )
            },
        }
        inventory_rows.append(
            {
                "site": spec["label"],
                "neotoma_dataset_id": dataset_id,
                "neotoma_site_id": spec["site_id"],
                "collection_unit": collection.get("handle"),
                "source_file": f"data/neotoma/raw/neotoma_pollen_dataset_downloads/{spec['part']}",
                "source_database": dataset["database"],
                "dataset_doi": ";".join(doi),
                "dataset_pi": ";".join(site_profiles[dataset_id]["dataset_pi"]),
                "collection_date": collection.get("colldate"),
                "latitude_wgs84": latitude,
                "longitude_wgs84": longitude,
                "chronology_id": chronology_id,
                "chronology_name": chronology_name,
                "age_units": "Calibrated radiocarbon years BP",
                "age_point_min_cal_bp": min(ages),
                "age_point_max_cal_bp": max(ages),
                "sample_age_uncertainty": "not supplied; older/younger bounds null",
                "sample_count": sample_count,
                "native_nisp_count": sample_totals[dataset_id],
                "closed_taxon_nisp_count": closed_totals[dataset_id],
                "excluded_nisp_count": sample_totals[dataset_id]
                - closed_totals[dataset_id],
                "closed_taxon_share": closed_totals[dataset_id]
                / sample_totals[dataset_id],
                "allowed_use": "EPD via public Neotoma: CC BY 4.0 with Neotoma, EPD and original investigator attribution",
                "pollen_ready": "yes for declared direct-pollen exploratory analysis",
                "lra_ready": "no: basin geometry, PPE, fall speed and dispersal profile not admitted",
                "basin_radius": "unresolved; not required by center-distance direct-pollen method",
                "ppe_fall_speed": "unresolved; not used by direct-pollen method",
            }
        )

    shared_native_taxa = set.intersection(*native_taxa_by_dataset.values())
    if shared_native_taxa != set(taxa):
        raise ValueError(
            "declared closed denominator differs from exact native taxon-name intersection"
        )
    common_bins = set.intersection(
        *(set(profile["bins"]) for profile in site_profiles.values())
    )
    if sorted(map(int, common_bins)) != sorted(config["common_age_bin_ids"]):
        raise ValueError(
            "declared common age bins differ from the prepared native chronology support"
        )
    if any(
        profile["bins"][bin_id]["closed_nisp_count"] <= 0
        for profile in site_profiles.values()
        for bin_id in common_bins
    ):
        raise ValueError(
            "shared age bin has zero count on the declared closed taxon axis"
        )

    for dataset_id, profile in site_profiles.items():
        target = workdir / "prepared" / f"dataset-{dataset_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    _write_csv(workdir / "cohort.csv", list(inventory_rows[0]), inventory_rows)
    _write_csv(workdir / "exclusions.csv", list(exclusions[0]), exclusions)
    source_hashes = {name: _sha(data_root / name) for name in source_files}
    (workdir / "input-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "swedish-direct-pollen-input-manifest.v1",
                "source": "Neotoma API frozen EPD downloads",
                "source_files": source_hashes,
                "config_sha256": _sha(config_path),
                "runner_sha256": _sha(Path(__file__)),
                "dataset_ids": list(DATASETS),
                "taxon_denominator": taxa,
                "age_bin_width_cal_bp": AGE_WIDTH,
                "zero_interpretation": "Neotoma observed-count matrix; unlisted taxon cells are zero-filled for this explicit subcomposition, following the documented Neotoma workflow",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "prepared_sites": list(site_profiles),
                "sample_counts": {
                    key: profile["sample_count"]
                    for key, profile in site_profiles.items()
                },
                "closed_taxa": list(taxa),
                "common_bins": sorted(
                    set.intersection(*(set(x["bins"]) for x in site_profiles.values())),
                    key=int,
                ),
                "excluded_rows": len(exclusions),
                "source_hashes": source_hashes,
            },
            indent=2,
        )
    )


def _load_profiles(workdir: Path) -> dict[str, dict[str, Any]]:
    return {
        dataset_id: json.loads(
            (workdir / "prepared" / f"dataset-{dataset_id}.json").read_text(
                encoding="utf-8"
            )
        )
        for dataset_id in DATASETS
    }


def predict(target_dataset_id: str, workdir: Path, config_path: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    site_metadata = config["sites"]
    if target_dataset_id not in site_metadata:
        raise ValueError(f"unknown target dataset {target_dataset_id}")
    target = site_metadata[target_dataset_id]
    target_group = target["group_id"]
    train_ids = [key for key in site_metadata if key != target_dataset_id]
    train = {
        key: json.loads(
            (workdir / "prepared" / f"dataset-{key}.json").read_text(encoding="utf-8")
        )
        for key in train_ids
    }
    all_bins = {str(value) for value in config["common_age_bin_ids"]}
    taxa = tuple(config["closed_taxa"])
    predictions: list[dict[str, Any]] = []
    fit_rows: list[dict[str, Any]] = []
    for bin_id in sorted(all_bins, key=int):
        bin_profiles = {key: value["bins"][bin_id] for key, value in train.items()}
        compositions = {
            profile["group_id"]: {
                taxon: count / sum(bin_profiles[key]["counts"].values())
                for taxon, count in bin_profiles[key]["counts"].items()
            }
            for key, profile in train.items()
        }
        coordinates = {
            profile["group_id"]: SiteCoordinate(
                profile["latitude"], profile["longitude"]
            )
            for key, profile in train.items()
        }
        target_coordinate = SiteCoordinate(target["latitude"], target["longitude"])
        distances = {
            profile["group_id"]: distance_km(
                coordinates[profile["group_id"]], target_coordinate
            )
            for key, profile in train.items()
        }
        fold = Fold(
            f"swedish-neotoma-site:{target['site_id']}:bin:{bin_id}",
            tuple(profile["record_id"] for profile in train.values()),
            (target["record_id"],),
            tuple(profile["group_id"] for profile in train.values()),
            (target_group,),
        )
        graph = {record_id: () for record_id in fold.train_record_ids}
        fold_predictions: dict[str, dict[str, float]] = {}
        for baseline_method in BASELINE_METHODS:
            output = predict_spatial_baseline(
                fold,
                compositions,
                method=baseline_method,
                input_ids=fold.train_record_ids,
                dependency_graph=graph,
                distances_km=(
                    distances if baseline_method != "training_mean" else None
                ),
                predictor_group_ids=fold.train_group_ids,
            )
            fold_predictions[baseline_method] = dict(output.fractions)
            fit_rows.append(
                {
                    "bin_id": int(bin_id),
                    "method": baseline_method,
                    "training_dataset_ids": train_ids,
                    "training_site_ids": [train[key]["site_id"] for key in train_ids],
                    "training_manifest_sha256": output.training_manifest_sha256,
                    "nearest_training_center_km": min(distances.values()),
                }
            )
        scale = median(list(distances.values()))
        fitted = fit_spatial_model(
            fold,
            {
                train[key]["group_id"]: half_count_composition(
                    bin_profiles[key]["counts"]
                )
                for key in train_ids
            },
            coordinates,
            config=SpatialConfig(
                scale,
                0.01,
                f"swedish-neotoma-exact-taxon-500bp:{target['site_id']}:{bin_id}",
            ),
            input_ids=fold.train_record_ids,
            dependency_graph=graph,
        )
        model_prediction = fitted.predict(
            target_group_id=target_group,
            coordinate=target_coordinate,
            support_id=fitted.config.support_id,
        )
        fold_predictions["clr_rbf_ridge"] = dict(model_prediction.fractions)
        fit_rows.append(
            {
                "bin_id": int(bin_id),
                "method": "clr_rbf_ridge",
                "training_dataset_ids": train_ids,
                "training_site_ids": [train[key]["site_id"] for key in train_ids],
                "model_sha256": fitted.model_sha256,
                "prediction_sha256": model_prediction.prediction_sha256,
                "length_scale_km": scale,
                "ridge_penalty": 0.01,
                "zero_handling": "add 0.5 to each declared training taxon only",
            }
        )
        for method, fractions in fold_predictions.items():
            predictions.append(
                {
                    "candidate_id": method,
                    "target_dataset_id": target_dataset_id,
                    "target_site_id": target["site_id"],
                    "bin_id": int(bin_id),
                    "target_coordinate_used": target_coordinate.as_dict(),
                    "target_outcome_input": "target count profile was not opened by this prediction process",
                    "predicted_fractions": fractions,
                    "taxon_denominator": taxa,
                    "training_dataset_ids": train_ids,
                }
            )
    output_dir = workdir / "predictions"
    output_dir.mkdir(exist_ok=True)
    path = output_dir / f"site-{target['site_id']}.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "swedish-direct-pollen-held-out-predictions.v1",
                "target_dataset_id": target_dataset_id,
                "target_site_id": target["site_id"],
                "predictions": predictions,
                "fit_records": fit_rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "target_dataset_id": target_dataset_id,
                "prediction_file": str(path),
                "sha256": _sha(path),
                "predictions": len(predictions),
            }
        )
    )


def score(workdir: Path) -> None:
    profiles = _load_profiles(workdir)
    score_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    for dataset_id, profile in profiles.items():
        saved = json.loads(
            (workdir / "predictions" / f"site-{profile['site_id']}.json").read_text(
                encoding="utf-8"
            )
        )
        if (
            saved["target_dataset_id"] != dataset_id
            or saved["target_site_id"] != profile["site_id"]
        ):
            raise ValueError("prediction identity differs from scored target")
        for prediction in saved["predictions"]:
            counts = profile["bins"][str(prediction["bin_id"])]["counts"]
            total = sum(counts.values())
            observed = {taxon: count / total for taxon, count in counts.items()}
            fractions = prediction["predicted_fractions"]
            scored = score_pollen(fractions, counts)
            hellinger = hellinger_distance(fractions, observed)
            score_rows.append(
                {
                    "candidate_id": prediction["candidate_id"],
                    "target_dataset_id": dataset_id,
                    "target_site_id": profile["site_id"],
                    "target_site": profile["site"],
                    "bin_id": prediction["bin_id"],
                    "bin_lower_cal_bp": prediction["bin_id"] * AGE_WIDTH,
                    "bin_upper_cal_bp_exclusive": (prediction["bin_id"] + 1)
                    * AGE_WIDTH,
                    "target_sample_count": profile["bins"][str(prediction["bin_id"])][
                        "sample_count"
                    ],
                    "target_closed_nisp_count": total,
                    "target_all_nisp_count": profile["bins"][str(prediction["bin_id"])][
                        "all_nisp_count"
                    ],
                    "target_excluded_nisp_count": profile["bins"][
                        str(prediction["bin_id"])
                    ]["all_nisp_count"]
                    - total,
                    "status": scored.status,
                    "mae_fraction": scored.mae_fraction,
                    "hellinger_distance": hellinger,
                    "training_dataset_ids": ";".join(
                        prediction["training_dataset_ids"]
                    ),
                    "prediction_sha256": _sha(
                        workdir / "predictions" / f"site-{profile['site_id']}.json"
                    ),
                }
            )
            for taxon in prediction["taxon_denominator"]:
                prediction_rows.append(
                    {
                        "candidate_id": prediction["candidate_id"],
                        "target_dataset_id": dataset_id,
                        "target_site_id": profile["site_id"],
                        "bin_id": prediction["bin_id"],
                        "taxon": taxon,
                        "observed_count": counts[taxon],
                        "predicted_fraction": fractions[taxon],
                        "target_outcome_opened_after_saved_prediction": True,
                    }
                )
    _write_csv(workdir / "scores.csv", list(score_rows[0]), score_rows)
    _write_csv(
        workdir / "predictions-scored.csv", list(prediction_rows[0]), prediction_rows
    )
    candidate_stats: dict[str, dict[str, Any]] = {}
    for method in METHODS:
        rows = [row for row in score_rows if row["candidate_id"] == method]
        by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_site[row["target_site"]].append(row)
        site_macro = {
            site: {
                "site_macro_mae_fraction": sum(row["mae_fraction"] for row in site_rows)
                / len(site_rows),
                "site_macro_hellinger": sum(
                    row["hellinger_distance"] for row in site_rows
                )
                / len(site_rows),
                "scored_bins": len(site_rows),
            }
            for site, site_rows in by_site.items()
        }
        candidate_stats[method] = {
            "attempted": len(rows),
            "scored": sum(row["status"] == "scored" for row in rows),
            "site_macro_mae_fraction": sum(
                x["site_macro_mae_fraction"] for x in site_macro.values()
            )
            / len(site_macro),
            "site_macro_hellinger": sum(
                x["site_macro_hellinger"] for x in site_macro.values()
            )
            / len(site_macro),
            "per_site": site_macro,
        }
    (workdir / "summary.json").write_text(
        json.dumps(candidate_stats, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Swedish Neotoma direct-pollen prediction",
        "",
        "This is a prior-exposed exploratory whole-site-held-out prediction of a declared 16-taxon exact-name pollen subcomposition. It is a statistical observed-pollen comparison, not REVEALS/LOVE, an LRA result, a vegetation-accuracy estimate, or a confirmatory test.",
        "",
        "The three independent Neotoma site IDs are held out one at a time. At each of 13 shared 500 calibrated-BP bins, the target coordinate is allowed and its pollen counts are omitted from that fold's prediction job. The prediction file is saved and hashed before the separate scoring job opens its target count profile. The fixed candidates are training mean, nearest site, inverse-distance-squared, and the existing CLR/WGS84 RBF-ridge with half-count replacement on training cells only, median positive training distance and ridge 0.01. No candidate selection uses these outcomes.",
        "",
        "Missing Neotoma NISP rows are interpreted as zero cells in the count matrix following the [documented Neotoma workflow](https://open.neotomadb.org/Current_Workshop/simple_workflow.html), which uses `pivot_wider(..., values_fill = 0)` for count matrices. The response is closed over the 16 exact taxon labels present in all three native inventories, without a taxon crosswalk. Those taxa contain 45–57% of each site's recorded NISP; all excluded labels/counts are enumerated in `exclusions.csv`. Scores apply only to this subcomposition.",
        "",
        "All four candidates cover the same 39 held-out site-bin targets. Site-macro scores average bins within each lake and then weight the three lakes equally. With three sites, aggregate uncertainty/generalization claims are limited. The two southern sites are close to each other while Abborrtjärnen is much farther north; this is an extremely small and geographically unbalanced test.",
        "",
        "| Candidate | Attempted | Scored | Site-macro MAE (fraction) | Site-macro Hellinger |",
        "|---|---:|---:|---:|---:|",
    ]
    for method, metrics in candidate_stats.items():
        lines.append(
            f"| {method} | {metrics['attempted']} | {metrics['scored']} | {metrics['site_macro_mae_fraction']:.6f} | {metrics['site_macro_hellinger']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Source and readiness",
            "",
            "The [EPD policy](https://epdweblog.org/epd_data_home/epd_policy/) states that EPD data available through Neotoma may be reused under CC BY 4.0 with Neotoma, EPD, and original investigator attribution. Dataset DOIs and contributor names are retained in `cohort.csv`. The direct-pollen channel is eligible under that rule. Separate LRA readiness remains false because source-backed basin geometry/radius, PPE, fall speeds and dispersal choices have not been admitted. No vegetation reference was opened or used.",
            "",
            "Native ages are sample-owned calibrated radiocarbon years BP under one Neotoma chronology ID per dataset; sample older/younger uncertainty bounds are null. Fixed 500-year bins are an exploratory aggregation choice. The existing question bundle remains relevant to Rootsi workbook age labels, rights and workbook-to-Neotoma relationships; it does not block this Neotoma-only prediction.",
            "",
            "## Reproduction",
            "",
            "Run `prepare`, then one `predict --target-dataset-id ID` for each of `19913`, `53995`, and `54001`, then `score`; see `config.json` and the managed job plans beside this result. The source files and configuration hashes are recorded in `input-manifest.json`.",
        ]
    )
    (workdir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": candidate_stats,
                "scored_rows": len(score_rows),
                "prediction_rows": len(prediction_rows),
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--data-root", type=Path, required=True)
    prepare_parser.add_argument("--workdir", type=Path, required=True)
    prepare_parser.add_argument("--config", type=Path, required=True)
    predict_parser = commands.add_parser("predict")
    predict_parser.add_argument("--target-dataset-id", required=True)
    predict_parser.add_argument("--workdir", type=Path, required=True)
    predict_parser.add_argument("--config", type=Path, required=True)
    score_parser = commands.add_parser("score")
    score_parser.add_argument("--workdir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.data_root, args.workdir, args.config)
    elif args.command == "predict":
        predict(args.target_dataset_id, args.workdir, args.config)
    else:
        score(args.workdir)


if __name__ == "__main__":
    main()
