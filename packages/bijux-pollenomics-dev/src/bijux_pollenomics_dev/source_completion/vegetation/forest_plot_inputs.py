"""Read fixed EMPD2–NFI development leads without inferring missing measurements."""

from __future__ import annotations

from collections import Counter
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from math import isfinite
from pathlib import Path
import sqlite3
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from bijux_pollenomics_dev.source_completion import empd2_nfi, empd2_nfi_pairing
from bijux_pollenomics_dev.source_completion.empd2_nfi_reference.measurement_schema import (
    _shared_strings,
)

AXIS = ("Pinus", "Picea", "Betula")
POLLEN_VARIABLES = {75: "Pinus", 126: "Picea", 12: "Betula"}
BASAL_FIELDS = ("BaPine", "BaContorta", "BaSpruce", "BaBirch", "BaOtherDec")
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_BASE = Path("reference-sources/empd2-nfi")


@dataclass(frozen=True)
class PollenPanel:
    """Reported source-count support; absent rows have no invented zero."""

    counts: tuple[int | None, ...]
    reported_total: int | None
    selected_total: int | None
    excluded_total: int | None
    row_count: int
    noncanonical_alias_rows: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DevelopmentPair:
    """Public existing identities and measurements without private plot fields."""

    candidate_id: str
    plot_year_id: str
    plot_year_reuse: int
    basal_area: tuple[str | None, ...]
    basal_reasons: tuple[str, ...]
    pollen: PollenPanel


def _measurement(cell: ET.Element | None) -> tuple[str | None, str | None]:
    if cell is None:
        return None, "missing_basal_area"
    if cell.get("t") not in (None, "n") or cell.find(_NS + "f") is not None:
        return None, "unsupported_basal_area_cell"
    value = cell.findtext(_NS + "v")
    if value in (None, ""):
        return None, "missing_basal_area"
    assert value is not None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None, "invalid_basal_area"
    if not number.is_finite() or number < 0:
        return None, "invalid_basal_area"
    return value, None


def read_workbook(
    path: Path, selected: set[tuple[str, str, str]]
) -> tuple[
    list[tuple[str, str, str, str, float, float]],
    dict[tuple[str, str, str], tuple[tuple[str | None, ...], tuple[str, ...]]],
]:
    """Decode six metadata columns, and five outcome cells only on selected rows."""
    metadata = []
    measurements = {}
    header_seen = False
    with ZipFile(path) as archive:
        strings = _shared_strings(archive)
        with archive.open("xl/worksheets/sheet2.xml") as stream:
            root: ET.Element | None = None
            for event, row in ET.iterparse(stream, events=("start", "end")):
                if root is None and event == "start":
                    root = row
                if event != "end" or row.tag != _NS + "row":
                    continue
                cells = {
                    cell.get("r", "").rstrip("0123456789"): cell
                    for cell in row.findall(_NS + "c")
                }
                if row.get("r") == "1":
                    if header_seen:
                        raise ValueError("NFI native header is duplicated")
                    header = {
                        key: empd2_nfi._cell(cell, strings)
                        for key, cell in cells.items()
                    }
                    if tuple(header.get(c) for c in "ABCDEF") != empd2_nfi._HEADERS:
                        raise ValueError("NFI native identity columns changed")
                    if (
                        tuple(header.get(c) for c in ("Z", "AA", "AB", "AC", "AD"))
                        != BASAL_FIELDS
                    ):
                        raise ValueError("NFI native basal-area columns changed")
                    header_seen = True
                else:
                    if not header_seen:
                        raise ValueError("NFI native header is missing")
                    values = empd2_nfi._selected(row, strings)
                    if any(value in (None, "") for value in values):
                        raise ValueError("NFI native metadata are incomplete")
                    year, tract, plot, date, east, north = values
                    assert year and tract and plot and date and east and north
                    x, y = float(east), float(north)
                    if not (isfinite(x) and isfinite(y)):
                        raise ValueError("NFI native coordinates are nonfinite")
                    metadata.append((year, tract, plot, date, x, y))
                    key = (tract, plot, year)
                    if key in selected:
                        if key in measurements:
                            raise ValueError("NFI selected plot-year is duplicated")
                        found = [
                            _measurement(cells.get(c))
                            for c in ("Z", "AA", "AB", "AC", "AD")
                        ]
                        measurements[key] = (
                            tuple(value for value, _ in found),
                            tuple(sorted({reason for _, reason in found if reason})),
                        )
                row.clear()
                if root is not None:
                    root.clear()
    if not header_seen or set(measurements) != selected:
        raise ValueError("NFI selected plot-year population is incomplete")
    return metadata, measurements


def _count(value: object) -> int | None:
    if type(value) is int:
        return value if 0 <= value < 2**53 else None
    if (
        type(value) is float
        and isfinite(value)
        and 0 <= value < 2**53
        and value.is_integer()
    ):
        return int(value)
    return None


