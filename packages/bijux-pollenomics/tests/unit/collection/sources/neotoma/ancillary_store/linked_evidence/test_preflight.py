"""Global source preflight closes both ledgers before either native buffer is read."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
    NeotomaResourceLimits,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from .native_products import selected


def forbid_entities(
    monkeypatch: pytest.MonkeyPatch, products: dict[str, Any]
) -> list[Path]:
    opened: list[Path] = []
    original = capture_opening()

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and any(
            parent in path.parents
            for parent in (products["capsule"], products["facet_capsule"])
        ):
            opened.append(path)
            raise AssertionError("Metadata preflight opened a native source entity")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    return opened


def test_scoped_linked_preflight_closes_both_source_ledgers_without_bodies(
    scoped_selection_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.preflight import (
        prepare_linked_access,
    )

    products = scoped_selection_products
    row, occurrence = selected(products)
    opened = forbid_entities(monkeypatch, products)
    prepared = prepare_linked_access(
        products["directory"],
        **products["kwargs"],
        evidence_sources=products["evidence_sources"],
        observation_id=row["observation_id"],
        occurrence_id=occurrence["occurrence_id"],
        kind="taxon",
        native_id=11,
    )
    assert prepared.proof["native_id"] == 11
    assert prepared.locator == occurrence["evidence_locator"]
    assert prepared.row == row
    assert prepared.response[1] >= prepared.response[0]["retained_body_bytes"]
    assert (
        prepared.source_response[1]
        >= prepared.source_response[0]["retained_body_bytes"]
    )
    assert prepared.source_entry["facet_key"] == prepared.proof["source_facet_key"]
    assert prepared.entity_bodies_verified is False
    assert prepared.native_field_value_verified is False
    assert opened == []


@pytest.mark.parametrize("change", ["identity", "budget", "occurrence"])
def test_linked_preflight_refuses_without_target_or_witness_body(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.preflight import (
        prepare_linked_access,
    )

    products = scoped_selection_products
    row, occurrence = selected(products)
    opened = forbid_entities(monkeypatch, products)
    kwargs = {**products["kwargs"]}
    if change == "budget":
        kwargs["limits"] = NeotomaResourceLimits(max_response_bytes=1)
    with pytest.raises(ValueError):
        prepare_linked_access(
            products["directory"],
            **kwargs,
            evidence_sources=products["evidence_sources"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"] + "999"
            if change == "occurrence"
            else occurrence["occurrence_id"],
            kind="taxon",
            native_id=12 if change == "identity" else 11,
        )
    assert opened == []
