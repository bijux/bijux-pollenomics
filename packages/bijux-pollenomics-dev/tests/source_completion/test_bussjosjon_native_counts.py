"""Guard unique orthographic joins for Bussjösjön source counts."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.bussjosjon_native_counts import (
    _source_samples,
    _workbook,
    compare_casefold_counts,
)

REPOSITORY = Path(__file__).resolve().parents[4]
SOURCE = (
    Path(
        os.environ.get(
            "BIJUX_POLLENOMICS_SOURCE_ROOT",
            REPOSITORY.parent / "-bijux-pollenomics-data",
        )
    )
    / "landclim/rootsi-workbooks/rootsi/BUS.xls"
)
GOVERNED = REPOSITORY / "docs/report/source-relations/neotoma/bus-native-correspondence"


def _inputs() -> tuple[list[str], list[dict[str, object]], list[dict[str, object]]]:
    headers = ["BETULA", "PINUS", "BETULA"]
    rows: list[dict[str, object]] = [
        {"sample_label": 0.0, "counts": [3, 5, 2]},
        {"sample_label": 20.0, "counts": [1, 0, 1]},
    ]
    samples: list[dict[str, object]] = [
        {
            "sampleid": 1,
            "depth": 0,
            "datum": [{"variablename": "Pinus", "value": 5, "units": "NISP"}],
        },
        {
            "sampleid": 2,
            "depth": 20,
            "datum": [{"variablename": "Betula", "value": 2, "units": "NISP"}],
        },
    ]
    return headers, rows, samples


def test_unique_casefold_labels_keep_duplicate_columns_excluded() -> None:
    headers, rows, samples = _inputs()
    cells, report = compare_casefold_counts(headers, rows, samples)
    assert len(cells) == 2
    assert report["unique_casefold_shared_taxon_labels"] == 1
    assert report["excluded_duplicate_workbook_labels"] == {"betula": [0, 2]}
    assert report["zero_only_duplicate_column_candidates"] == []
    assert report["cell_status_counts"] == {
        "absent_source_workbook_zero": 1,
        "explicit_agreement": 1,
        "explicit_neotoma_mass": 5,
        "workbook_mass_on_explicit_pairs": 5,
    }
    assert report["lra_admitted_samples"] == 0


def test_retained_zero_only_columns_remain_unapplied_candidates() -> None:
    if not SOURCE.is_file():
        pytest.skip("Private Rootsi workbook is not installed")
    headers, rows = _workbook(SOURCE)
    samples = _source_samples(
        REPOSITORY / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json"
    )
    _, summary = compare_casefold_counts(headers, rows, samples)
    governed = json.loads((GOVERNED / "report.json").read_text())
    assert summary == {key: governed[key] for key in summary}
    candidates = summary["zero_only_duplicate_column_candidates"]
    assert isinstance(candidates, list)
    assert all(isinstance(row, dict) for row in candidates)
    assert {row["casefold_label"] for row in candidates} == {"betula", "pinus"}
    assert sum(row["equal_pairs"] for row in candidates) == 138
    assert sum(row["source_mass"] for row in candidates) == 9076
    statuses = summary["cell_status_counts"]
    assert isinstance(statuses, dict)
    assert statuses["explicit_neotoma_mass"] == 44079


def test_source_unit_and_sample_axis_refuse() -> None:
    headers, rows, samples = _inputs()
    datum = samples[0]["datum"]
    assert isinstance(datum, list)
    first_datum = datum[0]
    assert isinstance(first_datum, dict)
    first_datum["units"] = "percent"
    with pytest.raises(ValueError, match="no NISP count unit"):
        compare_casefold_counts(headers, rows, samples)
    first_datum["units"] = "NISP"
    rows[0]["sample_label"] = 1.0
    with pytest.raises(ValueError, match="sample-label axes differ"):
        compare_casefold_counts(headers, rows, samples)


def test_repository_root_exposes_the_retained_correspondence_report() -> None:
    """Verify the actual repository locator without reading a private workbook."""
    assert (REPOSITORY / "configs/ci/report-ownership.json").is_file()
    assert GOVERNED.is_relative_to(REPOSITORY / "docs/report")
    assert (GOVERNED / "report.json").is_file()
