"""Declared block supports bind whole training groups before raw pollen access."""

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_PROFILE,
    BLOCK_SPLIT,
    FITTED_METHOD,
    SpatialBlockExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.fitted.admission import (
    admit_block_training,
    read_block_supports,
    retained_training_admission,
)
from bijux_pollenomics.analysis.lra_validation.splits import (
    grouped_block_holdouts,
    grouped_leave_one_out,
)

from ..test_inputs import fixture_inputs, store


def block_payload(root: Path) -> dict[str, Any]:
    value = fixture_inputs(root, count=9)
    value.pop("baselines")
    value.update(
        profile=BLOCK_PROFILE,
        method={"profile": FITTED_METHOD, "length_scale_km": 200, "ridge_penalty": 0.2},
        split={"profile": BLOCK_SPLIT, "minimum_buffer_m": 10000},
    )
    value["request_template"]["configuration"]["reveals"]["region_cutoff_m"] = 100000
    for index, site in enumerate(value["sites"]):
        block = index // 3
        site["block_id"] = f"block-{block}"
        geometry = json.loads((root / site["geometry"]["path"]).read_text())
        # p01 belongs to block0 but is physically near block1: its priority never exempts it.
        geometry.update(
            latitude=0, longitude=5.05 if index == 0 else block * 5 + (index % 3) * 0.05
        )
        site["geometry"] = store(root, site["geometry"]["path"], geometry)
        site["support"] = store(
            root,
            site["record_id"] + "-support.json",
            {
                "schema_version": "lra-block-support.v1",
                "profile": "declared-finite-cutoff-synthetic-v1",
                "record_id": site["record_id"],
                "geometry_sha256": site["geometry"]["sha256"],
                "unit": "m",
                "source_radius_m": 100000,
                "target_radius_m": 1000,
                "coordinate_uncertainty_m": 10,
            },
        )
    return value


def test_all_targets_and_regional_priority_obey_support_buffer(tmp_path: Path) -> None:
    spec = SpatialBlockExperimentSpec(block_payload(tmp_path))
    records = [site.record for site in spec.sites]
    groups = {
        record: f.test_group_ids[0]
        for f in grouped_leave_one_out(records)
        for record in f.test_record_ids
    }
    supports = read_block_supports(spec, tmp_path)
    fold = next(
        f for f in grouped_block_holdouts(records) if f.fold_id == "block:block-1"
    )
    admission = admit_block_training(spec, fold, groups, supports)
    assert admission.fold is fold and fold.test_record_ids == ("p04", "p05", "p06")
    assert admission.excluded_record_ids == ("p01",)
    assert set(admission.admitted_record_ids) == {"p02", "p03", "p07", "p08", "p09"}
    assert spec.regional_priority[0] == "p01"
    receipt = json.loads(json.dumps(admission.as_dict()))
    assert retained_training_admission(receipt, fold) == admission
    assert len(receipt["criterion"]["comparisons"]) == 18
    for key in ["p01", *fold.test_record_ids]:
        (
            tmp_path
            / next(site.raw.path for site in spec.sites if site.record.record_id == key)
        ).unlink()
    assert (
        admit_block_training(spec, fold, groups, read_block_supports(spec, tmp_path))
        == admission
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "smaller_source",
        "different_target",
        "bool_uncertainty",
        "wrong_geometry",
        "extra_pollen",
    ],
)
def test_incompatible_support_is_refused_before_observations(
    tmp_path: Path, mutation: str
) -> None:
    payload = block_payload(tmp_path)
    site = payload["sites"][0]
    support = json.loads((tmp_path / site["support"]["path"]).read_text())
    if mutation == "smaller_source":
        support["source_radius_m"] = 99999
    elif mutation == "different_target":
        support["target_radius_m"] = 999
    elif mutation == "bool_uncertainty":
        support["coordinate_uncertainty_m"] = True
    elif mutation == "wrong_geometry":
        support["geometry_sha256"] = "a" * 64
    else:
        support["pollen"] = [1, 2]
    site["support"] = store(tmp_path, site["support"]["path"], support)
    with pytest.raises(ValidationRefusal):
        read_block_supports(SpatialBlockExperimentSpec(payload), tmp_path)


