"""Worksheet ownership controls and independent original-file result observation."""

from __future__ import annotations

import argparse
import csv
import hashlib
from io import BytesIO
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pytest

NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _controlled_workbook(
    *,
    owner: str | None = None,
    duplicate: bool = False,
    missing: bool = False,
    formula: bool = False,
) -> bytes:
    from bijux_pollenomics_dev.source_completion.adna.mccoll_sample_context.workbook import (
        HEADERS,
        OWNERS,
        SHEETS,
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        workbook = ET.Element("{" + NS["x"] + "}workbook")
        sheets = ET.SubElement(workbook, "{" + NS["x"] + "}sheets")
        relationships = ET.Element(
            "Relationships",
            xmlns="http://schemas.openxmlformats.org/package/2006/relationships",
        )
        for ordinal, (table, name) in enumerate(SHEETS.items(), start=1):
            ET.SubElement(
                sheets,
                "{" + NS["x"] + "}sheet",
                {
                    "name": name,
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id": f"r{ordinal}",
                },
            )
            ET.SubElement(
                relationships,
                "Relationship",
                Id=f"r{ordinal}",
                Target=f"worksheets/sheet{ordinal}.xml",
            )
            tree = ET.Element("{" + NS["x"] + "}worksheet")
            data = ET.SubElement(tree, "{" + NS["x"] + "}sheetData")
            for number in [1, *OWNERS[table]]:
                row = ET.SubElement(data, "{" + NS["x"] + "}row", r=str(number))
                for column, header in HEADERS[table].items():
                    if (
                        missing
                        and table == "S5.1"
                        and number == 2323
                        and column == "AG"
                    ):
                        continue
                    cell = ET.SubElement(
                        row,
                        "{" + NS["x"] + "}c",
                        r=f"{column}{number}",
                        t="inlineStr",
                        s="3",
                    )
                    inline = ET.SubElement(cell, "{" + NS["x"] + "}is")
                    literal = (
                        header
                        if number == 1
                        else OWNERS[table][number]
                        if column == "A"
                        else "NA"
                    )
                    if (
                        owner is not None
                        and table == "S1.1"
                        and number == 575
                        and column == "A"
                    ):
                        literal = owner
                    ET.SubElement(inline, "{" + NS["x"] + "}t").text = literal
                    if formula and table == "S1.1" and number == 575 and column == "H":
                        cell.remove(inline)
                        cell.attrib.pop("t")
                        ET.SubElement(
                            cell, "{" + NS["x"] + "}f", t="normal"
                        ).text = "1+2"
                        ET.SubElement(cell, "{" + NS["x"] + "}v").text = "63.1232200"
                if duplicate and table == "S1.1" and number == 575:
                    ET.SubElement(row, "{" + NS["x"] + "}c", r="A575")
            archive.writestr(f"xl/worksheets/sheet{ordinal}.xml", ET.tostring(tree))
        archive.writestr("xl/workbook.xml", ET.tostring(workbook))
        archive.writestr("xl/_rels/workbook.xml.rels", ET.tostring(relationships))
    return buffer.getvalue()


def test_only_six_descriptive_rows_and_literal_missing_states() -> None:
    from bijux_pollenomics_dev.source_completion.adna.mccoll_sample_context.workbook import (
        literal_rows,
    )

    rows = literal_rows(_controlled_workbook(missing=True))
    assert len(rows) == 6 and sum(len(r["fields"]) for r in rows) == 162
    assert rows[0]["fields"]["H"]["resolved_literal"] == "NA"
    assert rows[-1]["fields"]["AG"]["cell_state"] == "missing_cell"
    assert all("AH" not in r["fields"] for r in rows)


@pytest.mark.parametrize("change", [{"owner": "another specimen"}, {"duplicate": True}])
def test_original_ownership_cannot_be_replaced_or_duplicated(
    change: dict[str, Any],
) -> None:
    from bijux_pollenomics_dev.source_completion.adna.mccoll_sample_context.workbook import (
        literal_rows,
    )

    with pytest.raises(ValueError, match="owner"):
        literal_rows(_controlled_workbook(**change))


def test_formula_cache_is_preserved_without_recalculation() -> None:
    from bijux_pollenomics_dev.source_completion.adna.mccoll_sample_context.workbook import (
        literal_rows,
    )

    cell = literal_rows(_controlled_workbook(formula=True))[0]["fields"]["H"]
    assert cell["resolved_literal"] == cell["native_value_literal"] == "63.1232200"
    assert cell["formula_literal"] == "1+2" and cell["formula_attributes"] == {
        "t": "normal"
    }


@pytest.mark.parametrize("duplicate", [False, True])
def test_aadr_descriptive_dates_remain_literal(tmp_path: Path, duplicate: bool) -> None:
    from bijux_pollenomics_dev.source_completion.adna.mccoll_sample_context.aadr import (
        PREFIXES,
        source_rows,
    )

    path = tmp_path / "source.anno"
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(["Genetic ID", *PREFIXES.values()])
        for sample in [
            "CGG_2_105915.SG",
            "CGG_2_105915.SG" if duplicate else "CGG_2_105916.SG",
        ]:
            writer.writerow(
                [
                    sample,
                    *[
                        "NA" if key == "dating_method" else "1025±125 BP"
                        for key in PREFIXES
                    ],
                ]
            )
    if duplicate:
        with pytest.raises(ValueError, match="two-conflict source population"):
            source_rows(path, "1240k")
    else:
        rows = source_rows(path, "1240k")
        assert rows[0]["fields"]["dating_method"]["literal"] == "NA"
        assert rows[0]["fields"]["date_mean_bp"]["literal"] == "1025±125 BP"


@pytest.mark.parametrize("mutation", ["none", "workbook", "pdf", "aadr"])
def test_publish_refuses_input_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    from bijux_pollenomics_dev.source_completion.adna.mccoll_sample_context import (
        workflow,
    )
    from bijux_pollenomics_dev.source_completion.adna.mccoll_sample_context.aadr import (
        PREFIXES,
        source_rows,
    )
    from bijux_pollenomics_dev.source_completion.adna.mccoll_sample_context.workbook import (
        literal_rows,
    )

    repository, sources = tmp_path / "repository", tmp_path / "originals"
    sources.mkdir()
    country = repository / workflow.COUNTRY
    country.mkdir(parents=True)
    (repository / "artifacts").mkdir()
    pinned = {}
    for name in workflow.SOURCES:
        body = (
            _controlled_workbook()
            if name == "media-1.xlsx"
            else b"Controlled identity fixture; not a source publication"
        )
        (sources / name).write_bytes(body)
        pinned[name] = (len(body), hashlib.sha256(body).hexdigest())
    monkeypatch.setattr(workflow, "SOURCES", pinned)
    monkeypatch.setattr(workflow, "revision", lambda _: "controlled-source")
    inputs = []
    for panel in ("1240k", "ho"):
        path = repository / "data/aadr/v66" / panel / "source.anno"
        path.parent.mkdir(parents=True)
        with path.open("w", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t")
            writer.writerow(["Genetic ID", *PREFIXES.values()])
            for sample in ("CGG_2_105915.SG", "CGG_2_105916.SG"):
                writer.writerow([sample, *["NA" for _ in PREFIXES]])
        inputs.append(
            {"path": str(path.relative_to(repository)), **workflow.identity(path)}
        )
    (country / "report.json").write_text(json.dumps({"source_inputs": inputs}))
    with (country / "decisions.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["genetic_id", "spatial_reason"])
        writer.writerows(
            (sample, "raw_country_conflict")
            for sample in ("CGG_2_105915.SG", "CGG_2_105916.SG")
        )

    def read_aadr(path: Path, panel: str) -> list[dict[str, Any]]:
        rows = source_rows(path, panel)
        if mutation == "workbook":
            (sources / "media-1.xlsx").write_bytes(b"changed before parsing")
        return rows

    def read_workbook(payload: bytes) -> list[dict[str, Any]]:
        rows = literal_rows(payload)
        if mutation == "pdf":
            (sources / "media-2.pdf").write_bytes(b"changed while reading")
        elif mutation == "aadr":
            (repository / inputs[0]["path"]).write_bytes(b"changed while reading")
        return rows

    monkeypatch.setattr(workflow, "source_rows", read_aadr)
    monkeypatch.setattr(workflow, "literal_rows", read_workbook)
    output = repository / "artifacts/context"
    if mutation == "none":
        assert (
            workflow.publish(repository, sources, output)["selected_descriptive_cells"]
            == 162
        )
    else:
        with pytest.raises(
            ValueError,
            match="Parsed McColl workbook identity differs|changed during reading",
        ):
            workflow.publish(repository, sources, output)
        assert not output.exists()


def observe(source_root: Path, repository: Path, result_path: Path) -> dict[str, Any]:
    """Reconstruct selected cells/ANNO records with stdlib, not the producer."""
    result = json.loads(result_path.read_bytes())

    def verify(path: Path, expected: dict[str, Any]) -> None:
        digest = hashlib.sha256()
        byte_count = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                byte_count += len(block)
        assert (
            digest.hexdigest() == expected["sha256"] and byte_count == expected["bytes"]
        )

    assert len(result["prepared_source_inputs"]) == 4
    assert {s["path"] for s in result["prepared_source_inputs"]} == {
        "2024.03.13.584607v2.full.pdf",
        "media-1.xlsx",
        "media-2.pdf",
        "media-15.pdf",
    }
    for source in result["prepared_source_inputs"]:
        verify(source_root / source["path"], source)
    expected_rows = {
        ("S1.1", 575),
        ("S1.1", 588),
        ("S1.1", 589),
        ("S1.1", 590),
        ("S1.1", 745),
        ("S5.1", 2323),
    }
    assert {
        (r["table"], r["physical_row"]) for r in result["workbook_rows"]
    } == expected_rows
    checked = 0
    with ZipFile(source_root / "media-1.xlsx") as archive:
        shared = [
            "".join(n.text or "" for n in s.findall(".//x:t", NS))
            for s in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall(
                "x:si", NS
            )
        ]
        for source in result["workbook_rows"]:
            assert (source["sheet_name"], source["worksheet_part"]) == (
                {
                    "S1.1": (
                        "S1.1. New Ancient Samples metad",
                        "xl/worksheets/sheet1.xml",
                    ),
                    "S5.1": (
                        "S5.1. Clustered Ancient Samples",
                        "xl/worksheets/sheet2.xml",
                    ),
                }[source["table"]]
            )
            assert source["owner_literal"] == source["fields"]["A"]["resolved_literal"]
            tree = ET.fromstring(archive.read(source["worksheet_part"]))
            cells = {
                node.attrib["r"]: node
                for node in tree.findall("x:sheetData/x:row/x:c", NS)
            }
            expected_columns = (
                set("ABCDEFGHIJKLMNOPQR")
                | {"U", "V", "W", "X", "Y", "Z", "AA", "AB", "AC", "AD", "AG"}
                if source["table"] == "S1.1"
                else set("ABCDEFGHIJKLMNO") | {"R", "AG"}
            )
            assert set(source["fields"]) == expected_columns
            for column, saved in source["fields"].items():
                reference = column + str(source["physical_row"])
                assert saved["reference"] == reference
                node = cells.get(reference)
                assert node is not None
                value, formula, inline = (
                    node.find("x:v", NS),
                    node.find("x:f", NS),
                    node.find("x:is", NS),
                )
                raw = None if value is None else value.text
                literal = (
                    shared[int(raw)]
                    if node.get("t") == "s" and raw is not None
                    else raw
                )
                if node.get("t") == "inlineStr" and inline is not None:
                    literal = "".join(
                        n.text or "" for n in inline.findall(".//x:t", NS)
                    )
                assert saved["formula_present"] == (formula is not None)
                assert saved["value_element_present"] == (value is not None)
                assert saved["inline_string_present"] == (inline is not None)
                assert saved["native_type_attribute"] == node.get("t")
                assert saved["native_style_attribute"] == node.get("s")
                assert (
                    saved["native_value_literal"] == raw
                    and saved["resolved_literal"] == literal
                )
                assert saved["formula_literal"] == (
                    None if formula is None else formula.text
                )
                assert saved["formula_attributes"] == (
                    {} if formula is None else dict(formula.attrib)
                )
                assert saved["cell_state"] == (
                    "present_blank"
                    if value is None and formula is None and inline is None
                    else "present_value"
                )
                header = cells[column + "1"]
                token = header.find("x:v", NS)
                assert token is not None and token.text is not None
                assert (
                    saved["header_literal"] == shared[int(token.text)]
                    and saved["header_reference"] == column + "1"
                )
                checked += 1
    assert checked == result["selected_descriptive_cells"] == 162
    assert len(result["aadr_rows"]) == 4
    matched_aadr = set()
    assert len(result["aadr_source_inputs"]) == 2
    for source in result["aadr_source_inputs"]:
        verify(repository / source["path"], source)
        with (repository / source["path"]).open(newline="") as stream:
            reader = csv.reader(stream, delimiter="\t")
            anno_header = next(reader)
            for number, row in enumerate(reader, start=2):
                for saved in result["aadr_rows"]:
                    if (
                        saved["panel"]
                        == ("1240k" if "/1240k/" in source["path"] else "ho")
                        and row[0] == saved["genetic_id"]
                    ):
                        matched_aadr.add((saved["panel"], saved["genetic_id"]))
                        assert saved["physical_row"] == number
                        assert all(
                            row[anno_header.index(cell["source_header"])]
                            == cell["literal"]
                            for cell in saved["fields"].values()
                        )
    assert matched_aadr == {
        (panel, sample)
        for panel in ("1240k", "ho")
        for sample in ("CGG_2_105915.SG", "CGG_2_105916.SG")
    }
    for name, expected in result["existing_country_account"].items():
        path = (
            repository / "reports/science/aadr-nordic-entities/country-support" / name
        )
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"]
    country_csv = (
        repository
        / "reports/science/aadr-nordic-entities/country-support/decisions.csv"
    )
    with country_csv.open(newline="") as stream:
        actual_conflicts = [
            row
            for row in csv.DictReader(stream)
            if row["genetic_id"] in {"CGG_2_105915.SG", "CGG_2_105916.SG"}
        ]
    assert len(actual_conflicts) == len(result["existing_country_conflicts"]) == 2
    assert sorted(actual_conflicts, key=lambda row: row["genetic_id"]) == sorted(
        result["existing_country_conflicts"], key=lambda row: row["genetic_id"]
    )
    for source in result["prepared_source_inputs"]:
        verify(source_root / source["path"], source)
    for source in result["aadr_source_inputs"]:
        verify(repository / source["path"], source)
    assert all(
        result[key] is False
        for key in (
            "date_conversion_performed",
            "coordinate_correction_performed",
            "merged_samples_counted_as_independent",
            "scientific_admission",
            "publisher_sources_redistributed",
        )
    )
    return {
        "status": "passed",
        "prepared_originals": 4,
        "original_rows": 6,
        "descriptive_cells": checked,
        "aadr_source_rows": 4,
        "country_decisions_unchanged": True,
        "interpretation_or_admission": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.output.exists():
        raise SystemExit("Refuse occupied observer output")
    summary = observe(arguments.source_root, arguments.repository, arguments.result)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))
