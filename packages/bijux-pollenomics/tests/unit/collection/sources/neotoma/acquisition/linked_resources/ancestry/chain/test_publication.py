"""Delta output retains ownership and complete independently resolved parents."""

from pathlib import Path
from typing import Any

import pytest

from .native_products import bindings, publish_chain


def test_zero_capture_delta_owns_no_source_copies(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        load_neotoma_taxon_ancestry_chain,
    )

    sources, pin, document = publish_chain(
        tmp_path / "delta", sources=bindings(chain_products)
    )
    assert list((tmp_path / "delta").iterdir()) == [tmp_path / "delta/manifest.json"]
    assert (tmp_path / "delta/manifest.json").stat().st_size < 10000
    assert (
        load_neotoma_taxon_ancestry_chain(
            tmp_path / "delta", expected_manifest_sha256=pin, sources=sources
        )
        == document
    )


def test_source_equal_byte_swap_during_write_refuses_before_final(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    import shutil

    import pytest

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
        publish_neotoma_taxon_ancestry_chain,
    )
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    sources = bindings(chain_products)
    document = derive_neotoma_taxon_ancestry_chain(
        sources=sources, parent_chain_sha256=None, new_capture_manifest_sha256s=()
    )
    original = OwnedTreeWriter.write_bytes
    moved = tmp_path / "detached-source"
    swapped: list[bool] = []

    def write(writer: Any, relative: str, content: bytes) -> None:
        original(writer, relative, content)
        if not swapped:
            sources.baseline_projection_directory.rename(moved)
            shutil.copytree(moved, sources.baseline_projection_directory)
            swapped.append(True)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", write)
    with pytest.raises(ValueError, match="identity|namespace|attachment"):
        publish_neotoma_taxon_ancestry_chain(
            tmp_path / "final", document=document, sources=sources
        )
    assert swapped and moved.exists() and sources.baseline_projection_directory.exists()
    assert not (tmp_path / "final").exists()


@pytest.mark.parametrize("boundary", ["stage", "rename", "readback"])
def test_equal_byte_output_substitution_refuses_and_retains(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, boundary: str
) -> None:
    import shutil

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        storage,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
        publish_neotoma_taxon_ancestry_chain,
    )
    from bijux_pollenomics.collection.sources.neotoma.publication import ownership

    sources = bindings(chain_products)
    document = derive_neotoma_taxon_ancestry_chain(
        sources=sources, parent_chain_sha256=None, new_capture_manifest_sha256s=()
    )
    final, saved = tmp_path / "final", tmp_path / "detached-output"
    load = storage._readback
    publish = vars(ownership)["publish_new_output_tree"]
    swapped, published = [], []

    def swap(path: Path) -> None:
        path.rename(saved)
        shutil.copytree(saved, path)
        swapped.append(path)

    def readback(path: Path, *args: Any, **kwargs: Any) -> Any:
        result = load(path, *args, **kwargs)
        if not swapped and (
            boundary == "stage"
            and path.name.startswith(".final")
            or boundary == "readback"
            and path == final
        ):
            swap(path)
        return result

    def publication(**kwargs: Any) -> None:
        publish(**kwargs)
        published.append(True)
        if boundary == "rename":
            swap(final)

    monkeypatch.setattr(storage, "_readback", readback)
    monkeypatch.setattr(ownership, "publish_new_output_tree", publication)
    with pytest.raises(ValueError, match="identity|inode"):
        publish_neotoma_taxon_ancestry_chain(final, document=document, sources=sources)
    assert swapped and saved.exists() and swapped[0].exists()
    assert (saved / "manifest.json").read_bytes() == (
        swapped[0] / "manifest.json"
    ).read_bytes()
    assert bool(published) is (boundary != "stage")


