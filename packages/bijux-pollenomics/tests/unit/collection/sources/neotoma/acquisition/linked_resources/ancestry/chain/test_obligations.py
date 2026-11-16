"""Every known incoming root contributes duties despite self and cyclic edges."""

from pathlib import Path
from typing import Any

import pytest

from .native_products import bindings, capture_parent, publish_chain


def test_new_back_edge_propagates_all_roots_without_new_seeds(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    sources, capture = capture_parent(chain_products, tmp_path / "back-edge", parent=11)
    _, _, document = publish_chain(
        tmp_path / "cycle-chain", sources=sources, captures=(capture,)
    )
    assert document["cycle_components"] == [[11, 12, 15]]
    assert all(
        row["current_root_dataset_ids"] == [201, 203] for row in document["taxa"]
    )
    assert document["summary"]["declared_seed_taxa"] == 2


def test_missing_capture_resolver_refuses(chain_products: dict[str, Any]) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    with pytest.raises(ValueError, match="source is missing"):
        derive_neotoma_taxon_ancestry_chain(
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=("a" * 64,),
        )


@pytest.mark.parametrize(
    "change",
    [
        "roots",
        "depth",
        "boolean_depth",
        "witness",
        "kind",
        "native",
        "late_unknown",
        "partial",
        "parent",
        "body_locator",
        "boolean_attempts",
    ],
)
def test_forged_or_incomplete_controls_refuse_before_new_body(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, change: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import change_capture, observe_native_body_opens

    sources, capture = capture_parent(chain_products, tmp_path / "detail")

    def mutate(manifest: dict[str, Any], plan: dict[str, Any]) -> None:
        entry = manifest["resources"][0]
        if change == "roots":
            entry["root_dataset_ids"] = [203]
        elif change == "depth":
            entry["recorded_hop"] = 0
        elif change == "boolean_depth":
            entry["recorded_hop"] = True
        elif change == "witness":
            entry["witness_edge_id"] = "0" * 64
        elif change == "kind":
            entry["kind"] = "publication"
        elif change == "native":
            entry["native_id"] = True
        elif change == "partial":
            manifest["status"] = "partial"
        elif change == "parent":
            plan["source_ancestry"]["manifest_sha256"] = "0" * 64
        elif change == "body_locator":
            entry["attempts"][0]["body_file"] = "../foreign.body"
        elif change == "boolean_attempts":
            plan["limits"]["max_attempts"] = True
        else:
            plan["frontier_target_keys"].append("taxon-999")
            manifest["resources"].append(
                {**entry, "target_key": "taxon-999", "native_id": 999}
            )

    sources, capture = change_capture(sources, capture, mutate)
    opened = observe_native_body_opens(monkeypatch, "taxon-15-current-attempt-1.body")
    with pytest.raises(ValueError):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(capture,),
        )
    assert opened == []


def test_real_descriptor_positive_control_reads_selected_new_body_once(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    import os

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import observe_native_body_opens

    sources, capture = capture_parent(chain_products, tmp_path / "detail")
    all_native = observe_native_body_opens(monkeypatch, None)
    opened = observe_native_body_opens(monkeypatch, "taxon-15-current-attempt-1.body")
    result = derive_neotoma_taxon_ancestry_chain(
        sources=sources,
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(capture,),
    )
    assert len(all_native) == 12
    assert len(opened) == 1
    assert result["summary"]["known_taxon_nodes"] == 4
    with pytest.raises(OSError):
        os.fstat(opened[0])


@pytest.mark.parametrize("alias", ["symlink", "hardlink", "fifo"])
def test_capture_body_alias_refuses_before_descriptor_open(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, alias: str
) -> None:
    import os

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import observe_native_body_opens

    sources, capture = capture_parent(chain_products, tmp_path / "detail")
    body = tmp_path / "detail/taxon-15-current-attempt-1.body"
    foreign = tmp_path / "foreign.body"
    body.rename(foreign)
    if alias == "symlink":
        body.symlink_to(foreign)
    elif alias == "hardlink":
        os.link(foreign, body)
    else:
        os.mkfifo(body)
    opened = observe_native_body_opens(monkeypatch, body.name)
    with pytest.raises(ValueError):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(capture,),
        )
    assert opened == [] and foreign.is_file()


def test_actual_growth_reads_only_original_size_plus_sentinel_and_closes_fd(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    import os

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    sources, capture = capture_parent(chain_products, tmp_path / "detail")
    body = tmp_path / "detail/taxon-15-current-attempt-1.body"
    size = body.stat().st_size
    real_open, real_read = os.open, os.read
    descriptors: list[int] = []
    read_bytes: list[int] = []
    grown: list[bool] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = real_open(path, flags, *args, **kwargs)
        if Path(path).name == body.name and not flags & os.O_DIRECTORY:
            descriptors.append(descriptor)
        return descriptor

    def read(descriptor: int, count: int) -> bytes:
        if descriptor in descriptors:
            if not grown:
                with body.open("ab") as stream:
                    stream.write(b"x" * 100000)
                grown.append(True)
            raw = real_read(descriptor, count)
            read_bytes.append(len(raw))
            return raw
        return real_read(descriptor, count)

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "read", read)
    with pytest.raises(ValueError, match="growth|identity|size"):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(capture,),
        )
    assert len(descriptors) == 1 and grown
    assert sum(read_bytes) <= size + 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])


