"""Derived detail qualification reuses authenticated readers without ledger edits."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    capture_neotoma_linked_resources,
)

from ..facets.parent_scope.native_sources import linked_scope_resolvers
from ..resources.native_payloads import response
from .test_capture import limits, plan, source
from .test_profiles import payload


def owner() -> Any:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.qualification"
    )


def acquired(
    tmp_path: Path, *, empty: bool = False, foreign: bool = False, status: int = 200
) -> tuple[Path, Any, dict[str, Path]]:
    digest, sources = source(tmp_path / "facets")

    def fetch(url: str, **k: Any) -> Any:
        kind = {"contacts": "contact", "publications": "publication", "taxa": "taxon"}[
            url.split("/")[-2]
        ]
        value = payload(kind)
        if kind == "contact":
            value["data"][0]["contactid"] = 999 if foreign else 8720
        if kind == "taxon":
            value["data"][0]["taxonid"] = 1
        if empty:
            value["data"] = []
        return response(url, json.dumps(value).encode(), status=status)

    root = tmp_path / "linked"
    captured = capture_neotoma_linked_resources(
        root,
        plan=plan(digest),
        source_facets=sources,
        limits=limits(),
        fetch=fetch,
        scope_inputs=linked_scope_resolvers(sources),
    )
    return root, captured, sources


def test_separate_detail_qualification_preserves_all_native_capture_bytes(
    tmp_path: Path,
) -> None:
    root, capture, sources = acquired(tmp_path)
    pins = {p: p.read_bytes() for p in root.iterdir()}
    report = owner().qualify_neotoma_linked_capture(
        root,
        expected_manifest_sha256=capture.manifest_sha256,
        source_facets=sources,
        limits=limits(),
        scope_inputs=linked_scope_resolvers(sources),
    )
    assert report["source_capture_relabelled"] is False
    assert report["partitions"] == {"parsed_linked_source": 3}
    assert all(
        row["source_terminal_status"] == "received_complete_unqualified_linked_resource"
        for row in report["resources"]
    )
    assert all(row["source_proofs"] for row in report["resources"])
    assert pins == {p: p.read_bytes() for p in root.iterdir()}


def test_source_explicit_empty_is_unavailable_without_general_absence_claim(
    tmp_path: Path,
) -> None:
    root, capture, sources = acquired(tmp_path, empty=True)
    report = owner().qualify_neotoma_linked_capture(
        root,
        expected_manifest_sha256=capture.manifest_sha256,
        source_facets=sources,
        limits=limits(),
        scope_inputs=linked_scope_resolvers(sources),
    )
    assert report["partitions"] == {"unavailable_linked_api_empty": 3}
    assert all(row["absence_certified"] is False for row in report["resources"])


def test_changed_actual_reader_buffer_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, capture, sources = acquired(tmp_path)
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        replay,
    )

    original = replay.replay_neotoma_linked_resources

    def swap(*args: Any, **kwargs: Any) -> Any:
        value = original(*args, **kwargs)
        (root / capture.resources[0]["attempts"][0]["body_file"]).write_bytes(
            b'{"foreign":true}'
        )
        return value

    monkeypatch.setattr(replay, "replay_neotoma_linked_resources", swap)
    with pytest.raises(ValueError):
        owner().qualify_neotoma_linked_capture(
            root,
            expected_manifest_sha256=capture.manifest_sha256,
            source_facets=sources,
            limits=limits(),
            scope_inputs=linked_scope_resolvers(sources),
        )


def test_foreign_native_owner_keeps_a_reasoned_accounting_row(tmp_path: Path) -> None:
    root, capture, sources = acquired(tmp_path, foreign=True)
    report = owner().qualify_neotoma_linked_capture(
        root,
        expected_manifest_sha256=capture.manifest_sha256,
        source_facets=sources,
        limits=limits(),
        scope_inputs=linked_scope_resolvers(sources),
    )
    assert len(report["resources"]) == 3
    assert report["partitions"] == {
        "parsed_linked_source": 2,
        "refused_linked_source": 1,
    }
    refused = next(
        row
        for row in report["resources"]
        if row["qualification_status"] == "refused_linked_source"
    )
    assert refused["source_proofs"] and "owner" in refused["reason"]


def test_unavailable_http_entities_do_not_open_the_native_body_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, capture, sources = acquired(tmp_path, status=500)
    monkeypatch.setattr(
        owner(),
        "read_neotoma_linked_body",
        lambda *a, **k: pytest.fail("unavailable body reader called"),
    )
    report = owner().qualify_neotoma_linked_capture(
        root,
        expected_manifest_sha256=capture.manifest_sha256,
        source_facets=sources,
        limits=limits(),
        scope_inputs=linked_scope_resolvers(sources),
    )
    assert report["partitions"] == {"not_qualified_source_result": 3}
