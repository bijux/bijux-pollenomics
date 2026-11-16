"""Maintained frontier capture produces strict replayable native receipt trees."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from ..native_products import bindings, publish_chain
from .native_payloads import native_response


def capture_api() -> Any:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
        capture_neotoma_taxon_ancestry_frontier,
    )

    return capture_neotoma_taxon_ancestry_frontier


def test_explicit_frontier_capture_replays_and_does_not_follow_new_parents(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    sources = bindings(chain_products)
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        assert kwargs["max_bytes"] == 2 * 1024 * 1024
        assert 0 < kwargs["timeout"] <= 60
        return native_response(chain_products, url)

    destination = tmp_path / "captured-parents"
    result = capture_api()(
        destination,
        sources=sources,
        parent_chain_sha256=None,
        target_keys=("taxon-15",),
        fetch=fetch,
    )
    assert calls == ["https://api.neotomadb.org/v2.0/data/taxa/15"]
    assert result.directory == destination
    assert result.request_count == 1
    raw = (destination / "capture-manifest.json").read_bytes()
    assert result.manifest_sha256 == sha256(raw).hexdigest()
    manifest = json.loads(raw)
    assert manifest["request_count"] == 1
    assert manifest["resources"][0]["recorded_hop"] == 1
    assert manifest["resources"][0]["root_dataset_ids"] == [201, 203]
    assert manifest["scientific_admission"] == "not_asserted"
    sources = replace(
        sources, ancestry_capture_sources={result.manifest_sha256: destination}
    )
    document = derive_neotoma_taxon_ancestry_chain(
        sources=sources,
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(result.manifest_sha256,),
    )
    assert document["baseline"]["seed_taxon_ids"] == [11, 12]
    assert (
        document["known_entity_results"]["taxon-15"]["qualification_status"]
        == "qualified_native_detail"
    )
    assert {row["target_key"] for row in document["frontier"]} >= {
        "taxon-16",
        "publication-19",
    }


@pytest.mark.parametrize("also_parent", [False, True])
def test_child_pointer_publications_use_same_maintained_capture_contract(
    chain_products: dict[str, Any], tmp_path: Path, also_parent: bool
) -> None:
    sources = bindings(chain_products)
    initial = tmp_path / "first-capture"
    result = capture_api()(
        initial,
        sources=sources,
        parent_chain_sha256=None,
        target_keys=("taxon-15",),
        fetch=lambda url, **kwargs: native_response(chain_products, url, **kwargs),
    )
    sources = replace(
        sources, ancestry_capture_sources={result.manifest_sha256: initial}
    )
    sources, parent, _ = publish_chain(
        tmp_path / "parent-chain",
        sources=sources,
        captures=(result.manifest_sha256,),
    )
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return native_response(chain_products, url, **kwargs)

    final = tmp_path / "publication-capture"
    publication = capture_api()(
        final,
        sources=sources,
        parent_chain_sha256=parent,
        target_keys=("publication-19", "taxon-16")
        if also_parent
        else ("publication-19",),
        fetch=fetch,
    )
    assert calls == ["https://api.neotomadb.org/v2.0/data/publications/19"] + (
        ["https://api.neotomadb.org/v2.0/data/taxa/16"] if also_parent else []
    )
    row = json.loads((final / "capture-manifest.json").read_bytes())["resources"][0]
    assert row["kind"] == "publication" and row["native_id"] == 19
    assert row["recorded_hop"] is None
    assert publication.request_count == 1 + int(also_parent)


@pytest.mark.parametrize(
    "kind", ["http", "non_json", "empty", "transport", "wrong_owner", "malformed_empty"]
)
def test_source_refusals_are_retained_without_retry_or_invented_absence(
    chain_products: dict[str, Any], tmp_path: Path, kind: str
) -> None:
    from .....resources.native_payloads import response

    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        if kind == "transport":
            raise OSError("generated source unavailable")
        if kind == "wrong_owner":
            wrong = native_response(chain_products, url.replace("/15", "/99"))
            return replace(wrong, final_url=url)
        body = (
            b"not JSON"
            if kind == "non_json"
            else b'{"status":"success","data":[],"message":"Literal empty source"}'
        )
        if kind == "malformed_empty":
            body = b'{"status":"success","data":[]}'
        return response(url, body, 503 if kind == "http" else 200)

    destination = tmp_path / "source-result"
    result = capture_api()(
        destination,
        sources=bindings(chain_products),
        parent_chain_sha256=None,
        target_keys=("taxon-15",),
        fetch=fetch,
    )
    manifest = json.loads((destination / "capture-manifest.json").read_bytes())
    expected = {
        "http": "unavailable_http",
        "non_json": "refused_native_json",
        "empty": "received_complete_unqualified_linked_resource",
        "transport": "unavailable_transport",
        "wrong_owner": "received_complete_unqualified_linked_resource",
        "malformed_empty": "received_complete_unqualified_linked_resource",
    }[kind]
    assert manifest["resources"][0]["terminal_status"] == expected
    assert len(calls) == result.request_count == 1
    assert len(manifest["resources"][0]["attempts"]) == 1
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    sources = replace(
        bindings(chain_products),
        ancestry_capture_sources={result.manifest_sha256: destination},
    )
    document = derive_neotoma_taxon_ancestry_chain(
        sources=sources,
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(result.manifest_sha256,),
    )
    qualification = document["known_entity_results"]["taxon-15"]["qualification_status"]
    assert qualification == (
        "successful_empty_not_absence"
        if kind == "empty"
        else "refused_source_profile"
        if kind in {"wrong_owner", "malformed_empty"}
        else "unavailable_source_result"
    )


@pytest.mark.parametrize("excess", [1, 2])
def test_single_sentinel_is_retained_and_larger_callback_entity_refuses(
    chain_products: dict[str, Any], tmp_path: Path, excess: int
) -> None:
    from .....resources.native_payloads import response

    destination = tmp_path / "bounded-entity"
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return replace(
            response(url, b"x" * (2 * 1024 * 1024 + excess)), body_complete=False
        )

    if excess == 2:
        with pytest.raises(ValueError, match="finite HTTP entity"):
            capture_api()(
                destination,
                sources=bindings(chain_products),
                parent_chain_sha256=None,
                target_keys=("taxon-15",),
                fetch=fetch,
            )
        assert not destination.exists()
    else:
        result = capture_api()(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=fetch,
        )
        row = json.loads((destination / "capture-manifest.json").read_bytes())[
            "resources"
        ][0]
        assert row["terminal_status"] == "refused_incomplete_body"
        assert result.response_bytes == 2 * 1024 * 1024 + 1
    assert len(calls) == 1


def test_readonly_mapping_resolvers_remain_valid_source_bindings(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from types import MappingProxyType

    sources = bindings(chain_products)
    recorded = replace(
        sources.recorded_baseline_sources,
        capture_sources=MappingProxyType(
            dict(sources.recorded_baseline_sources.capture_sources)
        ),
        source_facets=MappingProxyType(
            dict(sources.recorded_baseline_sources.source_facets)
        ),
    )
    sources = replace(
        sources,
        recorded_baseline_sources=recorded,
        chain_sources=MappingProxyType({}),
        ancestry_capture_sources=MappingProxyType({}),
        context_sources=MappingProxyType({}),
        native_archive_sources=MappingProxyType({}),
    )
    result = capture_api()(
        tmp_path / "readonly-resolver-capture",
        sources=sources,
        parent_chain_sha256=None,
        target_keys=("taxon-15",),
        fetch=lambda url, **kwargs: native_response(chain_products, url, **kwargs),
    )
    assert result.request_count == 1
