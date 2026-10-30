"""Retain sample-owned Galician worksheet cells without interpreting their dates."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from bijux_pollenomics_dev.ci.report_rebuild.contracts import load_json
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path

WORKBOOK = "data/adna/review/galician_cattle/dating-table.xlsx"
WORKSHEET = "xl/worksheets/sheet1.xml"
TABLE = "sample-context.csv"
SCHEMA = "galician-cattle-literal-context.v1"
HEADERS = {
    "A": "IUX Sample code",
    "B": "Site",
    "C": "species",
    "D": "type of sample",
    "E": "Age 14C BP",
    "F": "Dating Lab code",
    "G": "Age cal BP (2-sigma)",
    "H": "Age cal BC/AD ",
    "I": "context",
    "J": "lab code ",
}
FIELDS = (
    "biosample_accession",
    "paper_specimen_code",
    "paper_sample_label",
    "source_workbook",
    "worksheet_part",
    "cell_reference",
    "header_reference",
    "source_header_literal",
    "cell_state",
    "native_type_attribute",
    "native_style_attribute",
    "value_element_present",
    "native_value_literal",
    "resolved_literal",
    "formula_present",
    "formula_literal",
)
_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_ACCESSIONS = {f"SAMN181068{number}" for number in range(27, 38)}


def _text(element: ET.Element) -> str:
    """Concatenate displayed string runs without trimming or numerical coercion."""
    if element.find("x:rPh", _NS) is not None:
        raise ValueError("Galician literal context: phonetic strings unsupported")
    return "".join(node.text or "" for node in element.findall(".//x:t", _NS))


def _cells(payload: bytes) -> dict[str, dict[str, object]]:
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Galician literal context: duplicate ZIP member")
        shared = (
            [
                _text(item)
                for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall(
                    "x:si", _NS
                )
            ]
            if "xl/sharedStrings.xml" in names
            else []
        )
        worksheet = ET.fromstring(archive.read(WORKSHEET))
    result: dict[str, dict[str, object]] = {}
    for row in worksheet.findall("x:sheetData/x:row", _NS):
        for cell in row.findall("x:c", _NS):
            reference = cell.get("r", "")
            if (
                re.fullmatch(r"[A-Z]+[1-9][0-9]*", reference) is None
                or reference in result
                or reference.rstrip("0123456789") + row.get("r", "") != reference
            ):
                raise ValueError("Galician literal context: duplicate/invalid cell")
            value = cell.find("x:v", _NS)
            inline = cell.find("x:is", _NS)
            formula = cell.find("x:f", _NS)
            raw = value.text if value is not None else None
            literal = raw
            kind = cell.get("t")
            if kind == "s" and raw is not None:
                if re.fullmatch(r"[0-9]+", raw) is None or int(raw) >= len(shared):
                    raise ValueError("Galician literal context: invalid shared string")
                literal = shared[int(raw)]
            elif kind == "inlineStr" and inline is not None:
                literal = _text(inline)
            elif kind not in {None, "n", "b", "str", "e", "s", "inlineStr", "d"}:
                raise ValueError("Galician literal context: unsupported cell type")
            result[reference] = {
                "cell_state": "present_blank"
                if raw is None and inline is None and formula is None
                else "present_value",
                "native_type_attribute": kind,
                "native_style_attribute": cell.get("s"),
                "value_element_present": value is not None,
                "native_value_literal": raw,
                "resolved_literal": literal,
                "formula_present": formula is not None,
                "formula_literal": formula.text if formula is not None else None,
            }
    return result


def literal_context_rows(
    payload: bytes, crosswalk: list[dict[str, Any]]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Join exact existing specimen/BioSample rows; retain values without admission."""
    if (
        len(crosswalk) != 11
        or {item["biosample_accession"] for item in crosswalk} != _ACCESSIONS
        or {item["paper_row"] for item in crosswalk} != {*range(16, 26), 27}
    ):
        raise ValueError("Galician literal context: crosswalk population differs")
    cells = _cells(payload)
    for column, expected in HEADERS.items():
        header_cell = cells.get(f"{column}15", {})
        if header_cell.get("resolved_literal") != expected or header_cell.get(
            "formula_present"
        ):
            raise ValueError("Galician literal context: source header differs")
    rows: list[dict[str, object]] = []
    for item in sorted(crosswalk, key=lambda value: value["biosample_accession"]):
        number = item["paper_row"]
        for column, key in (
            ("A", "paper_specimen_code"),
            ("C", "source_species"),
            ("J", "paper_sample_label"),
        ):
            binding_cell = cells.get(f"{column}{number}", {})
            if binding_cell.get("resolved_literal") != item[key] or binding_cell.get(
                "formula_present"
            ):
                raise ValueError(
                    "Galician literal context: original specimen binding differs"
                )
        for column, header in HEADERS.items():
            reference = f"{column}{number}"
            cell = cells.get(reference)
            rows.append(
                {
                    "biosample_accession": item["biosample_accession"],
                    "paper_specimen_code": item["paper_specimen_code"],
                    "paper_sample_label": item["paper_sample_label"],
                    "source_workbook": WORKBOOK,
                    "worksheet_part": WORKSHEET,
                    "cell_reference": reference,
                    "header_reference": f"{column}15",
                    "source_header_literal": header,
                    **(cell if cell is not None else {"cell_state": "missing"}),
                }
            )
    return rows, {
        "schema_version": SCHEMA,
        "table": TABLE,
        "biosample_count": 11,
        "paper_source_specimen_count": 18,
        "selected_cell_count": len(rows),
        "cell_states": dict(
            sorted(Counter(str(row["cell_state"]) for row in rows).items())
        ),
        "formula_cell_count": sum(row.get("formula_present") is True for row in rows),
        "date_conversion_performed": False,
        "site_assignment_performed": False,
        "scientific_admission": False,
        "atlas_point_admitted": False,
    }


def _verified(repository: Path, identity: dict[str, Any]) -> bytes:
    relative = Path(identity["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Galician literal context: source path is not confined")
    raw = _regular_path(repository / relative).read_bytes()
    if (
        len(raw) != identity["bytes"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise ValueError("Galician literal context: original source identity differs")
    return raw


def write_literal_context(repository: Path, output: Path) -> None:
    """Add one optional literal-cell table to an already verified species export."""
    report = load_json(output / "report.json", "Galician species review")
    sources = report.get("source_hashes")
    if not isinstance(sources, dict):
        raise ValueError("Galician literal context: source identities missing")
    paper_identity = sources.get("paper_crosswalk_report")
    captures = sources.get("primary_captures")
    if not isinstance(paper_identity, dict) or not isinstance(captures, dict):
        raise ValueError("Galician literal context: source identities missing")
    paper = json.loads(_verified(repository, paper_identity))
    workbook = captures.get("dating_table")
    if not isinstance(workbook, dict):
        raise ValueError("Galician literal context: workbook identity missing")
    if workbook["path"] != WORKBOOK:
        raise ValueError("Galician literal context: workbook source differs")
    rows, summary = literal_context_rows(
        _verified(repository, workbook), paper["sample_label_to_biosample_crosswalk"]
    )
    with (output / TABLE).open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report["literal_context"] = summary
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
