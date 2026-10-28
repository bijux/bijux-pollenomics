"""Keep first-observed ordering refusal separate from source comparability."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from bijux_pollenomics_dev.lra_validation.neotoma_first_observed import (
    JsonObject,
    _screen_inventory,
)


def _claim(identifier: str, interval: tuple[float, float], status: str) -> JsonObject:
    return {
        "chronology_claim_id": identifier,
        "chronology_id": "native-chronology",
        "source_age_type": "Calendar years BP",
        "source_age_value": interval[0],
        "source_age_unit": "years BP",
        "calibration_status": "not_applicable",
        "comparability_status": status,
        "younger_bp": interval[0] if status == "comparable" else None,
        "older_bp": interval[1] if status == "comparable" else None,
        "admission_reason": "source_owned",
        "refusal_reason": "" if status == "comparable" else "native_context_only",
        "is_default_chronology": True,
        "source_relation_path": "native-claim-path",
    }


@pytest.mark.parametrize(
    "older,younger,status,blocked",
    [
        ((100, 110), (0, 99), "comparable", False),
        ((100, 110), (0, 100), "comparable", True),
        ((100, 110), (90, 105), "comparable", True),
        ((0, 1), (100, 110), "comparable", True),
        ((0, 0), (0, 0), "comparable", True),
        ((100.25, 101.5), (0.25, 100.0), "comparable", False),
        ((100.25, 101.5), (0.25, 100.25), "comparable", True),
        ((100, 110), (0, 100), "context_only", False),
        ((100, 110), (0, 100), "refused", False),
    ],
)
@pytest.mark.parametrize("complete", [False, True])
def test_native_comparable_sequence_order(
    older: tuple[float, float],
    younger: tuple[float, float],
    status: str,
    blocked: bool,
    complete: bool,
) -> None:
    claims = {
        "older-sample": [_claim("native-older", older, status)],
        "younger-sample": [_claim("native-younger", younger, status)],
    }
    original = deepcopy(claims)
    variable: JsonObject = {
        "variable_id": "native-variable",
        "source_reported_name": "Native unresolved source taxon",
        "source_taxon_id": None,
        "source_semantics": "source_literal",
        "source_units": ["NISP"],
    }
    samples: list[JsonObject] = [
        {
            "sample_id": "older-sample",
            "source_depth": 2,
            "collection_unit_id": "native-unit",
        },
        {
            "sample_id": "younger-sample",
            "source_depth": 1,
            "collection_unit_id": "native-unit",
        },
    ]
    observations: list[JsonObject] = (
        [
            {
                "observation_id": "native-observation-" + str(sample["sample_id"]),
                "sample_id": sample["sample_id"],
                "variable_id": "native-variable",
                "source_value": 1,
                "source_unit": "NISP",
                "source_denominator": None,
                "denominator_status": "not_supplied",
                "detection_status": "reported_positive",
                "unit_family": "count",
                "source_part_number": 1,
            }
            for sample in samples
        ]
        if complete
        else []
    )
    result = _screen_inventory(
        "controlled-site",
        variable,
        samples,
        observations,
        claims,
        "native_default",
        "native-snapshot",
    )
    blockers = cast(list[str], result["blocker_codes"])
    assert ("chronology_order_indeterminate" in blockers) is blocked
    assert result["status"] == "refused" and result["event"] is None
    assert result["estimator_invoked"] is False
    assert result["sample_universe_count"] == 2
    assert ("feature_sample_unreported" in blockers) is (not complete)
    assert result["complete_sample_observation_coverage"] is complete
    assert result["governed_sample_inputs_count"] == (
        2 if complete and status != "refused" else 0
    )
    assert "accepted_taxon_mapping_not_available" in blockers
    assert claims == original
