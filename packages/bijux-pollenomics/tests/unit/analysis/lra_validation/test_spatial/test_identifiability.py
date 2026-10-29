"""Raw feature identifiability remains distinct from a ridge-regularized solve."""

from __future__ import annotations

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import Fold, ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.spatial import (
    SiteCoordinate,
    SpatialConfig,
    fit_spatial_model,
    spatial_identifiability,
)


def test_ridge_rank_does_not_imply_data_identifiability() -> None:
    fold = Fold("outer", ("r1", "r2"), ("p10",), ("g1", "g2"), ("target",))
    model = fit_spatial_model(
        fold,
        {"g1": {"a": 0.8, "b": 0.2}, "g2": {"a": 0.4, "b": 0.6}},
        {"g1": SiteCoordinate(0, 0), "g2": SiteCoordinate(0, 0)},
        config=SpatialConfig(100, 0.1, "fixed"),
        input_ids=fold.train_record_ids,
        dependency_graph={"r1": (), "r2": ()},
    )
    before = model.model_sha256
    at_training = spatial_identifiability(
        model,
        target_group_id="target",
        coordinate=SiteCoordinate(0, 0),
        support_id="fixed",
    )
    remote = spatial_identifiability(
        model,
        target_group_id="target",
        coordinate=SiteCoordinate(0, 1),
        support_id="fixed",
    )
    assert remote["unpenalized_rank"] == 0 and remote["ridge_augmented_rank"] == 2
    assert remote["ridge_regularized_nonunique_features"] is True
    assert at_training["target_linear_function_in_training_row_span"] is True
    assert remote["target_linear_function_in_training_row_span"] is False
    assert model.model_sha256 == before
    assert remote["diagnostic_sha256"] != at_training["diagnostic_sha256"]
    with pytest.raises(ValidationRefusal):
        spatial_identifiability(
            model,
            target_group_id="g1",
            coordinate=SiteCoordinate(0, 0),
            support_id="fixed",
        )
    with pytest.raises(ValidationRefusal):
        spatial_identifiability(
            model,
            target_group_id="target",
            coordinate=SiteCoordinate(0, 0),
            support_id="other",
        )
