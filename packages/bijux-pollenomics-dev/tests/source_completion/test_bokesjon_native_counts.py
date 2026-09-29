"""Guard Bökesjön explicit counts, fractional depths and missing rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.bokesjon_native_counts import (
    _source_samples,
    _workbook,
    compare_cells,
)

REPOSITORY = Path(__file__).resolve().parents[4]
SOURCE = (
    REPOSITORY.parent
    / "bijux-pollenomics-data/landclim/rootsi-workbooks/rootsi/BOKE.xls"
)
GOVERNED = (
    REPOSITORY / "docs/report/source-relations/neotoma/boke-native-correspondence"
)


def _inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    workbook = [
        {
            "sample_depth_label": 207.5,
            "age_label": 10.02,
            "counts": {"Pediastrum": 3, "Betula": 1},
        },
        {
            "sample_depth_label": 12.0,
            "age_label": 20.0,
            "counts": {"Pediastrum": 0, "Betula": 5},
        },
    ]

    def age(value: float) -> list[dict[str, Any]]:
        return [
            {
                "chronologyname": "LANDCLIM",
                "agetype": "Calibrated radiocarbon years BP",
                "age": value,
                "ageolder": None,
                "ageyounger": None,
            }
        ]

    samples = [
        {
            "sampleid": 1,
            "depth": 207.5,
            "ages": age(10.0),
            "datum": [
                {
                    "variablename": "Pediastrum",
                    "value": 2,
                    "units": "NISP",
                    "element": "pollen",
                    "elementtype": "pollen",
                }
            ],
        },
        {
            "sampleid": 2,
            "depth": 12,
            "ages": age(20),
            "datum": [{"variablename": "Betula", "value": 5, "units": "NISP"}],
        },
    ]
    return workbook, samples


def test_fractional_depth_keeps_discrepancy_and_absent_source_distinct() -> None:
    workbook, samples = _inputs()
    cells, report = compare_cells(["Pediastrum", "Betula"], workbook, samples)
    assert len(cells) == 4
    assert report["cell_status_counts"] == {
        "absent_source_workbook_positive": 1,
        "absent_source_workbook_zero": 1,
        "explicit_agreement": 1,
        "explicit_difference": 1,
        "explicit_neotoma_mass": 7,
        "workbook_mass_on_explicit_pairs": 8,
    }
    assert report["max_absolute_numeric_age_label_difference"] == pytest.approx(0.02)
    assert report["age_labels_within_0_05_of_neotoma"] == 2
    assert report["lra_admitted_samples"] == 0


def test_retained_source_replays_governed_numeric_alignment() -> None:
    if not SOURCE.is_file():
        pytest.skip("Private Rootsi workbook is not installed")
    taxa, rows = _workbook(SOURCE)
    samples = _source_samples(
        REPOSITORY / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json"
    )
    _, summary = compare_cells(taxa, rows, samples)
    governed = json.loads((GOVERNED / "report.json").read_text())
    assert summary["age_labels_within_0_05_of_neotoma"] == 52
    difference = summary["max_absolute_numeric_age_label_difference"]
    assert isinstance(difference, (int, float))
    assert difference < 0.05
    assert summary == {key: governed[key] for key in summary}


def test_invalid_count_unit_and_depth_axis_refuse() -> None:
    workbook, samples = _inputs()
    samples[0]["datum"][0]["units"] = "percent"
    with pytest.raises(ValueError, match="no NISP count unit"):
        compare_cells(["Pediastrum", "Betula"], workbook, samples)
    samples[0]["datum"][0]["units"] = "NISP"
    workbook[0]["sample_depth_label"] = 208.5
    with pytest.raises(ValueError, match="depth axes differ"):
        compare_cells(["Pediastrum", "Betula"], workbook, samples)


def test_repeated_source_name_keeps_distinct_elements() -> None:
    workbook, samples = _inputs()
    samples[0]["datum"].append(
        {
            "variablename": "Pediastrum",
            "value": 1,
            "units": "NISP",
            "element": "colony",
            "elementtype": "colony",
        }
    )
    cells, report = compare_cells(["Pediastrum", "Betula"], workbook, samples)
    selected = next(
        row
        for row in cells
        if row["sample_depth_label"] == 207.5
        and row["taxon_exact_label"] == "Pediastrum"
    )
    assert selected["status"] == "ambiguous_source_duplicate"
    assert selected["neotoma_explicit_nisp"] == ""
    counts = report["cell_status_counts"]
    assert isinstance(counts, dict)
    assert counts["ambiguous_source_duplicate"] == 1
