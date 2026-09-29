"""Run a source-bound, country-held-out comparison of observed pollen counts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any, Literal, cast

from bijux_pollenomics.analysis.lra_validation.baselines import (
    predict_spatial_baseline,
)
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

BASELINE_METHODS: tuple[
    Literal["training_mean"],
    Literal["nearest_site"],
    Literal["inverse_distance_squared"],
] = (
    "training_mean",
    "nearest_site",
    "inverse_distance_squared",
)
METHODS = BASELINE_METHODS + ("clr_rbf_ridge",)
COUNTRIES = ("DK", "FI", "NO")
SWEDISH_DATASETS = {
    "19913": {"label": "Abborrtjärnen", "site_id": "13338", "part": "part-004.json"},
    "53995": {"label": "Bussjösjön", "site_id": "28869", "part": "part-008.json"},
    "54001": {"label": "Bökesjön", "site_id": "28872", "part": "part-008.json"},
}
TAXA = (
    "Alnus",
    "Amaranthaceae",
    "Betula",
    "Cichorioideae",
    "Cyperaceae",
    "Filipendula",
    "Frangula alnus",
    "Nuphar",
    "Plantago lanceolata",
    "Plantago media",
    "Populus",
    "Quercus",
    "Rosaceae undiff.",
    "Salix",
    "Thalictrum",
    "Ulmus",
)
AGE_WIDTH = 500
RELATIONAL_BUILD = (
    "sha256:92dd52619837f3641d004a1a5dbe38f9ab6023a79f61989314bb90e612eb58e1"
)
SOURCE_SNAPSHOT = (
    "sha256:b2bcb99157e10b0c9f13c228acc12eabcb39d96a1f39c86ec25e34aacd78c791"
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid Neotoma source table: {path}")
    if payload.get("source_snapshot_id") != SOURCE_SNAPSHOT:
        raise ValueError(f"unexpected Neotoma source snapshot: {path}")
    if payload.get("build_id") != RELATIONAL_BUILD:
        raise ValueError(f"unexpected Neotoma materialization: {path}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"invalid Neotoma source rows: {path}")
    return cast(list[dict[str, Any]], rows)


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _csv_write(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty tabular result: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _empty_bin() -> dict[str, Any]:
    return {
        "counts": dict.fromkeys(TAXA, 0),
        "all_pollen_nisp": 0,
        "closed_nisp": 0,
        "sample_ids": [],
    }


def _is_direct_pollen_count(row: dict[str, Any]) -> bool:
    value = row.get("source_value")
    name = row.get("source_reported_name")
    return (
        row.get("source_element") == "pollen"
        and row.get("source_element_type") == "pollen"
        and row.get("source_unit") == "NISP"
        and row.get("unit_family") == "count"
        and row.get("detection_status") == "reported_value"
        and type(value) is int
        and value >= 0
        and isinstance(name, str)
        and bool(name.strip())
    )


def _select_comparable_age(
    claims: list[dict[str, Any]], chronologies: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Select the sole comparable age or a unique source-flagged default."""
    if not claims:
        return None
    if len(claims) == 1:
        return claims[0]
    flagged = [
        claim
        for claim in claims
        if chronologies[claim["chronology_id"]]["source_is_default_assertion"]
    ]
    return flagged[0] if len(flagged) == 1 else None


def _site_coordinate(geography: str) -> SiteCoordinate:
    geometry = json.loads(geography) if isinstance(geography, str) else geography
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if kind == "Point" and isinstance(coordinates, list) and len(coordinates) >= 2:
        longitude, latitude = coordinates[:2]
    elif kind in {"Polygon", "MultiPolygon"}:
        polygons = [coordinates] if kind == "Polygon" else coordinates
        weighted_area = 0.0
        weighted_longitude = 0.0
        weighted_latitude = 0.0
        for polygon in polygons:
            for ring_index, ring in enumerate(polygon):
                area_twice = 0.0
                centroid_x = 0.0
                centroid_y = 0.0
                for current, following in zip(ring, ring[1:] + ring[:1], strict=True):
                    cross = current[0] * following[1] - following[0] * current[1]
                    area_twice += cross
                    centroid_x += (current[0] + following[0]) * cross
                    centroid_y += (current[1] + following[1]) * cross
                if abs(area_twice) < 1e-15:
                    raise ValueError("Neotoma site polygon has zero area")
                area = abs(area_twice) / 2
                center_x = centroid_x / (3 * area_twice)
                center_y = centroid_y / (3 * area_twice)
                signed_area = area if ring_index == 0 else -area
                weighted_area += signed_area
                weighted_longitude += signed_area * center_x
                weighted_latitude += signed_area * center_y
        if weighted_area <= 0:
            raise ValueError("Neotoma site polygon has no positive exterior area")
        longitude = weighted_longitude / weighted_area
        latitude = weighted_latitude / weighted_area
    else:
        raise ValueError(f"unsupported Neotoma site geometry type: {kind}")
    if not (math.isfinite(float(longitude)) and math.isfinite(float(latitude))):
        raise ValueError("Neotoma site geometry has no finite centroid")
    return SiteCoordinate(latitude=float(latitude), longitude=float(longitude))


