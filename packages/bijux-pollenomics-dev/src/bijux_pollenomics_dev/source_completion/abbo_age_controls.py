"""Reconcile published ABBO radiocarbon dates with Neotoma chronology controls."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
from typing import Any

SOURCE_SHA256 = "9717f1600c62659a33a4901da16c6b5fc3dac7cc47f8c005e54909568929704d"
SOURCE_MEMBER = "epd/pangaea/abbo-age-determination-pangaea-740080.tsv"
NEOTOMA = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json")
PROFILE = Path("docs/report/source-relations/neotoma/abbo-profile/report.json")
EXPECTED_COLUMNS = (
    "Depth sed [m]",
    "Thick [mm]",
    "Dated material",
    "Age dated [ka BP]",
    "Age e + [ka +]",
    "Age e - [ka -]",
    "Lab no",
)


def _identity(path: Path, repository: Path | None = None) -> dict[str, str]:
    return {
        "path": str(path.relative_to(repository)) if repository else SOURCE_MEMBER,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _published_dates(path: Path) -> list[dict[str, str]]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Published ABBO age source hash changed")
    text = raw.decode("utf-8")
    if (
        "10.1594/PANGAEA.740080" not in text
        or "Creative Commons Attribution-NonCommercial 3.0" not in text
    ):
        raise ValueError("Published ABBO age citation or license changed")
    table = text.split("*/\n", maxsplit=1)
    if len(table) != 2:
        raise ValueError("Published ABBO age table is missing")
    reader = csv.DictReader(io.StringIO(table[1]), delimiter="\t")
    if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
        raise ValueError("Published ABBO age columns changed")
    rows = list(reader)
    if len(rows) != 6 or len({row["Lab no"] for row in rows}) != 6:
        raise ValueError("Published ABBO age control count changed")
    return rows


def publish(repository: Path, source: Path, output: Path) -> dict[str, Any]:
    """Check raw dates exactly and retain only Neotoma-derived control values."""
    repository = repository.resolve()
    dates = _published_dates(source)
    neotoma_path, profile_path = repository / NEOTOMA, repository / PROFILE
    raw = json.loads(neotoma_path.read_text(encoding="utf-8"))
    site = next(
        row["site"]
        for row in raw["rows"]
        if row["site"]["dataset"]["datasetid"] == 19913
    )
    unit = site["collectionunit"]
    chronology = unit["chronologies"][0]["chronology"]
    metadata = chronology["chronology"]
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if (
        site["siteid"] != 13338
        or unit["handle"] != "ABBO"
        or chronology["chronologyid"] != 11516
        or metadata["agemodel"] != "linear interpolation"
        or metadata["modelagetype"] != "Calibrated radiocarbon years BP"
        or profile["matched_sample_depths"] != 107
        or profile["source_core_handle"] != "ABBO"
    ):
        raise ValueError("Neotoma ABBO chronology or confirmed profile changed")
    samples = unit["dataset"]["samples"]
    if len(samples) != 107 or any(
        len(sample["ages"]) != 1
        or sample["ages"][0]["chronologyid"] != 11516
        or sample["ages"][0]["agetype"] != "Calibrated radiocarbon years BP"
        or sample["ages"][0]["ageolder"] is not None
        or sample["ages"][0]["ageyounger"] is not None
        for sample in samples
    ):
        raise ValueError("Neotoma ABBO sample age or uncertainty contract changed")
    controls = {
        control["geochron"]["labnumber"]: control
        for control in chronology["chroncontrols"]
        if control["geochron"]["labnumber"] is not None
    }
    if len(controls) != 6 or len(chronology["chroncontrols"]) != 7:
        raise ValueError("Neotoma ABBO age control set changed")
    comparisons: list[dict[str, object]] = []
    for date in dates:
        lab = date["Lab no"]
        if lab not in controls:
            raise ValueError(f"Published ABBO lab number missing in Neotoma: {lab}")
        control = controls[lab]
        geochron = control["geochron"]
        expected = (
            Decimal(date["Depth sed [m]"]) * 100,
            Decimal(date["Thick [mm]"]) / 10,
            Decimal(date["Age dated [ka BP]"]) * 1000,
            Decimal(date["Age e + [ka +]"]) * 1000,
            Decimal(date["Age e - [ka -]"]) * 1000,
        )
        actual = tuple(
            Decimal(str(value))
            for value in (
                control["depth"],
                control["thickness"],
                geochron["geochronage"],
                geochron["geochronerrorolder"],
                geochron["geochronerroryounger"],
            )
        )
        if actual != expected:
            raise ValueError(f"Published/Neotoma ABBO date mismatch: {lab}")
        if geochron["agetype"] != "Radiocarbon years BP":
            raise ValueError(f"ABBO raw date age type changed: {lab}")
        comparisons.append(
            {
                "neotoma_chroncontrol_id": control["chroncontrolid"],
                "lab_number": lab,
                "depth_cm": control["depth"],
                "radiocarbon_bp": geochron["geochronage"],
                "radiocarbon_error_older_bp": geochron["geochronerrorolder"],
                "radiocarbon_error_younger_bp": geochron["geochronerroryounger"],
                "calibrated_control_bp": control["chroncontrolage"],
                "calibrated_younger_limit_bp": control["agelimityounger"],
                "calibrated_older_limit_bp": control["agelimitolder"],
                "published_date_fields_match": True,
            }
        )
    comparisons.sort(key=lambda row: float(str(row["depth_cm"])))
    top = next(
        control
        for control in chronology["chroncontrols"]
        if control["chroncontroltype"] == "Core top"
    )
    report: dict[str, Any] = {
        "schema_version": "abbo-published-neotoma-age-control-correspondence.v1",
        "dataset_id": 19913,
        "site_id": 13338,
        "chronology_id": 11516,
        "chronology_name": metadata["chronologyname"],
        "neotoma_age_model": metadata["agemodel"],
        "neotoma_model_age_unit": metadata["modelagetype"],
        "published_radiocarbon_date_count": len(dates),
        "exact_depth_lab_age_error_matches": len(comparisons),
        "neotoma_core_top": {
            "depth_cm": top["depth"],
            "age_cal_bp": top["chroncontrolage"],
            "independent_published_date": False,
        },
        "sample_age_uncertainty_bounds": "not supplied in Neotoma sample ages",
        "sample_count_without_age_uncertainty_bounds": len(samples),
        "pollen_profile_sample_depths_matched": profile["matched_sample_depths"],
        "pangaea_license": "CC-BY-NC-3.0; raw table retained outside product repository",
        "lra_admitted_samples": 0,
        "controls": comparisons,
        "inputs": [
            _identity(source),
            _identity(neotoma_path, repository),
            _identity(profile_path, repository),
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
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args.repository, args.source, args.output)))


if __name__ == "__main__":
    main()
