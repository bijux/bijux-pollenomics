"""Batched typed reads preserve the selected entity custody contract."""

from typing import Any

import pytest


def selected(products: dict[str, Any]) -> tuple[tuple[str, int, str], ...]:
    rows = [
        r
        for r in products["view"].observations
        if r["kind"] == "facet"
        and r["root_identity"]["dataset_id"] == 201
        and r["facet"] in {"taxa", "doi"}
        and r["capture_parent_scope_verification"] != "not_recorded_legacy_capture"
    ]
    assert {r["facet"] for r in rows} == {"taxa", "doi"}
    return tuple((r["observation_id"], 201, r["facet"]) for r in rows)


def test_batch_equals_independent_typed_reads(
    selected_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facet,
        read_neotoma_ancillary_facets,
    )

    p = selected_products
    requests = selected(p)
    expected = tuple(
        read_neotoma_ancillary_facet(
            p["directory"], **p["kwargs"], observation_id=o, dataset_id=d, facet=f
        )
        for o, d, f in requests
    )
    assert (
        read_neotoma_ancillary_facets(p["directory"], requests=requests, **p["kwargs"])
        == expected
    )


def test_batch_rejects_duplicate_selection(selected_products: dict[str, Any]) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facets,
    )

    p = selected_products
    request = selected(p)[0]
    with pytest.raises(ValueError, match="duplicate"):
        read_neotoma_ancillary_facets(
            p["directory"], requests=(request, request), **p["kwargs"]
        )


@pytest.mark.parametrize("member", ["context", "roster"])
def test_batch_refuses_scope_mutation_during_first_qualification(
    selected_products: dict[str, Any], monkeypatch: Any, member: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    p = selected_products
    calls = []
    original = typed_batch.qualify_neotoma_facet_body
    permission = (
        p["kwargs"]["context_directory"] / "manifest.json"
        if member == "context"
        else p["kwargs"]["native_archive_directory"] / "catalogue/source-inventory.json"
    )

    def qualify(*args: Any, **kwargs: Any) -> Any:
        value = original(*args, **kwargs)
        calls.append(1)
        permission.write_bytes(permission.read_bytes() + b"\n")
        return value

    monkeypatch.setattr(typed_batch, "qualify_neotoma_facet_body", qualify)
    with pytest.raises(ValueError):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"], requests=selected(p), **p["kwargs"]
        )
    assert calls == [1]


def test_batch_refuses_mutated_second_body_without_partial_result(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    p = selected_products
    requests = selected(p)
    original = typed_batch.qualify_neotoma_facet_body
    calls = []
    row = next(
        r for r in p["view"].observations if r["observation_id"] == requests[1][0]
    )
    target = (
        p["capsule"]
        / "captures"
        / row["source_capture_manifest_sha256"]
        / row["attempts"][-1]["body_file"]
    )

    def qualify(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        calls.append(1)
        if len(calls) == 1:
            target.write_bytes(target.read_bytes() + b" ")
        return result

    monkeypatch.setattr(typed_batch, "qualify_neotoma_facet_body", qualify)
    with pytest.raises(ValueError):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"], requests=requests, **p["kwargs"]
        )
    assert calls == [1]


def test_batch_preserves_qualification_error_and_closes(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    p = selected_products
    operations = []
    original = typed_batch.prepare_neotoma_preflight_batch

    def prepare(*args: Any, **kwargs: Any) -> Any:
        op = original(*args, **kwargs)
        operations.append(op)
        return op

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("qualification failure")

    monkeypatch.setattr(typed_batch, "prepare_neotoma_preflight_batch", prepare)
    monkeypatch.setattr(typed_batch, "qualify_neotoma_facet_body", fail)
    with pytest.raises(RuntimeError, match="qualification failure"):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"], requests=selected(p), **p["kwargs"]
        )
    assert operations[0]._status == "closed" and operations[0]._parts.closed
    with pytest.raises(ValueError, match="not open"):
        operations[0]._active()


def test_batch_refuses_aggregate_body_budget(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    monkeypatch.setattr(typed_batch, "_MAX_BODIES", 1)
    p = selected_products
    with pytest.raises(ValueError, match="body budget"):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"], requests=selected(p), **p["kwargs"]
        )


def test_batch_refuses_cross_entity_body_substitution(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    p = selected_products
    requests = selected(p)
    rows = {r["observation_id"]: r for r in p["view"].observations}

    def path(request: tuple[str, int, str]) -> Any:
        row = rows[request[0]]
        return (
            p["capsule"]
            / "captures"
            / row["source_capture_manifest_sha256"]
            / row["attempts"][-1]["body_file"]
        )

    target = path(requests[0])
    other = path(requests[1]).read_bytes()
    original = typed_batch._read

    def substitute(candidate: Any, bound: int) -> bytes:
        return other if candidate == target else original(candidate, bound)

    monkeypatch.setattr(typed_batch, "_read", substitute)
    with pytest.raises(ValueError, match="body identity"):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"], requests=requests, **p["kwargs"]
        )


def test_batch_refuses_wrong_site_or_observation_identity(
    selected_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facets,
    )

    p = selected_products
    row = selected(p)[0]
    for request in ((row[0], 202, row[2]), (row[0] + "999", row[1], row[2])):
        with pytest.raises(ValueError):
            read_neotoma_ancillary_facets(
                p["directory"], requests=(request,), **p["kwargs"]
            )


def test_duplicate_observation_with_changed_facet_refused(
    selected_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facets,
    )

    p = selected_products
    request = selected(p)[0]
    with pytest.raises(ValueError, match="duplicate"):
        read_neotoma_ancillary_facets(
            p["directory"],
            requests=(request, (request[0], request[1], "other")),
            **p["kwargs"],
        )


@pytest.mark.parametrize("failure", ["batch_close", "outer_exit"])
def test_final_validation_failure_never_returns(
    selected_products: dict[str, Any], monkeypatch: Any, failure: str
) -> None:
    from contextlib import contextmanager

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection.batch import (
        NeotomaPreflightBatch,
    )

    p = selected_products
    if failure == "batch_close":
        original = NeotomaPreflightBatch.close

        def fail(self: Any) -> None:
            original(self)
            raise RuntimeError("final validation failure")

        monkeypatch.setattr(NeotomaPreflightBatch, "close", fail)
    else:
        original_seals = typed_batch.context_seals

        @contextmanager
        def fail_exit(options: Any) -> Any:
            with original_seals(options) as guard:
                yield guard
            raise RuntimeError("final validation failure")

        monkeypatch.setattr(typed_batch, "context_seals", fail_exit)
    with pytest.raises(RuntimeError, match="final validation failure"):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"], requests=selected(p), **p["kwargs"]
        )


