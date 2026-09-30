"""Reconcile Laihalampi source metadata without opening pollen outcomes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from bijux_pollenomics.collection.intake.workbooks import read_xlsx_sheet_rows
from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    read_landclim_study_inventory,
)
from pyproj import Geod


LANDCLIM_I_SHA256 = "851774cece8fb87928028a0da0e9ab7314ac083fdcca2d1565c00a7aa24d7081"
LANDCLIM_II_SHA256 = "2d4a0cf1401e36c2606f7761cecc85c4bbc15272460c2a4926cb1702d4565ebb"
COHORT_SHA256 = "03fc3f0522c2e65082ea245785db84a76431eb6a099b81ce0358fbe9e249dc32"
SITE = "neotoma:site:28072"
DATASET = "neotoma:dataset:52082"
CORE = "neotoma:collection-unit:37925"
CALIBRATED = "neotoma:chronology:37925:37160"
RADIOCARBON = "neotoma:chronology:37925:37159"
SURFACES = (
    "sites",
    "datasets",
    "collection_units",
    "chronologies",
    "samples",
    "age_claims",
    "chronology_controls",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verified(path: Path, expected: str) -> Path:
    if sha256(path) != expected:
        raise ValueError(f"Source identity changed: {path}")
    return path


def one(rows: list[dict], **fields: str) -> dict:
    matches = [
        r for r in rows if all(r.get(key) == value for key, value in fields.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one source row for {fields}, found {len(matches)}")
    return matches[0]


def produce(repository: Path) -> dict:
    landclim = repository / "data/landclim/raw"
    verified(landclim / "landclim_i_land_cover_types.xlsx", LANDCLIM_I_SHA256)
    verified(landclim / "landclim_ii_site_metadata.xlsx", LANDCLIM_II_SHA256)
    source_i = read_xlsx_sheet_rows(
        landclim / "landclim_i_land_cover_types.xlsx", "SiteData"
    )
    if source_i[0][6] != "Area of site (ha) (*Actual size)":
        raise ValueError("LandClim I basin-area unit changed")
    row_i = [r for r in source_i if len(r) > 6 and r[:2] == ["FIN", "Laihalampi"]]
    if len(row_i) != 1 or row_i[0][6] != "25.50*":
        raise ValueError("LandClim I Laihalampi area changed")
    inventory = read_landclim_study_inventory(landclim)
    row_ii = one(
        [{v.column: v.raw for v in record.values} for record in inventory.records],
        SiteName="Laihalampi",
        Country="Finland",
    )
    expected = ("LAIH", "lake", "150", "24", "285", "Authors chronology", "R")
    observed = tuple(
        row_ii[key]
        for key in (
            "csvfilename",
            "siteType",
            "nPollenSamples",
            "nTWs",
            "siteradius",
            "chronologySource",
            "DataRestricted/NotRestriced",
        )
    )
    if observed != expected:
        raise ValueError(f"LandClim II Laihalampi metadata changed: {observed}")
    cohort = verified(
        repository / "docs/report/regions/nordic/direct-pollen/cohort.csv",
        COHORT_SHA256,
    )
    with cohort.open(newline="", encoding="utf-8") as stream:
        selected = one(list(csv.DictReader(stream)), site_id=SITE, country="FI")
    if selected["candidate_samples"] != "150" or selected["dataset_ids"] != DATASET:
        raise ValueError("Finnish selected source cohort changed")

    relational = repository / "data/neotoma/relational"
    manifest_path = relational / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    identities = {"manifest.json": sha256(manifest_path)}
    rows = {}
    for surface in SURFACES:
        parts = manifest["surfaces"][surface]["parts"]
        if len(parts) != 1:
            raise ValueError(f"Unexpected Neotoma partition: {surface}")
        part = parts[0]
        source = verified(relational / part["path"], part["sha256"])
        identities[part["path"]] = part["sha256"]
        payload = json.loads(source.read_text(encoding="utf-8"))
        if len(payload["rows"]) != part["row_count"]:
            raise ValueError(f"Neotoma source row count changed: {surface}")
        rows[surface] = payload["rows"]
    site = one(rows["sites"], site_id=SITE)
    dataset = one(rows["datasets"], dataset_id=DATASET)
    core = one(rows["collection_units"], collection_unit_id=CORE)
    author = one(rows["chronologies"], chronology_id=CALIBRATED)
    if (
        dataset["collection_unit_id"] != CORE
        or core["site_id"] != SITE
        or core["source_payload"]["handle"] != "LAIH"
    ):
        raise ValueError("Neotoma physical core relation changed")
    if (
        author["source_payload"]["chronology"]["agemodel"]
        != "non-parametric weighted regression"
    ):
        raise ValueError("Neotoma calibrated age model changed")
    samples = [r for r in rows["samples"] if r["dataset_id"] == DATASET]
    depths = sorted(r["source_depth"] for r in samples)
    if len(samples) != 150 or depths != list(range(1, 151)):
        raise ValueError("Neotoma 1-cm source sample series changed")
    sample_ids = {r["sample_id"] for r in samples}
    ages = [r for r in rows["age_claims"] if r["subject_id"] in sample_ids]
    if (
        len(ages) != 300
        or sum(
            r["chronology_id"] == CALIBRATED
            and r["comparability_status"] == "comparable"
            for r in ages
        )
        != 150
        or sum(
            r["chronology_id"] == RADIOCARBON
            and r["comparability_status"] == "context_only"
            for r in ages
        )
        != 150
    ):
        raise ValueError("Neotoma sample chronology support changed")
    controls = [
        r["source_payload"]
        for r in rows["chronology_controls"]
        if r["chronology_id"] == CALIBRATED
    ]
    labs = sorted(
        r["geochron"]["labnumber"] for r in controls if r["geochron"]["labnumber"]
    )
    if (
        labs != ["Hela-4417", "Hela-4418", "Hela-4419", "Hela-4420", "Hela-4459"]
        or len(controls) != 6
    ):
        raise ValueError("Neotoma calibrated control support changed")
    location = json.loads(site["source_payload"]["geography"])["coordinates"]
    _, _, separation = Geod(ellps="WGS84").inv(
        float(row_ii["londd"]), float(row_ii["latdd"]), *location
    )
    radius = float(row_ii["siteradius"])
    return {
        "schema_version": "laihalampi-source-reconciliation.v1",
        "site_id": SITE,
        "dataset_id": DATASET,
        "collection_unit_id": CORE,
        "paper_doi": "10.1016/S0277-3791(02)00189-0",
        "source_sha256": {
            "landclim_i": LANDCLIM_I_SHA256,
            "landclim_ii": LANDCLIM_II_SHA256,
            "cohort": COHORT_SHA256,
            **identities,
        },
        "landclim_ii_samples": 150,
        "neotoma_source_samples": len(samples),
        "neotoma_source_depth_cm": [depths[0], depths[-1]],
        "neotoma_comparable_calibrated_sample_ages": 150,
        "neotoma_context_only_radiocarbon_sample_ages": 150,
        "neotoma_calibrated_controls": len(controls),
        "neotoma_radiocarbon_control_labs": labs,
        "neotoma_has_assumed_core_top_control": any(
            r["depth"] == 0 and not r["geochron"]["labnumber"] for r in controls
        ),
        "landclim_ii_neotoma_point_separation_m": separation,
        "landclim_i_reported_area_ha": 25.5,
        "landclim_ii_radius_unit_unstated": radius,
        "conditional_area_if_radius_metres_ha": math.pi * radius**2 / 10000,
        "lra_admitted_samples": 0,
        "reason": "The named physical core and 150-sample lineage agree, but the exact LandClim selected ages, historical basin geometry, LRA denominator/taxon/PPE use and analytical rights remain unqualified.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Absent output destination required")
    result = produce(args.repository)
    args.output.mkdir(parents=True)
    (args.output / "report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
