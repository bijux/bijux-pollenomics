"""Retain explicit BOKE workbook cells without inventing a biological denominator."""

from __future__ import annotations

from collections.abc import Sequence
import hashlib
from math import isfinite
from pathlib import Path
from typing import Any

CEREALS = ("Triticum T.", "Hordeum T.", "Avena T.", "Secale cereale")
GROUPS = frozenset(
    {
        "Trees and shrubs",
        "Forest herbs and ferns",
        "Dry pastures",
        "Fresh meadows and pastures",
        "Ruderal communities",
        "Cultivated land",
        "Mire plants, wet meadows, lake shores",
        "Littoral vegetation",
        "True aquatics",
        "Pediastrum",
    }
)


def _role(label: str) -> str:
    if label == "Sample depth (cm)":
        return "sample_depth"
    if label == "Sample age (LANDCLIM)":
        return "source_age_label"
    if label == "Samplenumbers":
        return "sample_identifier"
    if label.startswith("Number of "):
        return "laboratory_measurement"
    if label.startswith("Pollen sum"):
        return "source_denominator_summary"
    if label in GROUPS:
        return "source_group_summary"
    if label == "Indeterminata":
        return "auxiliary_unidentified_summary"
    return "specimen_variable_unclassified"


def _count(cell: dict[str, Any]) -> tuple[int | None, str]:
    value = cell["value"]
    if cell["ctype"] in (0, 6):
        return None, "unavailable_blank_workbook_cell"
    if (
        cell["ctype"] != 2
        or isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        return None, "unavailable_non_numeric_workbook_cell"
    if not isfinite(value) or value < 0 or value != int(value):
        return None, "invalid_workbook_count"
    return int(
        value
    ), "explicit_workbook_positive" if value else "explicit_workbook_zero"


def audit_workbook_rows(
    headers: Sequence[str], rows: Sequence[dict[str, Any]], *, window: tuple[int, int]
) -> dict[str, Any]:
    """Separate specimen candidates, source summaries and laboratory variables."""
    if tuple(headers[:2]) != ("Sample depth (cm)", "Sample age (LANDCLIM)") or len(
        headers
    ) != len(set(headers)):
        raise ValueError("Workbook header identity is invalid")
    if window[0] >= window[1]:
        raise ValueError("Invalid workbook window")
    if len({r["row_zero_based"] for r in rows}) != len(rows):
        raise ValueError("Duplicate workbook source row")
    selected = []
    unknown = []
    for row in rows:
        if len(row["cells"]) != len(headers):
            raise ValueError("Workbook rectangle is incomplete")
        age_cell = row["cells"][1]
        age = age_cell["value"]
        if (
            age_cell["ctype"] != 2
            or isinstance(age, bool)
            or not isinstance(age, (int, float))
            or not isfinite(age)
        ):
            unknown.append(row["row_zero_based"])
            continue
        if not window[0] <= age < window[1]:
            continue
        cells = []
        for index, (label, cell) in enumerate(zip(headers, row["cells"], strict=True)):
            count, state = _count(cell)
            role = _role(label)
            if role in {
                "sample_depth",
                "source_age_label",
                "sample_identifier",
                "laboratory_measurement",
            }:
                value = cell["value"]
                numeric = (
                    cell["ctype"] == 2
                    and not isinstance(value, bool)
                    and isinstance(value, (int, float))
                    and isfinite(value)
                )
                count, state = (
                    None,
                    "reported_non_count_numeric"
                    if numeric
                    else "unavailable_non_count_value",
                )
            cells.append(
                {
                    "column_zero_based": index,
                    "source_label": label,
                    "source_role": role,
                    "ctype": cell["ctype"],
                    "value": cell["value"],
                    "count": count,
                    "state": state,
                }
            )
        by_label = {c["source_label"]: c for c in cells}
        cereal_cells = [
            by_label.get(
                label,
                {
                    "source_label": label,
                    "count": None,
                    "state": "missing_source_column",
                },
            )
            for label in CEREALS
        ]
        selected.append(
            {
                "row_zero_based": row["row_zero_based"],
                "depth_cm": row["cells"][0]["value"],
                "age_landclim": age,
                "cells": cells,
                "cereal_cells": cereal_cells,
                "source_pollen_sum": by_label.get("Pollen sum", {}).get("count"),
            }
        )
    sums = [row["source_pollen_sum"] for row in selected]
    return {
        "schema_version": "bokesjon-pilot-workbook-taxon-window.v1",
        "window": list(window),
        "source_row_count": len(rows),
        "header_count": len(headers),
        "rows": selected,
        "unassignable_age_rows": unknown,
        "source_pollen_sum_total": sum(sums)
        if sums and all(s is not None for s in sums) and not unknown
        else None,
        "all_biological_taxa_denominator": None,
        "native_zero_conversion_applied": False,
        "interpretation": "Explicit cells belong to this workbook only. Specimen-variable candidates include pollen, spores, stomata and algae; source groups/denominators and markers are not independent biological taxa. Source Pollen sum is not automatically a qualified terrestrial-pollen universe. No native identity, chronology-model equivalence or redistribution approval is inferred.",
    }


def audit_workbook_window(
    path: Path, *, window: tuple[int, int], expected_sha256: str
) -> dict[str, Any]:
    """Decode the pinned BOKE rectangle with the maintained optional xlrd owner."""
    from bijux_pollenomics.collection.sources.rootsi.cells.decoding import parser

    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != expected_sha256:
        raise ValueError("Workbook source identity changed")
    book = parser().open_workbook(file_contents=body, formatting_info=True)
    try:
        sheets = book.sheets()
        if len(sheets) != 1 or sheets[0].nrows != 53 or sheets[0].ncols != 168:
            raise ValueError("Expected the pinned BOKE53x168rectangle")
        sheet = sheets[0]
        headers = [str(sheet.cell(0, c).value) for c in range(sheet.ncols)]
        rows = [
            {
                "row_zero_based": r,
                "cells": [
                    {"ctype": sheet.cell(r, c).ctype, "value": sheet.cell(r, c).value}
                    for c in range(sheet.ncols)
                ],
            }
            for r in range(1, sheet.nrows)
        ]
        result = audit_workbook_rows(headers, rows, window=window)
        return {
            **result,
            "source_sha256": expected_sha256,
            "source_bytes": len(body),
            "sheet": sheet.name,
        }
    finally:
        book.release_resources()
