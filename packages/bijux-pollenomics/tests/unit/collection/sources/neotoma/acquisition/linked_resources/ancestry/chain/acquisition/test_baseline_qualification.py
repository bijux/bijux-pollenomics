"""Baseline reuse stays inside one live capture owner and never caches new bodies."""

from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
    layers,
    proofs,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
    derive_neotoma_taxon_ancestry_chain,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
    workflow,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.authority import (
    ChainOperation,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
    DEFAULT_LIMITS,
)

from ..native_products import bindings
from .native_payloads import native_response
from .test_refusals import body_opens


def test_capture_reuses_baseline_but_standalone_derivation_is_fresh(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    sources = bindings(chain_products)
    replays = []
    real = proofs.source_facts

    def facts(*args: Any, **kwargs: Any) -> Any:
        result = real(*args, **kwargs)
        replays.append(result)
        return result

    monkeypatch.setattr(layers, "source_facts", facts)
    capture = workflow.capture_neotoma_taxon_ancestry_frontier(
        tmp_path / "capture",
        sources=sources,
        parent_chain_sha256=None,
        target_keys=("taxon-15",),
        fetch=lambda url, **kwargs: native_response(chain_products, url, **kwargs),
    )
    assert len(replays) == 1
    result = derive_neotoma_taxon_ancestry_chain(
        sources=replace(
            sources,
            ancestry_capture_sources={capture.manifest_sha256: capture.directory},
        ),
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(capture.manifest_sha256,),
    )
    assert len(replays) == 2
    assert result["baseline"]["seed_taxon_ids"] == [11, 12]
    assert (
        result["known_entity_results"]["taxon-15"]["qualification_status"]
        == "qualified_native_detail"
    )


def test_verified_facts_are_detached_and_expire_with_original_owner(
    chain_products: dict[str, Any], monkeypatch: Any
) -> None:
    sources = bindings(chain_products)
    with ChainOperation(sources) as operation:
        operation.resolve(None, DEFAULT_LIMITS)
        qualified = operation._qualified_baseline
        assert qualified is not None and type(qualified._facts) is bytes
        first = qualified.read(sources, DEFAULT_LIMITS)
        first["authority"]["declared_seed_taxon_ids"].append(999)
        assert qualified.read(sources, DEFAULT_LIMITS)["authority"][
            "declared_seed_taxon_ids"
        ] == [11, 12]
        with pytest.raises(FrozenInstanceError):
            qualified._facts = b"{}"  # type: ignore[misc]
    opened = body_opens(monkeypatch)
    with pytest.raises(ValueError, match="closed"):
        qualified.read(sources, DEFAULT_LIMITS)
    assert not opened


@pytest.mark.parametrize("change", ["source", "limits"])
def test_verified_facts_cannot_cross_scope_or_limits(
    chain_products: dict[str, Any], tmp_path: Path, change: str
) -> None:
    sources = bindings(chain_products)
    with ChainOperation(sources) as operation:
        operation.resolve(None, DEFAULT_LIMITS)
        qualified = operation._qualified_baseline
        assert qualified is not None
        other = (
            replace(sources, baseline_projection_directory=tmp_path / "foreign")
            if change == "source"
            else sources
        )
        limits = (
            replace(DEFAULT_LIMITS, max_new_taxa=2)
            if change == "limits"
            else DEFAULT_LIMITS
        )
        with pytest.raises(ValueError, match="scope or limits"):
            qualified.read(other, limits)


def test_child_cannot_reactivate_qualification_after_owner_exit(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    sources = bindings(chain_products)
    with ChainOperation(sources) as operation:
        operation.resolve(None, DEFAULT_LIMITS)
        child = operation._capture_child("a" * 64, tmp_path / "unused")
    opened = body_opens(monkeypatch)
    with pytest.raises(ValueError, match="closed"), child:
        child.resolve(None, DEFAULT_LIMITS)
    assert not opened


@pytest.mark.parametrize(
    "damage", ["inplace", "inode", "leaf_alias", "ancestor", "role", "PI"]
)
@pytest.mark.parametrize("ancestry_products", [{"parent11": 14}], indirect=True)
def test_changed_original_source_refuses_before_second_fetch(
    chain_products: dict[str, Any], tmp_path: Path, damage: str
) -> None:
    sources = bindings(chain_products)
    body = next(chain_products["capture"].glob("taxon-11*.body"))
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
        load_neotoma_ancillary_context,
    )

    context = load_neotoma_ancillary_context(
        sources.current_context_directory,
        expected_manifest_sha256=sources.expected_current_context_sha256,
        native_archive_directory=sources.current_native_archive_directory,
    )
    scope = context.current_scope_inputs[
        context.manifest["native_archive"]["current_roster_sha256"]
    ]
    permission = scope.roster_path
    if damage == "PI":
        permission = next(next(iter(scope.metadata_captures.values())).glob("*.body"))
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        assert len(calls) == 1, "Revoked original authority reached another fetch"
        response = native_response(chain_products, url, **kwargs)
        if damage == "inplace":
            body.write_bytes(b"x" + body.read_bytes()[1:])
        elif damage == "inode":
            other = tmp_path / "same-bytes.body"
            other.write_bytes(body.read_bytes())
            other.replace(body)
        elif damage == "leaf_alias":
            other = tmp_path / "aliased.body"
            other.write_bytes(body.read_bytes())
            body.unlink()
            body.symlink_to(other)
        elif damage == "ancestor":
            root = chain_products["capture"]
            root.rename(tmp_path / "moved-original")
            root.mkdir()
            (root / "foreign.txt").write_text("Preserve foreign namespace")
        elif damage == "role":
            roster = json.loads(permission.read_bytes())
            incoming = next(
                row for row in roster["resources"] if row["dataset_id"] == 203
            )
            incoming["exposure_roles"]["current"] = "heldout_no_numerical_access"
            permission.write_text(json.dumps(roster))
        else:
            inventory = json.loads(permission.read_bytes())
            native = next(
                dataset
                for site in inventory["data"]
                for dataset in site["site"]["datasets"]
                if dataset["datasetid"] == 202
            )
            assert native["datasetpi"][0]["contactid"] == 900
            native["datasetpi"][0]["contactid"] = 901
            permission.write_text(json.dumps(inventory))
        return response

    destination = tmp_path / "refused-capture"
    with pytest.raises(
        ValueError, match="changed|alias|namespace|identity|attachment|member"
    ):
        workflow.capture_neotoma_taxon_ancestry_frontier(
            destination,
            sources=sources,
            parent_chain_sha256=None,
            target_keys=("taxon-14", "taxon-15"),
            fetch=fetch,
        )
    assert len(calls) == 1 and not destination.exists()
    if damage == "ancestor":
        assert (
            chain_products["capture"] / "foreign.txt"
        ).read_text() == "Preserve foreign namespace"


@pytest.mark.parametrize("stage", ["candidate", "final"])
@pytest.mark.parametrize("original", [False, True])
def test_changed_source_at_publication_boundary_refuses(
    chain_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: Any,
    stage: str,
    original: bool,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication.ownership import (
        publish_owned_source_tree,
    )

    real_publish = publish_owned_source_tree
    fired = []

    def publish(*args: Any, **kwargs: Any) -> Any:
        validate = kwargs["validate"]

        def inspect(path: Path) -> Any:
            current = "final" if path == kwargs["final"] else "candidate"
            if current == stage:
                selected = chain_products["capture"] if original else path
                body = next(selected.glob("*.body"))
                body.write_bytes(b"x" + body.read_bytes()[1:])
                fired.append(current)
            return validate(path)

        return real_publish(*args, **{**kwargs, "validate": inspect})

    monkeypatch.setattr(workflow, "publish_owned_source_tree", publish)
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return native_response(chain_products, url, **kwargs)

    with pytest.raises(ValueError):
        workflow.capture_neotoma_taxon_ancestry_frontier(
            tmp_path / "refused-publication",
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=fetch,
        )
    assert fired == [stage] and len(calls) == 1


def test_primary_validation_failure_survives_refusal_receipt_error(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication.ownership import (
        publish_owned_source_tree,
    )

    primary = RuntimeError("Generated primary validation failure")
    real = workflow._control

    def control(path: Path, payload: Any, writer: Any) -> str:
        if path.name == "refusal.json":
            raise OSError("Generated refusal receipt failure")
        return real(path, payload, writer)

    def publish(*args: Any, **kwargs: Any) -> Any:
        validate = kwargs["validate"]

        def refuse(path: Path) -> Any:
            validate(path)
            raise primary

        return publish_owned_source_tree(*args, **{**kwargs, "validate": refuse})

    monkeypatch.setattr(workflow, "_control", control)
    monkeypatch.setattr(workflow, "publish_owned_source_tree", publish)
    with pytest.raises(RuntimeError) as raised:
        workflow.capture_neotoma_taxon_ancestry_frontier(
            tmp_path / "refused-primary",
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=lambda url, **kwargs: native_response(chain_products, url, **kwargs),
        )
    assert raised.value is primary
    assert any("refusal receipt failed" in note for note in primary.__notes__)
