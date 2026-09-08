from __future__ import annotations

from pathlib import Path
from typing import cast
from unittest.mock import patch

from bijux_pollenomics.adna.projects.registry import sample_truth


def test_null_chronology_is_not_zero_bp() -> None:
    linked: dict[str, object] = {"paper_url": "https://example.test/paper"}
    null_start: dict[str, object] = {
        **linked,
        "chronology": {"time_start_bp": None, "time_end_bp": 0},
    }
    null_end: dict[str, object] = {
        **linked,
        "chronology": {"time_start_bp": 0, "time_end_bp": None},
    }
    zero_interval: dict[str, object] = {
        **linked,
        "chronology": {"time_start_bp": 0, "time_end_bp": 0},
        "coordinates": {
            "latitude_text": "0",
            "longitude_text": "0",
            "confidence": "exact",
        },
    }

    assert sample_truth._sample_truth_status(null_start) == "blocked_weak_chronology"
    assert sample_truth._sample_truth_status(null_end) == "blocked_weak_chronology"
    assert sample_truth._sample_truth_status(zero_interval) == "fully_grounded"


def test_project_grouping_retains_input_order() -> None:
    first: dict[str, object] = {
        "project_accession": " PRJ-B ",
        "identity": {"stable_token": "first"},
    }
    second: dict[str, object] = {
        "project_accession": "PRJ-A",
        "identity": {"stable_token": "second"},
    }
    third: dict[str, object] = {
        "project_accession": "PRJ-B",
        "identity": {"stable_token": "third"},
    }

    grouped = sample_truth._group_sample_rows_by_project([first, second, third])

    assert list(grouped) == ["PRJ-B", "PRJ-A"]
    assert grouped["PRJ-B"] == [first, third]


def test_aggregation_uses_facade_patch_seams() -> None:
    empty_truth: dict[str, object] = {"project_rows": []}
    with (
        patch.object(
            sample_truth,
            "build_animal_sample_foundation_truth",
            return_value=empty_truth,
        ) as foundation,
        patch.object(
            sample_truth, "build_project_locality_count_drift", return_value=()
        ),
        patch.object(sample_truth, "build_species_sample_count_drift", return_value=()),
        patch.object(sample_truth, "_load_all_sample_rows", return_value=[]) as samples,
        patch.object(sample_truth, "_load_all_locality_rows", return_value=[]),
    ):
        payload = sample_truth.build_animal_sample_aggregation_warnings(
            Path("data"), Path("report")
        )

    summary = cast(dict[str, object], payload["summary"])
    assert summary["total_sample_row_count"] == 0
    foundation.assert_called_once_with(Path("data"))
    samples.assert_called_once_with(Path("data"))
