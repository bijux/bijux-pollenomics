"""The complete original catalogue and older request remain distinct from transport."""

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.temporal.persistence.configuration import (
    TemporalPersistenceSpec,
    YoungerCalendarBin,
)

from .support import fixture_payload, spec_from_payload


def test_roundtrip_retains_original_fold_and_older_request(tmp_path: Path) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path))
    restored = TemporalPersistenceSpec.from_dict(spec.as_dict())
    assert restored.sha256 == spec.sha256
    assert restored.temporal_plan.fold == spec.temporal_plan.fold
    assert (
        restored.older_experiment.template()["temporal_matching"]
        == spec.older_experiment.template()["temporal_matching"]
    )
    assert restored.older_bin().bin_id != restored.younger_bin.bin_id
    assert spec.temporal_plan.chronologies[0].support is not None
    view = spec.as_dict()
    view["purpose"] = "final"
    with pytest.raises(ValidationRefusal):
        TemporalPersistenceSpec.from_dict(view)
    assert spec.as_dict()["purpose"] == "exploratory"


@pytest.mark.parametrize("value", [True, "10", float("inf"), 2**53 + 1])
def test_bin_refuses_implicit_or_inexact_values(value: object) -> None:
    with pytest.raises(ValidationRefusal):
        YoungerCalendarBin("young", cast(float, value), 100)


def test_signed_modern_calendar_remains_explicit() -> None:
    assert YoungerCalendarBin("modern", -70, -50).younger_bp == -70
    with pytest.raises(ValidationRefusal):
        YoungerCalendarBin("modern", -70, -50, "radiocarbon_bp")


def test_no_forged_fold_identity_or_bin_relabel(tmp_path: Path) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path))
    with pytest.raises(ValidationRefusal, match="singleton"):
        replace(
            spec,
            temporal_plan=replace(
                spec.temporal_plan,
                fold=replace(spec.temporal_plan.fold, fold_id="fabricated"),
            ),
        )
    with pytest.raises(ValidationRefusal, match="distinct"):
        replace(
            spec, younger_bin=replace(spec.younger_bin, bin_id=spec.older_bin().bin_id)
        )
