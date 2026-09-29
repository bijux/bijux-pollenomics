"""Protect source-default calibrated sample-age selection."""

from __future__ import annotations

from copy import deepcopy

import pytest

from bijux_pollenomics_dev.source_completion.swedish_lake_transfer import (
    _selected_claims,
)


def test_lake_transfer_uses_unique_nonnegative_default_calibrated_age() -> None:
    claim = {
        "subject_id": "sample-a",
        "subject_type": "sample",
        "country_code": "SE",
        "source_age_type": "Calibrated radiocarbon years BP",
        "is_default_chronology": True,
        "comparability_status": "comparable",
        "calibration_status": "calibrated",
        "source_age_value": 1200,
    }
    alternative = {**claim, "is_default_chronology": False}
    assert _selected_claims([alternative, claim]) == {"sample-a": claim}

    with pytest.raises(ValueError, match="Multiple source-default calibrated ages"):
        _selected_claims([claim, deepcopy(claim)])
    with pytest.raises(ValueError, match="nonnegative BP"):
        _selected_claims([{**claim, "source_age_value": -1}])
