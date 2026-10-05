"""Refuse altered scientific identities, count domains and covariance claims."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.source_observed_panels.account import (
    retained,
    support,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.source_observed_panels.covariance import (
    scalar_covariance,
    verify_result,
)


def test_known_binomial_and_shared_parameter_variance() -> None:
    q, counting, ppe = scalar_covariance([[1, 1]], [[1, 1]], [1, 1], [1, 0])
    assert (q, counting, ppe) == (0.5, 1 / 8, 1 / 16)


def test_explicit_observed_zero_preserves_boundary() -> None:
    assert scalar_covariance([[0, 20]], [[0.2, 0.7]], [5.106, 1], [0.303, 0]) == (
        0,
        0,
        0,
    )


@pytest.mark.parametrize("counts", [[[True, 1]], [[-1, 2]], [[1.5, 2]], [[0, 0]]])
def test_invalid_observed_count_cannot_become_panel(counts) -> None:
    with pytest.raises(ValueError):
        scalar_covariance(counts, [[1, 1]], [1, 1], [0, 0])


def test_altered_covariance_claim_is_refused() -> None:
    good = {
        "deposition": [[1, 1]],
        "conditional_panel_cover": [0.5, 0.5],
        "conditional_standard_error": [(3 / 16) ** 0.5] * 2,
        "counting_covariance": [[1 / 8, -1 / 8], [-1 / 8, 1 / 8]],
        "shared_ppe_covariance": [[1 / 16, -1 / 16], [-1 / 16, 1 / 16]],
        "total_conditional_covariance": [[3 / 16, -3 / 16], [-3 / 16, 3 / 16]],
        "direct_observed_panel_pollen_fraction": [0.5, 0.5],
    }
    assert max(verify_result(good, [[1, 1]], [1, 1], [1, 0]).values()) == 0
    bad = deepcopy(good)
    bad["total_conditional_covariance"][0][1] = 3 / 16
    with pytest.raises(ValueError, match="differs from scalar"):
        verify_result(bad, [[1, 1]], [1, 1], [1, 0])


def test_sample_identity_and_panel_denominator_are_required() -> None:
    good = {
        "counts": [1, 1],
        "reported_source_pollen_NISP_sum": 4,
        "selected_panel_count_denominator": 2,
        "unparameterized_reported_source_NISP_sum": 2,
        "native_sample_ids": [100, 101],
        "native_analysis_unit_ids": [80, 81],
        "native_sample_count": 2,
        "reported_source_panel_mass_fraction": 0.5,
    }
    assert support(good) == [1, 1]
    for change in [
        {"native_sample_ids": [100, 100]},
        {"unparameterized_reported_source_NISP_sum": 0},
        {"counts": [True, 1]},
    ]:
        with pytest.raises(ValueError):
            support({**good, **change})


def test_wrong_capture_identity_and_success_boolean_are_refused(tmp_path: Path) -> None:
    (tmp_path / "result.json").write_text("{}\n")
    receipt = {
        "status": "PASS",
        "native_exit_code": 0,
        "custody_after_unchanged": True,
        "custody_errors": [],
        "owned_survivors": {},
        "product_files": {"report.json": {"sha256": "0" * 64}},
    }
    (tmp_path / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="native capture authority"):
        retained(tmp_path, "result.json", "receipt.json", "report.json")
    receipt["native_exit_code"] = False
    (tmp_path / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="actual native success"):
        retained(tmp_path, "result.json", "receipt.json", "report.json")


def test_boolean_deposition_is_not_a_physical_measurement() -> None:
    with pytest.raises(ValueError, match="finite numeric"):
        scalar_covariance([[1, 1]], [[True, 1]], [1, 1], [0, 0])
