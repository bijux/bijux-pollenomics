"""Reconcile literal horse date fields to existing sample and chronology owners."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path

from ...identity import _clean_optional_source_text
from .cells import _SHEET_PART, _horse_cell, _horse_literal_cells

_HORSE_WORKBOOK = (
    "adna/governance/source_library/papers/10.1016-j.cell.2019.03.049/"
    "supplementary/1-s2.0-S0092867419303848-mmc1.xlsx"
)

_SOURCE_COLUMNS = ("D", "R", "S", "T", "U", "V", "W", "X")


def horse_source_chronology_fields(
    output_root: Path, *, owners: Mapping[str, tuple[str, str, str]]
) -> dict[str, dict[str, object]]:
    """Join native date fields to existing owners; confer no age-selection authority.

    Each owner supplies its sample label, physical row locator and logical source
    path from the maintained chronology consumer. The source supplies the complete
    horse population independently; neither a date nor a coordinate selects rows.
    """
    if not owners:
        return {}
    source = Path(output_root) / _HORSE_WORKBOOK
    if not source.exists():
        return {
            key: {
                "schema_version": "horse-source-chronology-fields.v1",
                "evidence_role": "source_context_only",
                "status": "refused",
                "reason_code": "horse_source_workbook_missing",
                "source_workbook": {
                    "path": f"data/{_HORSE_WORKBOOK}",
                    "sha256": None,
                    "byte_count": None,
                    "historical_acquisition_authenticated": False,
                },
                "repo_stable_sample_id": key,
                "source_population": None,
                "date_conversion_performed": False,
                "formula_evaluation_performed": False,
                "selected_chronology_changed": False,
                "scientific_admission": False,
            }
            for key in owners
        }
    if not source.is_file():
        raise ValueError("Horse source workbook is not a regular file")
    if source.is_symlink() or not source.resolve(strict=True).is_relative_to(
        Path(output_root).resolve(strict=True)
    ):
        raise ValueError("Horse source workbook escapes its governing data root")
    before = source.stat()
    if before.st_size > 4_000_000:
        raise ValueError("Horse source workbook exceeds the bounded reader limit")
    payload = source.read_bytes()
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Horse source workbook changed during reading")
    cells, physical_rows, merges = _horse_literal_cells(payload)
    for column, expected in {
        "A": "Sample name",
        "B": "Registration number",
        "I": "Species",
        "D": "Age (years ago) ",
    }.items():
        if _horse_cell(cells, f"{column}4")["resolved_literal"] != expected:
            raise ValueError("Horse source identity/date header differs")
    headers = [
        _horse_cell(cells, f"{column}{row}")
        for column in _SOURCE_COLUMNS
        for row in range(1, 5)
    ]
    source_owners: dict[str, tuple[int, str, str]] = {}
    excluded: Counter[str] = Counter()
    for row in physical_rows:
        if row <= 4:
            continue
        label = str(_horse_cell(cells, f"A{row}")["resolved_literal"] or "").strip()
        species = str(_horse_cell(cells, f"I{row}")["resolved_literal"] or "").strip()
        if not label or (species and species.casefold() != "horse"):
            excluded[species or "missing_sample_label"] += 1
            continue
        registration = str(_horse_cell(cells, f"B{row}")["resolved_literal"] or "")
        anchor = _clean_optional_source_text(registration) or label
        key = f"prjeb31613:{anchor}".casefold()
        if key in source_owners:
            raise ValueError("Horse source owner anchor is duplicated")
        source_owners[key] = (row, label, registration)
    if source_owners.keys() != owners.keys():
        raise ValueError("Horse source rows and chronology owners do not reconcile")
    column_counts: dict[str, dict[str, int]] = {}
    for column in _SOURCE_COLUMNS:
        states = Counter(
            str(_horse_cell(cells, f"{column}{row}")["cell_state"])
            for row, _, _ in source_owners.values()
        )
        column_counts[column] = {
            state: states[state]
            for state in ("present_value", "present_blank", "missing_cell")
        }
        column_counts[column]["formula_present"] = sum(
            _horse_cell(cells, f"{column}{row}")["formula_present"] is True
            for row, _, _ in source_owners.values()
        )
    result: dict[str, dict[str, object]] = {}
    for key, (row, label, registration) in source_owners.items():
        if owners[key] != (label, f"Sheet1!row{row}", f"data/{_HORSE_WORKBOOK}"):
            raise ValueError(
                "Horse chronology owner identity or physical locator differs"
            )
        result[key] = {
            "schema_version": "horse-source-chronology-fields.v1",
            "evidence_role": "source_context_only",
            "status": "retained_literal_source_fields",
            "source_workbook": {
                "path": f"data/{_HORSE_WORKBOOK}",
                "sha256": sha256(payload).hexdigest(),
                "byte_count": len(payload),
                "historical_acquisition_authenticated": False,
                "custody_limit": "Retained metadata describes a DOI-keyed local supplement stash; no historical source digest is supplied.",
            },
            "worksheet": "Sheet1",
            "worksheet_part": _SHEET_PART,
            "physical_row_number": row,
            "repo_stable_sample_id": key,
            "sample_label_literal": _horse_cell(cells, f"A{row}")["resolved_literal"],
            "registration_literal": registration,
            "identity_cells": [
                _horse_cell(cells, f"{column}{row}") for column in ("A", "B", "I")
            ],
            "header_cells": headers,
            "worksheet_merged_ranges": list(merges),
            "fields": [
                _horse_cell(cells, f"{column}{row}") for column in _SOURCE_COLUMNS
            ],
            "source_population": {
                "physical_data_rows": sum(number > 4 for number in physical_rows),
                "horse_rows": len(source_owners),
                "matched_chronology_owners": len(owners),
                "excluded_rows_by_source_species": dict(sorted(excluded.items())),
                "field_cell_states_by_column": column_counts,
            },
            "date_conversion_performed": False,
            "formula_evaluation_performed": False,
            "selected_chronology_changed": False,
            "scientific_admission": False,
        }
    return result