def _swedish_training(
    raw_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    wanted = set(SWEDISH_DATASETS)
    records: dict[str, dict[str, Any]] = {}
    used_files = sorted({spec["part"] for spec in SWEDISH_DATASETS.values()})
    for filename in used_files:
        payload = json.loads((raw_root / filename).read_text(encoding="utf-8"))
        for row in payload["rows"]:
            site = row["site"]
            dataset = site.get("dataset", {})
            dataset_id = str(dataset.get("datasetid"))
            if dataset_id not in wanted:
                continue
            if dataset_id in records:
                raise ValueError(f"duplicate Swedish Neotoma dataset {dataset_id}")
            records[dataset_id] = {"site": site, "dataset": dataset}
    if set(records) != wanted:
        raise ValueError(
            "the three previously admitted Swedish datasets are incomplete"
        )

    profiles: dict[str, dict[str, Any]] = {}
    source_hashes = {filename: _sha(raw_root / filename) for filename in used_files}
    for dataset_id, spec in SWEDISH_DATASETS.items():
        record = records[dataset_id]
        site, dataset = record["site"], record["dataset"]
        if (
            dataset.get("datasettype") != "pollen"
            or dataset.get("database") != "European Pollen Database"
            or str(site["siteid"]) != spec["site_id"]
        ):
            raise ValueError(f"Swedish source identity changed: {dataset_id}")
        collection = site["collectionunit"]
        nested = collection["dataset"]
        coordinate = _site_coordinate(site["geography"])
        bins: dict[str, dict[str, Any]] = defaultdict(_empty_bin)
        all_ages: list[float] = []
        for sample in nested["samples"]:
            ages = sample.get("ages", [])
            if (
                len(ages) != 1
                or ages[0].get("agetype") != "Calibrated radiocarbon years BP"
                or ages[0].get("age") is None
            ):
                raise ValueError(
                    f"Swedish sample lacks its admitted calibrated BP age: {dataset_id}"
                )
            age = float(ages[0]["age"])
            if not math.isfinite(age):
                raise ValueError("Swedish sample age is not finite")
            all_ages.append(age)
            bin_id = str(math.floor(age / AGE_WIDTH))
            seen: set[str] = set()
            all_count = 0
            taxon_counts: dict[str, int] = defaultdict(int)
            for datum in sample.get("datum", []):
                if datum.get("units") != "NISP" or datum.get("elementtype") != "pollen":
                    continue
                taxon, value = datum.get("variablename"), datum.get("value")
                if not isinstance(taxon, str) or type(value) is not int or value < 0:
                    raise ValueError("invalid Swedish NISP pollen observation")
                if taxon in seen:
                    raise ValueError(
                        f"duplicate Swedish exact taxon in sample: {taxon}"
                    )
                seen.add(taxon)
                all_count += value
                if taxon in TAXA:
                    taxon_counts[taxon] += value
            if all_count <= 0:
                raise ValueError(
                    "Swedish sample has no positive native NISP pollen count"
                )
            cell = bins[bin_id]
            cell["all_pollen_nisp"] += all_count
            cell["sample_ids"].append(str(sample.get("sampleid")))
            for taxon, value in taxon_counts.items():
                cell["counts"][taxon] += value
            cell["closed_nisp"] = sum(cell["counts"].values())
        profiles[dataset_id] = {
            "country": "SE",
            "dataset_id": dataset_id,
            "dataset_name": spec["label"],
            "site_id": spec["site_id"],
            "site_name": spec["label"],
            "group_id": f"neotoma-site:{spec['site_id']}",
            "record_id": f"neotoma-dataset:{dataset_id}",
            "coordinate": coordinate.as_dict(),
            "sample_count": len(nested["samples"]),
            "age_min_bp": min(all_ages),
            "age_max_bp": max(all_ages),
            "source_database": dataset.get("database"),
            "source_dois": dataset.get("doi", []),
            "contributors": [
                " ".join(
                    str(person.get(key) or "").strip()
                    for key in ("firstname", "familyname")
                ).strip()
                for person in dataset.get("datasetpi", [])
            ],
            "sample_age_basis": "Calibrated radiocarbon years BP",
            "bins": dict(bins),
        }
    return profiles, source_hashes


def _neotoma_candidates(
    relational_root: Path, raw_root: Path
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, str],
    str,
    dict[str, Any],
]:
    from bijux_pollenomics.analysis.lra.materialization.api import (
        inspect_neotoma_lra_pollen_screen,
    )

    manifest_path = relational_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("source_snapshot_id") != SOURCE_SNAPSHOT
        or manifest.get("build_id") != RELATIONAL_BUILD
    ):
        raise ValueError("Neotoma relational manifest identity changed")
    file_hashes: dict[str, str] = {"manifest.json": _sha(manifest_path)}

    def surface_rows(name: str) -> list[dict[str, Any]]:
        surface = manifest["surfaces"][name]
        result: list[dict[str, Any]] = []
        for part in surface["parts"]:
            path = relational_root / part["path"]
            digest = _sha(path)
            if digest != part["sha256"]:
                raise ValueError(f"Neotoma manifest digest mismatch: {part['path']}")
            file_hashes[part["path"]] = digest
            result.extend(_read_rows(path))
        if len(result) != surface["row_count"]:
            raise ValueError(f"Neotoma surface count mismatch: {name}")
        return result

    samples = surface_rows("samples")
    datasets = surface_rows("datasets")
    sites = surface_rows("sites")
    ages = surface_rows("age_claims")
    chronologies = surface_rows("chronologies")
    observations = surface_rows("observations")
    screen = inspect_neotoma_lra_pollen_screen(
        raw_root=raw_root,
        normalized_root=relational_root,
    ).as_dict()
    screened_candidates = set(screen["candidate_sample_ids"])
    age_by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for age_claim in ages:
        if (
            age_claim["subject_type"] == "sample"
            and age_claim["comparability_status"] == "comparable"
        ):
            age_by_sample[age_claim["subject_id"]].append(age_claim)
    dataset_by_id = {row["dataset_id"]: row for row in datasets}
    chronology_by_id = {row["chronology_id"]: row for row in chronologies}
    site_by_id = {row["site_id"]: row for row in sites}
    sample_by_id = {row["sample_id"]: row for row in samples}
    candidate_ids: set[str] = {
        sample_id
        for sample_id in screened_candidates
        if sample_id in sample_by_id
        and sample_by_id[sample_id]["country_code"] in COUNTRIES
    }
    for country in COUNTRIES:
        if (
            sum(
                sample_by_id[sample_id]["country_code"] == country
                for sample_id in candidate_ids
            )
            != screen["country_denominators"][country]["screen_candidate_samples"]
        ):
            raise ValueError(f"{country} pollen screen candidate count differs")

    profiles: dict[str, dict[str, Any]] = {}
    target_metadata: dict[str, dict[str, Any]] = {}
    age_basis_by_sample: dict[str, tuple[float, str]] = {}
    selected_age_claims_by_sample: dict[str, str] = {}
    for country in COUNTRIES:
        country_sample_ids = sorted(
            sid for sid in candidate_ids if sample_by_id[sid]["country_code"] == country
        )
        selected_country_sample_ids: list[str] = []
        excluded_age_claims: list[dict[str, Any]] = []
        site_records: dict[str, dict[str, Any]] = {}
        for sample_id in country_sample_ids:
            claims = age_by_sample[sample_id]
            if not claims:
                raise ValueError(f"screen candidate has no comparable age: {sample_id}")
            claim = _select_comparable_age(claims, chronology_by_id)
            if claim is None:
                excluded_age_claims.append(
                    {
                        "sample_id": sample_id,
                        "reason": "multiple_comparable_ages_without_one_source_default",
                        "claim_ids": sorted(
                            claim["chronology_claim_id"] for claim in claims
                        ),
                    }
                )
                continue
            selected_country_sample_ids.append(sample_id)
            selected_age_claims_by_sample[sample_id] = claim["chronology_claim_id"]
            age_type = claim["source_age_type"]
            if age_type not in {"Calibrated radiocarbon years BP", "Calendar years BP"}:
                raise ValueError(f"unsupported comparable BP basis: {age_type}")
            value = claim["source_age_value"]
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(
                    f"candidate sample has no finite comparable age: {sample_id}"
                )
            age_basis_by_sample[sample_id] = (float(value), age_type)
            sample_row = sample_by_id[sample_id]
            dataset = dataset_by_id[sample_row["dataset_id"]]
            site = site_by_id[sample_row["site_id"]]
            if dataset["country_code"] != country or site["country_code"] != country:
                raise ValueError(f"country source identity conflicts for {sample_id}")
            dataset_payload = dataset["source_payload"]
            if dataset_payload.get("database") != "European Pollen Database":
                raise ValueError(
                    f"non-EPD dataset in direct-pollen cohort: {sample_row['dataset_id']}"
                )
            if sample_row["site_id"] not in site_records:
                coordinate = _site_coordinate(site["source_payload"]["geography"])
                site_records[sample_row["site_id"]] = {
                    "country": country,
                    "site_id": sample_row["site_id"],
                    "site_name": site["source_payload"].get("sitename"),
                    "coordinate": coordinate.as_dict(),
                    "group_id": sample_row["site_id"],
                    "dataset_ids": set(),
                    "sample_ids": [],
                    "ages": [],
                    "bins": defaultdict(_empty_bin),
                    "dataset_details": {},
                }
            site_record = site_records[sample_row["site_id"]]
            site_record["dataset_ids"].add(sample_row["dataset_id"])
            site_record["sample_ids"].append(sample_id)
            sample_age_bp, age_basis = age_basis_by_sample[sample_id]
            site_record["ages"].append(sample_age_bp)
            detail = site_record["dataset_details"].setdefault(
                sample_row["dataset_id"],
                {
                    "dataset_name": dataset_payload.get("datasetname"),
                    "source_dois": dataset_payload.get("doi", []),
                    "contributors": [
                        " ".join(
                            str(person.get(key) or "").strip()
                            for key in ("firstname", "familyname")
                        ).strip()
                        for person in dataset_payload.get("datasetpi", [])
                    ],
                    "sample_age_bases": Counter(),
                },
            )
            detail["sample_age_bases"][age_basis] += 1

        country_bins: dict[str, set[str]] = defaultdict(set)
        for sample_id in selected_country_sample_ids:
            sample_row = sample_by_id[sample_id]
            sample_age_bp, _ = age_basis_by_sample[sample_id]
            country_bins[sample_row["site_id"]].add(
                str(math.floor(sample_age_bp / AGE_WIDTH))
            )
        metadata_sites: list[dict[str, Any]] = []
        for site_id, site_record in sorted(site_records.items()):
            metadata_sites.append(
                {
                    "country": country,
                    "site_id": site_id,
                    "site_name": site_record["site_name"],
                    "group_id": site_record["group_id"],
                    "coordinate": site_record["coordinate"],
                    "dataset_details": {
                        dataset_id: {
                            **detail,
                            "sample_age_bases": dict(detail["sample_age_bases"]),
                        }
                        for dataset_id, detail in sorted(
                            site_record["dataset_details"].items()
                        )
                    },
                    "candidate_sample_ids": sorted(site_record["sample_ids"]),
                    "candidate_bin_ids": sorted(country_bins[site_id], key=int),
                }
            )
            dataset_ids = sorted(site_record["dataset_ids"])
            profile = {
                "country": country,
                "site_id": site_id,
                "site_name": site_record["site_name"],
                "group_id": site_record["group_id"],
                "record_id": f"neotoma-site:{site_id}",
                "coordinate": site_record["coordinate"],
                "dataset_ids": dataset_ids,
                "sample_count": len(site_record["sample_ids"]),
                "age_min_bp": min(site_record["ages"]),
                "age_max_bp": max(site_record["ages"]),
                "dataset_details": site_record["dataset_details"],
                "bins": {},
            }
            profiles[f"{country}:{site_id}"] = profile
        target_metadata[country] = {
            "country": country,
            "candidate_samples": len(selected_country_sample_ids),
            "source_screen_candidate_samples": len(country_sample_ids),
            "excluded_age_claims": excluded_age_claims,
            "selected_age_claim_ids": {
                sample_id: selected_age_claims_by_sample[sample_id]
                for sample_id in selected_country_sample_ids
            },
            "sites": metadata_sites,
        }

    # Populate only the profiles that can be used as training data. Target
    # outcomes are read again after prediction files are frozen.
    for row in observations:
        sample_id = row["sample_id"]
        candidate_sample = sample_by_id.get(sample_id)
        if sample_id not in selected_age_claims_by_sample or candidate_sample is None:
            continue
        if not _is_direct_pollen_count(row):
            continue
        country = candidate_sample["country_code"]
        sample_age_bp, _ = age_basis_by_sample[sample_id]
        bin_id = str(math.floor(sample_age_bp / AGE_WIDTH))
        site_id = candidate_sample["site_id"]
        profile = profiles[f"{country}:{site_id}"]
        cell = profile["bins"].setdefault(bin_id, _empty_bin())
        value = row["source_value"]
        cell["all_pollen_nisp"] += value
        cell["sample_ids"].append(sample_id)
        label = row["source_reported_name"]
        if label in TAXA:
            cell["counts"][label] += value
        cell["closed_nisp"] = sum(cell["counts"].values())

    # Keep site/bins with an age-and-count screen but no closed taxa in the
    # target metadata; scoring will report those as denominator refusals.
    for country in COUNTRIES:
        for site in target_metadata[country]["sites"]:
            profile = profiles[f"{country}:{site['site_id']}"]
            for bin_id in site["candidate_bin_ids"]:
                profile["bins"].setdefault(bin_id, _empty_bin())

    return (
        profiles,
        target_metadata,
        file_hashes,
        hashlib.sha256(
            json.dumps(screen, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        screen["country_denominators"],
    )


def prepare(relational_root: Path, raw_root: Path, workdir: Path) -> None:
    swedish, raw_hashes = _swedish_training(raw_root)
    (
        nordic,
        target_metadata,
        relational_hashes,
        screen_hash,
        screen_country_denominators,
    ) = _neotoma_candidates(relational_root, raw_root)
    all_profiles = {**swedish, **nordic}
    workdir.mkdir(parents=True, exist_ok=True)
    inputs = workdir / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    for country in COUNTRIES:
        training_profiles = {
            key: value
            for key, value in all_profiles.items()
            if value["country"] != country
        }
        _json_write(inputs / f"training-{country}.json", training_profiles)
        _json_write(inputs / f"metadata-{country}.json", target_metadata[country])
    _json_write(workdir / "target-metadata.json", target_metadata)
    _json_write(
        workdir / "input-manifest.json",
        {
            "schema_version": "nordic-direct-pollen-inputs.v1",
            "runner_sha256": _sha(Path(__file__).resolve()),
            "source_snapshot_id": SOURCE_SNAPSHOT,
            "relational_build_id": RELATIONAL_BUILD,
            "relational_file_sha256": relational_hashes,
            "pollen_screen_sha256": screen_hash,
            "source_screen_country_denominators": screen_country_denominators,
            "swedish_raw_file_sha256": raw_hashes,
            "country_candidate_samples": {
                country: target_metadata[country]["candidate_samples"]
                for country in COUNTRIES
            },
            "swedish_training_datasets": sorted(SWEDISH_DATASETS),
            "taxon_axis": list(TAXA),
            "age_bin_width_bp": AGE_WIDTH,
            "target_outcomes_in_prediction_inputs": False,
        },
    )
    print(
        json.dumps(
            {
                "country_candidates": {
                    country: {
                        "samples": target_metadata[country]["candidate_samples"],
                        "sites": len(target_metadata[country]["sites"]),
                    }
                    for country in COUNTRIES
                },
                "training_profiles": {
                    country: sum(
                        profile["country"] != country
                        for profile in all_profiles.values()
                    )
                    for country in COUNTRIES
                },
                "input_manifest": str(workdir / "input-manifest.json"),
            },
            indent=2,
        )
    )


def _coordinate(payload: dict[str, Any]) -> SiteCoordinate:
    return SiteCoordinate(
        latitude=float(payload["latitude"]), longitude=float(payload["longitude"])
    )


def predict_country(workdir: Path, country: str) -> None:
    if country not in COUNTRIES:
        raise ValueError(f"unsupported held-out country: {country}")
    inputs = workdir / "inputs"
    training: dict[str, dict[str, Any]] = json.loads(
        (inputs / f"training-{country}.json").read_text(encoding="utf-8")
    )
    metadata = json.loads(
        (inputs / f"metadata-{country}.json").read_text(encoding="utf-8")
    )
    rows: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    for target in metadata["sites"]:
        target_group = target["group_id"]
        target_coordinate = _coordinate(target["coordinate"])
        for bin_id in target["candidate_bin_ids"]:
            bin_training = {
                key: profile
                for key, profile in training.items()
                if bin_id in profile["bins"]
                and profile["bins"][bin_id]["closed_nisp"] > 0
            }
            groups = {profile["group_id"] for profile in bin_training.values()}
            if len(groups) < 2:
                refused.append(
                    {
                        "country": country,
                        "site_id": target["site_id"],
                        "bin_id": int(bin_id),
                        "reason": "fewer_than_two_training_site_groups_with_positive_closed_counts",
                        "training_groups": sorted(groups),
                    }
                )
                continue
            record_ids = tuple(
                profile["record_id"] for _, profile in sorted(bin_training.items())
            )
            group_ids = tuple(
                profile["group_id"] for _, profile in sorted(bin_training.items())
            )
            fold = Fold(
                f"country-held-out:{country}:site:{target['site_id']}:bin:{bin_id}",
                record_ids,
                (f"neotoma-site:{target['site_id']}:bin:{bin_id}",),
                group_ids,
                (target_group,),
            )
            graph = dict.fromkeys(record_ids, ())
            compositions = {
                profile["group_id"]: {
                    taxon: count / profile["bins"][bin_id]["closed_nisp"]
                    for taxon, count in profile["bins"][bin_id]["counts"].items()
                }
                for _, profile in sorted(bin_training.items())
            }
            coordinates = {
                profile["group_id"]: _coordinate(profile["coordinate"])
                for profile in bin_training.values()
            }
            distances = {
                group_id: distance_km(coordinate, target_coordinate)
                for group_id, coordinate in coordinates.items()
            }
            if any(not math.isfinite(value) for value in distances.values()):
                raise ValueError("a spatial baseline distance is not finite")
            fold_predictions: dict[str, dict[str, float]] = {}
            for method in BASELINE_METHODS:
                estimate = predict_spatial_baseline(
                    fold,
                    compositions,
                    method=method,
                    input_ids=record_ids,
                    dependency_graph=graph,
                    distances_km=distances if method != "training_mean" else None,
                    predictor_group_ids=group_ids,
                )
                fold_predictions[method] = dict(estimate.fractions)
            scale = median(distances.values())
            if not scale > 0:
                refused.append(
                    {
                        "country": country,
                        "site_id": target["site_id"],
                        "bin_id": int(bin_id),
                        "reason": "nonpositive_median_training_distance",
                        "training_groups": sorted(groups),
                    }
                )
                continue
            fitted = fit_spatial_model(
                fold,
                {
                    profile["group_id"]: half_count_composition(
                        profile["bins"][bin_id]["counts"]
                    )
                    for profile in bin_training.values()
                },
                coordinates,
                config=SpatialConfig(
                    scale,
                    0.01,
                    f"nordic-direct-pollen:{country}:{target['site_id']}:{bin_id}",
                ),
                input_ids=record_ids,
                dependency_graph=graph,
            )
            model = fitted.predict(
                target_group_id=target_group,
                coordinate=target_coordinate,
                support_id=fitted.config.support_id,
            )
            fold_predictions["clr_rbf_ridge"] = dict(model.fractions)
            for output_method in METHODS:
                rows.append(
                    {
                        "country": country,
                        "target_site_id": target["site_id"],
                        "target_site_name": target["site_name"],
                        "bin_id": int(bin_id),
                        "method": output_method,
                        "prediction_fractions": fold_predictions[output_method],
                        "taxon_axis": list(TAXA),
                        "training_site_ids": sorted(
                            profile["site_id"] for profile in bin_training.values()
                        ),
                        "training_group_ids": sorted(groups),
                        "target_coordinate_input": target["coordinate"],
                        "target_pollen_counts_read": False,
                    }
                )
    prediction_path = workdir / f"predictions-{country}.json"
    _json_write(
        prediction_path,
        {
            "schema_version": "nordic-direct-pollen-country-held-out.v1",
            "country": country,
            "target_outcome_use": "No target pollen count profile is present in this process input.",
            "predictions": rows,
            "refused_targets": refused,
        },
    )
    print(
        json.dumps(
            {
                "country": country,
                "prediction_file": str(prediction_path),
                "sha256": _sha(prediction_path),
                "predictions": len(rows),
                "refused_target_bins": len(refused),
            },
            indent=2,
        )
    )


def _nordic_target_outcomes(
    relational_root: Path, country: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    manifest = json.loads(
        (relational_root / "manifest.json").read_text(encoding="utf-8")
    )
    surface = manifest["surfaces"]["observations"]
    samples = _read_rows(
        relational_root / manifest["surfaces"]["samples"]["parts"][0]["path"]
    )
    ages = _read_rows(
        relational_root / manifest["surfaces"]["age_claims"]["parts"][0]["path"]
    )
    selected_age_claim_ids = metadata["selected_age_claim_ids"]
    age_by_sample = {
        row["subject_id"]: row
        for row in ages
        if row["subject_type"] == "sample"
        and row["comparability_status"] == "comparable"
        and selected_age_claim_ids.get(row["subject_id"]) == row["chronology_claim_id"]
    }
    if set(age_by_sample) != set(selected_age_claim_ids):
        raise ValueError("selected target age-claim identities changed before scoring")
    sample_by_id = {row["sample_id"]: row for row in samples}
    outcome_ids: set[str] = set()
    for site in metadata["sites"]:
        outcome_ids.update(site["candidate_sample_ids"])
    by_site_bin: dict[str, dict[str, Any]] = defaultdict(_empty_bin)
    for part in surface["parts"]:
        path = relational_root / part["path"]
        if _sha(path) != part["sha256"]:
            raise ValueError(
                f"Neotoma observation part digest mismatch: {part['path']}"
            )
        for row in _read_rows(path):
            sample_id = row["sample_id"]
            if sample_id not in outcome_ids:
                continue
            if not _is_direct_pollen_count(row):
                continue
            sample = sample_by_id[sample_id]
            claim = age_by_sample[sample_id]
            age = float(claim["source_age_value"])
            bin_id = str(math.floor(age / AGE_WIDTH))
            key = f"{sample['site_id']}:{bin_id}"
            cell = by_site_bin[key]
            cell["sample_ids"].append(sample_id)
            cell["all_pollen_nisp"] += row["source_value"]
            if row["source_reported_name"] in TAXA:
                cell["counts"][row["source_reported_name"]] += row["source_value"]
            cell["closed_nisp"] = sum(cell["counts"].values())
    return {"country": country, "sites": dict(by_site_bin)}


def score(relational_root: Path, workdir: Path, publish_dir: Path) -> None:
    input_manifest = json.loads((workdir / "input-manifest.json").read_text())
    prediction_payloads: dict[str, dict[str, Any]] = {}
    prediction_hashes: dict[str, str] = {}
    target_metadata = json.loads((workdir / "target-metadata.json").read_text())
    for country in COUNTRIES:
        path = workdir / f"predictions-{country}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["country"] != country:
            raise ValueError("held-out prediction country differs from its output path")
        prediction_payloads[country] = payload
        prediction_hashes[country] = _sha(path)

    target_outcomes = {
        country: _nordic_target_outcomes(
            relational_root, country, target_metadata[country]
        )
        for country in COUNTRIES
    }
    scores: list[dict[str, Any]] = []
    for country in COUNTRIES:
        outcomes = target_outcomes[country]
        target_site_names = {
            site["site_id"]: site["site_name"]
            for site in target_metadata[country]["sites"]
        }
        for prediction in prediction_payloads[country]["predictions"]:
            key = f"{prediction['target_site_id']}:{prediction['bin_id']}"
            observed = outcomes["sites"].get(key)
            if observed is None or observed["closed_nisp"] <= 0:
                continue
            for method in (prediction["method"],):
                estimate = prediction["prediction_fractions"]
                result = score_pollen(estimate, observed["counts"])
                observed_fractions = {
                    taxon: count / observed["closed_nisp"]
                    for taxon, count in observed["counts"].items()
                }
                scores.append(
                    {
                        "country": country,
                        "target_site_id": prediction["target_site_id"],
                        "target_site_name": target_site_names[
                            prediction["target_site_id"]
                        ],
                        "bin_id": prediction["bin_id"],
                        "bin_lower_bp": prediction["bin_id"] * AGE_WIDTH,
                        "bin_upper_bp_exclusive": (prediction["bin_id"] + 1)
                        * AGE_WIDTH,
                        "method": method,
                        "status": result.status,
                        "mae_fraction": result.mae_fraction,
                        "hellinger_distance": hellinger_distance(
                            estimate, observed_fractions
                        ),
                        "target_sample_count": len(set(observed["sample_ids"])),
                        "target_closed_nisp": observed["closed_nisp"],
                        "target_all_pollen_nisp": observed["all_pollen_nisp"],
                        "training_site_ids": ";".join(prediction["training_site_ids"]),
                        "prediction_sha256": prediction_hashes[country],
                    }
                )
    if not scores:
        raise ValueError(
            "no country-held-out targets had a scorable closed pollen profile"
        )

    coverage_rows: list[dict[str, Any]] = []
    for country in COUNTRIES:
        candidates = {
            (site["site_id"], int(bin_id))
            for site in target_metadata[country]["sites"]
            for bin_id in site["candidate_bin_ids"]
        }
        outcome_bins = target_outcomes[country]["sites"]
        positive_closed = {
            (key.rsplit(":", 1)[0], int(key.rsplit(":", 1)[1]))
            for key, row in outcome_bins.items()
            if row["closed_nisp"] > 0
        }
        predicted = {
            (row["target_site_id"], row["bin_id"])
            for row in prediction_payloads[country]["predictions"]
        }
        scored = {
            (row["target_site_id"], row["bin_id"])
            for row in scores
            if row["country"] == country and row["method"] == METHODS[0]
        }
        names = {
            site["site_id"]: site["site_name"]
            for site in target_metadata[country]["sites"]
        }
        for site_id in sorted(names):
            site_candidates = {pair for pair in candidates if pair[0] == site_id}
            site_eligible = {pair for pair in positive_closed if pair[0] == site_id}
            site_predicted = {pair for pair in predicted if pair[0] == site_id}
            site_scored = {pair for pair in scored if pair[0] == site_id}
            coverage_rows.append(
                {
                    "country": country,
                    "site_id": site_id,
                    "site_name": names[site_id],
                    "candidate_age_count_bins": len(site_candidates),
                    "positive_closed_taxon_bins": len(site_eligible),
                    "predicted_bins": len(site_predicted),
                    "scored_bins": len(site_scored),
                    "empty_or_refused_outcome_bins": len(
                        site_candidates - site_eligible
                    ),
                    "eligible_bins_without_prediction": len(
                        site_eligible - site_predicted
                    ),
                }
            )

    stats: list[dict[str, Any]] = []
    for country in COUNTRIES:
        country_rows = [row for row in scores if row["country"] == country]
        for method in METHODS:
            method_rows = [row for row in country_rows if row["method"] == method]
            by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in method_rows:
                by_site[row["target_site_id"]].append(row)
            per_site = []
            for site_id, site_rows in sorted(by_site.items()):
                per_site.append(
                    {
                        "country": country,
                        "site_id": site_id,
                        "site_name": site_rows[0]["target_site_name"],
                        "method": method,
                        "scored_bins": len(site_rows),
                        "site_macro_mae_fraction": sum(
                            row["mae_fraction"] for row in site_rows
                        )
                        / len(site_rows),
                        "site_macro_hellinger": sum(
                            row["hellinger_distance"] for row in site_rows
                        )
                        / len(site_rows),
                    }
                )
            stats.append(
                {
                    "country": country,
                    "method": method,
                    "attempted_predictions": sum(
                        row["method"] == method
                        for row in prediction_payloads[country]["predictions"]
                    ),
                    "scored_bins": len(method_rows),
                    "scored_sites": len(per_site),
                    "site_macro_mae_fraction": (
                        sum(row["site_macro_mae_fraction"] for row in per_site)
                        / len(per_site)
                        if per_site
                        else None
                    ),
                    "site_macro_hellinger": (
                        sum(row["site_macro_hellinger"] for row in per_site)
                        / len(per_site)
                        if per_site
                        else None
                    ),
                }
            )
    _csv_write(workdir / "scores.csv", scores)
    _csv_write(workdir / "site-scores.csv", stats)
    _csv_write(workdir / "coverage.csv", coverage_rows)
    training_source_rows: list[dict[str, Any]] = []
    for held_out_country in COUNTRIES:
        training = json.loads(
            (workdir / "inputs" / f"training-{held_out_country}.json").read_text(
                encoding="utf-8"
            )
        )
        for profile in training.values():
            available_bins = ";".join(
                bin_id
                for bin_id, cell in sorted(
                    profile["bins"].items(), key=lambda pair: int(pair[0])
                )
                if cell["closed_nisp"] > 0
            )
            if "dataset_ids" in profile:
                dataset_details = profile["dataset_details"]
                sources = [
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": detail["dataset_name"],
                        "source_dois": detail["source_dois"],
                        "contributors": detail["contributors"],
                    }
                    for dataset_id, detail in sorted(dataset_details.items())
                ]
            else:
                sources = [
                    {
                        "dataset_id": profile["dataset_id"],
                        "dataset_name": profile["dataset_name"],
                        "source_dois": profile["source_dois"],
                        "contributors": profile["contributors"],
                    }
                ]
            for source in sources:
                training_source_rows.append(
                    {
                        "held_out_country": held_out_country,
                        "training_country": profile["country"],
                        "site_id": profile["site_id"],
                        "site_name": profile["site_name"],
                        "dataset_id": source["dataset_id"],
                        "dataset_name": source["dataset_name"],
                        "source_database": "European Pollen Database",
                        "dataset_dois": ";".join(source["source_dois"]),
                        "contributors": ";".join(source["contributors"]),
                        "training_samples": profile["sample_count"],
                        "positive_closed_taxon_bins": available_bins,
                    }
                )
    _csv_write(workdir / "training-sources.csv", training_source_rows)
    prediction_rows = []
    for country in COUNTRIES:
        for row in prediction_payloads[country]["predictions"]:
            prediction_rows.append(
                {
                    "country": country,
                    "target_site_id": row["target_site_id"],
                    "target_site_name": row["target_site_name"],
                    "bin_id": row["bin_id"],
                    "method": row["method"],
                    "predicted_fractions": json.dumps(
                        row["prediction_fractions"], sort_keys=True
                    ),
                    "training_site_ids": ";".join(row["training_site_ids"]),
                    "prediction_sha256": prediction_hashes[country],
                }
            )
    _csv_write(workdir / "predictions.csv", prediction_rows)
    cohort_rows: list[dict[str, Any]] = []
    for country in COUNTRIES:
        for site in target_metadata[country]["sites"]:
            cohort_rows.append(
                {
                    "country": country,
                    "site_id": site["site_id"],
                    "site_name": site["site_name"],
                    "candidate_samples": len(site["candidate_sample_ids"]),
                    "candidate_age_bins": ";".join(site["candidate_bin_ids"]),
                    "coordinate_source": "Neotoma site geometry centroid (WGS84)",
                    "dataset_ids": ";".join(sorted(site["dataset_details"])),
                    "dataset_names": ";".join(
                        str(detail["dataset_name"] or "")
                        for _, detail in sorted(site["dataset_details"].items())
                    ),
                    "dataset_dois": ";".join(
                        doi
                        for _, detail in sorted(site["dataset_details"].items())
                        for doi in detail["source_dois"]
                    ),
                    "contributors": ";".join(
                        contributor
                        for _, detail in sorted(site["dataset_details"].items())
                        for contributor in detail["contributors"]
                    ),
                }
            )
    _csv_write(workdir / "cohort.csv", cohort_rows)
    _publish_results(
        publish_dir,
        workdir,
        stats,
        coverage_rows,
        training_source_rows,
        scores,
        prediction_payloads,
        prediction_hashes,
        input_manifest,
        target_metadata,
    )
    print(
        json.dumps(
            {
                "scored_rows": len(scores),
                "country_method_summary": stats,
                "published_to": str(publish_dir),
            },
            indent=2,
        )
    )


def _publish_results(
    publish_dir: Path,
    workdir: Path,
    stats: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    training_source_rows: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    predictions: dict[str, dict[str, Any]],
    prediction_hashes: dict[str, str],
    input_manifest: dict[str, Any],
    target_metadata: dict[str, Any],
) -> None:
    publish_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "scores.csv",
        "site-scores.csv",
        "coverage.csv",
        "training-sources.csv",
        "predictions.csv",
        "cohort.csv",
    ):
        (publish_dir / name).write_bytes((workdir / name).read_bytes())
    for country in COUNTRIES:
        path = publish_dir / f"predictions-{country}.json"
        _json_write(path, predictions[country])
    cohort_counts = {
        country: {
            "candidate_samples": target_metadata[country]["candidate_samples"],
            "candidate_sites": len(target_metadata[country]["sites"]),
        }
        for country in COUNTRIES
    }
    lines = [
        "# Nordic country-held-out direct-pollen predictions",
        "",
        "This is a prior-exposed exploratory prediction of a closed 16-label, exact-name Neotoma pollen subcomposition. It predicts observed pollen composition; it is not an LRA reconstruction, measured vegetation estimate, or confirmatory test.",
        "",
        "The entire target country is omitted from each prediction's training set. Denmark, Finland and Norway contribute the source-backed physical site groups counted below; Sweden contributes the three previously admitted Neotoma training sites. Targets use selected sample-owned Neotoma ages and site coordinates only. Prediction files are saved and hashed before the scoring command reads held-out count profiles.",
        "",
        "The fixed methods are training mean, nearest site, inverse-distance-squared, and the existing CLR/WGS84 RBF-ridge (half-count smoothing on training cells, median positive training-distance scale, ridge 0.01). They are comparisons, not a Nordic-tuned winner search. No target-country outcome is used to choose taxa: the 16 literal labels are inherited from the earlier Swedish direct-pollen cohort.",
        "",
        "The exact axis is a closed subcomposition. A missing literal Neotoma NISP row is treated as an unreported zero cell under the documented Neotoma count-matrix workflow. All remaining pollen labels are outside the response and are not interpreted as absent vegetation. Coordinates for source polygon geometries use their WGS84 geometric centroids; source point geometries are retained as points.",
        "",
        "| Held-out country | Candidate samples | Candidate sites | Candidate bins | Positive 16-label bins | Predicted bins | Scored bins | Refused bins |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for country in COUNTRIES:
        country_coverage = [row for row in coverage_rows if row["country"] == country]
        candidate_bins = sum(
            row["candidate_age_count_bins"] for row in country_coverage
        )
        eligible_bins = sum(
            row["positive_closed_taxon_bins"] for row in country_coverage
        )
        predicted_bins = sum(row["predicted_bins"] for row in country_coverage)
        scored_bins = sum(row["scored_bins"] for row in country_coverage)
        refused_bins = candidate_bins - scored_bins
        lines.append(
            f"| {country} | {cohort_counts[country]['candidate_samples']} | {cohort_counts[country]['candidate_sites']} | {candidate_bins} | {eligible_bins} | {predicted_bins} | {scored_bins} | {refused_bins} |"
        )
    lines.extend(
        [
            "",
            "| Country | Method | Attempted predictions | Scored bins | Scored sites | Site-macro MAE | Site-macro Hellinger |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in stats:
        mae = (
            "—"
            if row["site_macro_mae_fraction"] is None
            else f"{row['site_macro_mae_fraction']:.6f}"
        )
        hellinger = (
            "—"
            if row["site_macro_hellinger"] is None
            else f"{row['site_macro_hellinger']:.6f}"
        )
        lines.append(
            f"| {row['country']} | {row['method']} | {row['attempted_predictions']} | {row['scored_bins']} | {row['scored_sites']} | {mae} | {hellinger} |"
        )
    lines.extend(
        [
            "",
            "Site-macro scores average bins within each physical site and then weight sites equally within country. Denmark has one physical site group and cannot estimate between-site Danish variation. Country-held-out scores are descriptive transfer results from this captured EPD subset, not evidence for all Nordic landscapes or all time periods. `coverage.csv` retains site-level age/count candidate bins and separates positive closed-axis outcomes, predicted bins, scored bins, empty/refused target outcomes, and eligible bins without a prediction.",
            "",
            "## Source and limits",
            "",
            "The Danish, Finnish, Norwegian and Swedish cohorts come from European Pollen Database datasets distributed through Neotoma. The [Neotoma source review](../../../../public/pollenomics-data/sources/neotoma.md) records EPD reuse under CC BY 4.0 with Neotoma, EPD, and original investigator attribution. Dataset identifiers, DOIs, and contributors are retained in `cohort.csv` and `training-sources.csv`. No PPE, fall-speed, basin-area, or vegetation-reference assumption is needed for observed-pollen prediction; those inputs remain blocked for LRA and measured-vegetation claims.",
            "",
            "All selected candidates have one source-owned comparable sample-age claim after the declared chronology rule: when several comparable claims exist, use the unique source-flagged default for its age type; otherwise refuse the sample. Neotoma permits one default chronology per age type, so a radiocarbon and a calibrated chronology can both be flagged without contradicting each other ([Neotoma chronology manual](https://open.neotomadb.org/manual/chronology-age-related-tables-1.html)). The corrected source projection removes false cross-age-type conflicts while retaining genuine same-age-type conflicts. Sample age type labels remain in the input profiles. Source uncertainty bounds vary by record and are not propagated into the exploratory fixed 500-year bins.",
            "",
            "Target bins lacking two positive-count training sites, bins with no positive count on the fixed 16-label axis, and predictions without target outcomes remain unscored; the CSV files retain the actual prediction and scoring denominators. Spatial coordinates from polygon geometry centroids are approximate source locations. No independent vegetation truth was used.",
            "",
            "## Reproduction",
            "",
            "From the repository root, run `PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src .venv/bin/python -m bijux_pollenomics_dev.source_completion.nordic_direct_pollen prepare --relational-root data/neotoma/relational --raw-root data/neotoma/raw/neotoma_pollen_dataset_downloads --workdir artifacts/nordic-direct-pollen`, then run `predict` separately for `DK`, `FI` and `NO`, then run `score` with `--relational-root data/neotoma/relational --workdir artifacts/nordic-direct-pollen --publish-dir docs/report/regions/nordic/direct-pollen`. The prediction commands do not read the held-out outcome inputs. Input and prediction hashes are retained in `manifest.json`.",
            "",
        ]
    )
    report_path = publish_dir / "RESULTS.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    _json_write(
        publish_dir / "manifest.json",
        {
            "schema_version": "nordic-direct-pollen-results.v1",
            "source_snapshot_id": SOURCE_SNAPSHOT,
            "input_identity": input_manifest,
            "prediction_sha256": prediction_hashes,
            "scores_sha256": _sha(publish_dir / "scores.csv"),
            "site_scores_sha256": _sha(publish_dir / "site-scores.csv"),
            "coverage_sha256": _sha(publish_dir / "coverage.csv"),
            "training_sources_sha256": _sha(publish_dir / "training-sources.csv"),
            "prediction_table_sha256": _sha(publish_dir / "predictions.csv"),
            "cohort_sha256": _sha(publish_dir / "cohort.csv"),
            "results_sha256": _sha(report_path),
            "prediction_counts": {
                country: len(predictions[country]["predictions"])
                for country in COUNTRIES
            },
            "scored_rows": len(scores),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--relational-root", type=Path, required=True)
    prepare_parser.add_argument("--raw-root", type=Path, required=True)
    prepare_parser.add_argument("--workdir", type=Path, required=True)
    predict_parser = commands.add_parser("predict")
    predict_parser.add_argument("--country", choices=COUNTRIES, required=True)
    predict_parser.add_argument("--workdir", type=Path, required=True)
    score_parser = commands.add_parser("score")
    score_parser.add_argument("--relational-root", type=Path, required=True)
    score_parser.add_argument("--workdir", type=Path, required=True)
    score_parser.add_argument("--publish-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.relational_root, args.raw_root, args.workdir)
    elif args.command == "predict":
        predict_country(args.workdir, args.country)
    else:
        score(args.relational_root, args.workdir, args.publish_dir)


if __name__ == "__main__":
    main()
