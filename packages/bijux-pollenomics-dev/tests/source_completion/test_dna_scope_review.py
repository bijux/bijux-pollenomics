"""Human release rows and animal sample points keep different authority."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.dna_scope_review import INPUTS, derive

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module")
def values() -> dict[str, dict[str, Any]]:
    return {name: json.loads((ROOT / name).read_text()) for name in INPUTS}


def test_source_populations_and_refusals_stay_separate(
    values: dict[str, dict[str, Any]],
) -> None:
    report = derive(ROOT, values)
    assert report["human"]["source_rows"] == 51_005
    assert report["human"]["genetic_ids"] == 27_755
    assert report["human"]["scientifically_admitted"] is False
    assert report["animal"]["foundation_sample_rows"] == 1_450
    assert report["animal"]["point_features"] == 170
    assert report["animal"]["distinct_point_sample_ids"] == 331
    assert report["animal"]["nordic_point_features"] == 8
    assert report["animal"]["nordic_point_sample_ids"] == 12
    assert report["animal"]["foundation_missing_paper_link_rows"] == 11
    assert report["animal"]["point_source_path_field_status_counts"] == {
        "all_paths_present": 338,
        "partial_alternative_paths": 2,
    }
    assert len(report["animal"]["point_source_artifacts"]) == 11
    assert report["pollen_evidence_admitted"] is False


def test_human_admission_change_refuses(values: dict[str, dict[str, Any]]) -> None:
    changed = deepcopy(values)
    changed[INPUTS[1]]["scientifically_admitted"] = True
    with pytest.raises(ValueError, match="admission posture"):
        derive(ROOT, changed)


def test_animal_sample_collision_refuses(values: dict[str, dict[str, Any]]) -> None:
    changed = deepcopy(values)
    rows = changed[INPUTS[3]]["rows"]
    rows[1]["sample_record_ids"] = rows[0]["sample_record_ids"]
    with pytest.raises(ValueError, match="sample/site/project lineage"):
        derive(ROOT, changed)


def test_animal_chronology_basis_refuses(values: dict[str, dict[str, Any]]) -> None:
    changed = deepcopy(values)
    changed[INPUTS[3]]["rows"][0]["chronology"]["dating_basis"] = ""
    with pytest.raises(ValueError, match="chronology basis"):
        derive(ROOT, changed)


def test_animal_accountability_gap_refuses(values: dict[str, dict[str, Any]]) -> None:
    changed = deepcopy(values)
    changed[INPUTS[4]]["rows"][0]["fully_accountable"] = False
    with pytest.raises(ValueError, match="sample/site/project lineage"):
        derive(ROOT, changed)


def test_missing_animal_source_artifact_refuses(
    values: dict[str, dict[str, Any]],
) -> None:
    changed = deepcopy(values)
    changed[INPUTS[3]]["rows"][0]["source_artifact_path"] = "data/adna/absent.json"
    with pytest.raises(ValueError, match="source artifact missing"):
        derive(ROOT, changed)
