"""Resolution and accepted-concept universe separation."""

from __future__ import annotations

from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
)
from bijux_pollenomics.analysis.propagation.network import (
    PropagationPairRefusal,
    evaluate_propagation_pair,
    generate_propagation_network,
)

from .support import event, scenario


def test_signal_resolution_and_role_universes_remain_separate() -> None:
    taxon_a = event("taxon-a")
    taxon_b = event(
        "taxon-b", latitude=55.7, longitude=13.19, younger_bp=5500, older_bp=5500
    )
    role_a = event(
        "role-a",
        resolution="ecological_role",
        feature_key="role:cereal_indicator",
    )
    role_b = event(
        "role-b",
        resolution="ecological_role",
        feature_key="role:cereal_indicator",
        latitude=55.7,
        longitude=13.19,
        younger_bp=5500,
        older_bp=5500,
    )

    result = scenario(
        generate_propagation_network((taxon_a, role_b, taxon_b, role_a)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert {row.feature_key for row in result.evaluated_pairs} == {
        "taxon:triticum_aestivum",
        "role:cereal_indicator",
    }
    assert all(
        row.source_event_id.startswith("event:")
        and row.target_event_id.startswith("event:")
        for row in result.evaluated_pairs
    )
    assert len(result.evaluated_pairs) == 4


def test_taxon_universe_requires_the_same_accepted_concept() -> None:
    accepted_a = event("accepted-a")
    accepted_b = event(
        "accepted-b",
        latitude=55.7,
        longitude=13.19,
        younger_bp=5500,
        older_bp=5500,
        accepted_taxon_concept_id="accepted-taxon-2",
    )

    result = scenario(
        generate_propagation_network((accepted_a, accepted_b)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    direct = evaluate_propagation_pair(accepted_a, accepted_b)

    assert not result.evaluated_pairs
    assert isinstance(direct, PropagationPairRefusal)
    assert direct.reason_code == "incompatible_feature"
