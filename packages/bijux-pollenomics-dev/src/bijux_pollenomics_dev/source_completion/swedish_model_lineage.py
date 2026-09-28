"""Trace observed Swedish pollen sites into published LandClim grid metadata."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

COHORT = Path("docs/report/pollen-reconstruction/swedish-direct-pollen/cohort.csv")
SITES = Path("data/landclim/normalized/nordic_pollen_site_sequences.geojson")
SYNTHESIS = Path("docs/report/countries/sweden/sweden_land_use_synthesis_v66.csv")


def _identity(path: Path, repository: Path) -> dict[str, str]:
    return {
        "path": str(path.relative_to(repository)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    latitude = math.radians(lat_b - lat_a)
    longitude = math.radians(lon_b - lon_a)
    a = (
        math.sin(latitude / 2) ** 2
        + math.cos(math.radians(lat_a))
        * math.cos(math.radians(lat_b))
        * math.sin(longitude / 2) ** 2
    )
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def publish(repository: Path, output: Path) -> dict[str, Any]:
    """Report exact metadata overlaps without asserting sample-level identity."""
    repository = repository.resolve()
    cohort_path, sites_path, synthesis_path = (
        repository / COHORT,
        repository / SITES,
        repository / SYNTHESIS,
    )
    with cohort_path.open(newline="", encoding="utf-8") as stream:
        cohort = list(csv.DictReader(stream))
    site_features = json.loads(sites_path.read_text(encoding="utf-8"))["features"]
    with synthesis_path.open(newline="", encoding="utf-8") as stream:
        synthesis = list(csv.DictReader(stream))
    if len(cohort) != 3 or len(synthesis) != 150:
        raise ValueError("Swedish cohort or six-target synthesis changed")
    features = {
        feature["properties"]["record_id"]: feature
        for feature in site_features
        if feature["properties"]["record_id"].startswith("937075:")
    }
    sites: list[dict[str, object]] = []
    for row in cohort:
        key = f"937075:{row['collection_unit'].replace('ABBO', 'ABB')}"
        feature = features[key]
        properties = feature["properties"]
        popup = {item["label"]: item["value"] for item in properties["popup_rows"]}
        lon, lat = feature["geometry"]["coordinates"]
        distance = _distance_km(
            float(row["latitude_wgs84"]), float(row["longitude_wgs84"]), lat, lon
        )
        matching_count = int(popup["Pollen samples"]) == int(row["sample_count"])
        if not matching_count or distance > 0.001 or popup["Sequence file"] != key[7:]:
            raise ValueError(f"LandClim/Neotoma site metadata mismatch: {key}")
        sites.append(
            {
                "neotoma_site_id": int(row["neotoma_site_id"]),
                "neotoma_dataset_id": int(row["neotoma_dataset_id"]),
                "landclim_record_id": key,
                "site": row["site"],
                "sample_count_each": int(row["sample_count"]),
                "coordinate_distance_km": round(distance, 6),
                "landclim_grid_record_id": int(popup["LCGRID_ID"]),
                "landclim_access_marker": popup["Access posture"],
                "conclusion": "same_site_metadata_not_authenticated_sample_identity",
            }
        )
    by_target: dict[str, dict[str, str]] = {}
    for row in synthesis:
        name = row["target_name"]
        if name in by_target:
            if (
                row["landclim_grid_record_id"]
                != by_target[name]["landclim_grid_record_id"]
            ):
                raise ValueError(f"Target grid changes with time: {name}")
        else:
            by_target[name] = row
    if len(by_target) != 6:
        raise ValueError("Expected six southern Sweden targets")
    targets: list[dict[str, object]] = []
    for name, row in sorted(by_target.items()):
        grid = int(row["landclim_grid_record_id"])
        matching = [site for site in sites if site["landclim_grid_record_id"] == grid]
        targets.append(
            {
                "target": name,
                "landclim_grid_record_id": grid,
                "shared_input_site_records": [
                    site["landclim_record_id"] for site in matching
                ],
                "distances_to_matching_sites_km": {
                    str(site["landclim_record_id"]): round(
                        _distance_km(
                            float(row["latitude"]),
                            float(row["longitude"]),
                            float(cohort_row["latitude_wgs84"]),
                            float(cohort_row["longitude_wgs84"]),
                        ),
                        3,
                    )
                    for site in matching
                    for cohort_row in cohort
                    if int(cohort_row["neotoma_site_id"]) == site["neotoma_site_id"]
                },
                "independent_model_validation": (
                    "unestablished_input_reuse_risk" if matching else "unassessed"
                ),
            }
        )
    report: dict[str, Any] = {
        "schema_version": "swedish-pollen-landclim-input-lineage.v1",
        "question": "Can the current southern Sweden LandClim model rows independently validate the Swedish Neotoma pollen sites?",
        "answer": "No independent validation is established: the LandClim metadata place the matching BUS and BOKE site records in the grid used by five synthesis targets. Exact sample-level reuse and model influence require separate source proof.",
        "matched_site_count": len(sites),
        "target_count": len(targets),
        "targets_sharing_bus_boke_grid": sum(
            bool(target["shared_input_site_records"]) for target in targets
        ),
        "sites": sites,
        "targets": targets,
        "source_roles": {
            "neotoma": "observed pollen site/count metadata",
            "landclim_sites": "published model input site metadata; not independently measured vegetation",
            "synthesis": "modeled cover by published grid/time window",
        },
        "inputs": [
            _identity(path, repository)
            for path in (cohort_path, sites_path, synthesis_path)
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args.repository, args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