def test_saved_buffer_distance_cannot_be_rehashed_into_admission(
    tmp_path: Path,
) -> None:
    spec = SpatialBlockExperimentSpec(block_payload(tmp_path))
    records = [site.record for site in spec.sites]
    groups = {
        record: f.test_group_ids[0]
        for f in grouped_leave_one_out(records)
        for record in f.test_record_ids
    }
    fold = grouped_block_holdouts(records)[0]
    admission = admit_block_training(
        spec, fold, groups, read_block_supports(spec, tmp_path)
    )
    receipt = json.loads(json.dumps(admission.as_dict()))
    criterion = receipt["criterion"]
    criterion["comparisons"][0]["distance"]["lower_bound_m"] += 1
    from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json

    altered = replace(admission, criterion_json=canonical_json(criterion))
    with pytest.raises(ValidationRefusal, match="block"):
        retained_training_admission(json.loads(json.dumps(altered.as_dict())), fold)


@pytest.mark.parametrize("field", ["block_id", "support"])
def test_blocks_require_declarations_for_every_site(tmp_path: Path, field: str) -> None:
    payload = block_payload(tmp_path)
    payload["sites"][0].pop(field)
    with pytest.raises(ValidationRefusal):
        SpatialBlockExperimentSpec(payload)


@pytest.mark.parametrize(
    "mutation",
    ["training_coordinate", "target_coordinate", "target_geometry", "target_radius"],
)
def test_retained_support_must_match_actual_model_and_target(
    tmp_path: Path, mutation: str
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments.fitted.admission import (
        validate_prediction_support,
    )

    spec = SpatialBlockExperimentSpec(block_payload(tmp_path))
    records = [site.record for site in spec.sites]
    groups = {
        record: f.test_group_ids[0]
        for f in grouped_leave_one_out(records)
        for record in f.test_record_ids
    }
    supports = read_block_supports(spec, tmp_path)
    fold = next(
        f for f in grouped_block_holdouts(records) if f.fold_id == "block:block-1"
    )
    admission = admit_block_training(spec, fold, groups, supports)
    target = supports["p04"]
    row: dict[str, Any] = {
        "record_id": "p04",
        "target_geometry_sha256": target.geometry_sha256,
        "support": {"local_support_radius_m": 1000},
        "forward_preparation": {"regional_cutoff_m": 100000},
        "training_products": [
            {"record_id": record} for record in admission.admitted_record_ids
        ],
    }
    fit: dict[str, Any] = {
        "training_coordinates": {
            groups[record]: {
                "latitude": supports[record].source.latitude,
                "longitude": supports[record].source.longitude,
            }
            for record in admission.admitted_record_ids
        }
    }
    spatial: dict[str, Any] = {
        "coordinate": {
            "latitude": target.target.latitude,
            "longitude": target.target.longitude,
        }
    }
    validate_prediction_support(row, fit, spatial, admission)
    if mutation == "training_coordinate":
        fit["training_coordinates"][groups["p02"]]["latitude"] += 1
    elif mutation == "target_coordinate":
        spatial["coordinate"]["latitude"] += 1
    elif mutation == "target_geometry":
        row["target_geometry_sha256"] = "a" * 64
    else:
        row["support"]["local_support_radius_m"] = 999
    with pytest.raises(ValidationRefusal):
        validate_prediction_support(row, fit, spatial, admission)


def test_forged_group_map_cannot_change_buffer_exclusions(tmp_path: Path) -> None:
    spec = SpatialBlockExperimentSpec(block_payload(tmp_path))
    records = [site.record for site in spec.sites]
    groups = {
        record: f.test_group_ids[0]
        for f in grouped_leave_one_out(records)
        for record in f.test_record_ids
    }
    groups["p01"], groups["p02"] = groups["p02"], groups["p01"]
    with pytest.raises(ValidationRefusal) as error:
        admit_block_training(
            spec,
            grouped_block_holdouts(records)[0],
            groups,
            read_block_supports(spec, tmp_path),
        )
    assert error.value.reason_code == "block_group_identity_mismatch"
