"""Protect source separation and uncertainty in the Swedish lake comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.swedish_lake_trajectory import (
    LINEAGE,
    PREPARED,
    SEAD,
    publish,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = REPOSITORY / "docs/report/countries/sweden/observed-pollen-trajectory"


def test_governed_trajectory_keeps_pollen_and_context_roles(tmp_path: Path) -> None:
    report = publish(REPOSITORY, tmp_path)
    assert (tmp_path / "report.json").read_bytes() == (
        GOVERNED / "report.json"
    ).read_bytes()
    assert (tmp_path / "transitions.csv").read_bytes() == (
        GOVERNED / "transitions.csv"
    ).read_bytes()
    assert report["bin_count"] == 13
    assert report["transition_count"] == 48
    assert {row["pollen_site_direction_outcome"] for row in report["transitions"]} == {
        "descriptive_agreement",
        "descriptive_contradiction",
        "cannot_conclude_denominator_or_effect_threshold",
    }
    assert {row["land_use_outcome"] for row in report["windows"]} == {
        "cannot_conclude_no_independent_vegetation_measurement"
    }
    bus = report["windows"][2]["observations"]["BUS"]["sead_chronology_context"]
    assert bus["10km_neotoma_point"]["dated_feature_count"] == 129
    assert bus["10km_inventory_point"]["dated_feature_count"] == 115


def test_sample_age_bounds_change_requires_new_review(tmp_path: Path) -> None:
    for source in (SEAD, LINEAGE, PREPARED / "dataset-54001.json"):
        destination = tmp_path / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(REPOSITORY / source)
    source = REPOSITORY / PREPARED / "dataset-53995.json"
    data = json.loads(source.read_text())
    data["sample_age_bounds_present"] = True
    destination = tmp_path / PREPARED / "dataset-53995.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Sample-age uncertainty contract changed"):
        publish(tmp_path, tmp_path / "output")
