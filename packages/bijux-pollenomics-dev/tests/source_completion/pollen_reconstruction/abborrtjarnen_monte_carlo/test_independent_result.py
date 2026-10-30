"""Saved scalar displays cannot promote empirical zero or clip signed variance."""

from typing import Any

import pytest

from .independent_result import check_group
from .independent_sampling import scalar_axes


@pytest.mark.parametrize(
    "change",
    [
        "negative_variance",
        "zero_claim",
        "wrong_axis",
        "clipped_covariance",
        "nonfinite",
    ],
)
def test_saved_scalar_or_covariance_misrepresentation_refuses(change: str) -> None:
    zero = (0.0,) * 20
    covariance = (zero,) * 20
    record: dict[str, Any] = {
        "mean": list(zero),
        "mc_covariance": [list(zero) for _ in range(20)],
        "scalars": [
            {
                "scalar_id": identity,
                "empirical_mean": 0.0,
                "mc_variance": 0.0,
                "mcse": 0.0,
                "mcse_status": "empirically_zero_batch_variation_not_zero_target_error",
            }
            for identity in scalar_axes()
        ],
    }
    assert check_group(record, zero, covariance) == 0
    if change == "negative_variance":
        record["scalars"][0]["mc_variance"] = -1e-30
    elif change == "zero_claim":
        record["scalars"][0]["mcse_status"] = "zero_target_error"
    elif change == "wrong_axis":
        record["scalars"][20]["scalar_id"]["older_window_id"] = 3
    elif change == "clipped_covariance":
        record["mc_covariance"][0][1] = 0.01
    else:
        record["scalars"][0]["mc_variance"] = float("nan")
    with pytest.raises(ValueError):
        check_group(record, zero, covariance)
