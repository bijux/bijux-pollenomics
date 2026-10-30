"""Keep native sample-cell evidence distinct from interpreted animal context."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
from io import BytesIO
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

import pytest

from bijux_pollenomics_dev.source_completion.adna import (
    galician_literal_context as context,
)

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


@pytest.fixture
def crosswalk() -> list[dict[str, Any]]:
    return [
        {
            "biosample_accession": f"SAMN181068{index + 27}",
            "paper_row": number,
            "paper_specimen_code": "UK-LU-01" if number == 27 else f"specimen-{number}",
            "paper_sample_label": "Bt_CO_(60BP)" if number == 27 else f"label-{number}",
            "source_species": "Bos primigenius" if index < 3 else "Bos taurus",
        }
        for index, number in enumerate([*range(16, 26), 27])
    ]


def _workbook(
    crosswalk: list[dict[str, Any]],
    changes: dict[str, tuple[str | None, str | None, str | None]] | None = None,
    *,
    missing: str | None = None,
    duplicate: bool = False,
) -> bytes:
    sheet = ET.Element(f"{{{NS}}}worksheet")
    data = ET.SubElement(sheet, f"{{{NS}}}sheetData")
    strings = ET.Element(f"{{{NS}}}sst")
    values: list[str] = []

    def shared(row: ET.Element, ref: str, value: str) -> ET.Element:
        item = ET.SubElement(strings, f"{{{NS}}}si")
        ET.SubElement(item, f"{{{NS}}}t").text = value
        values.append(value)
        cell = ET.SubElement(row, f"{{{NS}}}c", r=ref, t="s")
        ET.SubElement(cell, f"{{{NS}}}v").text = str(len(values) - 1)
        return cell

    header = ET.SubElement(data, f"{{{NS}}}row", r="15")
    for col, text in context.HEADERS.items():
        shared(header, f"{col}15", text)
    for item in crosswalk:
        number = item["paper_row"]
        row = ET.SubElement(data, f"{{{NS}}}row", r=str(number))
        literals = {
            "A": item["paper_specimen_code"],
            "B": "Chan do Lindeiro (entrance)" if number == 27 else " Cave site ",
            "C": item["source_species"],
            "D": "humerus",
            "E": "100% modern C" if number == 27 else "8297 ± 59 ",
            "F": "Beta-366974" if number == 27 else "Lab-12 (*)",
            "G": "9250 ± 215",
            "H": "last 60 years" if number == 27 else "7520 to 7090 BC",
            "I": "Recent" if number == 27 else "Mesolithic",
            "J": item["paper_sample_label"],
        }
        for col, literal in literals.items():
            ref = f"{col}{number}"
            if ref == missing:
                continue
            if ref == "G27":
                cell = ET.SubElement(row, f"{{{NS}}}c", r=ref, s="5")
            else:
                cell = shared(row, ref, literal)
            if changes and ref in changes:
                kind, raw, formula = changes[ref]
                cell.clear()
                cell.set("r", ref)
                cell.set("s", "14")
                if kind is not None:
                    cell.set("t", kind)
                if raw is not None:
                    if kind == "inlineStr":
                        inline = ET.SubElement(cell, f"{{{NS}}}is")
                        ET.SubElement(inline, f"{{{NS}}}t").text = raw
                    else:
                        ET.SubElement(cell, f"{{{NS}}}v").text = raw
                if formula is not None:
                    ET.SubElement(cell, f"{{{NS}}}f").text = formula
        if duplicate and number == 16:
            shared(row, "B16", "duplicate")
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(context.WORKSHEET, ET.tostring(sheet))
        archive.writestr("xl/sharedStrings.xml", ET.tostring(strings))
    return output.getvalue()


def test_exact_cells_retain_units_and_do_not_convert_label_age(
    crosswalk: list[dict[str, Any]],
) -> None:
    rows, summary = context.literal_context_rows(_workbook(crosswalk), crosswalk)
    assert len(rows) == 110
    assert Counter(row["biosample_accession"] for row in rows) == dict.fromkeys(
        (item["biosample_accession"] for item in crosswalk), 10
    )
    by_ref = {row["cell_reference"]: row for row in rows}
    assert by_ref["E16"]["resolved_literal"] == "8297 ± 59 "
    assert by_ref["B16"]["resolved_literal"] == " Cave site "
    assert by_ref["E16"]["source_header_literal"] == "Age 14C BP"
    assert by_ref["G16"]["source_header_literal"] == "Age cal BP (2-sigma)"
    assert by_ref["H16"]["source_header_literal"] == "Age cal BC/AD "
    assert by_ref["E27"]["paper_sample_label"] == "Bt_CO_(60BP)"
    assert by_ref["B27"]["resolved_literal"] == "Chan do Lindeiro (entrance)"
    assert by_ref["E27"]["resolved_literal"] == "100% modern C"
    assert by_ref["G27"]["cell_state"] == "present_blank"
    assert by_ref["G27"]["resolved_literal"] is None
    assert by_ref["H27"]["resolved_literal"] == "last 60 years"
    assert summary["cell_states"] == {"present_blank": 1, "present_value": 109}
    assert summary["paper_source_specimen_count"] == 18
    assert summary["biosample_count"] == 11
    for key in (
        "date_conversion_performed",
        "site_assignment_performed",
        "scientific_admission",
        "atlas_point_admitted",
    ):
        assert summary[key] is False


@pytest.mark.parametrize("mode", ["missing", "blank", "zero"])
def test_missing_blank_and_zero_are_distinct(
    crosswalk: list[dict[str, Any]], mode: str
) -> None:
    payload = _workbook(
        crosswalk,
        {"G27": (None, "0", None)} if mode == "zero" else None,
        missing="G27" if mode == "missing" else None,
    )
    rows, _ = context.literal_context_rows(payload, crosswalk)
    cell = next(row for row in rows if row["cell_reference"] == "G27")
    expected = {"missing": "missing", "blank": "present_blank", "zero": "present_value"}
    assert cell["cell_state"] == expected[mode]
    assert cell.get("resolved_literal") == ("0" if mode == "zero" else None)
    assert cell.get("value_element_present") is (
        True if mode == "zero" else False if mode == "blank" else None
    )


@pytest.mark.parametrize(
    ("kind", "literal"),
    [
        ("n", "43831"),
        ("b", "0"),
        ("e", "#VALUE!"),
        ("d", "2020-01-01"),
        ("inlineStr", " \u00a0text "),
        ("inlineStr", ""),
    ],
)
def test_native_types_and_date_styles_never_coerce_values(
    crosswalk: list[dict[str, Any]], kind: str, literal: str
) -> None:
    rows, _ = context.literal_context_rows(
        _workbook(crosswalk, {"G27": (kind, literal, None)}), crosswalk
    )
    cell = next(row for row in rows if row["cell_reference"] == "G27")
    assert cell["native_type_attribute"] == kind
    assert cell["native_style_attribute"] == "14"
    assert cell["resolved_literal"] == literal
    assert cell["formula_present"] is False


def test_formula_without_cache_does_not_invent_a_value(
    crosswalk: list[dict[str, Any]],
) -> None:
    rows, _ = context.literal_context_rows(
        _workbook(crosswalk, {"G27": ("n", None, "1950-1890")}), crosswalk
    )
    cell = next(row for row in rows if row["cell_reference"] == "G27")
    assert cell["cell_state"] == "present_value"
    assert cell["formula_present"] is True
    assert cell["value_element_present"] is False
    assert cell["native_value_literal"] is cell["resolved_literal"] is None


def test_formula_and_cached_value_are_evidence_not_a_computed_date(
    crosswalk: list[dict[str, Any]],
) -> None:
    rows, summary = context.literal_context_rows(
        _workbook(crosswalk, {"G27": ("n", "60", "1950-1890")}), crosswalk
    )
    cell = next(row for row in rows if row["cell_reference"] == "G27")
    assert cell["formula_present"] is True
    assert cell["formula_literal"] == "1950-1890"
    assert cell["native_value_literal"] == cell["resolved_literal"] == "60"
    assert summary["formula_cell_count"] == 1
    assert summary["date_conversion_performed"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate-cell",
        "specimen",
        "label",
        "formula-binding",
        "shared-index",
        "missing-binding",
    ],
)
def test_ambiguous_or_changed_identity_cells_refuse(
    crosswalk: list[dict[str, Any]], mutation: str
) -> None:
    changes: dict[str, dict[str, tuple[str | None, str | None, str | None]]] = {
        "specimen": {"A16": ("inlineStr", "foreign", None)},
        "label": {"J16": ("inlineStr", "foreign", None)},
        "formula-binding": {"A16": ("str", "specimen-16", '"specimen-16"')},
        "shared-index": {"G27": ("s", "-1", None)},
    }
    with pytest.raises(ValueError, match="cell|specimen|shared string"):
        context.literal_context_rows(
            _workbook(
                crosswalk,
                changes.get(mutation),
                duplicate=mutation == "duplicate-cell",
                missing="A16" if mutation == "missing-binding" else None,
            ),
            crosswalk,
        )


def test_crosswalk_cannot_repeat_or_invent_a_sample(
    crosswalk: list[dict[str, Any]],
) -> None:
    payload = _workbook(crosswalk)
    changed = [*crosswalk[:-1], crosswalk[0]]
    with pytest.raises(ValueError, match="population"):
        context.literal_context_rows(payload, changed)


def test_optional_writer_keeps_existing_species_output_and_preserves_csv_cells(
    tmp_path: Path, crosswalk: list[dict[str, Any]]
) -> None:
    root = tmp_path / "repository"
    workbook = root / context.WORKBOOK
    workbook.parent.mkdir(parents=True)
    payload = _workbook(crosswalk)
    workbook.write_bytes(payload)
    paper = root / "data/review.json"
    paper.write_text(json.dumps({"sample_label_to_biosample_crosswalk": crosswalk}))

    def identity(path: Path) -> dict[str, object]:
        raw = path.read_bytes()
        return {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }

    output = root / "artifacts/result"
    output.mkdir(parents=True)
    original = {
        "source_hashes": {
            "paper_crosswalk_report": identity(paper),
            "primary_captures": {"dating_table": identity(workbook)},
        },
        "unchanged_species": {"Bos taurus": 8, "Bos primigenius": 3},
    }
    (output / "report.json").write_text(json.dumps(original))
    (output / "samples.csv").write_bytes(b"original species output\n")
    context.write_literal_context(root, output)
    report = json.loads((output / "report.json").read_bytes())
    assert {
        key: value for key, value in report.items() if key != "literal_context"
    } == original
    assert (output / "samples.csv").read_bytes() == b"original species output\n"
    assert workbook.read_bytes() == payload
    with (output / context.TABLE).open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 110
    blank = next(row for row in rows if row["cell_reference"] == "G27")
    assert blank["cell_state"] == "present_blank"
    assert blank["value_element_present"] == "False"
    assert blank["native_type_attribute"] == blank["resolved_literal"] == ""
    assert (
        next(row for row in rows if row["cell_reference"] == "E16")["resolved_literal"]
        == "8297 ± 59 "
    )
