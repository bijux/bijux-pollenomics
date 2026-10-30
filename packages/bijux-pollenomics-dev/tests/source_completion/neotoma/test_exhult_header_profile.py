"""Declared exact presentation-header profiles for controlled Exhult cells."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.neotoma import exhult_cells as cells

from .test_exhult_count_correspondence import datum, sample, workbook


def profiled_row() -> dict[str, Any]:
    row = workbook()
    labels = [*cells.LATIN_HEADERS, "Unselected", "Duplicate", "Duplicate"]
    row["features"] = [
        {"column": col + 3, "label": label, "value": value, "type": 2}
        for col, (label, value) in enumerate(
            zip(labels, (2, 3, 0, 100, 0, 0), strict=True)
        )
    ]
    return row


def profiled_native() -> dict[str, Any]:
    source = sample()
    source["datum"] += [datum("Pinus", 4, taxonid=200)]
    return source


def test_declared_three_header_profile_has_complete_disjoint_partition() -> None:
    row, source = profiled_row(), profiled_native()
    original = deepcopy((row, source))
    outputs, summary = cells.compare([row], [source], profile="explicit-latin-headers")
    result = outputs[0]
    assert result["explicit_agreement"] == result["explicit_difference"] == 1
    assert result["absent_source_workbook_zero"] == 1
    assert result["absent_source_workbook_positive"] == 0
    assert result["excluded_nonselected_header"] == 1
    assert result["duplicate_workbook_label"] == 2
    assert sum(summary["cell_status_counts"].values()) == 6
    assert summary["selected_profile_columns"] == 3
    assert summary["workbook_feature_columns"] == 6
    assert summary["declared_header_pairs"] == cells.LATIN_HEADERS
    assert result["paired_workbook_mass"] == 5
    assert result["paired_native_nisp_mass"] == 6
    assert result["exceptions"][0]["label"] == r"\iPinus\i (tall)"
    assert result["native_only_labels"] == []
    assert (row, source) == original


def test_literal_default_does_not_apply_presentation_profile() -> None:
    inputs = [profiled_row()], [profiled_native()]
    implicit = cells.compare(*inputs)
    explicit = cells.compare(*inputs, profile="literal")
    assert implicit == explicit
    rows, summary = implicit
    assert summary["declared_header_pairs"] == {}
    assert rows[0]["explicit_agreement"] == rows[0]["explicit_difference"] == 0
    assert rows[0]["absent_source_workbook_positive"] == 3
    assert "excluded_nonselected_header" not in rows[0]


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "stripped", "case", "common_name"]
)
def test_profile_requires_all_three_complete_exact_headers_once(change: str) -> None:
    row = profiled_row()
    if change == "missing":
        row["features"].pop(0)
    elif change == "duplicate":
        row["features"].append(deepcopy(row["features"][0]))
    else:
        row["features"][0]["label"] = {
            "stripped": "Betula",
            "case": r"\iBETULA\i (björk)",
            "common_name": r"\iBetula\i (birch)",
        }[change]
    with pytest.raises(ValueError, match="present exactly once"):
        cells.compare([row], [profiled_native()], profile="explicit-latin-headers")


@pytest.mark.parametrize("ambiguity", ["anchor", "variable", "repeated_datum"])
def test_profile_does_not_bypass_native_ambiguity(ambiguity: str) -> None:
    row, sources = profiled_row(), [profiled_native()]
    if ambiguity == "anchor":
        sources.append(profiled_native())
        sources[-1]["sampleid"] = 11
    elif ambiguity == "variable":
        second = profiled_native()
        second["sampleid"], second["depth"] = 11, 2
        second["datum"][0]["taxonid"] = 101
        sources.append(second)
    else:
        sources[0]["datum"].append(deepcopy(sources[0]["datum"][0]))
    outputs, _ = cells.compare([row], sources, profile="explicit-latin-headers")
    assert outputs[0]["explicit_agreement"] == 0
    if ambiguity == "anchor":
        assert outputs[0]["unassessed_anchor"] == 3
    else:
        assert outputs[0]["ambiguous_source"] == 1


@pytest.mark.parametrize("explicit_zero", [False, True])
def test_profile_keeps_absent_zero_distinct_from_native_zero(
    explicit_zero: bool,
) -> None:
    source = profiled_native()
    if explicit_zero:
        source["datum"].append(datum("Alnus", 0, taxonid=300))
    outputs, _ = cells.compare(
        [profiled_row()], [source], profile="explicit-latin-headers"
    )
    assert outputs[0]["explicit_agreement"] == (2 if explicit_zero else 1)
    assert outputs[0]["absent_source_workbook_zero"] == (0 if explicit_zero else 1)


def test_nonselected_literal_name_does_not_expand_declared_panel() -> None:
    row = profiled_row()
    row["features"][3]["label"] = "Betula"
    outputs, _ = cells.compare(
        [row], [profiled_native()], profile="explicit-latin-headers"
    )
    assert outputs[0]["explicit_agreement"] == 1
    assert outputs[0]["excluded_nonselected_header"] == 1
