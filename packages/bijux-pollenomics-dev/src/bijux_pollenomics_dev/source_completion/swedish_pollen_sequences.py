"""Publish source-owned sample trajectories for the admitted Swedish EPD cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.source_completion.swedish_direct_pollen import DATASETS


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build(data_root: Path, destination: Path) -> dict[str, Any]:
    """Keep source identities and observed NISP separate from derived fractions."""
    if not destination.exists():
        destination.mkdir(parents=True)
    if any(destination.iterdir()):
        raise ValueError("sequence destination must be empty")
    parts = sorted({spec["part"] for spec in DATASETS.values()})
    source_hashes = {part: _sha(data_root / part) for part in parts}
    sites: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    controls: list[dict[str, Any]] = []
    found: set[str] = set()
    for part in parts:
        payload = json.loads((data_root / part).read_text(encoding="utf-8"))
        for source_index, wrapper in enumerate(payload["rows"]):
            site = wrapper["site"]
            collection = site["collectionunit"]
            dataset = collection["dataset"]
            dataset_id = str(dataset["datasetid"])
            if dataset_id not in DATASETS:
                continue
            spec = DATASETS[dataset_id]
            if (
                dataset_id in found
                or str(site["siteid"]) != spec["site_id"]
                or spec["part"] != part
                or dataset["datasettype"] != "pollen"
                or dataset["database"] != "European Pollen Database"
                or len(collection["chronologies"]) != 1
            ):
                raise ValueError(f"source identity or chronology changed: {dataset_id}")
            found.add(dataset_id)
            chronology = collection["chronologies"][0]["chronology"]
            chronology_id = collection["defaultchronology"]
            model = chronology["chronology"]
            if model["modelagetype"] != "Calibrated radiocarbon years BP":
                raise ValueError(f"unusable chronology model: {dataset_id}")
            longitude, latitude = json.loads(site["geography"])["coordinates"]
            locator = f"{part}#rows/{source_index}/site/collectionunit/dataset"
            site_row = {
                "dataset_id": dataset_id,
                "site_id": str(site["siteid"]),
                "site_name": site["sitename"],
                "longitude": longitude,
                "latitude": latitude,
                "collection_unit_id": str(collection["collectionunitid"]),
                "collection_unit_handle": collection["handle"],
                "collection_date": collection["colldate"],
                "dataset_doi": dataset["doi"],
                "dataset_contributors": [
                    person["contactname"] for person in dataset["datasetpi"]
                ],
                "chronology_id": chronology_id,
                "chronology_name": model["chronologyname"],
                "age_model": model["agemodel"],
                "source_locator": locator,
            }
            sites.append(site_row)
            for control_index, control in enumerate(chronology["chroncontrols"]):
                controls.append(
                    {
                        "dataset_id": dataset_id,
                        "chronology_id": chronology_id,
                        "control_id": control["chroncontrolid"],
                        "depth": control["depth"],
                        "depth_unit": None,
                        "calibrated_age_bp": control["chroncontrolage"],
                        "younger_bp": control["agelimityounger"],
                        "older_bp": control["agelimitolder"],
                        "control_type": control["chroncontroltype"],
                        "geochron": control.get("geochron"),
                        "source_locator": (
                            f"{part}#rows/{source_index}/site/collectionunit/"
                            f"chronologies/0/chronology/chroncontrols/{control_index}"
                        ),
                    }
                )
            for sample_index, sample in enumerate(dataset["samples"]):
                age_rows = sample["ages"]
                if len(age_rows) != 1:
                    raise ValueError(f"ambiguous age for {dataset_id}/{sample_index}")
                age = age_rows[0]
                if (
                    age["chronologyid"] != chronology_id
                    or age["agetype"] != "Calibrated radiocarbon years BP"
                    or age["age"] is None
                ):
                    raise ValueError(
                        f"sample chronology changed: {dataset_id}/{sample_index}"
                    )
                sample_id = str(sample["sampleid"])
                sample_locator = f"{locator}/samples/{sample_index}"
                native = [
                    (datum_index, datum)
                    for datum_index, datum in enumerate(sample["datum"])
                    if datum["units"] == "NISP" and datum["elementtype"] == "pollen"
                ]
                if not native or any(
                    type(d["value"]) is not int or d["value"] < 0 for _, d in native
                ):
                    raise ValueError(
                        f"invalid NISP pollen for {dataset_id}/{sample_id}"
                    )
                identities = [(d["taxonid"], d["variablename"]) for _, d in native]
                if len(set(identities)) != len(identities):
                    raise ValueError(
                        f"duplicate native taxon for {dataset_id}/{sample_id}"
                    )
                denominator = sum(d["value"] for _, d in native)
                if denominator <= 0:
                    raise ValueError(
                        f"empty NISP denominator: {dataset_id}/{sample_id}"
                    )
                samples.append(
                    {
                        "dataset_id": dataset_id,
                        "site_id": site_row["site_id"],
                        "sample_id": sample_id,
                        "analysis_unit_id": sample["analysisunitid"],
                        "sample_name": sample["samplename"],
                        "depth": sample["depth"],
                        "depth_unit": None,
                        "calibrated_age_bp": age["age"],
                        "age_younger_bp": age["ageyounger"],
                        "age_older_bp": age["ageolder"],
                        "chronology_id": chronology_id,
                        "sample_analysts": [
                            p["contactname"] for p in sample["sampleanalyst"]
                        ],
                        "reported_nisp_denominator": denominator,
                        "quality_flags": ["sample_age_bounds_missing"]
                        if age["ageyounger"] is None or age["ageolder"] is None
                        else [],
                        "source_locator": sample_locator,
                    }
                )
                for datum_index, datum in native:
                    observations.append(
                        {
                            "dataset_id": dataset_id,
                            "site_id": site_row["site_id"],
                            "sample_id": sample_id,
                            "calibrated_age_bp": age["age"],
                            "depth": sample["depth"],
                            "taxon_id": datum["taxonid"],
                            "taxon_native": datum["variablename"],
                            "count": datum["value"],
                            "unit": "NISP",
                            "denominator": denominator,
                            "percent_of_reported_pollen_nisp": 100
                            * datum["value"]
                            / denominator,
                            "source_denominator": None,
                            "source_locator": f"{sample_locator}/datum/{datum_index}",
                        }
                    )
    if found != set(DATASETS):
        raise ValueError(
            f"missing Swedish EPD datasets: {sorted(set(DATASETS) - found)}"
        )
    sites.sort(key=lambda row: row["dataset_id"])
    samples.sort(
        key=lambda row: (row["dataset_id"], row["calibrated_age_bp"], row["sample_id"])
    )
    observations.sort(
        key=lambda row: (
            row["dataset_id"],
            row["calibrated_age_bp"],
            row["sample_id"],
            row["taxon_id"],
        )
    )
    controls.sort(key=lambda row: (row["dataset_id"], row["depth"], row["control_id"]))
    _write(destination / "sites.json", sites)
    _write(destination / "samples.json", samples)
    _write(destination / "observations.json", observations)
    _write(destination / "chronology-controls.json", controls)
    features = []
    for site in sites:
        cohort = [
            row for row in observations if row["dataset_id"] == site["dataset_id"]
        ]
        ages = [row["calibrated_age_bp"] for row in cohort]
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [site["longitude"], site["latitude"]],
                },
                "properties": {
                    "dataset_id": site["dataset_id"],
                    "site_name": site["site_name"],
                    "sample_count": sum(
                        row["dataset_id"] == site["dataset_id"] for row in samples
                    ),
                    "observation_count": len(cohort),
                    "reported_pollen_nisp": sum(row["count"] for row in cohort),
                    "age_min_cal_bp": min(ages),
                    "age_max_cal_bp": max(ages),
                    "source_locator": site["source_locator"],
                },
            }
        )
    _write(
        destination / "map-summary.geojson",
        {"type": "FeatureCollection", "features": features},
    )
    manifest = {
        "schema_version": "swedish-native-pollen-sequences.v1",
        "source_files_sha256": source_hashes,
        "selection": "three declared Swedish EPD/Neotoma direct-pollen cohort datasets; all native NISP pollen rows",
        "denominator": "sum of reported native pollen NISP rows within each sample; no zero rows inferred",
        "age_posture": "sample-owned selected calibrated ages and source controls; no new age model or interpolation",
        "sample_count": len(samples),
        "observation_count": len(observations),
        "control_count": len(controls),
        "files_sha256": {
            name: _sha(destination / name)
            for name in (
                "sites.json",
                "samples.json",
                "observations.json",
                "chronology-controls.json",
                "map-summary.geojson",
            )
        },
    }
    _write(destination / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.data_root, args.destination), indent=2))


if __name__ == "__main__":
    main()