def test_cleanup_exception_does_not_mask_primary(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection.batch import (
        NeotomaPreflightBatch,
    )

    original = NeotomaPreflightBatch._abort

    def cleanup(self: Any) -> None:
        original(self)
        raise RuntimeError("cleanup failure")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("primary qualification failure")

    monkeypatch.setattr(NeotomaPreflightBatch, "_abort", cleanup)
    monkeypatch.setattr(typed_batch, "qualify_neotoma_facet_body", fail)
    p = selected_products
    with pytest.raises(ValueError, match="primary qualification failure") as error:
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"], requests=selected(p), **p["kwargs"]
        )
    assert any("cleanup failure" in note for note in error.value.__notes__)


@pytest.mark.parametrize("kind", ["size", "replace", "hardlink"])
def test_batch_refuses_changed_body_physical_identity(
    selected_products: dict[str, Any], monkeypatch: Any, kind: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    p = selected_products
    requests = selected(p)
    original = typed_batch.qualify_neotoma_facet_body
    calls = []
    row = next(
        r for r in p["view"].observations if r["observation_id"] == requests[1][0]
    )
    target = (
        p["capsule"]
        / "captures"
        / row["source_capture_manifest_sha256"]
        / row["attempts"][-1]["body_file"]
    )

    def qualify(*args: Any, **kwargs: Any) -> Any:
        value = original(*args, **kwargs)
        calls.append(1)
        if len(calls) == 1:
            body = target.read_bytes()
            if kind == "size":
                target.write_bytes(body + b" ")
            elif kind == "replace":
                replacement = target.with_name("replacement")
                replacement.write_bytes(body)
                replacement.replace(target)
            else:
                target.with_name("link").hardlink_to(target)
        return value

    monkeypatch.setattr(typed_batch, "qualify_neotoma_facet_body", qualify)
    with pytest.raises((ValueError, OSError)):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"], requests=requests, **p["kwargs"]
        )
    assert calls == [1]


@pytest.mark.parametrize(
    "field",
    [
        "expected_manifest_sha256",
        "expected_context_sha256",
        "expected_native_archive_sha256",
    ],
)
def test_batch_refuses_independent_anchor_mismatch(
    selected_products: dict[str, Any], field: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facets,
    )

    p = selected_products
    options = {**p["kwargs"], field: "0" * 64}
    with pytest.raises(ValueError):
        read_neotoma_ancillary_facets(p["directory"], requests=selected(p), **options)
