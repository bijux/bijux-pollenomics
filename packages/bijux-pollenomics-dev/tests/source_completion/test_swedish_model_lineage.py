"""Keep modeled cover from becoming an independent pollen validation claim."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.swedish_model_lineage import (
    COHORT,
    SITES,
    SYNTHESIS,
    publish,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = REPOSITORY / "docs/report/countries/sweden/pollen-model-lineage"


def test_published_grid_lineage_is_replayable(tmp_path: Path) -> None:
    report = publish(REPOSITORY, tmp_path)
    assert (tmp_path / "report.json").read_bytes() == (
        GOVERNED / "report.json"
    ).read_bytes()
    assert report["matched_site_count"] == 3
    assert report["targets_sharing_bus_boke_grid"] == 5
    assert {
        row["target"]
        for row in report["targets"]
        if row["independent_model_validation"] == "unassessed"
    } == {"Finjasjön"}


def test_changed_site_sample_count_refuses_identity(tmp_path: Path) -> None:
    for source in (SITES, SYNTHESIS):
        destination = tmp_path / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(REPOSITORY / source)
    source_cohort = REPOSITORY / COHORT
    with source_cohort.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    rows[1]["sample_count"] = "70"
    destination = tmp_path / COHORT
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="metadata mismatch: 937075:BUS"):
        publish(tmp_path, tmp_path / "output")