def test_original_default_eleven_part_bytes_match_frozen_legacy_digest() -> None:
    from hashlib import sha256

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        publication,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.models import (
        SCHEMA,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    document = {
        **dict.fromkeys(publication.COLLECTIONS, []),
        "schema_version": SCHEMA,
        "seeds": [
            {"native_id": identity, "text": "Å字\n" * 9000} for identity in range(340)
        ],
    }
    manifest, buffers = publication._pack(document)
    assert len(buffers) == 11
    assert (
        sha256(encoded_json(manifest)).hexdigest()
        == "0e8000d4c12d60a77efab58f2eb8d642d2325f2427a3ed6243099faa851c459f"
    )
    assert all(
        sha256(buffers[part["path"]]).hexdigest() == part["sha256"]
        for part in manifest["parts"]
    )


@pytest.mark.parametrize(
    "limit,value",
    [
        ("max_additional_parent_hops", True),
        ("max_additional_parent_hops", 33),
        ("max_new_taxa", 0),
        ("max_new_requests", 10001),
        ("max_literal_edges", 100001),
    ],
)
def test_invalid_limits_refuse_before_resolvers(limit: str, value: Any) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        NeotomaTaxonAncestryChainLimits,
        derive_neotoma_taxon_ancestry_chain,
    )

    invalid: Any = None
    with pytest.raises(ValueError, match="bounds"):
        derive_neotoma_taxon_ancestry_chain(
            sources=invalid,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(),
            limits=NeotomaTaxonAncestryChainLimits(**{limit: value}),
        )


@pytest.mark.parametrize("source_kind", ["context", "native"])
def test_equal_pin_current_copy_cannot_replace_recorded_source_path_seal(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, source_kind: str
) -> None:
    from dataclasses import replace
    import shutil

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
        publish_neotoma_taxon_ancestry_chain,
    )
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    sources = bindings(chain_products)
    original = chain_products["sources"]
    recorded = (
        original.context_directory
        if source_kind == "context"
        else original.native_archive_directory
    )
    copied = tmp_path / "portable-current"
    shutil.copytree(recorded, copied)
    sources = replace(
        sources,
        **{
            "current_context_directory"
            if source_kind == "context"
            else "current_native_archive_directory": copied
        },
    )
    document = derive_neotoma_taxon_ancestry_chain(
        sources=sources, parent_chain_sha256=None, new_capture_manifest_sha256s=()
    )
    write = OwnedTreeWriter.write_bytes
    swapped: list[bool] = []
    detached = tmp_path / "detached-recorded-source"

    def observe(writer: Any, relative: str, raw: bytes) -> None:
        write(writer, relative, raw)
        if not swapped:
            recorded.rename(detached)
            shutil.copytree(detached, recorded)
            swapped.append(True)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", observe)
    with pytest.raises(ValueError, match="identity|namespace|attachment"):
        publish_neotoma_taxon_ancestry_chain(
            tmp_path / "final", document=document, sources=sources
        )
    assert swapped and detached.exists() and recorded.exists() and copied.exists()
    assert not (tmp_path / "final").exists()


def test_operational_file_profile_exact_boundary_uses_real_inventory(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        AncestrySourceBudget,
    )
    from bijux_pollenomics.core.filesystem import BoundedInputTree

    directory = tmp_path / "source-profile"
    directory.mkdir()
    for identity in range(40960):
        (directory / f"member-{identity}").touch()
    budget = AncestrySourceBudget()
    with BoundedInputTree(directory, max_files=40961, max_bytes=1) as tree:
        budget.include(tree.files)
    assert len(budget.members) == 40960
    assert sum(budget.members.values()) == 0
    (directory / "one-more-member").touch()
    with (
        BoundedInputTree(directory, max_files=40961, max_bytes=1) as tree,
        pytest.raises(ValueError, match="budget"),
    ):
        budget.include(tree.files)


@pytest.mark.parametrize("maximum", [0, -1, True, 40961, 40960.0, "40960"])
def test_operational_file_profile_requires_positive_native_bound(maximum: Any) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        AncestrySourceBudget,
    )

    with pytest.raises(ValueError, match="file bound"):
        AncestrySourceBudget(max_files=maximum)
