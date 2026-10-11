"""The selected Swedish core keeps age alternatives out of target bins."""

from __future__ import annotations

from copy import deepcopy

import pytest

from bijux_pollenomics_dev.source_completion.swedish_neotoma_holdout import (
    _claims_for_samples,
)


def test_selected_sample_needs_one_default_comparable_calibrated_age() -> None:
    samples = {"sample-a": {"sample_id": "sample-a"}}
    claim = {
        "subject_id": "sample-a",
        "subject_type": "sample",
        "is_default_chronology": True,
        "comparability_status": "comparable",
        "calibration_status": "calibrated",
        "source_age_type": "Calibrated radiocarbon years BP",
        "source_age_value": 1200,
    }
    assert _claims_for_samples([claim], samples) == {"sample-a": claim}

    alternative = deepcopy(claim)
    alternative["is_default_chronology"] = False
    assert _claims_for_samples([alternative, claim], samples) == {"sample-a": claim}

    with pytest.raises(ValueError, match="Multiple selected ages"):
        _claims_for_samples([claim, claim], samples)
    with pytest.raises(ValueError, match="lack unique default calibrated ages"):
        _claims_for_samples([alternative], samples)
