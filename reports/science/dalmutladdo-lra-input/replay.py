"""Reconcile Dalmutladdo source metadata and published age controls."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from bijux_pollenomics.collection.intake.workbooks import read_xlsx_sheet_rows
from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    read_landclim_study_inventory,
)
from pyproj import Geod


PAPER_SHA256 = "6c7a3c0deb6c38ee487f16e78a48e8be7ce9d5803e78f90bfd945b73e5b46121"
LANDCLIM_I_SHA256 = "851774cece8fb87928028a0da0e9ab7314ac083fdcca2d1565c00a7aa24d7081"
LANDCLIM_II_SHA256 = "2d4a0cf1401e36c2606f7761cecc85c4bbc15272460c2a4926cb1702d4565ebb"
COHORT_SHA256 = "03fc3f0522c2e65082ea245785db84a76431eb6a099b81ce0358fbe9e249dc32"
SITE_ID = "neotoma:site:13388"
DATASET_ID = "neotoma:dataset:20034"
CORE_ID = "neotoma:collection-unit:14989"
AUTHOR_CHRONOLOGY = "neotoma:chronology:14989:11601"
EPD_CHRONOLOGY = "neotoma:chronology:14989:11600"
CONTROL = re.compile(
    r"^\s*(\d+)–(\d+)\s+(Hela-\d+)\s+(.+?)\s+"
    r"(\d+)\x03(\d+)\s+(\d+)\s+(\d+)–(\d+)\s*$"
)
SURFACES = (
    "sites",
    "datasets",
    "collection_units",
    "chronologies",
    "samples",
    "age_claims",
    "chronology_controls",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def verified(path: Path, expected: str) -> Path:
    if digest(path) != expected:
        raise ValueError(f"Source identity changed: {path}")
    return path


def unique(rows: list[dict], **fields: str) -> dict:
    selected = [
        row
        for row in rows
        if all(row.get(name) == value for name, value in fields.items())
    ]
    if len(selected) != 1:
        raise ValueError(f"Expected one source row for {fields}, found {len(selected)}")
    return selected[0]


def produce(repository: Path, paper: Path) -> tuple[list[dict], dict]:
    paper = verified(paper, PAPER_SHA256)
    landclim = repository / "data/landclim/raw"
    verified(landclim / "landclim_i_land_cover_types.xlsx", LANDCLIM_I_SHA256)
    verified(landclim / "landclim_ii_site_metadata.xlsx", LANDCLIM_II_SHA256)
    cohort_path = verified(
        repository / "docs/report/regions/nordic/direct-pollen/cohort.csv",
        COHORT_SHA256,
    )
    paper_text = subprocess.run(
        [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            "-sOutputFile=-",
            str(paper),
        ],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    if not re.search(r"Dalmutladdo\s+69°10.*?\s+355\s+7\.2\s+11\.5", paper_text):
        raise ValueError("Published Table 1 lake size or location changed")
    if (
        "72 from Dalmutladdo" not in paper_text
        or "at least 500 pollen grains" not in paper_text.lower()
    ):
        raise ValueError("Published sample count or counting rule changed")
    paper_controls = []
    for line in paper_text.splitlines():
        match = CONTROL.match(line)
        if match:
            low, high, lab, material, carbon, error, calendar, younger, older = (
                match.groups()
            )
            paper_controls.append(
                {
                    "lab": lab,
                    "depth_cm": (int(low) + int(high)) / 2,
                    "material": material.strip(),
                    "radiocarbon_bp": int(carbon),
                    "radiocarbon_error": int(error),
                    "published_calibrated_bp": int(calendar),
                    "published_younger_bp": int(younger),
                    "published_older_bp": int(older),
                }
            )
    if len(paper_controls) != 11 or len({r["lab"] for r in paper_controls}) != 11:
        raise ValueError("Published Table 2 control rows changed")

    inventory = read_landclim_study_inventory(landclim)
    ii = unique(
        [{v.column: v.raw for v in record.values} for record in inventory.records],
        SiteName="Dalmutladdo",
        Country="Norway",
    )
    if (
        ii["siteType"],
        ii["nPollenSamples"],
        ii["siteradius"],
        ii["chronologySource"],
        ii["DataRestricted/NotRestriced"],
    ) != ("lake", "72", "160", "Authors chronology", "NR"):
        raise ValueError("LandClim II Dalmutladdo source row changed")
    i_rows = read_xlsx_sheet_rows(
        landclim / "landclim_i_land_cover_types.xlsx", "SiteData"
    )
    if i_rows[0][6] != "Area of site (ha) (*Actual size)":
        raise ValueError("LandClim I basin-area unit changed")
    i_row = [r for r in i_rows if len(r) > 6 and r[:2] == ["NOR", "Dalmutladdo"]]
    if len(i_row) != 1 or i_row[0][6] != "8.00*":
        raise ValueError("LandClim I Dalmutladdo area changed")
    with cohort_path.open(newline="", encoding="utf-8") as source:
        cohort = unique(list(csv.DictReader(source)), site_id=SITE_ID, country="NO")
    if cohort["candidate_samples"] != "72" or cohort["dataset_ids"] != DATASET_ID:
        raise ValueError("Nordic selected source cohort changed")

    relational = repository / "data/neotoma/relational"
    manifest_path = relational / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    identities = {"manifest.json": digest(manifest_path)}
    rows = {}
    for surface in SURFACES:
        parts = manifest["surfaces"][surface]["parts"]
        if len(parts) != 1:
            raise ValueError(f"Unexpected Neotoma source partition: {surface}")
        part = parts[0]
        file = verified(relational / part["path"], part["sha256"])
        identities[part["path"]] = part["sha256"]
        payload = json.loads(file.read_text(encoding="utf-8"))
        if len(payload["rows"]) != part["row_count"]:
            raise ValueError(f"Neotoma source row count changed: {surface}")
        rows[surface] = payload["rows"]
    site = unique(rows["sites"], site_id=SITE_ID)
    dataset = unique(rows["datasets"], dataset_id=DATASET_ID)
    core = unique(rows["collection_units"], collection_unit_id=CORE_ID)
    author = unique(rows["chronologies"], chronology_id=AUTHOR_CHRONOLOGY)
    if dataset["collection_unit_id"] != CORE_ID or core["site_id"] != SITE_ID:
        raise ValueError("Neotoma site/core/dataset relation changed")
    if (
        core["source_payload"]["handle"] != "DALMUT"
        or author["source_payload"]["chronology"]["agemodel"]
        != "Weighted mixed effects regression procedure (Heegaard 2003)"
    ):
        raise ValueError("Neotoma physical core or author age model changed")
    samples = [r for r in rows["samples"] if r["dataset_id"] == DATASET_ID]
    if len(samples) != 72 or {r["collection_unit_id"] for r in samples} != {CORE_ID}:
        raise ValueError("Neotoma Dalmutladdo sample identity changed")
    sample_ids = {r["sample_id"] for r in samples}
    ages = [r for r in rows["age_claims"] if r["subject_id"] in sample_ids]
    if (
        len(ages) != 144
        or sum(
            r["chronology_id"] == AUTHOR_CHRONOLOGY
            and r["comparability_status"] == "comparable"
            for r in ages
        )
        != 72
        or sum(
            r["chronology_id"] == EPD_CHRONOLOGY
            and r["comparability_status"] == "context_only"
            for r in ages
        )
        != 72
    ):
        raise ValueError("Neotoma Dalmutladdo age-claim support changed")
    source_location = json.loads(site["source_payload"]["geography"])["coordinates"]
    _, _, separation_m = Geod(ellps="WGS84").inv(
        float(ii["londd"]), float(ii["latdd"]), *source_location
    )

    controls = [
        r["source_payload"]
        for r in rows["chronology_controls"]
        if r["chronology_id"] == AUTHOR_CHRONOLOGY
    ]
    by_lab = {
        r["geochron"]["labnumber"]: r for r in controls if r["geochron"]["labnumber"]
    }
    if len(by_lab) != 11:
        raise ValueError("Neotoma author chronology control count changed")
    compared = []
    for source in paper_controls:
        retained = by_lab[source["lab"]]
        geochron = retained["geochron"]
        source_fields_match = (
            source["depth_cm"] == retained["depth"]
            and source["radiocarbon_bp"] == geochron["geochronage"]
            and source["radiocarbon_error"] == geochron["geochronerrorolder"]
            and source["radiocarbon_error"] == geochron["geochronerroryounger"]
        )
        compared.append(
            {
                **source,
                "neotoma_calibrated_bp": retained["chroncontrolage"],
                "neotoma_younger_bp": retained["agelimityounger"],
                "neotoma_older_bp": retained["agelimitolder"],
                "source_fields_match": source_fields_match,
                "calibrated_centre_matches": source["published_calibrated_bp"]
                == retained["chroncontrolage"],
                "calibrated_bounds_match": (
                    source["published_younger_bp"],
                    source["published_older_bp"],
                )
                == (retained["agelimityounger"], retained["agelimitolder"]),
                "published_bounds_contain_centre": source["published_younger_bp"]
                <= source["published_calibrated_bp"]
                <= source["published_older_bp"],
            }
        )
    compared.sort(key=lambda row: row["depth_cm"])
    if not all(row["source_fields_match"] for row in compared):
        raise ValueError("Published radiocarbon source controls no longer match")
    radius_m = float(ii["siteradius"])
    result = {
        "schema_version": "dalmutladdo-source-reconciliation.v1",
        "site_id": SITE_ID,
        "dataset_id": DATASET_ID,
        "collection_unit_id": CORE_ID,
        "paper_doi": "10.1111/j.1502-3885.2004.tb01142.x",
        "paper_pdf_sha256": PAPER_SHA256,
        "landclim_i_sha256": LANDCLIM_I_SHA256,
        "landclim_ii_sha256": LANDCLIM_II_SHA256,
        "cohort_sha256": COHORT_SHA256,
        "neotoma_source_sha256": identities,
        "landclim_ii_pollen_samples": 72,
        "published_pollen_samples": 72,
        "neotoma_source_samples": len(samples),
        "neotoma_author_calibrated_age_claims": 72,
        "neotoma_epd_uncalibrated_context_claims": 72,
        "landclim_ii_neotoma_point_separation_m": separation_m,
        "landclim_ii_radius_unit_unstated": radius_m,
        "conditional_area_if_radius_metres_ha": math.pi * radius_m**2 / 10000,
        "landclim_i_reported_area_ha": 8.0,
        "paper_reported_area_ha": 7.2,
        "published_controls": len(compared),
        "radiocarbon_source_control_matches": sum(
            r["source_fields_match"] for r in compared
        ),
        "calibrated_centre_matches": sum(
            r["calibrated_centre_matches"] for r in compared
        ),
        "calibrated_bound_matches": sum(r["calibrated_bounds_match"] for r in compared),
        "published_bounds_excluding_printed_centre": [
            r["lab"] for r in compared if not r["published_bounds_contain_centre"]
        ],
        "lra_admitted_samples": 0,
        "reason": "Physical site, core and chronology lineage is strong; the three basin-size claims differ and none supplies age-specific basin geometry, while exact LRA taxon/PPE/denominator use remains unreviewed.",
    }
    return compared, result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Absent output destination required")
    controls, report = produce(args.repository, args.paper)
    args.output.mkdir(parents=True)
    with (args.output / "controls.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(controls[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(controls)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