def read_pollen(path: Path, samples: set[str]) -> dict[str, PollenPanel]:
    """Use exact canonical native genus IDs, without source alias aggregation."""
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        for variable, name in POLLEN_VARIABLES.items():
            found = db.execute(
                "SELECT acc_var_,original_varname,acc_varname,groupid FROM p_vars WHERE var_=?",
                (variable,),
            ).fetchall()
            if found != [(variable, name, name, "TRSH")]:
                raise ValueError("EMPD2 literal genus dictionary changed")
        result = {}
        for sample in sorted(samples):
            flags = db.execute(
                "SELECT ispercent,isdigitised FROM metadata WHERE samplename=?",
                (sample,),
            ).fetchall()
            reasons: set[str] = set()
            if flags != [(0, 0)]:
                reasons.add("pollen_count_units_or_digitisation_unresolved")
            rows = db.execute(
                'SELECT c.var_,c."count",v.acc_var_ FROM p_counts c '
                "LEFT JOIN p_vars v ON v.var_=c.var_ WHERE c.samplename=? ORDER BY c.var_",
                (sample,),
            ).fetchall()
            if len({row[0] for row in rows}) != len(rows):
                raise ValueError("EMPD2 native count variable is duplicated")
            parsed = {variable: _count(value) for variable, value, _ in rows}
            if not rows or any(value is None for value in parsed.values()):
                reasons.add("invalid_or_missing_native_pollen_count")
            counts = tuple(parsed.get(variable) for variable in (75, 126, 12))
            if any(variable not in parsed for variable in POLLEN_VARIABLES):
                reasons.add("absent_literal_pollen_genus_row")
            total = sum(value for value in parsed.values() if value is not None)
            reported = (
                total if rows and all(v is not None for v in parsed.values()) else None
            )
            selected_total = (
                sum(value for value in counts if value is not None)
                if all(v is not None for v in counts)
                else None
            )
            excluded = (
                reported - selected_total
                if reported is not None and selected_total is not None
                else None
            )
            result[sample] = PollenPanel(
                counts,
                reported,
                selected_total,
                excluded,
                len(rows),
                sum(
                    variable not in POLLEN_VARIABLES and canonical in POLLEN_VARIABLES
                    for variable, _, canonical in rows
                ),
                tuple(sorted(reasons)),
            )
        return result
    finally:
        db.close()


def read_inputs(
    repository: Path, private_source_store: Path
) -> tuple[tuple[DevelopmentPair, ...], int]:
    """Bind the fixed sixteen leads to existing public opaque identities."""
    schema_name = "docs/report/validation/empd2-nfi-pairing/nfi-measurement-schema.json"
    lock = json.loads((repository / "reports/source-lock.json").read_text())
    schema = empd2_nfi._read_pinned_json(
        repository / schema_name, lock["sources"][schema_name]
    )
    if (
        schema.get("source_sha256") != empd2_nfi_pairing.NFI_SHA256
        or schema.get("candidate_tree_basal_area_unit") != "m2/ha"
        or schema.get("candidate_tree_basal_area_fields")
        != {
            "BaPine": "Basal area of pine (m2/ha)",
            "BaContorta": "Basal area of contorta (m2/ha)",
            "BaSpruce": "Basal area of spruce (m2/ha)",
            "BaBirch": "Basal area of birch (m2/ha)",
            "BaOtherDec": "Basal area of other deciduous species (m2/ha)",
        }
        or schema.get("plot_area_description")
        != "Circular plot r=7 => 153.94 m2 (only un-divided plots included)"
        or schema.get("source_plot_support", {}).get("plot_area_m2_each") != 153.94
    ):
        raise ValueError("NFI basal-area unit or plot-support source basis changed")
    projection, dossier, _ = empd2_nfi_pairing.review_inputs(
        repository, private_source_store
    )
    source_root = private_source_store / _BASE
    workbook, pollen = (
        source_root / "nfi/swedish-plot-data.xlsx",
        source_root / "empd2/source.sqlite3",
    )
    for path, checksum in (
        (workbook, empd2_nfi_pairing.NFI_SHA256),
        (pollen, empd2_nfi_pairing.EMPD2_SHA256),
    ):
        if (
            any(p.is_symlink() for p in (path, *path.parents))
            or empd2_nfi_pairing._file_sha(path) != checksum
        ):
            raise ValueError("Original measured source identity changed")
    candidates = projection["candidate_rows"]
    selected = {(r["nfi_tract"], r["nfi_plot"], r["nfi_year"]) for r in candidates}
    if len(candidates) != 16 or len(selected) != 14:
        raise ValueError("Frozen development population changed")
    metadata, measured = read_workbook(workbook, selected)
    decisions = empd2_nfi_pairing.decision_rows(projection, dossier, metadata)
    public = empd2_nfi_pairing.public_rows(decisions)
    published_path = repository / "docs/report/validation/empd2-nfi-pairing/pairs.csv"
    with published_path.open(newline="") as stream:
        published = list(csv.DictReader(stream))
    fields = ("candidate_id", "nfi_row_identity_sha256", "empd2_sample")
    if sorted(tuple(row[f] for f in fields) for row in public) != sorted(
        tuple(row[f] for f in fields) for row in published
    ):
        raise ValueError("Existing public development identities changed")
    panels = read_pollen(pollen, {r["pollen_sample"] for r in candidates})
    by_sample = {r["empd2_sample"]: r for r in public}
    reused = Counter(r["nfi_row_identity_sha256"] for r in public)
    pairs = []
    for candidate in sorted(candidates, key=lambda r: r["pollen_sample"]):
        item = by_sample[candidate["pollen_sample"]]
        candidate_id, plot_year_id = (
            item["candidate_id"],
            item["nfi_row_identity_sha256"],
        )
        if not isinstance(candidate_id, str) or not isinstance(plot_year_id, str):
            raise ValueError("Existing public identities must be strings")
        key = (candidate["nfi_tract"], candidate["nfi_plot"], candidate["nfi_year"])
        values, reasons = measured[key]
        pairs.append(
            DevelopmentPair(
                candidate_id,
                plot_year_id,
                reused[plot_year_id],
                values,
                reasons,
                panels[candidate["pollen_sample"]],
            )
        )
    for path, checksum in (
        (workbook, empd2_nfi_pairing.NFI_SHA256),
        (pollen, empd2_nfi_pairing.EMPD2_SHA256),
    ):
        if empd2_nfi_pairing._file_sha(path) != checksum:
            raise ValueError("Measured source changed during decoding")
    return tuple(pairs), len({(tract, plot) for tract, plot, _ in selected})
