"""Cached metadata preserves before-body capture and operation cache limits."""

from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
    NeotomaResourceLimits,
)

from ..native_products import selected_products as selected_products
from .native_inputs import (
    api,
    facet_row,
    linked_rows,
    observe,
)
from .native_inputs import (
    scoped_inputs as scoped_inputs,
)
from .native_inputs import (
    scoped_selection_products as scoped_selection_products,
)


@pytest.mark.parametrize("invalid", [True, 0, -1, "100", 1024 * 1024 * 1024])
def test_operation_cache_limit_is_explicit_native_integer_with_existing_ceiling(
    selected_products: dict[str, Any], invalid: Any
) -> None:
    source = selected_products
    with pytest.raises(ValueError):
        api().prepare_neotoma_preflight_batch(
            source["directory"], **source["kwargs"], metadata_max_bytes=invalid
        )


def test_actual_source_ledger_caller_bound_refuses_before_any_entity(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = selected_products
    row = facet_row(source)
    observe(monkeypatch, source)
    with (
        api().prepare_neotoma_preflight_batch(
            source["directory"],
            **{
                **source["kwargs"],
                "limits": NeotomaResourceLimits(max_response_bytes=1),
            },
        ) as batch,
        pytest.raises(ValueError, match="budget|bytes"),
    ):
        batch.facet(observation_id=row["observation_id"], dataset_id=201, facet="taxa")


def test_private_part_reader_cannot_bypass_the_lower_size_and_sha_guard(
    scoped_selection_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        evidence,
    )

    source = scoped_selection_products
    row, occurrences = linked_rows(source, 11)
    locator = occurrences[0]["evidence_locator"]
    directory = source["evidence_sources"][locator["evidence_manifest_sha256"]]
    header = evidence.read_neotoma_linked_evidence_metadata(
        directory, expected_manifest_sha256=locator["evidence_manifest_sha256"]
    )
    part = next(
        part for part in header["parts"] if part["sha256"] == locator["part_sha256"]
    )
    with pytest.raises(ValueError, match="identity|digest|SHA"):
        evidence._part(directory, part, reader=lambda _path, _sha, bound: b"x" * bound)


@pytest.mark.parametrize("bound", ["bytes", "files"])
def test_cache_capacity_refuses_before_any_metadata_buffer_open(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, bound: str
) -> None:
    source = selected_products
    counts = observe(monkeypatch, source)
    options = (
        {"metadata_max_bytes": 1} if bound == "bytes" else {"metadata_max_files": 1}
    )
    with (
        pytest.raises(ValueError, match="budget"),
        api().prepare_neotoma_preflight_batch(
            source["directory"], **source["kwargs"], **options
        ),
    ):
        pass
    assert sum(counts.values()) == (0 if bound == "bytes" else 1)


@pytest.mark.parametrize("change", ["identity", "occurrence", "budget"])
def test_cached_scoped_target_keeps_exact_selector_and_both_budget_guards(
    scoped_selection_products: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    from .native_inputs import scoped_arguments

    source = scoped_selection_products
    row, occurrences = linked_rows(source, 11)
    observe(monkeypatch, source)
    kwargs = scoped_arguments(source)
    if change == "budget":
        kwargs["limits"] = NeotomaResourceLimits(max_response_bytes=1)
    with api().prepare_neotoma_preflight_batch(source["directory"], **kwargs) as batch:
        options = {
            "observation_id": row["observation_id"],
            "occurrence_id": occurrences[0]["occurrence_id"],
            "kind": "taxon",
            "native_id": 11,
        }
        if change != "budget":
            batch.linked(**options)
        if change == "identity":
            options["native_id"] = 12
        elif change == "occurrence":
            options["occurrence_id"] += "999"
        with pytest.raises(ValueError):
            batch.linked(**options)


def test_evidence_header_cached_buffer_keeps_independent_expected_digest(
    scoped_selection_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence import (
        _index,
    )

    source = scoped_selection_products
    digest, directory = next(iter(source["evidence_sources"].items()))
    raw = (directory / "evidence-manifest.json").read_bytes()
    with pytest.raises(ValueError, match="identity|digest|SHA"):
        _index(
            directory,
            digest,
            reader=lambda _path, _sha, _bound: raw.replace(b"{", b"[", 1),
        )


def test_evidence_header_cached_buffer_keeps_independent_byte_bound(
    scoped_selection_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        evidence,
    )

    source = scoped_selection_products
    digest, directory = next(iter(source["evidence_sources"].items()))
    raw = (directory / "evidence-manifest.json").read_bytes()
    monkeypatch.setattr(evidence, "MAX_MANIFEST_BYTES", len(raw) - 1)
    with pytest.raises(ValueError, match="identity|bound|bytes"):
        evidence._index(directory, digest, reader=lambda _path, _sha, _bound: raw)


@pytest.mark.parametrize(
    "budget",
    ["request_ordinal", "total_exhausted", "total_remaining", "response_bytes"],
)
def test_batch_replays_selected_attempt_ordinal_and_remaining_byte_budget(
    selected_products: dict[str, Any], monkeypatch: pytest.MonkeyPatch, budget: str
) -> None:
    from ..native_products import rewrite_capture

    source = selected_products
    row = next(
        row
        for row in source["view"].observations
        if row.get("facet") == "doi"
        and row["root_identity"]["dataset_id"] == 201
        and row["capture_parent_scope_verification"] == "not_recorded_legacy_capture"
    )
    with api().prepare_neotoma_preflight_batch(
        source["directory"], **source["kwargs"]
    ) as batch:
        positive = batch.facet(
            observation_id=row["observation_id"], dataset_id=201, facet="doi"
        )
    size = positive.source["body_descriptor"]["bytes"]

    def mutate(
        document: dict[str, Any], control: dict[str, Any], directory: Any
    ) -> None:
        previous = directory / document["facets"][0]["attempts"][0]["body_file"]
        field, value = {
            "request_ordinal": ("max_requests", 1),
            "total_exhausted": ("max_total_bytes", previous.stat().st_size),
            "total_remaining": ("max_total_bytes", previous.stat().st_size + size - 1),
            "response_bytes": ("max_response_bytes", size - 1),
        }[budget]
        control["limits"][field] = value

    old = row["source_capture_manifest_sha256"]
    digest = rewrite_capture(source, old, mutate)
    observe(monkeypatch, source)
    with (
        api().prepare_neotoma_preflight_batch(
            source["directory"], **source["kwargs"]
        ) as batch,
        pytest.raises(ValueError, match="budget|bound|limit"),
    ):
        batch.facet(
            observation_id=row["observation_id"].replace(old, digest),
            dataset_id=201,
            facet="doi",
        )
