"""Require source-exact ABBO radiocarbon control correspondence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.abbo_age_controls import (
    NEOTOMA,
    PROFILE,
    publish,
)

REPOSITORY = Path(__file__).resolve().parents[4]
SOURCE = (
    REPOSITORY.parent
    / "bijux-pollenomics-data/epd/pangaea/abbo-age-determination-pangaea-740080.tsv"
)
GOVERNED = REPOSITORY / "docs/report/source-relations/neotoma/abbo-age-controls"


def test_six_published_dates_match_neotoma_controls(tmp_path: Path) -> None:
    report = publish(REPOSITORY, SOURCE, tmp_path)
    assert (tmp_path / "report.json").read_bytes() == (
        GOVERNED / "report.json"
    ).read_bytes()
    assert report["exact_depth_lab_age_error_matches"] == 6
    assert report["neotoma_age_model"] == "linear interpolation"
    assert report["sample_age_uncertainty_bounds"] == (
        "not supplied in Neotoma sample ages"
    )
    assert {row["lab_number"] for row in report["controls"]} == {
        "Poz-4445",
        "Poz-4446",
        "Poz-4511",
        "Poz-4447",
        "Poz-4512",
        "Poz-4514",
    }


def test_changed_neotoma_radiocarbon_age_refuses_match(tmp_path: Path) -> None:
    raw = json.loads((REPOSITORY / NEOTOMA).read_text())
    abbo = next(
        row for row in raw["rows"] if row["site"]["dataset"]["datasetid"] == 19913
    )
    control = abbo["site"]["collectionunit"]["chronologies"][0]["chronology"][
        "chroncontrols"
    ][0]
    control["geochron"]["geochronage"] = 1661
    destination = tmp_path / NEOTOMA
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"rows": [abbo]}))
    profile = tmp_path / PROFILE
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.symlink_to(REPOSITORY / PROFILE)
    with pytest.raises(ValueError, match="date mismatch: Poz-4445"):
        publish(tmp_path, SOURCE, tmp_path / "output")
