"""Published ancestry layers retain source closure and bounded edge references."""

from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.models import (
    SCHEMA,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
    encoded_json,
)


def test_exclusive_roundtrip_preserves_source_pointers(
    ancestry_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
        load_neotoma_taxon_ancestry,
        publish_neotoma_taxon_ancestry,
    )

    sources = ancestry_products["sources"]
    document = derive_neotoma_taxon_ancestry(sources)
    root = tmp_path / "ancestry"
    publish_neotoma_taxon_ancestry(root, document=document, sources=sources)
    digest = sha256((root / "manifest.json").read_bytes()).hexdigest()
    assert (
        load_neotoma_taxon_ancestry(
            root, expected_manifest_sha256=digest, sources=sources
        )
        == document
    )


def test_selected_metadata_returns_native_edge_locators_without_body_open(
    ancestry_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
        publish_neotoma_taxon_ancestry,
        read_neotoma_taxon_ancestry_target,
    )

    sources = ancestry_products["sources"]
    document = derive_neotoma_taxon_ancestry(sources)
    root = tmp_path / "ancestry"
    publish_neotoma_taxon_ancestry(root, document=document, sources=sources)
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    selected = read_neotoma_taxon_ancestry_target(
        root,
        expected_manifest_sha256=sha256(
            (root / "manifest.json").read_bytes()
        ).hexdigest(),
        kind="taxon",
        native_id=15,
    )
    assert selected["recorded_node"]["current_root_dataset_ids"] == [201, 203]
    assert len(selected["recorded_edges"]) == 1
    assert selected["recorded_edges"][0]["json_pointer"] == "/data/0/highertaxonid"
    assert selected["recorded_edges"][0]["source"]["body_sha256"]
    assert selected["native_source_fields_revalidated"] is False
    assert selected["current_roles_revalidated"] is False
    assert opened == []


@pytest.mark.parametrize("boundary", ["stage", "rename", "readback"])
def test_equal_byte_publication_substitution_refuses_and_retains(
    ancestry_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, boundary: str
) -> None:
    import shutil

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
        publication,
    )
    from bijux_pollenomics.collection.sources.neotoma.publication import ownership

    sources = ancestry_products["sources"]
    document = derive_neotoma_taxon_ancestry(sources)
    final = tmp_path / "ancestry"
    saved = tmp_path / "detached-owner"
    swapped = []
    published = []
    load = publication.load_neotoma_taxon_ancestry
    publish = vars(ownership)["publish_new_output_tree"]

    def swap(root: Path) -> None:
        root.rename(saved)
        shutil.copytree(saved, root)
        swapped.append(root)

    def observed_load(root: Path, **kwargs: Any) -> Any:
        result = load(root, **kwargs)
        if not swapped and (
            boundary == "stage"
            and root != final
            or boundary == "readback"
            and root == final
        ):
            swap(root)
        return result

    def observed_publish(**kwargs: Any) -> None:
        publish(**kwargs)
        published.append(True)
        if boundary == "rename":
            swap(final)

    monkeypatch.setattr(publication, "load_neotoma_taxon_ancestry", observed_load)
    monkeypatch.setattr(ownership, "publish_new_output_tree", observed_publish)
    with pytest.raises(ValueError, match="identity|inode"):
        publication.publish_neotoma_taxon_ancestry(
            final, document=document, sources=sources
        )
    assert len(swapped) == 1 and len(published) == (0 if boundary == "stage" else 1)
    assert (saved / "manifest.json").read_bytes() == (
        swapped[0] / "manifest.json"
    ).read_bytes()


def test_existing_output_preserved_before_source_resolution(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        publish_neotoma_taxon_ancestry,
    )

    final = tmp_path / "foreign"
    final.mkdir()
    (final / "preserve").write_bytes(b"owned by another producer")
    invalid: Any = None
    with pytest.raises(FileExistsError):
        publish_neotoma_taxon_ancestry(final, document={}, sources=invalid)
    assert list(final.iterdir()) == [final / "preserve"]


