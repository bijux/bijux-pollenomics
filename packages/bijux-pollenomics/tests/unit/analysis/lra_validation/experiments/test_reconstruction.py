"""Regional ancestry and source-domain failures precede numerical submission."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    grouped_leave_one_out,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    ExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reconstruction import (
    reconstruct_fold,
)

from .test_inputs import fixture_inputs


def test_withheld_priority_cannot_become_regional_anchor(tmp_path: Path) -> None:
    payload = fixture_inputs(tmp_path)
    payload["regional_priority"] = ["p01"]
    spec = ExperimentSpec(payload)
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    fold = next(fold for fold in folds if "p01" in fold.test_record_ids)
    groups = {
        record: other.test_group_ids[0]
        for other in folds
        for record in other.test_record_ids
    }
    with pytest.raises(ValidationRefusal) as error:
        reconstruct_fold(
            spec,
            fold,
            groups,
            input_root=tmp_path,
            cache_root=tmp_path / "cache",
            report_root=tmp_path / "batch",
            workers=1,
        )
    assert error.value.reason_code == "missing_regional_anchor"
    assert not (tmp_path / "batch").exists()


def test_alias_group_observations_need_explicit_selection(tmp_path: Path) -> None:
    payload = fixture_inputs(tmp_path, 5)
    payload["sites"][0]["identity_keys"] = ["same-physical-core"]
    payload["sites"][1]["identity_keys"] = ["same-physical-core"]
    spec = ExperimentSpec(payload)
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    fold = next(fold for fold in folds if "p05" in fold.test_record_ids)
    groups = {
        record: other.test_group_ids[0]
        for other in folds
        for record in other.test_record_ids
    }
    with pytest.raises(ValidationRefusal) as error:
        reconstruct_fold(
            spec,
            fold,
            groups,
            input_root=tmp_path,
            cache_root=tmp_path / "cache",
            report_root=tmp_path / "batch",
            workers=1,
        )
    assert error.value.reason_code == "unsupported_multi_record_group"
