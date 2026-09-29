"""Compare pinned Swedish site identities without transferring basin geometry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any
import unicodedata
from xml.etree import ElementTree as ET
from zipfile import ZipFile

XML = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_name(name: str) -> str:
    return unicodedata.normalize("NFC", name).strip().casefold()


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance between (longitude, latitude) WGS84 point labels."""
    lon_a, lat_a = map(radians, a)
    lon_b, lat_b = map(radians, b)
    angle = 2 * asin(
        sqrt(
            sin((lat_b - lat_a) / 2) ** 2
            + cos(lat_a) * cos(lat_b) * sin((lon_b - lon_a) / 2) ** 2
        )
    )
    return 6371.0088 * angle


def point_geometry(payload: dict[str, object]) -> tuple[float, float] | None:
    raw = payload.get("geography")
    if not isinstance(raw, str):
        return None
    geometry = json.loads(raw)
    if geometry.get("type") != "Point":
        return None
    if geometry.get("crs", {}).get("properties", {}).get("name") != "EPSG:4326":
        raise ValueError("Neotoma point CRS is not EPSG:4326")
    coordinates = geometry["coordinates"]
    if len(coordinates) != 2:
        raise ValueError("Neotoma point axis differs")
    longitude, latitude = map(float, coordinates)
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise ValueError("Neotoma point is outside geographic bounds")
    return longitude, latitude


def sheet_rows(archive: ZipFile, member: str) -> list[tuple[int, dict[str, str]]]:
    shared = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    strings = [
        "".join(node.text or "" for node in item.findall(".//x:t", XML))
        for item in shared.findall("x:si", XML)
    ]
    sheet = ET.fromstring(archive.read(member))
    result = []
    for row in sheet.findall(".//x:sheetData/x:row", XML):
        cells = {}
        for cell in row.findall("x:c", XML):
            value = cell.find("x:v", XML)
            if value is None or value.text is None:
                continue
            value_text = value.text
            column = "".join(letter for letter in cell.attrib["r"] if letter.isalpha())
            cells[column] = (
                strings[int(value_text)] if cell.attrib.get("t") == "s" else value_text
            )
        result.append((int(row.attrib["r"]), cells))
    return result


def published_sites(workbook: Path, receipt_path: Path) -> list[dict[str, Any]]:
    receipt = json.loads(receipt_path.read_text())
    asset = next(
        row
        for row in receipt["assets"]
        if row["filename"] == workbook.name and row["dataset_id"] == "937075"
    )
    if digest(workbook) != asset["sha256"]:
        raise ValueError("Pinned LandClim II workbook digest differs")
    with ZipFile(workbook) as archive:
        definitions = dict(
            (row.get("A"), row.get("B"))
            for _, row in sheet_rows(archive, "xl/worksheets/sheet1.xml")
        )
        if definitions.get("siteradius") != "radius of the site in meters":
            raise ValueError(
                "Published geometry unit is not documented radius in metres"
            )
        rows = sheet_rows(archive, "xl/worksheets/sheet2.xml")
    header = rows[0][1]
    if [header.get(column) for column in "ABCDEFHIK"] != [
        "SiteName",
        "csvfilename",
        "siteType",
        "siteradius",
        "londd",
        "latdd",
        "LCGRID_ID",
        "Country",
        "DataRestricted/NotRestriced",
    ]:
        raise ValueError("Published site axes differ")
    result = []
    for row_number, row in rows[1:]:
        if row.get("I") != "Sweden":
            continue
        result.append(
            {
                "row": row_number,
                "name": row["A"],
                "sequence": row["B"],
                "site_type": row.get("C"),
                "radius_m": row.get("D"),
                "point": (float(row["E"]), float(row["F"])),
                "grid": row.get("H"),
                "count_availability_label": row.get("K"),
            }
        )
    return result


