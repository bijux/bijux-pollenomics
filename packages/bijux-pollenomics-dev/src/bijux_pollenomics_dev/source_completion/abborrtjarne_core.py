"""Compare one Swedish Neotoma core lead with published LandClim metadata."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET
from zipfile import ZipFile

XML = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
SITE_ID = 13338
DATASET_ID = 19913
SAMPLE_ID = 173174
WORKBOOK_ROW = 968


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _workbook_row(path: Path, number: int) -> tuple[dict[str, str], dict[str, str]]:
    """Read only the published metadata sheet and its shared string table."""
    with ZipFile(path) as archive:
        strings = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        values = [
            "".join(node.text or "" for node in item.findall(".//x:t", XML))
            for item in strings.findall("x:si", XML)
        ]
        definitions = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        radius_definitions = []
        for row in definitions.findall(".//x:sheetData/x:row", XML):
            cells = {
                "".join(
                    letter for letter in cell.attrib["r"] if letter.isalpha()
                ): values[int(value.text)]
                if cell.attrib.get("t") == "s"
                else value.text
                for cell in row.findall("x:c", XML)
                if (value := cell.find("x:v", XML)) is not None
                and value.text is not None
            }
            if cells.get("A") == "siteradius":
                radius_definitions.append(cells.get("B"))
        if radius_definitions != ["radius of the site in meters"]:
            raise ValueError("Published site-radius unit is not documented in metres")
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet2.xml"))
    selected: dict[int, dict[str, str]] = {}
    for element in sheet.findall(".//x:sheetData/x:row", XML):
        row_number = int(element.attrib["r"])
        if row_number not in (1, number):
            continue
        cells = {}
        for cell in element.findall("x:c", XML):
            value = cell.find("x:v", XML)
            if value is None or value.text is None:
                continue
            column = "".join(letter for letter in cell.attrib["r"] if letter.isalpha())
            cells[column] = (
                values[int(value.text)] if cell.attrib.get("t") == "s" else value.text
            )
        selected[row_number] = cells
    if set(selected) != {1, number}:
        raise ValueError("Selected LandClim metadata row is absent")
    return selected[1], selected[number]


def _count_labels(datums: list[dict[str, Any]]) -> dict[str, int]:
    """Keep original NISP categories distinct; no pollen denominator is inferred."""
    totals: Counter[str] = Counter()
    for datum in datums:
        value = datum["value"]
        if (
            datum["units"] != "NISP"
            or isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise ValueError("Sample datum lacks exact nonnegative NISP count")
        category = (
            "pollen"
            if datum["element"] == datum["elementtype"] == "pollen"
            else "nonpollen"
            if datum["element"] == datum["elementtype"]
            and datum["element"] in {"spore", "stomate", "colony"}
            else None
        )
        if category is None:
            raise ValueError("Sample datum has unresolved source element labels")
        totals[f"{category}_observations"] += 1
        totals[f"{category}_count_sum"] += value
        if value == 0:
            totals[f"{category}_observed_zeros"] += 1
        if datum["variablename"] == "Indeterminable" and category == "pollen":
            totals["indeterminable_pollen_count"] += value
    return {
        key: totals[key]
        for key in (
            "pollen_observations",
            "pollen_count_sum",
            "pollen_observed_zeros",
            "nonpollen_observations",
            "nonpollen_count_sum",
            "nonpollen_observed_zeros",
            "indeterminable_pollen_count",
        )
    }


def _distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon_a, lat_a = map(radians, a)
    lon_b, lat_b = map(radians, b)
    angle = 2 * asin(
        sqrt(
            sin((lat_b - lat_a) / 2) ** 2
            + cos(lat_a) * cos(lat_b) * sin((lon_b - lon_a) / 2) ** 2
        )
    )
    return 6_371_008.8 * angle


def compare_core(
    raw_part: Path,
    raw_manifest: Path,
    workbook: Path,
    workbook_receipt: Path,
    count_mass: Path,
    projection: Path,
) -> dict[str, object]:
    """State observed agreements and disagreements without admitting a core join."""
    raw_index = json.loads(raw_manifest.read_text())
    part = next(
        item
        for item in raw_index["parts"]
        if DATASET_ID in item["downloaded_dataset_ids"]
    )
    if part["filename"] != raw_part.name or part["part_number"] != 4:
        raise ValueError("Neotoma dataset is outside the selected raw part")
    raw = json.loads(raw_part.read_text())
    if (
        raw["part_number"] != 4
        or raw["downloaded_dataset_ids"] != part["downloaded_dataset_ids"]
    ):
        raise ValueError("Neotoma raw part does not match its manifest")
    sites = [
        row["site"]
        for row in raw["rows"]
        if row["site"]["dataset"]["datasetid"] == DATASET_ID
    ]
    if len(sites) != 1 or sites[0]["siteid"] != SITE_ID:
        raise ValueError("Abborrtjärnen Neotoma dataset/site identity differs")
    site = sites[0]
    core = site["collectionunit"]
    dataset = core["dataset"]
    samples = dataset["samples"]
    selected = [sample for sample in samples if sample["sampleid"] == SAMPLE_ID]
    if len(selected) != 1:
        raise ValueError("Selected Neotoma sample is absent or repeated")
    sample = selected[0]
    counts = _count_labels(sample["datum"])
    mass = json.loads(count_mass.read_text())
    mass_rows = [
        row
        for row in mass["sample_rows"]
        if row["sample_id"] == f"neotoma:sample:{SAMPLE_ID}"
    ]
    if (
        len(mass_rows) != 1
        or mass["lra_accepted_samples"] != 0
        or mass_rows[0]["known_compatible_pollen_denominator_status"] != "not_evaluated"
        or len(mass_rows[0]["source_unit_partitions"]) != 1
    ):
        raise ValueError("Retained Neotoma count-mass receipt differs")
    unit = mass_rows[0]["source_unit_partitions"][0]
    if (
        unit["source_unit"] != "NISP"
        or counts["pollen_observations"] != unit["pollen_count_observations"]
        or counts["pollen_count_sum"] != unit["pollen_exact_count_sum"]
        or counts["nonpollen_observations"] != unit["nonpollen_count_observations"]
        or counts["nonpollen_count_sum"] != unit["nonpollen_exact_count_sum"]
    ):
        raise ValueError("Raw Neotoma counts and retained mass do not reconcile")
    prerequisite = json.loads(projection.read_text())
    selected_age = [
        row
        for row in prerequisite["chronology_rows"]
        if row["sample_id"] == f"neotoma:sample:{SAMPLE_ID}"
    ]
    if (
        len(selected_age) != 1
        or selected_age[0]["site_id"] != f"neotoma:site:{SITE_ID}"
        or selected_age[0]["chronology_disposition"] != "not_evaluated"
        or len(selected_age[0]["candidate_age_claims"]) != 1
        or prerequisite["denominators"]["accepted_samples"] != 0
        or mass["source_snapshot_id"]
        != prerequisite["source_identities"]["source_snapshot_id"]
    ):
        raise ValueError("Retained chronology or source identity differs")
    age = selected_age[0]["candidate_age_claims"][0]["source_claim"]
    if (
        len(sample["ages"]) != 1
        or sample["ages"][0]["age"] != age["source_age_value"]
        or sample["ages"][0]["chronologyid"]
        != int(age["chronology_id"].rsplit(":", 1)[1])
    ):
        raise ValueError("Raw and projected chronology claims differ")
    receipt = json.loads(workbook_receipt.read_text())
    asset = next(
        item
        for item in receipt["assets"]
        if item["filename"] == workbook.name and item["dataset_id"] == "937075"
    )
    if _digest(workbook) != asset["sha256"]:
        raise ValueError("Pinned LandClim metadata workbook differs")
    header, published = _workbook_row(workbook, WORKBOOK_ROW)
    if (
        [header.get(column) for column in ("A", "B", "C", "D", "L", "N", "O", "Q")]
        != [
            "SiteName",
            "csvfilename",
            "siteType",
            "siteradius",
            "nPollenSamples",
            "TopBP",
            "BotBP",
            "chronologySource",
        ]
        or published["A"] != site["sitename"]
        or published["B"] != "ABB"
        or published["I"] != "Sweden"
        or int(published["L"]) != len(samples)
    ):
        raise ValueError("Published Abborrtjärnen metadata axes differ")
    geometry = json.loads(site["geography"])
    if (
        geometry["type"] != "Point"
        or geometry["crs"]["properties"]["name"] != "EPSG:4326"
    ):
        raise ValueError("Neotoma geometry lacks the declared point CRS")
    coordinates = geometry["coordinates"]
    if len(coordinates) != 2:
        raise ValueError("Neotoma point coordinate axis differs")
    neotoma_point = float(coordinates[0]), float(coordinates[1])
    published_point = float(published["E"]), float(published["F"])
    distance = _distance_m(neotoma_point, published_point)
    if distance > 1:
        raise ValueError("Published and Neotoma points differ beyond one metre")
    raw_range = dataset["agerange"]
    if (
        len(raw_range) != 1
        or raw_range[0]["units"] != "Calibrated radiocarbon years BP"
    ):
        raise ValueError("Neotoma dataset age-range units differ")
    return {
        "schema_version": "swedish-abborrtjarne-core-correspondence.v1",
        "neotoma_site_id": f"neotoma:site:{SITE_ID}",
        "neotoma_dataset_id": f"neotoma:dataset:{DATASET_ID}",
        "neotoma_sample_id": f"neotoma:sample:{SAMPLE_ID}",
        "neotoma_dataset_doi": dataset["doi"],
        "neotoma_core_handle": core["handle"],
        "neotoma_core_location": core["location"],
        "neotoma_site_description": site["sitedescription"],
        "neotoma_downloaded_sample_count": len(samples),
        "neotoma_dataset_age_range": raw_range[0],
        "sample_candidate_age": {
            "value_bp": age["source_age_value"],
            "younger_bp": age["source_age_younger"],
            "older_bp": age["source_age_older"],
            "chronology_name": age["chronology_name"],
            "disposition": "not_evaluated",
        },
        "sample_counts": counts,
        "landclim_metadata_row": WORKBOOK_ROW,
        "landclim_sequence": published["B"],
        "landclim_site_type": published["C"],
        "landclim_site_radius_m": int(published["D"]),
        "landclim_sample_count": int(published["L"]),
        "landclim_top_bp_label": published["N"],
        "landclim_bottom_bp_label": published["O"],
        "landclim_chronology_source": published["Q"],
        "landclim_restriction_label": published["K"],
        "landclim_elevation_m": int(published["G"]),
        "neotoma_elevation_m": site["altitude"],
        "point_distance_m": distance,
        "cross_source_core_identity": "not_established",
        "radius_transfer": "refused",
        "pollen_denominator_status": "not_evaluated",
        "rights_status": "not_evaluated",
        "lra_admitted_samples": 0,
        "input_sha256": {
            "raw_part": _digest(raw_part),
            "raw_manifest": _digest(raw_manifest),
            "workbook": asset["sha256"],
            "workbook_receipt": _digest(workbook_receipt),
            "count_mass": _digest(count_mass),
            "projection": _digest(projection),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "raw_part",
        "raw_manifest",
        "workbook",
        "workbook_receipt",
        "count_mass",
        "projection",
        "output",
    ):
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, required=True)
    args = parser.parse_args()
    result = compare_core(
        args.raw_part,
        args.raw_manifest,
        args.workbook,
        args.workbook_receipt,
        args.count_mass,
        args.projection,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    counts = cast(dict[str, int], result["sample_counts"])
    age = cast(dict[str, object], result["sample_candidate_age"])
    age_range = cast(dict[str, object], result["neotoma_dataset_age_range"])
    elevation_difference = cast(int, result["landclim_elevation_m"]) - cast(
        int, result["neotoma_elevation_m"]
    )
    (args.output / "REPORT.md").write_text(
        "# Abborrtjärnen core correspondence lead\n\n"
        "Pinned Neotoma dataset 19913 and PANGAEA 937075 LandClim II metadata "
        "both name Abborrtjärnen. Their reported points are "
        f"{result['point_distance_m']:.3f} m apart, and both list "
        f"{result['neotoma_downloaded_sample_count']} pollen samples. Neotoma "
        f"calls the core `{result['neotoma_core_handle']}` and LandClim calls "
        f"the sequence `{result['landclim_sequence']}`. The reported elevations "
        f"differ by {elevation_difference} m. "
        "These are strong identity leads but do not establish that the physical "
        "core, sampled basin and age model are identical.\n\n"
        f"Neotoma sample {SAMPLE_ID} has {counts['pollen_observations']} labeled "
        f"pollen NISP observations totaling {counts['pollen_count_sum']}, including "
        f"{counts['indeterminable_pollen_count']} Indeterminable grains, and "
        f"{counts['nonpollen_observations']} nonpollen observations totaling "
        f"{counts['nonpollen_count_sum']}. Its only retained candidate age is "
        f"{age['value_bp']} calibrated BP without "
        "younger/older bounds. The original categories are preserved; no compatible "
        "pollen denominator or taxon/PPE mapping is selected.\n\n"
        f"LandClim row {WORKBOOK_ROW} reports a {result['landclim_site_radius_m']} m "
        f"site radius, chronology source `{result['landclim_chronology_source']}`, "
        f"TopBP/BottomBP labels {result['landclim_top_bp_label']}/"
        f"{result['landclim_bottom_bp_label']}, and restriction label "
        f"`{result['landclim_restriction_label']}`. Neotoma's downloaded dataset "
        f"reports an age range {age_range['ageyoung']} to "
        f"{age_range['ageold']} calibrated radiocarbon "
        "years BP. These series-end values differ and are not treated as a matched "
        "chronology. Neotoma's core water depth is not basin radius; LandClim's "
        "radius is not transferred. Core identity, time support, denominator, "
        "source-backed method parameters and analytical-use rights remain decisions "
        "before an LRA request. Zero samples are admitted.\n"
    )
    print(
        json.dumps(
            {"sample_counts": counts, "point_distance_m": result["point_distance_m"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