@pytest.mark.parametrize("alias", ["directory", "leaf"])
def test_selected_metadata_alias_refuses_before_foreign_part_open(
    ancestry_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, alias: str
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
        publish_neotoma_taxon_ancestry,
        read_neotoma_taxon_ancestry_target,
    )

    sources = ancestry_products["sources"]
    document = derive_neotoma_taxon_ancestry(sources)
    root = tmp_path / "ancestry"
    publish_neotoma_taxon_ancestry(root, document=document, sources=sources)
    manifest_raw = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    part = next(row for row in manifest["parts"] if row["collection"] == "taxa")
    original_path = root / part["path"]
    owned = original_path.parent if alias == "directory" else original_path
    foreign = tmp_path / "foreign-part"
    owned.rename(foreign)
    owned.symlink_to(foreign, target_is_directory=alias == "directory")
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path in (original_path, foreign) or foreign in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError, match="alias|symlink"):
        read_neotoma_taxon_ancestry_target(
            root,
            expected_manifest_sha256=sha256(manifest_raw).hexdigest(),
            kind="taxon",
            native_id=15,
        )
    assert opened == [] and foreign.exists() and owned.is_symlink()


@pytest.mark.parametrize("references", [[{}], [[]], [None], [1, "a"]])
def test_selected_malformed_edge_kinds_have_controlled_refusal(
    tmp_path: Path, references: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        publication,
    )

    document = {
        **dict.fromkeys(publication.COLLECTIONS, []),
        "schema_version": SCHEMA,
        "authority": {"context_manifest_sha256": "0" * 64},
        "taxa": [
            {
                "native_id": 11,
                "target_kind": "taxon",
                "target_key": "taxon-11",
                "edge_ids": references,
            }
        ],
    }
    manifest, buffers = publication._pack(document)
    for name, raw in buffers.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    raw = encoded_json(manifest)
    (tmp_path / "manifest.json").write_bytes(raw)
    with pytest.raises(ValueError, match="edge references"):
        publication.read_neotoma_taxon_ancestry_target(
            tmp_path,
            expected_manifest_sha256=sha256(raw).hexdigest(),
            kind="taxon",
            native_id=11,
        )


def test_chunking_work_is_linear_and_preserves_every_native_record(
    monkeypatch: Any,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        publication,
    )

    rows = [
        {
            "native_id": identity,
            "text": "Å字\n" * 80,
            "source": {"native": None, "integers": [10**100, identity]},
        }
        for identity in range(1, 257)
    ]
    document = {**dict.fromkeys(publication.COLLECTIONS, []), "seeds": rows}
    original = encoded_json
    encoded_rows = 0

    def count(value: Any) -> bytes:
        nonlocal encoded_rows
        if isinstance(value, dict) and isinstance(value.get("rows"), list):
            encoded_rows += len(value["rows"])
        return original(value)

    monkeypatch.setattr(publication, "PART_BYTES", 8192)
    monkeypatch.setattr(publication, "HARD_PART_BYTES", 10000)
    monkeypatch.setattr(publication, "encoded_json", count)
    manifest, buffers = publication._pack(document)
    decoded = [
        row
        for part in manifest["parts"]
        for row in json.loads(buffers[part["path"]])["rows"]
    ]
    assert len(buffers) > 1 and decoded == rows
    assert all(len(raw) <= 8192 for raw in buffers.values())
    assert encoded_rows <= 2 * len(rows)


def test_single_oversized_native_record_refuses_without_splitting(
    monkeypatch: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        publication,
    )

    monkeypatch.setattr(publication, "PART_BYTES", 2048)
    monkeypatch.setattr(publication, "HARD_PART_BYTES", 4096)
    document = {
        **dict.fromkeys(publication.COLLECTIONS, []),
        "seeds": [{"literal_source_text": "Å" * 4096}],
    }
    with pytest.raises(ValueError, match="part.*bound"):
        publication._pack(document)
