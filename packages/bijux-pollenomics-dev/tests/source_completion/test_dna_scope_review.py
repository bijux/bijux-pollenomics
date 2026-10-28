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
    assert report["animal"]["foundation_sample_rows"] == 1_468
    assert report["animal"]["point_features"] == 165
    assert report["animal"]["distinct_point_sample_ids"] == 322
    assert report["animal"]["nordic_point_features"] == 8
    assert report["animal"]["nordic_point_sample_ids"] == 12
    assert report["animal"]["foundation_missing_paper_link_rows"] == 11
    assert report["animal"]["point_source_path_field_status_counts"] == {
        "all_paths_present": 328,
        "partial_alternative_paths": 2,
    }
    point_artifacts = report["animal"]["point_source_artifacts"]
    assert len(point_artifacts) == 10
    assert (
        "data/adna/governance/source_library/papers/10.1016-j.cell.2019.03.049/"
        "supplementary/1-s2.0-S0092867419303848-mmc1.xlsx"
    ) not in {item["path"] for item in point_artifacts}
    assert report["pollen_evidence_admitted"] is False


def test_unqualified_horse_elapsed_ages_remain_outside_point_population(
    values: dict[str, dict[str, Any]],
) -> None:
    # Source-owned elapsed ages retain their rows without gaining a BP epoch.
    removed_sample_ids = {
        "equus_caballus:sample:prjeb31613:batagai_5155",
        "equus_caballus:sample:prjeb31613:cgg_1_010022",
        "equus_caballus:sample:prjeb31613:cgg_1_010023",
        "equus_caballus:sample:prjeb31613:cgg_1_018522",
        "equus_caballus:sample:prjeb31613:cgg_1_018529",
        "equus_caballus:sample:prjeb31613:cgg_1_018533",
        "equus_caballus:sample:prjeb31613:cgg_1_018540",
        "equus_caballus:sample:prjeb31613:cgg_1_019154",
        "equus_caballus:sample:prjeb31613:cgg_1_019192",
    }
    animal = values[INPUTS[3]]["rows"]
    published_samples = {
        sample_id for row in animal for sample_id in row["sample_record_ids"]
    }
    assert removed_sample_ids.isdisjoint(published_samples)
    assert all(row["primary_project_accession"] != "PRJEB31613" for row in animal)
    source_project = next(
        row
        for row in values[INPUTS[2]]["project_rows"]
        if row["project_accession"] == "PRJEB31613"
    )
    assert source_project["sample_row_count"] == 245
    assert source_project["blocked_weak_chronology_count"] == 245
    assert source_project["fully_grounded_count"] == 0
    # A distinct project with qualified source BP chronology remains represented.
    assert any(row["primary_project_accession"] == "PRJEB44430" for row in animal)


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
