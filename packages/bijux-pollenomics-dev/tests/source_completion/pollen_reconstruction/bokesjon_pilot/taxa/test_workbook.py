"""Explicit workbook cells retain their own source roles and zero authority."""

from __future__ import annotations

from typing import Any

import pytest


def workbook(cereal: Any = 0, ctype: int = 2) -> dict[str, Any]:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa.workbook import (
        audit_workbook_rows,
    )

    headers = [
        "Sample depth (cm)",
        "Sample age (LANDCLIM)",
        "Betula",
        "Triticum T.",
        "Hordeum T.",
        "Avena T.",
        "Secale cereale",
        "Number of counted markers",
        "Trees and shrubs",
        "Pollen sum",
        "indeterminata",
        "Indeterminata",
    ]
    values = [10, 2800, 20, cereal, 0, 0, 0, 100, 20, 20, 0, 0]
    rows = [
        {
            "row_zero_based": 1,
            "cells": [
                {"ctype": ctype if i == 3 else 2, "value": v}
                for i, v in enumerate(values)
            ],
        }
    ]
    return audit_workbook_rows(headers, rows, window=(2700, 3200))


def test_cereal_zeros_are_explicit_workbook_cells_not_native_observations() -> None:
    result = workbook()
    assert len(result["rows"][0]["cereal_cells"]) == 4
    assert all(
        c["state"] == "explicit_workbook_zero"
        for c in result["rows"][0]["cereal_cells"]
    )
    assert result["source_pollen_sum_total"] == 20
    assert result["all_biological_taxa_denominator"] is None
    roles = {c["source_label"]: c["source_role"] for c in result["rows"][0]["cells"]}
    assert roles["Number of counted markers"] == "laboratory_measurement"
    assert roles["Trees and shrubs"] == "source_group_summary"
    assert roles["Pollen sum"] == "source_denominator_summary"
    assert len(result["rows"][0]["cells"]) == 12


@pytest.mark.parametrize("value,ctype", [("", 0), ("0", 1), (True, 2), (-1, 2), (0, 3)])
def test_blank_text_and_invalid_cereal_cells_do_not_become_zeros(
    value: Any, ctype: int
) -> None:
    result = workbook(value, ctype)
    first = result["rows"][0]["cereal_cells"][0]
    assert first["state"] != "explicit_workbook_zero"
    assert first["count"] is None


def test_lab_and_age_numbers_are_not_misclassified_as_invalid_grain_counts() -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa.workbook import (
        audit_workbook_rows,
    )

    headers = [
        "Sample depth (cm)",
        "Sample age (LANDCLIM)",
        "Number of volumes 2 (1/4 cm3)",
        "Pollen sum",
    ]
    rows = [
        {
            "row_zero_based": 1,
            "cells": [{"ctype": 2, "value": v} for v in [12.5, 2800.5, 0.25, 10]],
        }
    ]
    result = audit_workbook_rows(headers, rows, window=(2700, 3200))
    cells = result["rows"][0]["cells"]
    assert cells[2]["state"] == "reported_non_count_numeric"
    assert cells[2]["count"] is None
    assert cells[1]["state"] == "reported_non_count_numeric"


def test_duplicate_workbook_owner_cannot_double_the_denominator() -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa.workbook import (
        audit_workbook_rows,
    )

    headers = ["Sample depth (cm)", "Sample age (LANDCLIM)", "Pollen sum"]
    row = {
        "row_zero_based": 1,
        "cells": [{"ctype": 2, "value": v} for v in [10, 2800, 20]],
    }
    with pytest.raises(ValueError, match="Duplicate"):
        audit_workbook_rows(headers, [row, row], window=(2700, 3200))
