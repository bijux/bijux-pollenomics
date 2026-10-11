"""Require source-exact ABBO radiocarbon control correspondence."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion import abbo_age_controls as study
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


@pytest.fixture
def control_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Exercise control matching using repository-retained facts, without a source claim."""
    retained = json.loads((GOVERNED / "report.json").read_text())
    rows = ["\t".join(study.EXPECTED_COLUMNS)]
    for control in retained["controls"]:
        values = (
            str(Decimal(str(control["depth_cm"])) / 100),
            "10",
            "fixture material",
            str(Decimal(str(control["radiocarbon_bp"])) / 1000),
            str(Decimal(str(control["radiocarbon_error_older_bp"])) / 1000),
            str(Decimal(str(control["radiocarbon_error_younger_bp"])) / 1000),
            control["lab_number"],
        )
        rows.append("\t".join(values))
    source = tmp_path / "control-fixture.tsv"
    source.write_text(
        "Repository facts fixture; not an independent publisher capture.\n"
        "10.1594/PANGAEA.740080; Creative Commons Attribution-NonCommercial 3.0\n"
        "*/\n" + "\n".join(rows) + "\n"
    )
    monkeypatch.setattr(
        study, "SOURCE_SHA256", hashlib.sha256(source.read_bytes()).hexdigest()
    )
    return source


def test_six_retained_control_facts_match_neotoma_controls(
    tmp_path: Path, control_source: Path
) -> None:
    report = publish(REPOSITORY, control_source, tmp_path / "output")
    expected = json.loads((GOVERNED / "report.json").read_text())
    expected["inputs"][0]["sha256"] = hashlib.sha256(
        control_source.read_bytes()
    ).hexdigest()
    assert report == expected
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


def test_changed_neotoma_radiocarbon_age_refuses_match(
    tmp_path: Path, control_source: Path
) -> None:
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
        publish(tmp_path, control_source, tmp_path / "output")


def test_changed_control_source_refused_before_matching(control_source: Path) -> None:
    control_source.write_bytes(control_source.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="source hash changed"):
        study._published_dates(control_source)


@pytest.mark.skipif(
    os.environ.get("BIJUX_RUN_ABBO_AGE_CONTROL_SOURCE_INTEGRATION") != "1",
    reason="explicit original published age-table source replay opt-in required",
)
def test_original_published_table_replays_governed_bytes(tmp_path: Path) -> None:
    source = Path(os.environ.get("BIJUX_ABBO_AGE_CONTROL_SOURCE", str(SOURCE)))
    publish(REPOSITORY, source, tmp_path)
    assert (tmp_path / "report.json").read_bytes() == (
        GOVERNED / "report.json"
    ).read_bytes()
