"""Independently decode four native HYDE country-table inputs and their arithmetic."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
import hashlib
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

COUNTRY_NAMES = {
    "Denmark": ("DK", "208"),
    "Finland": ("FI", "246"),
    "Norway": ("NO", "578"),
    "Sweden": ("SE", "752"),
}
YEARS = (500, 1000, 1500, 1700, 1900, 2000, 2025)
SCENARIOS = ("base", "lower", "upper")
FIELDS = (
    "country",
    "hyde_iso_code",
    "source_year_ce_label",
    "scenario",
    "cropland_km2",
    "difference_from_base_km2",
)
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def fail(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def country_mapping(outer_bytes: bytes) -> dict[str, str]:
    """Check the exact source code mapping using only the declared workbook XML."""
    with ZipFile(BytesIO(outer_bytes)) as outer:
        workbook = outer.read("HYDE_country_codes.xlsx")
    with ZipFile(BytesIO(workbook)) as inner:
        text_root = ET.fromstring(inner.read("xl/sharedStrings.xml"))
        shared = [
            "".join(node.itertext()) for node in text_root if node.tag == NS + "si"
        ]
        root = ET.fromstring(inner.read("xl/worksheets/sheet1.xml"))
    found = {}
    for row in root.iter(NS + "row"):
        cells = {}
        for cell in row:
            if cell.tag != NS + "c":
                continue
            value = cell.find(NS + "v")
            if value is None:
                continue
            address = cell.attrib.get("r", "")
            column = "".join(letter for letter in address if letter.isalpha())
            fail(
                bool(column) and column not in cells, "Duplicate/missing workbook cell"
            )
            lexical = value.text or ""
            if cell.attrib.get("t") == "s":
                fail(
                    lexical.isdecimal() and int(lexical) < len(shared),
                    "Invalid shared string index",
                )
                lexical = shared[int(lexical)]
            cells[column] = lexical
        name = cells.get("B", "").strip()
        if name in COUNTRY_NAMES:
            code, expected_iso = COUNTRY_NAMES[name]
            fail(
                code not in found and cells.get("A") == expected_iso,
                "Country mapping duplicates or differs",
            )
            found[code] = expected_iso
    fail(
        found == dict(COUNTRY_NAMES.values()),
        "Four exact country mappings required",
    )
    return found


def values(table: bytes, mapping: dict[str, str]) -> dict[tuple[str, int], Decimal]:
    """Rejoin country IDs and lexical CE columns without calendar or interval inference."""
    lines = table.decode("utf-8-sig").splitlines()
    fail(bool(lines), "Empty country table")
    columns = lines[0].split()
    fail(
        bool(columns) and columns[0] == "region" and len(columns) == len(set(columns)),
        "Country table header differs",
    )
    fail(all(str(year) in columns for year in YEARS), "Missing literal CE label")
    ids = {iso: code for code, iso in mapping.items()}
    result = {}
    seen = set()
    for line in lines[1:]:
        parts = line.split()
        fail(
            len(parts) == len(columns) and parts[0] not in seen,
            "Duplicate country or malformed source table",
        )
        seen.add(parts[0])
        if parts[0] not in ids:
            continue
        for year in YEARS:
            lexical = parts[columns.index(str(year))]
            try:
                number = Decimal(lexical)
            except InvalidOperation as error:
                raise ValueError("Nonnumeric source value") from error
            fail(
                number.is_finite() and number >= 0,
                "Nonfinite or negative source modeled area",
            )
            result[(ids[parts[0]], year)] = number
    fail(len(result) == 28, "Incomplete country/year source population")
    return result


def joined_rows(
    mapping: dict[str, str], scenarios: dict[str, dict[tuple[str, int], Decimal]]
) -> list[dict[str, str | int]]:
    fail(list(scenarios) == list(SCENARIOS), "Scenario identity/order differs")
    fail(
        mapping == dict(COUNTRY_NAMES.values()),
        "Country mapping differs",
    )
    rows: list[dict[str, str | int]] = []
    for code, iso in COUNTRY_NAMES.values():
        for year in YEARS:
            baseline = scenarios["base"][(code, year)]
            for scenario in SCENARIOS:
                value = scenarios[scenario][(code, year)]
                rows.append(
                    dict(
                        zip(
                            FIELDS,
                            (
                                code,
                                iso,
                                year,
                                scenario,
                                str(value),
                                "0" if scenario == "base" else str(value - baseline),
                            ),
                            strict=True,
                        )
                    )
                )
    fail(len(rows) == 84, "Complete84 modeled rows required")
    return rows


def csv_bytes(rows: list[dict[str, str | int]]) -> bytes:
    out = StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def report_and_csv(
    source_root: Path, historical_report: dict[str, Any]
) -> tuple[dict[str, Any], bytes]:
    """Require the complete historical metadata contract and derive all current source values."""
    general = source_root / "original/general_files.zip"
    mapping = country_mapping(general.read_bytes())
    inputs = [
        {
            "path": "original/general_files.zip",
            "sha256": hashlib.sha256(general.read_bytes()).hexdigest(),
        }
    ]
    scenarios = {}
    for scenario in SCENARIOS:
        name = "original/gbc2025_7apr_" + scenario + "/txt/cropland_c.txt"
        raw = (source_root / name).read_bytes()
        scenarios[scenario] = values(raw, mapping)
        inputs.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest()})
    rows = joined_rows(mapping, scenarios)
    # Noncomputed metadata is separately closed/typed by contracts.validate_scope;
    # no source-derived amount is copied from the retained report or CSV.
    expected = dict(historical_report)
    expected.update(
        country_codes=mapping,
        inputs=inputs,
        rows=len(rows),
        country_years=len(mapping) * len(YEARS),
        scenarios=list(scenarios),
        source_year_ce_labels=list(YEARS),
    )
    return expected, csv_bytes(rows)
