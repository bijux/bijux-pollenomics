"""Verify real-count site holdouts and unavailable-window accounting."""

from __future__ import annotations

import csv

import pytest

from bijux_pollenomics_dev.essd_reproduction.observed_pollen_baseline import (
    SiteCounts,
    _site_counts,
    evaluate_grid,
)


def test_held_out_pollen_never_enters_its_training_mean() -> None:
    sites = [
        SiteCounts(
            "A", "a" * 64, {"50": {"oak": 10, "pine": 0}, "225": {"oak": 0, "pine": 10}}
        ),
        SiteCounts("B", "b" * 64, {"50": {"oak": 0, "pine": 10}}),
        SiteCounts("C", "c" * 64, {"50": {"oak": 0, "pine": 10}}),
    ]

    scores, predictions, summary = evaluate_grid(
        "512", ["50", "225"], ["oak", "pine"], sites
    )

    a = next(
        row
        for row in scores
        if row["held_out_site_id"] == "A" and row["bin_id_bp"] == "50"
    )
    assert a["mae_fraction"] == 1.0
    assert a["total_variation"] == 1.0
    a_oak = next(
        row
        for row in predictions
        if row["held_out_site_id"] == "A" and row["taxon"] == "oak"
    )
    assert a_oak["predicted_fraction"] == 0.0
    assert a_oak["observed_count"] == 10
    refused = next(
        row
        for row in scores
        if row["held_out_site_id"] == "A" and row["bin_id_bp"] == "225"
    )
    assert refused["status"] == "no_training_site_same_bin"
    assert summary["attempted_site_bins"] == 4
    assert summary["scored_site_bins"] == 3
    assert summary["refused_no_training_site_bins"] == 1


def test_source_reader_refuses_noninteger_counts_and_missing_basin(tmp_path) -> None:
    path = tmp_path / "LRAready_A.csv"

    def write(count: str, radius: str) -> None:
        with path.open("w", newline="") as stream:
            csv.writer(stream).writerows(
                [["TW", "50"], ["radius", radius], ["model", "2"], ["Oak", count]]
            )

    write("1.5", "150")
    with pytest.raises(ValueError, match="exact nonnegative integer"):
        _site_counts(path, "A", ["50"], ["Oak"], ["oak"])

    write("10", "0")
    with pytest.raises(ValueError, match="lacks basin inputs"):
        _site_counts(path, "A", ["50"], ["Oak"], ["oak"])


def test_source_reader_does_not_turn_zero_count_into_observation(tmp_path) -> None:
    path = tmp_path / "LRAready_A.csv"
    with path.open("w", newline="") as stream:
        csv.writer(stream).writerows(
            [
                ["TW", "50", "225"],
                ["radius", "150", "0"],
                ["model", "2", "0"],
                ["Oak", "10", "0"],
            ]
        )
    site = _site_counts(path, "A", ["50", "225"], ["Oak"], ["oak"])
    assert site.by_bin == {"50": {"oak": 10}}
    with pytest.raises(ValueError, match="axes differ"):
        _site_counts(path, "A", ["50", "250"], ["Oak"], ["oak"])
