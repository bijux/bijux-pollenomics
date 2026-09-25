"""Guard unique orthographic joins for Bussjösjön source counts."""

from __future__ import annotations

import pytest

from bijux_pollenomics_dev.source_completion.bussjosjon_native_counts import (
    compare_casefold_counts,
)


def _inputs():
    headers = ["BETULA", "PINUS", "BETULA"]
    rows = [
        {"sample_label": 0.0, "counts": [3, 5, 2]},
        {"sample_label": 20.0, "counts": [1, 0, 1]},
    ]
    samples = [
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
    assert report["cell_status_counts"] == {
        "absent_source_workbook_zero": 1,
        "explicit_agreement": 1,
        "explicit_neotoma_mass": 5,
        "workbook_mass_on_explicit_pairs": 5,
    }
    assert report["lra_admitted_samples"] == 0


def test_source_unit_and_sample_axis_refuse() -> None:
    headers, rows, samples = _inputs()
    samples[0]["datum"][0]["units"] = "percent"
    with pytest.raises(ValueError, match="no NISP count unit"):
        compare_casefold_counts(headers, rows, samples)
    samples[0]["datum"][0]["units"] = "NISP"
    rows[0]["sample_label"] = 1.0
    with pytest.raises(ValueError, match="sample-label axes differ"):
        compare_casefold_counts(headers, rows, samples)
