"""Selected native entities never outrun their independently pinned current scope."""

from typing import Any

import pytest

from ..native_products import facet_row


@pytest.mark.parametrize(
    "member", ["context", "roster", "native_manifest", "metadata_body"]
)
@pytest.mark.parametrize(
    "reader", ["read_neotoma_ancillary_facet_entity", "read_neotoma_ancillary_facet"]
)
def test_selected_facet_rechecks_current_inputs_after_preflight(
    selected_products: dict[str, Any], monkeypatch: Any, member: str, reader: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        entities,
    )

    products = selected_products
    native = products["kwargs"]["native_archive_directory"]
    paths = {
        "context": products["kwargs"]["context_directory"] / "manifest.json",
        "roster": native / "catalogue/source-inventory.json",
        "native_manifest": native / "manifest.json",
        "metadata_body": next((native / "captures").glob("*/*.body")),
    }
    permission = paths[member]
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection.access import (
        _body,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection.preflight import (
        prepare_facet_access,
    )

    prepare, body = prepare_facet_access, _body
    returned: list[bytes] = []

    def prepared(*args: Any, **kwargs: Any) -> Any:
        result = prepare(*args, **kwargs)
        permission.write_bytes(permission.read_bytes() + b"\n")
        return result

    def observe(*args: Any, **kwargs: Any) -> Any:
        result = body(*args, **kwargs)
        returned.append(result[0])
        return result

    monkeypatch.setattr(entities, "prepare_facet_access", prepared)
    monkeypatch.setattr(entities, "_body", observe)
    row = facet_row(products)
    with pytest.raises(ValueError):
        getattr(entities, reader)(
            products["directory"],
            **products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert returned == []


def test_selected_linked_rechecks_scope_between_witness_and_target(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence import (
        selection,
    )

    products = selected_products
    row = next(r for r in products["view"].observations if r["kind"] == "linked")
    occurrence = products["view"].linked_occurrences[0]
    permission = products["kwargs"]["context_directory"] / "manifest.json"
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection.access import (
        _body,
    )

    original = _body
    bodies: list[bytes] = []

    def read(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        bodies.append(result[0])
        if len(bodies) == 1:
            permission.write_bytes(permission.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(selection, "_body", read)
    with pytest.raises(ValueError):
        selection.read_linked_entity(
            products["directory"],
            **products["kwargs"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="taxon",
            native_id=1,
        )
    assert len(bodies) == 1


def test_typed_facet_keeps_current_scope_until_qualification_finishes(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        entities,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.profiles import (
        qualify_neotoma_facet_body,
    )

    products = selected_products
    permission = products["kwargs"]["context_directory"] / "manifest.json"
    qualified: list[str] = []

    def qualify(*args: Any, **kwargs: Any) -> Any:
        result = qualify_neotoma_facet_body(*args, **kwargs)
        qualified.append(result["qualification_status"])
        permission.write_bytes(permission.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(entities, "qualify_neotoma_facet_body", qualify)
    row = facet_row(products)
    with pytest.raises(ValueError):
        entities.read_neotoma_ancillary_facet(
            products["directory"],
            **products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert qualified == ["qualified_source_schema"]


def test_typed_linked_keeps_current_scope_until_native_parser_finishes(
    scoped_selection_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence import (
        selection,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.profiles import (
        parse_neotoma_linked_source,
    )

    products = scoped_selection_products
    row = next(
        r
        for r in products["view"].observations
        if r["kind"] == "linked"
        and r["identity"]["kind"] == "taxon"
        and r["identity"]["native_id"] == 11
    )
    occurrence = next(
        r
        for r in products["view"].linked_occurrences
        if r["observation_id"] == row["observation_id"]
    )
    permission = products["kwargs"]["context_directory"] / "manifest.json"
    qualified: list[int] = []

    def parse(*args: Any, **kwargs: Any) -> Any:
        result = parse_neotoma_linked_source(*args, **kwargs)
        qualified.append(len(result.records))
        permission.write_bytes(permission.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(selection, "parse_neotoma_linked_source", parse)
    with pytest.raises(ValueError):
        selection.read_linked(
            products["directory"],
            **products["kwargs"],
            evidence_sources=products["evidence_sources"],
            observation_id=row["observation_id"],
            occurrence_id=occurrence["occurrence_id"],
            kind="taxon",
            native_id=11,
        )
    assert qualified == [1]


def test_typed_facet_uses_one_complete_scope_lifetime(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from contextlib import contextmanager

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        entities,
    )

    original = entities.context_seals
    events: list[str] = []

    @contextmanager
    def counted(options: Any) -> Any:
        events.append("enter")
        try:
            with original(options) as guard:
                yield guard
        finally:
            events.append("close")

    monkeypatch.setattr(entities, "context_seals", counted)
    products = selected_products
    row = facet_row(products)
    result = entities.read_neotoma_ancillary_facet(
        products["directory"],
        **products["kwargs"],
        observation_id=row["observation_id"],
        dataset_id=201,
        facet="taxa",
    )
    assert (
        result["source_qualification"]["qualification_status"]
        == "qualified_source_schema"
    )
    assert events == ["enter", "close"]


def test_typed_facet_refuses_scope_change_after_body(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        entities,
    )

    products = selected_products
    permission = products["kwargs"]["context_directory"] / "manifest.json"
    original = entities._body

    def read(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        permission.write_bytes(permission.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(entities, "_body", read)
    qualified: list[bool] = []
    monkeypatch.setattr(
        entities,
        "qualify_neotoma_facet_body",
        lambda *args, **kwargs: qualified.append(True),
    )
    row = facet_row(products)
    with pytest.raises(ValueError):
        entities.read_neotoma_ancillary_facet(
            products["directory"],
            **products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert qualified == []


def test_typed_facet_closes_scope_when_qualification_raises(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from contextlib import contextmanager

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        entities,
    )

    original = entities.context_seals
    events: list[str] = []

    @contextmanager
    def observed(options: Any) -> Any:
        events.append("enter")
        try:
            with original(options) as guard:
                yield guard
        finally:
            events.append("close")

    monkeypatch.setattr(entities, "context_seals", observed)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("qualification failure")

    monkeypatch.setattr(entities, "qualify_neotoma_facet_body", fail)
    row = facet_row(selected_products)
    with pytest.raises(RuntimeError, match="qualification failure"):
        entities.read_neotoma_ancillary_facet(
            selected_products["directory"],
            **selected_products["kwargs"],
            observation_id=row["observation_id"],
            dataset_id=201,
            facet="taxa",
        )
    assert events == ["enter", "close"]
