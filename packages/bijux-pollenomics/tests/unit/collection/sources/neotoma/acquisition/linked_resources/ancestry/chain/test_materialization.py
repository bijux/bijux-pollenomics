"""One live source qualification supplies a complete independently readable chain."""

from hashlib import sha256
from pathlib import Path
import shutil
from typing import Any

import pytest

from .native_products import bindings, capture_parent


def test_materialized_capture_matches_fresh_legacy_projection_and_selected_reader(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        publication as baseline_publication,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        publication,
        read_neotoma_taxon_chain_target,
    )

    sources, capture = capture_parent(chain_products, tmp_path / "detail")
    replay = baseline_publication._load_taxon_ancestry
    calls: list[Path] = []

    def count(directory: Path, **kwargs: Any) -> Any:
        calls.append(directory)
        return replay(directory, **kwargs)

    monkeypatch.setattr(baseline_publication, "_load_taxon_ancestry", count)
    document = publication.derive_neotoma_taxon_ancestry_chain(
        sources=sources,
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(capture,),
    )
    expected = publication.publish_neotoma_taxon_ancestry_chain(
        tmp_path / "legacy", document=document, sources=sources
    )
    assert len(calls) == 2
    calls.clear()
    actual = publication.materialize_neotoma_taxon_ancestry_chain(
        tmp_path / "materialized",
        sources=sources,
        parent_chain_sha256=None,
        new_capture_manifest_sha256s=(capture,),
    )
    assert len(calls) == 1 and actual == expected
    for member in (tmp_path / "legacy").rglob("*"):
        if member.is_file():
            assert (
                member.read_bytes()
                == (
                    tmp_path / "materialized" / member.relative_to(tmp_path / "legacy")
                ).read_bytes()
            )
    pin = sha256((tmp_path / "materialized/manifest.json").read_bytes()).hexdigest()
    selected = read_neotoma_taxon_chain_target(
        tmp_path / "materialized",
        expected_manifest_sha256=pin,
        kind="taxon",
        native_id=16,
        chain_sources={
            pin: tmp_path / "materialized",
            chain_products["baseline_sha256"]: chain_products["baseline"],
        },
    )
    assert selected["recorded_edges"]
    assert selected["GET_authorized"] is False
    assert selected["current_roles_revalidated"] is False
    assert len(calls) == 1


def test_materialization_refuses_source_replacement_during_write(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        publication,
    )
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    sources = bindings(chain_products)
    original = OwnedTreeWriter.write_bytes
    detached = tmp_path / "detached-source"
    swaps: list[bool] = []

    def write(writer: Any, relative: str, content: bytes) -> None:
        original(writer, relative, content)
        if not swaps:
            sources.baseline_projection_directory.rename(detached)
            shutil.copytree(detached, sources.baseline_projection_directory)
            swaps.append(True)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", write)
    with pytest.raises(ValueError, match="identity|namespace|attachment"):
        publication.materialize_neotoma_taxon_ancestry_chain(
            tmp_path / "final",
            sources=sources,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(),
        )
    assert swaps and detached.exists() and not (tmp_path / "final").exists()


@pytest.mark.parametrize("boundary", ["stage", "rename", "readback"])
def test_materialization_refuses_substituted_completed_output(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, boundary: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        storage,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        publication,
    )
    from bijux_pollenomics.collection.sources.neotoma.publication import ownership

    final, detached = tmp_path / "final", tmp_path / "detached-output"
    original_readback = storage._readback
    original_publish = vars(ownership)["publish_new_output_tree"]
    swaps: list[Path] = []

    def swap(path: Path) -> None:
        path.rename(detached)
        shutil.copytree(detached, path)
        swaps.append(path)

    def readback(path: Path, *args: Any, **kwargs: Any) -> Any:
        result = original_readback(path, *args, **kwargs)
        if not swaps and (
            boundary == "stage"
            and path.name.startswith(".final")
            or boundary == "readback"
            and path == final
        ):
            swap(path)
        return result

    def publish(**kwargs: Any) -> None:
        original_publish(**kwargs)
        if boundary == "rename":
            swap(final)

    monkeypatch.setattr(storage, "_readback", readback)
    monkeypatch.setattr(ownership, "publish_new_output_tree", publish)
    with pytest.raises(ValueError, match="identity|inode"):
        publication.materialize_neotoma_taxon_ancestry_chain(
            final,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(),
        )
    assert swaps and detached.exists() and swaps[0].exists()


def test_materialization_cannot_return_before_source_owner_closes(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        publication,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.authority import (
        ChainOperation,
    )

    original = ChainOperation.__exit__
    closed: list[bool] = []

    def close(operation: Any, *args: Any) -> None:
        original(operation, *args)
        closed.append(True)
        raise OSError("source closure failed")

    monkeypatch.setattr(ChainOperation, "__exit__", close)
    with pytest.raises(OSError, match="source closure failed"):
        publication.materialize_neotoma_taxon_ancestry_chain(
            tmp_path / "final",
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(),
        )
    assert closed and (tmp_path / "final/manifest.json").is_file()


@pytest.mark.parametrize("value", [True, 0, 10001])
def test_materialization_invalid_limits_refuse_before_source_resolution(
    tmp_path: Path, value: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        NeotomaTaxonAncestryChainLimits,
        materialize_neotoma_taxon_ancestry_chain,
    )

    unavailable: Any = None
    with pytest.raises(ValueError, match="bounds"):
        materialize_neotoma_taxon_ancestry_chain(
            tmp_path / "final",
            sources=unavailable,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(),
            limits=NeotomaTaxonAncestryChainLimits(max_new_requests=value),
        )
    assert not (tmp_path / "final").exists()


def test_materialization_preserves_existing_destination_before_source_resolution(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        materialize_neotoma_taxon_ancestry_chain,
    )

    final = tmp_path / "final"
    final.mkdir()
    (final / "foreign.txt").write_text("existing unrelated owner")
    unavailable: Any = None
    with pytest.raises(FileExistsError):
        materialize_neotoma_taxon_ancestry_chain(
            final,
            sources=unavailable,
            parent_chain_sha256=None,
            new_capture_manifest_sha256s=(),
        )
    assert (final / "foreign.txt").read_text() == "existing unrelated owner"
