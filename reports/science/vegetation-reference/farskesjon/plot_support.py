"""Assess the source-bound Färskesjön pollen and nearest NFI plot supports."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from xml.etree import ElementTree
from zipfile import ZipFile

from pyproj import Geod, Transformer


EXPECTED_SHA256 = {
    "empd2/source.sqlite3": "5634e85d922ee0741c41a77d081010c9cc1c113966b283bc52e2051a9d3722e2",
    "nfi/swedish-plot-data.xlsx": "862d13f26b868e3b32504f0f714f369018e700e54b245fcd2e16c80640316294",
    "pairing/spatial-feasibility.json": "5d35aed59cb5e3b49582976264837fab1c8d4ffa3dc1937e73bf2f04f32e2c66",
}
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
SAMPLE = "Nielsen_b4"
VOLUME_COLUMNS = {
    "U": "pine",
    "V": "contorta",
    "W": "spruce",
    "X": "birch",
    "Y": "other_deciduous",
}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _selected_plot(book: Path, key: tuple[str, str, str]) -> tuple[dict[str, str], str]:
    with ZipFile(book) as archive:
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        properties = workbook.find("s:workbookPr", NS)
        if properties is not None and properties.get("date1904", "0") not in {
            "0",
            "false",
        }:
            raise ValueError("Unexpected Excel date epoch")
        strings = [
            "".join(item.itertext())
            for item in ElementTree.fromstring(
                archive.read("xl/sharedStrings.xml")
            ).findall("s:si", NS)
        ]
        expected_headers = [
            "Year",
            "TractID",
            "PlotID",
            "Inventory_Date",
            "Easting",
            "Northing",
            "PlotArea",
            "LandUseClass",
        ]
        if strings[: len(expected_headers)] != expected_headers:
            raise ValueError("NFI plot identity headers changed")
        if [strings[i] for i in range(20, 25)] != [
            "VolPine",
            "VolContorta",
            "VolSpruce",
            "VolBirch",
            "VolOtherDec",
        ]:
            raise ValueError("NFI tree volume headers changed")
        matches: list[tuple[dict[str, str], str]] = []
        with archive.open("xl/worksheets/sheet2.xml") as stream:
            for _, row in ElementTree.iterparse(stream, events=("end",)):
                if not row.tag.endswith("}row"):
                    continue
                cells = {
                    re.match(r"[A-Z]+", cell.attrib["r"]).group(): cell.findtext(
                        "s:v", namespaces=NS
                    )
                    for cell in row.findall("s:c", NS)
                }
                if (cells.get("A"), cells.get("B"), cells.get("C")) == key:
                    matches.append((cells, row.attrib["r"]))
                row.clear()
        if len(matches) != 1:
            raise ValueError("Expected exactly one source NFI plot-year row")
        with archive.open("xl/worksheets/sheet1.xml") as stream:
            descriptions = {}
            for _, row in ElementTree.iterparse(stream, events=("end",)):
                if row.tag.endswith("}row"):
                    cells = row.findall("s:c", NS)
                    if len(cells) >= 2:
                        values = []
                        for cell in cells[:2]:
                            value = cell.findtext("s:v", namespaces=NS)
                            values.append(
                                strings[int(value)]
                                if cell.get("t") == "s" and value
                                else value
                            )
                        descriptions[values[0]] = values[1]
                    row.clear()
        if (
            descriptions.get("PlotArea")
            != "Circular plot r=7 => 153.94 m2 (only un-divided plots included)"
        ):
            raise ValueError("NFI plot area description changed")
        if any(
            descriptions.get(f"Vol{name}") != f"Volume of {label} (m3/ha)"
            for name, label in [
                ("Pine", "pine"),
                ("Contorta", "contorta"),
                ("Spruce", "spruce"),
                ("Birch", "birch"),
                ("OtherDec", "other deciduous species"),
            ]
        ):
            raise ValueError("NFI volume units changed")
        return matches[0]


def assess(source_root: Path) -> dict[str, object]:
    """Compare two observed supports without assigning plot trees to the lake."""
    source_root = source_root.resolve()
    for relative, expected in EXPECTED_SHA256.items():
        if _sha(source_root / relative) != expected:
            raise ValueError(f"Source changed: {relative}")
    pairing = json.loads((source_root / "pairing/spatial-feasibility.json").read_text())
    leads = [
        row
        for row in pairing["nearest_nfi_row_by_pollen_sample"]
        if row["pollen_sample"] == SAMPLE
    ]
    if len(leads) != 1:
        raise ValueError("The Färskesjön spatial lead changed")
    lead = leads[0]
    key = (lead["nfi_year"], lead["nfi_tract"], lead["nfi_plot"])
    cells, _ = _selected_plot(source_root / "nfi/swedish-plot-data.xlsx", key)
    with sqlite3.connect(source_root / "empd2/source.sqlite3") as connection:
        metadata = connection.execute(
            "SELECT notes, originalsamplename, samplecontext, sampletype, "
            "samplemethod, agebp, ageuncertainty, country, longitude, latitude "
            "FROM metadata WHERE samplename = ?",
            (SAMPLE,),
        ).fetchall()
        publications = connection.execute(
            "SELECT p.doi FROM publications p JOIN metapubli m "
            "ON m.publiid = p.publiid WHERE m.samplename = ?",
            (SAMPLE,),
        ).fetchall()
    if len(metadata) != 1 or publications != [("10.1177/0959683614556552",)]:
        raise ValueError("EMPD2 sample or publication identity changed")
    note, original, context, sample_type, method, age, age_type, country, lon, lat = (
        metadata[0]
    )
    if (note, original, context, sample_type, method, age, age_type, country) != (
        "Surface smaple collected September 2013",
        "Farskesjon 0-1 cm",
        "lake",
        "sediment",
        "gravity corer",
        -63,
        "A",
        "Sweden",
    ):
        raise ValueError("EMPD2 Färskesjön source claim changed")
    date_serial = float(cells["D"])
    inventory = datetime(1899, 12, 30) + timedelta(days=date_serial)
    if inventory.date() != date(2013, 5, 17) or cells["A"] != "2013":
        raise ValueError("NFI inventory date changed")
    plot_area = float(cells["G"])
    radius = math.sqrt(plot_area / math.pi)
    if abs(radius - 7) > 0.001:
        raise ValueError("NFI plot radius and area disagree")
    plot_lon, plot_lat = Transformer.from_crs(
        "EPSG:3006", "EPSG:4326", always_xy=True
    ).transform(float(cells["E"]), float(cells["F"]))
    _, _, separation = Geod(ellps="WGS84").inv(
        plot_lon, plot_lat, float(lon), float(lat)
    )
    if abs(separation - lead["distance_m_wgs84"]) > 1e-6:
        raise ValueError("Recomputed WGS84 distance differs from the retained lead")
    volumes = {name: float(cells[column]) for column, name in VOLUME_COLUMNS.items()}
    if any(value < 0 or not math.isfinite(value) for value in volumes.values()):
        raise ValueError("NFI plot volume is invalid")
    return {
        "schema_version": "farskesjon-pollen-nfi-plot-support.v1",
        "source_sha256": EXPECTED_SHA256,
        "empd2_sample": SAMPLE,
        "empd2_source_note": note,
        "empd2_context": "lake surface sediment, 0–1 cm; agebp -63 is source age, not collection date",
        "nfi_inventory_date": inventory.date().isoformat(),
        "nfi_source_date_serial": cells["D"],
        "nfi_land_use_class_native": cells["H"],
        "nfi_plot_area_m2": plot_area,
        "nfi_plot_radius_m": radius,
        "distance_between_source_points_m": separation,
        "point_separation_minus_plot_radius_m": separation - radius,
        "nfi_tree_volume_m3_per_ha": volumes,
        "nfi_tree_volume_total_m3_per_ha": sum(volumes.values()),
        "inventory_precedes_possible_september_sampling_days": [
            (date(2013, 9, 1) - inventory.date()).days,
            (date(2013, 9, 30) - inventory.date()).days,
        ],
        "vegetation_pair_admission": "refused",
        "reason": "One 7 m radius forest plot sampled 107–136 days before a lake surface sample and 427 m from its point does not measure the lake pollen's regional vegetation footprint; plot tree volume classes are not 31-taxon landscape cover fractions.",
        "coordinate_publication": "withheld; plot source identifiers and coordinates stay in the private source store",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Absent output destination required")
    report = assess(args.source_root)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )
    print(
        json.dumps({"admission": report["vegetation_pair_admission"], "sample": SAMPLE})
    )


if __name__ == "__main__":
    main()
