"""Trace the Danish Solsø pollen cohort into two published source generations."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.spatial import SiteCoordinate
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km
from bijux_pollenomics.collection.intake.workbooks import read_xlsx_sheet_rows
from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    read_landclim_study_inventory,
)

from .nordic_direct_pollen import (
    _neotoma_candidates,
    _read_rows,
    _sha,
    _site_coordinate,
)

LANDCLIM_I = Path("data/landclim/raw/landclim_i_land_cover_types.xlsx")
LANDCLIM_II = Path("data/landclim/raw/landclim_ii_site_metadata.xlsx")
RELATIONAL = Path("data/neotoma/relational")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
COHORT = Path("docs/report/regions/nordic/direct-pollen/cohort.csv")
DIRECT_MANIFEST = Path("docs/report/regions/nordic/direct-pollen/manifest.json")
SITE_ID = "neotoma:site:3432"


def _required(row: dict[str, str | None], field: str) -> str:
    value = row.get(field)
    if not value:
        raise ValueError(f"LandClim II Solsø {field} is missing")
    return value


def _surface_rows(
    root: Path, manifest: dict[str, Any], hashes: dict[str, str], surface: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for part in manifest["surfaces"][surface]["parts"]:
        path = root / part["path"]
        digest = hashes.get(part["path"])
        if digest is None:
            digest = _sha(path)
        if digest != part["sha256"]:
            raise ValueError(f"Neotoma surface identity changed: {part['path']}")
        rows = _read_rows(path)
        if len(rows) != part["row_count"]:
            raise ValueError(f"Neotoma surface row count changed: {part['path']}")
        result.extend(rows)
    return result


def publish(repository: Path, output: Path) -> dict[str, Any]:
    """Retain source-owned area, core and age differences without LRA admission."""
    repository = repository.resolve()
    i_path = repository / LANDCLIM_I
    inventory = read_landclim_study_inventory(repository / LANDCLIM_I.parent)
    ii_records = [
        record
        for record in inventory.records
        if any(
            value.column == "csvfilename" and value.raw == "Solsoe"
            for value in record.values
        )
    ]
    if len(ii_records) != 1:
        raise ValueError("LandClim II Solsø sequence identity changed")
    ii_record = ii_records[0]
    ii = {value.column: value.raw for value in ii_record.values}
    if (
        ii["SiteName"] != "Solsø"
        or ii["Country"] != "Denmark"
        or ii["siteType"] != "lake"
    ):
        raise ValueError("LandClim II Solsø metadata changed")
    i_rows = read_xlsx_sheet_rows(i_path, "SiteData")
    i_records = [
        (number, row)
        for number, row in enumerate(i_rows, start=1)
        if number > 2 and len(row) > 6 and row[1] == "Solsø"
    ]
    if len(i_records) != 1 or i_records[0][1][0] != "DK":
        raise ValueError("LandClim I Solsø site identity changed")
    i_number, i_row = i_records[0]
    if i_rows[0][6] != "Area of site (ha) (*Actual size)":
        raise ValueError("LandClim I area unit changed")

    direct_manifest_path, cohort_path = (
        repository / DIRECT_MANIFEST,
        repository / COHORT,
    )
    direct_manifest = json.loads(direct_manifest_path.read_text(encoding="utf-8"))
    if _sha(cohort_path) != direct_manifest["cohort_sha256"]:
        raise ValueError("Nordic held-out cohort identity changed")
    with cohort_path.open(newline="", encoding="utf-8") as stream:
        danish_cohort = [
            row for row in csv.DictReader(stream) if row["country"] == "DK"
        ]
    if len(danish_cohort) != 1 or danish_cohort[0]["site_id"] != SITE_ID:
        raise ValueError("Danish held-out site identity changed")
    _, metadata, hashes, screen_hash, screen_denominators = _neotoma_candidates(
        repository / RELATIONAL, repository / RAW
    )
    identity = direct_manifest["input_identity"]
    if (
        hashes != identity["relational_file_sha256"]
        or screen_hash != identity["pollen_screen_sha256"]
        or screen_denominators != identity["source_screen_country_denominators"]
    ):
        raise ValueError("Nordic held-out source closure changed")
    selected_site = next(
        (site for site in metadata["DK"]["sites"] if site["site_id"] == SITE_ID),
        None,
    )
    if selected_site is None:
        raise ValueError("Solsø is absent from selected Danish source sites")
    selected_ids = set(selected_site["candidate_sample_ids"])
    if len(selected_ids) != int(danish_cohort[0]["candidate_samples"]):
        raise ValueError("Solsø selected sample count changed")

    relational_root = repository / RELATIONAL
    relational_manifest = json.loads(
        (relational_root / "manifest.json").read_text(encoding="utf-8")
    )
    site = next(
        row
        for row in _surface_rows(relational_root, relational_manifest, hashes, "sites")
        if row["site_id"] == SITE_ID
    )
    collections = {
        row["collection_unit_id"]: row
        for row in _surface_rows(
            relational_root, relational_manifest, hashes, "collection_units"
        )
        if row["site_id"] == SITE_ID
    }
    datasets = {
        row["dataset_id"]: row
        for row in _surface_rows(
            relational_root, relational_manifest, hashes, "datasets"
        )
        if row["site_id"] == SITE_ID
    }
    samples = [
        row
        for row in _surface_rows(
            relational_root, relational_manifest, hashes, "samples"
        )
        if row["site_id"] == SITE_ID
    ]
    if len(collections) != 2 or len(datasets) != 2 or len(samples) != 92:
        raise ValueError("Neotoma Solsø core or source-sample denominator changed")
    source_ids = {row["sample_id"] for row in samples}
    if not selected_ids <= source_ids or len(source_ids) != len(samples):
        raise ValueError("Selected Solsø samples do not belong to source cores")
    claims_by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in _surface_rows(
        relational_root, relational_manifest, hashes, "age_claims"
    ):
        if claim["subject_type"] == "sample" and claim["subject_id"] in source_ids:
            claims_by_sample[claim["subject_id"]].append(claim)
    excluded_ids = sorted(source_ids - selected_ids)
    if len(excluded_ids) != 1:
        raise ValueError("Solsø age-screen refusal denominator changed")
    excluded_claims = claims_by_sample[excluded_ids[0]]
    if (
        len(excluded_claims) != 2
        or Counter(c["comparability_status"] for c in excluded_claims)
        != {"refused": 1, "context_only": 1}
        or next(c for c in excluded_claims if c["comparability_status"] == "refused")[
            "admission_reason"
        ]
        != "negative_bp"
    ):
        raise ValueError("Solsø excluded sample age reason changed")
    published_age_bounds = (
        int(_required(ii, "TopBP")),
        int(_required(ii, "BotBP")),
    )
    if published_age_bounds[0] > published_age_bounds[1]:
        raise ValueError("LandClim II Solsø age range is reversed")
    calibrated_claims = [
        claim
        for sample_id in source_ids
        for claim in claims_by_sample[sample_id]
        if claim["calibration_status"] == "calibrated"
    ]
    if (
        len(calibrated_claims) != len(samples)
        or {claim["subject_id"] for claim in calibrated_claims} != source_ids
        or any(claim["source_age_value"] is None for claim in calibrated_claims)
    ):
        raise ValueError("Solsø calibrated sample-age denominator changed")
    within_age_span = [
        claim
        for claim in calibrated_claims
        if published_age_bounds[0]
        <= claim["source_age_value"]
        <= published_age_bounds[1]
    ]
    outside_age_span = sorted(
        (
            {
                "sample_id": claim["subject_id"],
                "collection_unit_id": claim["collection_unit_id"],
                "calibrated_age_bp": claim["source_age_value"],
            }
            for claim in calibrated_claims
            if not (
                published_age_bounds[0]
                <= claim["source_age_value"]
                <= published_age_bounds[1]
            )
        ),
        key=lambda row: row["sample_id"],
    )
    cores: list[dict[str, Any]] = []
    for dataset_id, dataset in sorted(datasets.items()):
        collection_id = dataset["collection_unit_id"]
        collection = collections[collection_id]
        members = [row for row in samples if row["dataset_id"] == dataset_id]
        chosen = [row for row in members if row["sample_id"] in selected_ids]
        if not chosen or len(chosen) != len(members) - sum(
            row["sample_id"] in excluded_ids for row in members
        ):
            raise ValueError("Solsø per-core sample count does not close")
        age_types = Counter(
            claim["source_age_type"]
            for row in chosen
            for claim in claims_by_sample[row["sample_id"]]
            if claim["comparability_status"] == "comparable"
        )
        if (
            sum(age_types.values()) != len(chosen)
            or dict(age_types)
            != selected_site["dataset_details"][dataset_id]["sample_age_bases"]
        ):
            raise ValueError(
                "Solsø selected core age basis differs from held-out cohort"
            )
        cores.append(
            {
                "dataset_id": dataset_id,
                "collection_unit_id": collection_id,
                "handle": collection["source_payload"]["handle"],
                "collection_date": collection["source_payload"]["colldate"],
                "depositional_environment": collection["source_payload"][
                    "depositionalenvironment"
                ],
                "source_sample_count": len(members),
                "selected_sample_count": len(chosen),
                "selected_depth_range_source_unit_unstated": [
                    min(row["source_depth"] for row in chosen),
                    max(row["source_depth"] for row in chosen),
                ],
                "selected_comparable_age_types": dict(sorted(age_types.items())),
                "source_dois": dataset["source_payload"]["doi"],
                "source_hiatus_note": collection["source_payload"]["notes"],
            }
        )
    if sum(row["selected_sample_count"] for row in cores) != len(selected_ids):
        raise ValueError("Solsø selected core count does not close")
    center = _site_coordinate(site["source_payload"]["geography"])
    published_center = SiteCoordinate(
        latitude=float(_required(ii, "latdd")),
        longitude=float(_required(ii, "londd")),
    )
    radius_number = float(_required(ii, "siteradius"))
    report: dict[str, Any] = {
        "schema_version": "solsoe-source-lineage.v1",
        "site_id": SITE_ID,
        "landclim_i": {
            "source_locator": f"landclim_i_land_cover_types.xlsx#SiteData!{i_number}",
            "reported_site_area_ha": float(i_row[6]),
            "source_archive": i_row[2],
            "source_basin_type": i_row[7],
        },
        "landclim_ii": {
            "source_locator": ii_record.source_locator,
            "reported_site_radius_unit_unstated": radius_number,
            "conditional_circular_area_if_radius_metres_ha": round(
                math.pi * radius_number**2 / 10000, 6
            ),
            "reported_pollen_samples": int(_required(ii, "nPollenSamples")),
            "reported_time_windows": int(_required(ii, "nTWs")),
            "reported_age_range_bp": [
                *published_age_bounds,
            ],
            "reported_chronology_source": ii["chronologySource"],
            "reported_access_marker": ii["DataRestricted/NotRestriced"],
            "grid_id": int(_required(ii, "LCGRID_ID")),
        },
        "neotoma": {
            "site_geometry_type": json.loads(site["source_payload"]["geography"])[
                "type"
            ],
            "source_site_area_unit_unstated": site["source_payload"]["area"],
            "site_centroid_to_landclim_ii_km": round(
                distance_km(center, published_center), 6
            ),
            "source_sample_count": len(samples),
            "held_out_selected_sample_count": len(selected_ids),
            "calibrated_age_span_comparison": {
                "source_age_type": "Calibrated radiocarbon years BP",
                "source_calibrated_sample_count": len(calibrated_claims),
                "within_published_bounds_inclusive": len(within_age_span),
                "within_published_bounds_by_core": dict(
                    sorted(
                        Counter(
                            claim["collection_unit_id"] for claim in within_age_span
                        ).items()
                    )
                ),
                "outside_published_bounds": outside_age_span,
                "within_bounds_excess_over_published_sample_count": len(within_age_span)
                - int(_required(ii, "nPollenSamples")),
            },
            "cores": cores,
            "excluded_sample": {
                "sample_id": excluded_ids[0],
                "source_depth_unit_unstated": next(
                    row["source_depth"]
                    for row in samples
                    if row["sample_id"] == excluded_ids[0]
                ),
                "age_claims": [
                    {
                        "age_type": claim["source_age_type"],
                        "age": claim["source_age_value"],
                        "younger": claim["source_age_younger"],
                        "comparability_status": claim["comparability_status"],
                        "admission_reason": claim["admission_reason"],
                    }
                    for claim in sorted(
                        excluded_claims, key=lambda claim: claim["source_age_type"]
                    )
                ],
            },
        },
        "lra_admitted_samples": 0,
        "interpretation": "Published Solsø site metadata and Neotoma cores share a close site lineage. Applying the published 10–11659 BP age bounds to all 92 Neotoma calibrated sample ages retains 90, still 11 more than the published 79; this conditional screen cannot explain the denominator and does not identify the author chronology or input subset. The reported LandClim I area and conditional LandClim II radius arithmetic are not sample-age basin boundaries.",
        "inputs": [
            {"path": str(LANDCLIM_I), "sha256": _sha(i_path)},
            {"path": str(LANDCLIM_II), "sha256": inventory.workbook_sha256},
            {"path": str(COHORT), "sha256": _sha(cohort_path)},
            {"path": str(DIRECT_MANIFEST), "sha256": _sha(direct_manifest_path)},
            {
                "path": str(RELATIONAL / "manifest.json"),
                "sha256": hashes["manifest.json"],
            },
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
    report = publish(args.repository, args.output)
    print(json.dumps({"cores": len(report["neotoma"]["cores"])}))


if __name__ == "__main__":
    main()
