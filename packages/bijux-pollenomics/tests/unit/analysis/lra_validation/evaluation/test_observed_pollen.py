"""Synthetic success/failure, target separation and attempted scoring leakage."""

from __future__ import annotations

from dataclasses import replace

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    ObservedPollenAdmission,
    PollenChannel,
)
from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    evaluate_final,
    validate_evaluation_policy,
)

from .support import (
    ACCESS,
    bind_prediction,
    policy_payload,
    rows_fixture,
    scope_fixture,
)


@pytest.mark.parametrize(
    "mutation",
    ["no_admission", "owner_edge", "protected_vegetation", "other_target_pollen"],
)
def test_local_observed_channel_never_relabels_the_outer_fold(mutation: str) -> None:
    scope = scope_fixture()
    channels = tuple(
        ObservationChannels(
            site.record_id,
            site.group_id,
            (PollenChannel(site.pollen_observation_id, "a" * 64),),
            (site.vegetation_observation_id,),
        )
        for site in scope.sites
    )
    graph = dict(scope.dependency_graph)
    graph.update({site.pollen_observation_id: () for site in scope.sites})
    if mutation == "owner_edge":
        graph["pollen:2"] = ("p2",)
    elif mutation == "protected_vegetation":
        graph["pollen:2"] = ("vegetation:2",)
    elif mutation == "other_target_pollen":
        graph["pollen:2"] = ("pollen:3",)
    scope = replace(
        scope, observation_channels=channels, dependency_graph=tuple(graph.items())
    )
    original = scope.folds[0].as_dict()
    payload = policy_payload(scope)
    payload["cells"] = payload["cells"][:1]
    payload["cells"][0]["experiment"] = "local_pollen_available"
    policy = validate_evaluation_policy(
        payload, scope=scope, first_test_access_at=ACCESS
    )
    rows = tuple(
        bind_prediction(
            replace(
                row,
                experiment="local_pollen_available",
                fit_input_ids=(*row.fit_input_ids, "pollen:" + row.record_id[1:]),
                observed_pollen=None
                if mutation == "no_admission"
                else ObservedPollenAdmission(
                    row.record_id,
                    "g" + row.record_id[1:],
                    (PollenChannel("pollen:" + row.record_id[1:], "a" * 64),),
                ),
            )
        )
        for row in rows_fixture(scope)
        if row.target == "vegetation_cover"
    )
    with pytest.raises(ValidationRefusal):
        evaluate_final(policy, scope=scope, rows=rows)
    assert scope.folds[0].as_dict() == original
