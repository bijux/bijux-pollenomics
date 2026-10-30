"""Synthetic native-cell and source-count contracts; no private outcomes opened."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sqlite3
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from bijux_pollenomics_dev.source_completion import empd2_nfi, empd2_nfi_pairing
from bijux_pollenomics_dev.source_completion.vegetation import (
    forest_plot_inputs as subject,
)

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
KEY = ("private-tract", "private-plot", "2013")


def cell(
    value: str | None, *, kind: str | None = None, formula: bool = False
) -> ET.Element:
    result = ET.Element(NS + "c")
    if kind:
        result.set("t", kind)
    if formula:
        ET.SubElement(result, NS + "f").text = "1+1"
    if value is not None:
        ET.SubElement(result, NS + "v").text = value
    return result


def workbook(
    path: Path,
    values: tuple[str | None, ...],
    *,
    duplicate: bool = False,
    header: bool = True,
) -> None:
    root = ET.Element(NS + "worksheet")
    data = ET.SubElement(root, NS + "sheetData")
    columns = ("A", "B", "C", "D", "E", "F", "Z", "AA", "AB", "AC", "AD")
    headers = (*empd2_nfi._HEADERS, *subject.BASAL_FIELDS)
    if header:
        row = ET.SubElement(data, NS + "row", r="1")
        for column, header_value in zip(columns, headers, strict=True):
            item = cell(header_value)
            item.set("r", column + "1")
            row.append(item)
    for index in range(2, 4 if duplicate else 3):
        row = ET.SubElement(data, NS + "row", r=str(index))
        native = (KEY[2], KEY[0], KEY[1], "41350", "500000", "6500000", *values)
        for column, value in zip(columns, native, strict=True):
            item = cell(value)
            item.set("r", column + str(index))
            row.append(item)
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", f'<sst xmlns="{NS[1:-1]}"/>')
        archive.writestr("xl/worksheets/sheet2.xml", ET.tostring(root))


def database(
    path: Path,
    counts: tuple[tuple[int, object], ...],
    *,
    flags: tuple[int | None, int | None] = (0, 0),
) -> None:
    with sqlite3.connect(path) as db:
        db.executescript(
            "CREATE TABLE p_vars(var_ INTEGER,acc_var_ INTEGER,original_varname TEXT,acc_varname TEXT,groupid TEXT);"
            "CREATE TABLE metadata(samplename TEXT,ispercent INTEGER,isdigitised INTEGER);"
            'CREATE TABLE p_counts(samplename TEXT,var_ INTEGER,"count" NUMERIC);'
        )
        db.executemany(
            "INSERT INTO p_vars VALUES(?,?,?,?,?)",
            [
                (variable, variable, name, name, "TRSH")
                for variable, name in subject.POLLEN_VARIABLES.items()
            ],
        )
        db.execute("INSERT INTO p_vars VALUES(900,75,'Pinus:fragment','Pinus','TRSH')")
        db.execute("INSERT INTO metadata VALUES('sample',?,?)", flags)
        db.executemany("INSERT INTO p_counts VALUES('sample',?,?)", counts)


def test_native_basal_literals_zero_and_exact_selected_rows(tmp_path: Path) -> None:
    path = tmp_path / "source.xlsx"
    workbook(path, ("0", "0.10", "1.25", "2", "3e-2"))
    metadata, measured = subject.read_workbook(path, {KEY})
    assert metadata == [("2013", KEY[0], KEY[1], "41350", 500000.0, 6500000.0)]
    assert measured == {KEY: (("0", "0.10", "1.25", "2", "3e-2"), ())}
    # Unselected outcomes do not become an opportunistic expanded cohort.
    assert subject.read_workbook(path, set())[1] == {}


@pytest.mark.parametrize(
    "duplicate,header,selected",
    [
        (True, True, {KEY}),
        (False, False, {KEY}),
        (False, True, {("other", "plot", "2013")}),
    ],
)
def test_native_source_identity_population_refuses(
    tmp_path: Path, duplicate: bool, header: bool, selected: set[tuple[str, str, str]]
) -> None:
    path = tmp_path / "source.xlsx"
    workbook(path, ("1",) * 5, duplicate=duplicate, header=header)
    with pytest.raises(ValueError):
        subject.read_workbook(path, selected)


@pytest.mark.parametrize(
    "value,kind,formula,reason",
    [
        (None, None, False, "missing_basal_area"),
        ("", None, False, "missing_basal_area"),
        ("0", "b", False, "unsupported_basal_area_cell"),
        ("0", "s", False, "unsupported_basal_area_cell"),
        ("2", None, True, "unsupported_basal_area_cell"),
        (None, None, True, "unsupported_basal_area_cell"),
        ("-1", None, False, "invalid_basal_area"),
        ("NaN", None, False, "invalid_basal_area"),
        ("Infinity", None, False, "invalid_basal_area"),
        ("unknown", None, False, "invalid_basal_area"),
    ],
)
def test_native_missing_or_unsupported_basal_cell(
    value: str | None, kind: str | None, formula: bool, reason: str
) -> None:
    assert subject._measurement(cell(value, kind=kind, formula=formula)) == (
        None,
        reason,
    )


def test_literal_genera_exclude_aliases_and_keep_reported_denominators(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.sqlite3"
    database(path, ((75, 0), (126, 3), (12, 7), (900, 11), (999, 13)))
    panel = subject.read_pollen(path, {"sample"})["sample"]
    assert panel == subject.PollenPanel((0, 3, 7), 34, 10, 24, 5, 1, ())


@pytest.mark.parametrize(
    "value", [None, -1, 0.5, float("inf"), "unknown", 2**53, 2**53 + 1]
)
def test_invalid_native_counts_remain_missing_and_refused(
    tmp_path: Path, value: object
) -> None:
    path = tmp_path / "source.sqlite3"
    database(path, ((75, value), (126, 3), (12, 7)))
    panel = subject.read_pollen(path, {"sample"})["sample"]
    assert panel.counts == (None, 3, 7)
    assert panel.reported_total is panel.selected_total is panel.excluded_total is None
    assert panel.reasons == ("invalid_or_missing_native_pollen_count",)


def test_absent_genus_is_not_explicit_zero(tmp_path: Path) -> None:
    path = tmp_path / "source.sqlite3"
    database(path, ((126, 3), (12, 7)))
    panel = subject.read_pollen(path, {"sample"})["sample"]
    assert panel.counts == (None, 3, 7)
    assert panel.reported_total == 10 and panel.selected_total is None
    assert panel.reasons == ("absent_literal_pollen_genus_row",)


def test_missing_unselected_count_never_certifies_complete_reported_sum(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.sqlite3"
    database(path, ((75, 2), (126, 3), (12, 7), (900, None)))
    panel = subject.read_pollen(path, {"sample"})["sample"]
    assert panel.counts == (2, 3, 7) and panel.selected_total == 12
    assert panel.reported_total is panel.excluded_total is None
    assert panel.reasons == ("invalid_or_missing_native_pollen_count",)


@pytest.mark.parametrize("flags", [(1, 0), (0, 1), (None, 0)])
def test_percentage_or_digitised_or_unresolved_source_refuses(
    tmp_path: Path, flags: tuple[int | None, int | None]
) -> None:
    path = tmp_path / "source.sqlite3"
    database(path, ((75, 2), (126, 3), (12, 7)), flags=flags)
    assert subject.read_pollen(path, {"sample"})["sample"].reasons == (
        "pollen_count_units_or_digitisation_unresolved",
    )


@pytest.mark.parametrize("change", ["dictionary", "duplicate"])
def test_genus_identity_or_native_join_duplication_refuses(
    tmp_path: Path, change: str
) -> None:
    path = tmp_path / "source.sqlite3"
    database(path, ((75, 2), (126, 3), (12, 7)))
    with sqlite3.connect(path) as db:
        if change == "dictionary":
            db.execute("UPDATE p_vars SET original_varname='Pinus:type' WHERE var_=75")
        else:
            db.execute("INSERT INTO p_counts VALUES('sample',75,2)")
    with pytest.raises(ValueError):
        subject.read_pollen(path, {"sample"})


def test_count_admission_precedes_float_conversion_and_sums_as_python_int(
    tmp_path: Path,
) -> None:
    assert subject._count(True) is None
    assert subject._count(3.0) == 3
    path = tmp_path / "source.sqlite3"
    database(path, ((75, 2**53 - 1), (126, 2), (12, 2)))
    panel = subject.read_pollen(path, {"sample"})["sample"]
    assert panel.selected_total == 2**53 + 3
    assert not panel.reasons


def test_frozen_public_identities_and_plot_year_groups_are_reused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "shared"
    paths = source / subject._BASE
    for relative in ("nfi/swedish-plot-data.xlsx", "empd2/source.sqlite3"):
        path = paths / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"controlled-original")
    candidates = [
        {
            "pollen_sample": f"sample-{i}",
            "nfi_tract": "private",
            "nfi_plot": str(i % 14),
            "nfi_year": "2013",
        }
        for i in range(16)
    ]
    public = [
        {
            "candidate_id": f"existing-{i}",
            "nfi_row_identity_sha256": f"opaque-{i % 14}",
            "empd2_sample": f"sample-{i}",
        }
        for i in range(16)
    ]
    destination = tmp_path / "repo/docs/report/validation/empd2-nfi-pairing/pairs.csv"
    destination.parent.mkdir(parents=True)
    schema = {
        "source_sha256": empd2_nfi_pairing.NFI_SHA256,
        "candidate_tree_basal_area_unit": "m2/ha",
        "candidate_tree_basal_area_fields": dict(
            zip(
                subject.BASAL_FIELDS,
                (
                    f"Basal area of {name} (m2/ha)"
                    for name in (
                        "pine",
                        "contorta",
                        "spruce",
                        "birch",
                        "other deciduous species",
                    )
                ),
                strict=True,
            )
        ),
        "plot_area_description": "Circular plot r=7 => 153.94 m2 (only un-divided plots included)",
        "source_plot_support": {"plot_area_m2_each": 153.94},
    }
    schema_path = destination.with_name("nfi-measurement-schema.json")
    schema_path.write_text(json.dumps(schema))
    lock = tmp_path / "repo/reports/source-lock.json"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps(
            {
                "sources": {
                    schema_path.relative_to(
                        tmp_path / "repo"
                    ).as_posix(): hashlib.sha256(schema_path.read_bytes()).hexdigest()
                }
            }
        )
    )
    with destination.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, public[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(public)
    monkeypatch.setattr(
        empd2_nfi_pairing,
        "review_inputs",
        lambda *_: ({"candidate_rows": candidates}, {}, {}),
    )
    monkeypatch.setattr(
        empd2_nfi_pairing,
        "_file_sha",
        lambda p: (
            empd2_nfi_pairing.NFI_SHA256
            if p.suffix == ".xlsx"
            else empd2_nfi_pairing.EMPD2_SHA256
        ),
    )
    monkeypatch.setattr(
        subject,
        "read_workbook",
        lambda _p, keys: ([], dict.fromkeys(keys, (("1",) * 5, ()))),
    )
    monkeypatch.setattr(empd2_nfi_pairing, "decision_rows", lambda *_: [])
    monkeypatch.setattr(empd2_nfi_pairing, "public_rows", lambda _: public)
    panel = subject.PollenPanel((1, 2, 3), 6, 6, 0, 3, 0, ())
    monkeypatch.setattr(
        subject, "read_pollen", lambda _p, names: dict.fromkeys(names, panel)
    )
    result, physical_plots = subject.read_inputs(tmp_path / "repo", source)
    assert physical_plots == 14
    assert len(result) == 16 and len({row.plot_year_id for row in result}) == 14
    assert (
        next(row for row in result if row.candidate_id == "existing-0").plot_year_reuse
        == 2
    )
    assert {row.candidate_id for row in result} == {
        row["candidate_id"] for row in public
    }
    destination.write_text(destination.read_text().replace("existing-0", "different-0"))
    with pytest.raises(ValueError, match="public development identities"):
        subject.read_inputs(tmp_path / "repo", source)
    schema_path.write_text(schema_path.read_text() + " ")
    with pytest.raises(ValueError, match="input_digest_mismatch"):
        subject.read_inputs(tmp_path / "repo", source)
    schema["candidate_tree_basal_area_unit"] = "m2/plot"
    schema_path.write_text(json.dumps(schema))
    lock.write_text(
        json.dumps(
            {
                "sources": {
                    schema_path.relative_to(
                        tmp_path / "repo"
                    ).as_posix(): hashlib.sha256(schema_path.read_bytes()).hexdigest()
                }
            }
        )
    )
    with pytest.raises(ValueError, match="unit or plot-support"):
        subject.read_inputs(tmp_path / "repo", source)