def test_cycle_algorithm_keeps_restrictive_incoming_root_at_fixed_point(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.authority import (
        ChainOperation,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        DEFAULT_LIMITS,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.projection import (
        project,
    )

    sources, capture = capture_parent(chain_products, tmp_path / "loop", parent=11)
    with ChainOperation(sources) as operation:
        state, _ = operation.resolve(None, DEFAULT_LIMITS)
        operation.captures(state, None, (capture,), DEFAULT_LIMITS)
    # Pure projection inputs exercise a second incoming path; public source
    # authentication and actual protected-body gates have separate controls.
    state["direct_roots"] = {
        "taxon-11": {201},
        "taxon-12": {203},
        "publication-13": {201},
    }
    graph = project(
        state,
        {201: "development_resource_discovery", 203: "heldout_no_numerical_access"},
        DEFAULT_LIMITS,
    )
    assert graph["cycle_components"] == [[11, 12, 15]]
    assert all(
        row["current_root_dataset_ids"] == [201, 203] for row in graph["nodes"].values()
    )
    assert all(
        row["current_use_role"] == "heldout_no_numerical_access"
        for row in graph["nodes"].values()
    )


def test_independent_pi_duty_survives_a_weaker_later_metadata_epoch() -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        entity_role,
    )

    role = entity_role(
        {"kind": "contact", "native_id": 901},
        {201},
        {201: "development_resource_discovery"},
        [
            {"protected": {"901": {"exposure_role": "heldout_no_numerical_access"}}},
            {"protected": {}},
        ],
    )
    assert role == "heldout_no_numerical_access"


def test_unknown_capture_resolver_refuses_before_baseline_native_replay(
    chain_products: dict[str, Any], monkeypatch: Any
) -> None:
    import os

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    opened, original = [], os.open

    def observe(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original(path, flags, *args, **kwargs)
        if Path(path).name.startswith(("taxon-", "publication-")) and str(
            path
        ).endswith(".body"):
            opened.append(path)
        return descriptor

    monkeypatch.setattr(os, "open", observe)
    with pytest.raises(ValueError, match="source is missing"):
        derive_neotoma_taxon_ancestry_chain(
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=("a" * 64,),
        )
    assert opened == []


@pytest.mark.parametrize(
    "change",
    [
        "late_unknown_target",
        "missing_body",
        "wrong_receipt_digest",
        "unknown_control_key",
    ],
)
def test_complete_capture_metadata_refusal_opens_no_native_body(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, change: str
) -> None:
    import os

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )

    from .native_products import change_capture

    sources, pin = capture_parent(chain_products, tmp_path / "capture")

    def alter(manifest: dict[str, Any], plan: dict[str, Any]) -> None:
        if change == "late_unknown_target":
            manifest["resources"].append(
                {
                    **manifest["resources"][0],
                    "target_key": "taxon-999",
                    "native_id": 999,
                }
            )
            plan["frontier_target_keys"].append("taxon-999")
        elif change == "wrong_receipt_digest":
            manifest["resources"][0]["attempts"][0]["receipt_sha256"] = "0" * 64
        elif change == "unknown_control_key":
            manifest["resources"][0]["caller_authorized"] = True

    sources, pin = change_capture(sources, pin, alter)
    if change == "missing_body":
        (tmp_path / "capture/taxon-15-current-attempt-1.body").unlink()
    original, opened = os.open, []

    def observe(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original(path, flags, *args, **kwargs)
        if (
            not flags & os.O_DIRECTORY
            and Path(path).name.startswith(("taxon-", "publication-", "contact-"))
            and str(path).endswith(".body")
        ):
            opened.append(path)
        return descriptor

    monkeypatch.setattr(os, "open", observe)
    with pytest.raises(ValueError):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(pin,),
        )
    assert opened == []


def test_real_input_tree_sizes_enforce_aggregate_before_body(
    tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        MAX_SOURCE_BYTES,
        AncestrySourceBudget,
    )
    from bijux_pollenomics.core.filesystem import BoundedInputTree

    budget = AncestrySourceBudget()
    for name in ("first", "second"):
        directory = tmp_path / name
        directory.mkdir()
        with (directory / "member.bin").open("wb") as stream:
            stream.truncate(400 * 1024 * 1024)
    monkeypatch.setattr(
        BoundedInputTree,
        "read",
        lambda *args, **kwargs: pytest.fail("Budget inventory opened a body"),
    )
    with BoundedInputTree(
        tmp_path / "first", max_files=2, max_bytes=512 * 1024 * 1024
    ) as first:
        budget.include(first.files)
        budget.include(first.files)
        assert len(budget.members) == 1
        assert sum(budget.members.values()) == 400 * 1024 * 1024
    with (
        BoundedInputTree(
            tmp_path / "second", max_files=2, max_bytes=512 * 1024 * 1024
        ) as second,
        pytest.raises(ValueError, match="budget"),
    ):
        budget.include(second.files)
    assert sum(budget.members.values()) > MAX_SOURCE_BYTES


@pytest.mark.parametrize("stage", ["before_entity", "after_receipt"])
def test_current_permission_drift_refuses_before_new_entity_body(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, stage: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.authority import (
        ChainOperation,
    )

    from .native_products import observe_native_body_opens

    sources, capture = capture_parent(chain_products, tmp_path / "detail")
    permission = sources.current_context_directory / "manifest.json"
    original_entity, original_read = ChainOperation.entity, ChainOperation.read
    in_entity = False
    mutated = False

    def revoke() -> None:
        nonlocal mutated
        permission.write_bytes(permission.read_bytes())
        mutated = True

    def entity(operation: Any, *args: Any, **kwargs: Any) -> Any:
        nonlocal in_entity
        in_entity = True
        if stage == "before_entity":
            revoke()
        return original_entity(operation, *args, **kwargs)

    def read(operation: Any, root: Path, name: str, bound: int) -> bytes:
        raw = original_read(operation, root, name, bound)
        if in_entity and stage == "after_receipt" and name.endswith(".receipt.json"):
            revoke()
        return raw

    opened = observe_native_body_opens(monkeypatch, "taxon-15-current-attempt-1.body")
    monkeypatch.setattr(ChainOperation, "entity", entity)
    monkeypatch.setattr(ChainOperation, "read", read)
    with pytest.raises(ValueError, match="changed"):
        derive_neotoma_taxon_ancestry_chain(
            sources=sources,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(capture,),
        )
    assert mutated
    assert opened == []
