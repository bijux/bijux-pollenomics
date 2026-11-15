"""Selected source preflight authenticates custody and budgets without body access."""

from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
    NeotomaResourceLimits,
)

from .native_products import facet_row, observe_entities


def test_facet_preflight_has_no_entity_or_native_profile_claim(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection.preflight import (
        prepare_facet_access,
    )

    row = facet_row(selected_products)
    opened = observe_entities(monkeypatch, selected_products, set())
    prepared = prepare_facet_access(
        selected_products["directory"],
        **selected_products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="taxa",
    )
    assert prepared.row == row
    assert prepared.resource.dataset_id == 201
    assert (
        prepared.response[0]["body_file"] == prepared.entry["attempts"][-1]["body_file"]
    )
    assert prepared.response[1] >= prepared.response[0]["retained_body_bytes"]
    assert prepared.parents[201]["effective_scope_role"] in {
        "development_resource_discovery",
        "exposed_development",
    }
    assert prepared.entity_bodies_verified is False
    assert prepared.native_field_value_verified is False
    assert opened == []


@pytest.mark.parametrize("change", ["identity", "budget"])
def test_facet_preflight_refuses_before_any_entity(
    selected_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection.preflight import (
        prepare_facet_access,
    )

    row = facet_row(selected_products)
    opened = observe_entities(monkeypatch, selected_products, set())
    extra = (
        {"limits": NeotomaResourceLimits(max_response_bytes=1)}
        if change == "budget"
        else {}
    )
    with pytest.raises(ValueError):
        prepare_facet_access(
            selected_products["directory"],
            **{**selected_products["kwargs"], **extra},
            observation_id=row["observation_id"],
            dataset_id=202 if change == "identity" else 201,
            facet="taxa",
        )
    assert opened == []
