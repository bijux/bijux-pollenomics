"""Independent NFI dictionary/header and selected metadata checks; tree outcomes stay unselected."""

from __future__ import annotations
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

SOURCE = Path("reference-sources/empd2-nfi/nfi/swedish-plot-data.xlsx")
SOURCE_SHA = "862d13f26b868e3b32504f0f714f369018e700e54b245fcd2e16c80640316294"
GUIDE_SHA = "793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
BASAL = ("BaPine", "BaContorta", "BaSpruce", "BaBirch", "BaOtherDec")
IDENTITY = ("Year", "TractID", "PlotID", "Inventory_Date", "Easting", "Northing")


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"Physical input absent: {path}")
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def exact(a: Any, b: Any) -> None:
    require(type(a) is type(b), "JSON type changed")
    if isinstance(a, dict):
        require(set(a) == set(b), "JSON keys changed")
        for k in a:
            exact(a[k], b[k])
    elif isinstance(a, list):
        require(len(a) == len(b), "JSON length changed")
        for x, y in zip(a, b, strict=True):
            exact(x, y)
    else:
        require(a == b, "JSON value changed")


def source_projection(
    source: Path, *, expected_sha: str = SOURCE_SHA
) -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha(source) == expected_sha, "Pinned original workbook differs")
    decoded: Counter[str] = Counter()

    def cell_value(cell: ET.Element, strings: list[str], scope: str) -> str:
        column = cell.attrib["r"].rstrip("0123456789")
        require(
            scope in ("dictionary", "header")
            or (scope == "support" and column in ("D", "G", "H")),
            "Forbidden measurement outcome cell selection",
        )
        decoded[scope] += 1
        value = cell.find(NS + "v")
        require(
            value is not None and value.text is not None,
            "Selected metadata cell has no scalar",
        )
        assert value is not None and value.text is not None
        return strings[int(value.text)] if cell.get("t") == "s" else value.text

    with ZipFile(source) as archive:
        shared = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        strings = [
            "".join(node.text or "" for node in row.iter(NS + "t"))
            for row in shared.findall(NS + "si")
        ]
        dictionary = {}
        for row in ET.fromstring(archive.read("xl/worksheets/sheet1.xml")).iter(
            NS + "row"
        ):
            columns = {
                c.attrib["r"].rstrip("0123456789"): cell_value(c, strings, "dictionary")
                for c in row.findall(NS + "c")
                if c.attrib["r"].rstrip("0123456789") in ("A", "B")
            }
            name = columns.get("A")
            if name and name != "Column":
                require(
                    name not in dictionary and bool(columns.get("B")),
                    "Dictionary identity incomplete/duplicated",
                )
                dictionary[name] = columns["B"]
        headers: list[str] = []
        count = 0
        dates = []
        land: Counter[str] = Counter()
        with archive.open("xl/worksheets/sheet2.xml") as stream:
            for _, row in ET.iterparse(stream, events=("end",)):
                if row.tag != NS + "row":
                    continue
                if not headers:
                    require(row.get("r") == "1", "Native header must be first row")
                    headers = [
                        cell_value(c, strings, "header") for c in row.findall(NS + "c")
                    ]
                    require(
                        len(headers) == 47
                        and len(set(headers)) == 47
                        and tuple(headers[:6]) == IDENTITY
                        and tuple(headers[25:30]) == BASAL
                        and headers[6:8] == ["PlotArea", "LandUseClass"],
                        "Source-owned NFI column identities differ",
                    )
                else:
                    cells = {
                        c.attrib["r"].rstrip("0123456789"): cell_value(
                            c, strings, "support"
                        )
                        for c in row.findall(NS + "c")
                        if c.attrib["r"].rstrip("0123456789") in ("D", "G", "H")
                    }
                    require(
                        set(cells) == {"D", "G", "H"} and cells["G"] == "153.94",
                        "Native plot area/support changed",
                    )
                    date = float(cells["D"])
                    require(math.isfinite(date), "Nonfinite inventory date")
                    dates.append(date)
                    land[cells["H"]] += 1
                    count += 1
                row.clear()
    require(
        count == 43892 and decoded["support"] == 3 * count,
        "Selected metadata population differs",
    )
    basal = {name: dictionary[name] for name in BASAL}
    require(
        all(v.endswith("(m2/ha)") for v in basal.values()), "Basal field units differ"
    )
    require(
        dictionary["PlotArea"].startswith("Circular plot r=7 => 153.94 m2")
        and "Forestland according to FAO-definitions" in dictionary["LandUseClass"],
        "Source metadata definitions differ",
    )
    result = {
        "schema_version": "nfi-measurement-schema.1",
        "source_path_in_private_store": SOURCE.as_posix(),
        "source_sha256": expected_sha,
        "workbook_header_count": len(headers),
        "workbook_headers": headers,
        "headers_without_exact_dictionary_entry": [
            h for h in headers if h not in dictionary
        ],
        "identity_and_geometry_headers": list(IDENTITY),
        "inventory_date_description": dictionary["Inventory_Date"],
        "plot_area_description": dictionary["PlotArea"],
        "land_use_description": dictionary["LandUseClass"],
        "candidate_tree_basal_area_fields": basal,
        "candidate_tree_basal_area_unit": "m2/ha",
        "source_plot_support": {
            "plot_year_rows": count,
            "plot_area_m2_each": 153.94,
            "land_use_code_counts": dict(sorted(land.items())),
            "inventory_date_excel_serial_min": min(dates),
            "inventory_date_excel_serial_max": max(dates),
            "metadata_cells_decoded": 3 * count,
        },
        "measurement_outcome_cells_decoded": 0,
        "benchmark_admission": "no_measured_pairs_admitted",
    }
    require(
        sha(source) == expected_sha,
        "Original workbook changed during metadata observation",
    )
    return result, {
        "semantic_cells_decoded": dict(decoded),
        "measurement_outcome_cells_decoded": 0,
        "native_metadata_columns": ["D", "G", "H"],
        "worksheet_XML_streamed_including_unselected_cells": True,
        "no_tree_outcome_values_displayed_or_scored": True,
    }
