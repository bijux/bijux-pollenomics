"""Source inversion, spatial forwarding and baseline failure isolation."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.inputs import (
    SourcePanel,
    TargetGeometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.prediction import (
    normalized_bounds,
    predict,
)


def controlled_geometry(core: str, anchors: list[str]) -> dict[str, Any]:
    return {
        "core": core,
        "anchor_order": anchors,
        "anchor_xy_m": [[1.0, 0.0], [0.0, 2.0]],
        "centre_weights": [0.8, 0.2],
        "radius_m": 1.0,
        "status": "qualified",
        "homogeneous_taxa": [
            {"status": "qualified", "factor": 1.0, "estimated_absolute_error": 0.0}
            for _ in range(2)
        ],
        "taxa": [
            {
                "primary": {"anchor_factors": [0.6, 0.4], "homogeneous_factor": 1.0},
                "step_bounds": {"anchor_factor_bounds": [[0.5, 0.7], [0.3, 0.5]]},
            },
            {
                "primary": {"anchor_factors": [0.2, 0.8], "homogeneous_factor": 1.0},
                "step_bounds": {"anchor_factor_bounds": [[0.1, 0.3], [0.7, 0.9]]},
            },
        ],
    }


def examples() -> tuple[TargetGeometry, tuple[SourcePanel, SourcePanel]]:
    target = TargetGeometry("T", 1, 2, 3, (0.0, 0.0), 1.0, (1, 2), (1,))
    anchors = (
        SourcePanel("A", 4, 5, 6, (1.0, 0.0), 1.0, (1, 2), (2,), (1, 1)),
        SourcePanel("B", 7, 8, 9, (0.0, 2.0), 1.0, (1, 2), (3,), (3, 1)),
    )
    return target, anchors


def test_anchor_inversion_uses_own_receiver_and_spatial_depositions_add() -> None:
    target, anchors = examples()
    geometry = controlled_geometry("T", ["A", "B"])
    result = predict(
        target,
        anchors,
        geometry,
        {"T": [1.0, 1.0], "A": [1.0, 2.0], "B": [1.0, 2.0]},
        [2.0, 1.0],
    )
    assert result["training"][0]["cover"] == pytest.approx([0.5, 0.5])
    assert result["training"][1]["cover"] == pytest.approx([0.75, 0.25])
    # PPE*(.6*.5+.4*.75, .2*.5+.8*.25) = (1.2,.3).
    assert result["families"]["spatial_cover_idw_forward"][
        "pollen_fraction"
    ] == pytest.approx([0.8, 0.2])
    assert result["families"]["direct_pollen_idw"]["pollen_fraction"] == pytest.approx(
        [0.55, 0.45]
    )


def test_weighted_method_failure_does_not_refuse_old_baselines() -> None:
    target, anchors = examples()
    geometry = controlled_geometry("T", ["A", "B"])
    geometry["status"] = "refused_geometry"
    result = predict(
        target, anchors, geometry, {k: [1.0, 1.0] for k in ["T", "A", "B"]}, [2.0, 1.0]
    )
    assert result["families"]["direct_pollen_idw"]["status"] == "predicted"
    assert result["families"]["centre_cover_idw_forward"]["status"] == "predicted"
    assert (
        result["families"]["spatial_cover_idw_forward"]["status"]
        == "refused_prediction"
    )


def test_positive_two_axis_ranges_close_conservatively() -> None:
    result = normalized_bounds([[1.0, 2.0], [3.0, 4.0]])
    assert result[0] == pytest.approx([0.2, 0.4])
    assert result[1] == pytest.approx([0.6, 0.8])


def test_training_place_cannot_equal_target() -> None:
    target, anchors = examples()
    replaced = SourcePanel("A", 1, 5, 6, (1.0, 0.0), 1.0, (1, 2), (2,), (1, 1))
    with pytest.raises(ValueError, match="Held place"):
        predict(
            target,
            (replaced, anchors[1]),
            controlled_geometry("T", ["A", "B"]),
            {},
            [2.0, 1.0],
        )
