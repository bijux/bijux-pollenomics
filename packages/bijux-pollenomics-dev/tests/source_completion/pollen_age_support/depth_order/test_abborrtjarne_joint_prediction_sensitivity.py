"""The joint source consumer retains one compact shared chronology account."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order import (
    abborrtjarne_joint_prediction_sensitivity as adapter,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order import (
    abborrtjarne_prediction_sensitivity as source,
)

from .test_abborrtjarne_prediction_sensitivity import _bytes, _support
from .test_abborrtjarne_prediction_sensitivity import controlled as controlled


def test_controlled_joint_consumer_retains_one_complete_shared_allocation(
    controlled: Any,
) -> None:
    rows, raw, frozen, config = controlled
    report = adapter.derive(_support(rows), _bytes(raw), _bytes(frozen), _bytes(config))
    assert report["refusal"] is None
    assert len(report["sample_order"]) == 107
    assert report["taxon_axis"] == list(source.TAXA)
    assert report["search"]["joint_feasible_nonempty_membership_count"] == 1
    assert report["search"]["scored_positive_closed_count_membership_count"] == 1
    assert report["search"]["zero_closed_count_excluded_membership_count"] == 0
    assert len(report["attaining_allocations"]) == 1
    name, allocation = next(iter(report["attaining_allocations"].items()))
    assert [b["bin_id"] for b in allocation["bins"]] == [3, 4, 5, 9]
    assert len(allocation["age_order"]["ages_in_source_order"]) == 107
    assert len(allocation["method_equal_bin_mae"]) == 4
    for bounds in report["method_equal_bin_mae_bounds"]:
        assert bounds["lower"] == bounds["upper"]
        assert bounds["lower"]["allocation"] == name
        assert (
            bounds["lower"]["value"]
            == allocation["method_equal_bin_mae"][bounds["method"]]
        )
    for pair in report["paired_equal_bin_mae_difference_bounds"]:
        scores = allocation["method_equal_bin_mae"]
        left, right = (scores[pair[key]] for key in ("left_method", "right_method"))
        value = pair["lower"]["value"]
        assert Fraction(value["numerator"], value["denominator"]) == Fraction(
            left["numerator"], left["denominator"]
        ) - Fraction(right["numerator"], right["denominator"])
    encoded = json.dumps(report).encode()
    assert encoded.count(b'"sample_id"') == 107
    assert len(encoded) < 40_000


@pytest.mark.parametrize("mode", ["inconsistent", "empty", "zero"])
def test_controlled_refusals_keep_complete_populations_and_null_scores(
    controlled: Any, mode: str
) -> None:
    rows, raw, frozen, config = deepcopy(controlled)
    samples = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"]
    for index, (row, sample) in enumerate(zip(rows, samples, strict=True)):
        if mode == "inconsistent":
            row["depth_cm"] = str(-index)
            sample["depth"] = -index
        elif mode == "empty":
            age = 6000 + index
            row.update(
                neotoma_age_cal_bp=str(age),
                legacyage_min_cal_bp=str(age),
                legacyage_max_cal_bp=str(age),
            )
            sample["ages"][0]["age"] = age
        elif index == 1:
            for datum in sample["datum"]:
                if datum["variablename"] != "Pinus":
                    datum["value"] = 0
            row["closed_nisp_count"], row["all_nisp_count"] = "0", "1"
    report = adapter.derive(_support(rows), _bytes(raw), _bytes(frozen), _bytes(config))
    assert (
        report["refusal"]
        == {
            "inconsistent": "native_age_order_infeasible",
            "empty": "no_joint_nonempty_bin_selection",
            "zero": "zero_closed_count_in_every_joint_allocation",
        }[mode]
    )
    assert report["search"]["scored_positive_closed_count_membership_count"] == 0
    assert not report["possible_winners"] and not report["attaining_allocations"]
    assert all(
        b["lower"] is b["upper"] is None for b in report["method_equal_bin_mae_bounds"]
    )


def test_input_drift_refuses_before_joint_calculation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "artifacts").mkdir()
    relative = Path("shared-raw.json")
    (repository / relative).write_bytes(b"changed")
    monkeypatch.setattr(adapter, "_revision", lambda _: "a" * 40)
    monkeypatch.setattr(source, "INPUTS", {relative: "0" * 64})
    with pytest.raises(ValueError, match="identity differs"):
        adapter.run(repository, repository / "artifacts" / "report.json")
    assert not (repository / "artifacts" / "report.json").exists()