def compare(
    workbook: Path, receipt_path: Path, projection_path: Path, sites_path: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    landclim = published_sites(workbook, receipt_path)
    projection = json.loads(projection_path.read_text())
    selected = {
        row["site_id"]
        for row in projection["basin_rows"]
        if row["country_code"] == "SE"
    }
    if projection["denominators"]["accepted_samples"] != 0 or not selected:
        raise ValueError("Swedish candidate projection is not a refused cohort")
    site_capture = json.loads(sites_path.read_text())
    source_sites = {row["site_id"]: row for row in site_capture["rows"]}
    if not selected <= source_sites.keys():
        raise ValueError("Selected Neotoma site identity is absent")
    rows: list[dict[str, Any]] = []
    for site_id in sorted(selected, key=lambda value: int(value.rsplit(":", 1)[1])):
        source = source_sites[site_id]["source_payload"]
        name = source["sitename"]
        point = point_geometry(source)
        namesakes = [
            site
            for site in landclim
            if normalized_name(str(site["name"])) == normalized_name(name)
        ]
        nearest = (
            min(landclim, key=lambda site: distance_km(point, site["point"]))
            if point
            else None
        )
        name_match = (
            min(namesakes, key=lambda site: distance_km(point, site["point"]))
            if point and namesakes
            else None
        )
        rows.append(
            {
                "neotoma_site_id": site_id,
                "neotoma_name": name,
                "neotoma_lon": point[0] if point else None,
                "neotoma_lat": point[1] if point else None,
                "neotoma_altitude_m": source.get("altitude"),
                "neotoma_geometry_type": "Point" if point else "non_point_or_missing",
                "nearest_landclim_sequence": nearest["sequence"] if nearest else None,
                "nearest_landclim_distance_km": round(
                    distance_km(point, nearest["point"]), 6
                )
                if nearest and point is not None
                else None,
                "same_name_count": len(namesakes),
                "same_name_sequence": name_match["sequence"] if name_match else None,
                "same_name_distance_km": round(
                    distance_km(point, name_match["point"]), 6
                )
                if name_match and point is not None
                else None,
                "same_name_radius_m": name_match["radius_m"] if name_match else None,
                "same_name_site_type": name_match["site_type"] if name_match else None,
                "same_name_source_row": name_match["row"] if name_match else None,
                "same_name_count_availability_label": name_match[
                    "count_availability_label"
                ]
                if name_match
                else None,
                "identity_decision": "not_established",
                "radius_transfer": "refused",
            }
        )
    klot = next(row for row in rows if row["neotoma_site_id"] == "neotoma:site:13336")
    if klot["same_name_sequence"] != "KLO":
        raise ValueError("Klotjärnen source comparison did not close")
    report = {
        "schema_version": "swedish-cross-source-site-comparison.v1",
        "landclim_workbook_sha256": digest(workbook),
        "landclim_receipt_sha256": digest(receipt_path),
        "neotoma_projection_sha256": digest(projection_path),
        "neotoma_sites_part_sha256": digest(sites_path),
        "neotoma_swedish_candidate_sites": len(rows),
        "landclim_swedish_sequences": len(landclim),
        "neotoma_point_sites": sum(
            row["neotoma_geometry_type"] == "Point" for row in rows
        ),
        "same_name_candidates": sum(bool(row["same_name_count"]) for row in rows),
        "same_name_point_candidates": sum(
            row["same_name_distance_km"] is not None for row in rows
        ),
        "same_name_within_10m": sum(
            row["same_name_distance_km"] is not None
            and row["same_name_distance_km"] < 0.01
            for row in rows
        ),
        "same_name_within_1km": sum(
            row["same_name_distance_km"] is not None
            and row["same_name_distance_km"] < 1
            for row in rows
        ),
        "identity_admitted": 0,
        "lra_samples_admitted": 0,
        "klotjarnen": klot,
        "distance_method": "haversine_wgs84_point_labels_km",
        "identity_rule": "name_and_coordinates_are_review_leads_not_transfer_authority",
    }
    return rows, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("workbook", "receipt", "projection", "sites"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output
    rows, report = compare(args.workbook, args.receipt, args.projection, args.sites)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "site-comparison.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    klot = report["klotjarnen"]
    (output / "REPORT.md").write_text(
        "# Swedish cross-source site comparison\n\n"
        f"The pinned LandClim II metadata has {report['landclim_swedish_sequences']} "
        f"Swedish sequences; the retained Neotoma prerequisite projection has "
        f"{report['neotoma_swedish_candidate_sites']} Swedish candidate sites, "
        f"{report['neotoma_point_sites']} with point coordinates. "
        f"{report['same_name_point_candidates']} have a same-name published "
        f"sequence with comparable point coordinates; "
        f"{report['same_name_within_10m']} are within 10 m. These are "
        "identity review leads, not admitted cross-source joins.\n\n"
        f"For Klotjärnen, Neotoma site 13336 is at "
        f"({klot['neotoma_lon']}, {klot['neotoma_lat']}) and altitude "
        f"{klot['neotoma_altitude_m']} m. LandClim II sequence KLO "
        f"(workbook row {klot['same_name_source_row']}) documents a "
        f"{klot['same_name_radius_m']} m site radius but is "
        f"{klot['same_name_distance_km']:.3f} km away. The radius cannot "
        "be transferred to the Neotoma site from its name.\n\n"
        "The workbook defines `siteradius` as metres; the source receipt "
        "authenticates the workbook. Site names and coordinates do not "
        "establish matching cores, source rights, chronological support or "
        "pollen-count denominators. No LRA samples are admitted by this "
        "comparison. `site-comparison.csv` retains each source lead and "
        "the refusal status.\n"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "neotoma_swedish_candidate_sites",
                    "landclim_swedish_sequences",
                    "neotoma_point_sites",
                    "same_name_candidates",
                    "same_name_within_10m",
                    "klotjarnen",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
