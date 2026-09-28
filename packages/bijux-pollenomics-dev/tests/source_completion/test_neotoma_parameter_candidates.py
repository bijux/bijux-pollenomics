"""Literal parameter-name leads cannot silently become LRA taxon decisions."""

from __future__ import annotations

from copy import deepcopy
import csv
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.neotoma_parameter_candidates import (
    PARAMETERS,
    PRIORITY,
    derive,
)

REPOSITORY = Path(__file__).resolve().parents[4]


def _inputs() -> tuple[list[dict[str, str]], dict[str, object]]:
    with (REPOSITORY / PARAMETERS).open(encoding="utf-8-sig", newline="") as handle:
        parameters = list(csv.DictReader(handle))
    priority = json.loads((REPOSITORY / PRIORITY).read_text(encoding="utf-8"))
    return parameters, priority


def test_exact_parameter_names_keep_source_units_and_review_gate() -> None:
    report = derive(*_inputs())
    assert report["parameter_row_count"] == 31
    assert report["exact_name_parameter_count"] == 20
    assert report["exact_name_concept_count"] == 23
    assert report["lra_accepted_samples"] == 0
    assert report["scientific_admission_allowed"] is False
    rows = {row["parameter_source_name"]: row for row in report["rows"]}
    for name in ("Betula", "Tilia", "Ulmus"):
        assert {source["source_unit"] for source in rows[name]["source_concepts"]} == {
            "NISP",
            "NISP digitized",
        }
    assert rows["Cerealia-t"]["literal_name_match_status"] == "no_exact_source_name"


def test_changed_concept_review_status_requires_new_decision() -> None:
    parameters, priority = _inputs()
    changed = deepcopy(priority)
    changed["rows"][0]["review_state"] = "accepted"
    with pytest.raises(ValueError, match="review state changed"):
        derive(parameters, changed)
