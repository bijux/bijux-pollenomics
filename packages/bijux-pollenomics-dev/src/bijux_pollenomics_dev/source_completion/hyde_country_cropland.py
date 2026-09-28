"""Extract source-reported HYDE cropland totals for four Nordic countries."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


SCENARIOS = ("base", "lower", "upper")
COUNTRIES = {
    "DK": ("Denmark", "208"),
    "FI": ("Finland", "246"),
    "NO": ("Norway", "578"),
    "SE": ("Sweden", "752"),
}
YEARS = (500, 1000, 1500, 1700, 1900, 2000, 2025)
XML_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
GENERAL = "original/general_files.zip"
TABLE = "original/gbc2025_7apr_{scenario}/txt/cropland_c.txt"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _country_codes(archive: bytes) -> dict[str, str]:
    with ZipFile(BytesIO(archive)) as outer:
        workbook = outer.read("HYDE_country_codes.xlsx")
    with ZipFile(BytesIO(workbook)) as inner:
        strings_root = ElementTree.fromstring(inner.read("xl/sharedStrings.xml"))
        strings = [
            "".join(node.itertext()) for node in strings_root.findall(f"{XML_NS}si")
        ]
        sheet = ElementTree.fromstring(inner.read("xl/worksheets/sheet1.xml"))
    found: dict[str, str] = {}
    for row in sheet.findall(f".//{XML_NS}sheetData/{XML_NS}row"):
        cells: dict[str, str] = {}
        for cell in row.findall(f"{XML_NS}c"):
            value = cell.find(f"{XML_NS}v")
            if value is None:
                continue
            column = "".join(char for char in cell.attrib["r"] if char.isalpha())
            cells[column] = (
                strings[int(value.text or "0")]
                if cell.attrib.get("t") == "s"
                else value.text or ""
            )
        name = cells.get("B", "").strip()
        for country, (expected_name, _) in COUNTRIES.items():
            if name == expected_name:
                if country in found:
                    raise ValueError(f"Duplicate country mapping: {country}")
                found[country] = cells["A"]
    expected = {country: iso for country, (_, iso) in COUNTRIES.items()}
    if found != expected:
        raise ValueError(f"HYDE country code mapping changed: {found}")
    return found


def _table(data: bytes, codes: dict[str, str]) -> dict[tuple[str, int], Decimal]:
    lines = data.decode("utf-8-sig").splitlines()
    header = lines[0].split()
    if (
        header[0] != "region"
        or len(header) != len(set(header))
        or not set(map(str, YEARS)) <= set(header)
    ):
        raise ValueError("HYDE country table year columns changed")
    year_columns = {year: header.index(str(year)) for year in YEARS}
    by_iso = {iso: country for country, iso in codes.items()}
    found: dict[tuple[str, int], Decimal] = {}
    all_codes: set[str] = set()
    for line in lines[1:]:
        cells = line.split()
        if len(cells) != len(header) or cells[0] in all_codes:
            raise ValueError("HYDE country table shape or code changed")
        all_codes.add(cells[0])
        country = by_iso.get(cells[0])
        if country is None:
            continue
        for year, column in year_columns.items():
            try:
                area = Decimal(cells[column])
            except InvalidOperation as exc:
                raise ValueError("Non-numeric HYDE cropland total") from exc
            if not area.is_finite() or area < 0:
                raise ValueError("Invalid HYDE cropland total")
            found[(country, year)] = area
    if len(found) != len(COUNTRIES) * len(YEARS):
        raise ValueError("Missing HYDE Nordic country/year total")
    return found


def publish(source_root: Path, output: Path) -> dict[str, object]:
    root = source_root.resolve()
    inputs: list[dict[str, str]] = []
    general = (root / GENERAL).read_bytes()
    inputs.append({"path": GENERAL, "sha256": _sha(general)})
    codes = _country_codes(general)
    scenarios: dict[str, dict[tuple[str, int], Decimal]] = {}
    for scenario in SCENARIOS:
        relative = TABLE.format(scenario=scenario)
        data = (root / relative).read_bytes()
        inputs.append({"path": relative, "sha256": _sha(data)})
        scenarios[scenario] = _table(data, codes)

    rows: list[dict[str, str | int]] = []
    for country in COUNTRIES:
        for year in YEARS:
            base = scenarios["base"][(country, year)]
            for scenario in SCENARIOS:
                value = scenarios[scenario][(country, year)]
                rows.append(
                    {
                        "country": country,
                        "hyde_iso_code": codes[country],
                        "source_year_ce_label": year,
                        "scenario": scenario,
                        "cropland_km2": str(value),
                        "difference_from_base_km2": "0"
                        if scenario == "base"
                        else str(value - base),
                    }
                )
    report: dict[str, object] = {
        "schema_version": "hyde-source-reported-nordic-cropland.v1",
        "measure": "HYDE source-reported country cropland area in km2; modeled land use",
        "source_family": "HYDE 3.5 local gbc2025_7apr release",
        "country_codes": codes,
        "source_year_ce_labels": list(YEARS),
        "scenarios": list(SCENARIOS),
        "rows": len(rows),
        "country_years": len(COUNTRIES) * len(YEARS),
        "inputs": inputs,
        "rights": "Local Yoda metadata and License.txt say CC BY-NC 4.0; README and NetCDF declarations say CC BY 3.0. Derived summary retained under restrictive interpretation; redistribution review pending.",
        "interpretation": "These are native source country totals, not a new grid-country overlay, independent observed vegetation, uncertainty intervals, or pollen covariates. CE labels are retained without BP/NetCDF calendar conversion. The 2025 column exists in these tables while release coverage prose conflicts.",
        "remaining": [
            "unreviewed_grid_variables_and_years",
            "release_rights_reconciliation",
            "time_mapping_for_pollen_study",
            "paired_no_hyde_hyde_ablation",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (output / "country-years.csv").write_text(buffer.getvalue(), encoding="utf-8")
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args.source_root, args.output), indent=2))


if __name__ == "__main__":
    main()
