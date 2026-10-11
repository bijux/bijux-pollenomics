"""Real staged preparation preserves source ownership through failure and publication races."""

import base64
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.hyde.local import (
    LocalInventoryLimits,
    preparation,
    prepare_local_hyde_inventory,
    read_local_hyde_inventory,
    reading,
    replay_local_hyde_inventory,
)
from bijux_pollenomics.collection.sources.hyde.local.contracts import LocalHydeInventory
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from .test_inventory import source_fixture


def test_prepare_read_replay_preserve_exact_metadata_without_native_copies(
    tmp_path: Path,
) -> None:
    source = source_fixture(tmp_path / "raw")
    product = prepare_local_hyde_inventory(source, tmp_path / "custody")
    assert product.file_count == 6 and product.dataset_file_count == 5
    assert product.archive_member_count == 4
    assert {p.name for p in product.directory.iterdir()} == {
        "manifest.json",
        "files.json",
        "archives.json",
        "metadata.json",
    }
    metadata = json.loads((product.directory / "metadata.json").read_text())
    for row in metadata:
        assert (
            base64.b64decode(row["bytes_base64"]) == (source / row["path"]).read_bytes()
        )
    manifest = json.loads((product.directory / "manifest.json").read_text())
    assert (
        manifest["public_release_allowed"] is False
        and manifest["native_release_status"] == "unverified"
    )
    assert manifest["native_metadata_interpretation"] == "not_performed"
    assert (
        read_local_hyde_inventory(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )
        == product
    )
    replay_local_hyde_inventory(product, source)


def test_ancillary_changes_alter_custody_but_not_dataset_identity(
    tmp_path: Path,
) -> None:
    source = source_fixture(tmp_path / "raw")
    first = prepare_local_hyde_inventory(source, tmp_path / "first")
    (source / ".DS_Store").write_bytes(b"different ancillary data")
    second = prepare_local_hyde_inventory(source, tmp_path / "second")
    assert first.manifest_sha256 != second.manifest_sha256
    assert first.dataset_inventory_sha256 == second.dataset_inventory_sha256
    assert first.dataset_byte_count == second.dataset_byte_count
    with pytest.raises(IntakeRefusal, match="hyde_source_replay_mismatch"):
        replay_local_hyde_inventory(first, source)


@pytest.mark.parametrize("mutation", ["raw", "ancillary", "addition", "removal"])
def test_changes_after_retained_validation_refuse_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    source = source_fixture(tmp_path / "raw")
    original = reading.read_local_hyde_inventory

    def changed(
        directory: Path, *, expected_manifest_sha256: str
    ) -> LocalHydeInventory:
        result = original(directory, expected_manifest_sha256=expected_manifest_sha256)
        if mutation == "raw":
            (source / "native.nc").write_bytes(b"changed")
        elif mutation == "ancillary":
            (source / ".DS_Store").write_bytes(b"changed")
        elif mutation == "addition":
            (source / "new.bin").write_bytes(b"new")
        else:
            (source / "zero.bin").unlink()
        return result

    monkeypatch.setattr(reading, "read_local_hyde_inventory", changed)
    with pytest.raises(IntakeRefusal, match="hyde_source_changed"):
        prepare_local_hyde_inventory(source, tmp_path / "custody")
    assert not (tmp_path / "custody").exists()
    assert len(list(tmp_path.glob(".custody.pending-*"))) == 1


def test_destination_race_never_overwrites_competing_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = source_fixture(tmp_path / "raw")
    original = publish_new_output_tree

    def raced(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        (final_output_root / "owner").write_text("other-owner")
        original(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(preparation, "publish_new_output_tree", raced)
    with pytest.raises(IntakeRefusal):
        prepare_local_hyde_inventory(source, tmp_path / "custody")
    assert (tmp_path / "custody" / "owner").read_text() == "other-owner"
    assert len(list(tmp_path.glob(".custody.pending-*"))) == 1


def test_metadata_capture_limits_keep_null_reference_without_truncation(
    tmp_path: Path,
) -> None:
    source = source_fixture(tmp_path / "raw")
    product = prepare_local_hyde_inventory(
        source,
        tmp_path / "custody",
        limits=LocalInventoryLimits(maximum_metadata_file_bytes=1),
    )
    metadata = json.loads((product.directory / "metadata.json").read_text())
    assert all(
        row["bytes_base64"] is None
        and row["capture_status"] == "hash_reference_size_limit"
        for row in metadata
    )
    replay_local_hyde_inventory(product, source)


@pytest.mark.parametrize("kind", ["nested", "existing", "source_link"])
def test_bad_destination_or_source_refuses_without_native_copy(
    tmp_path: Path, kind: str
) -> None:
    source = source_fixture(tmp_path / "raw")
    destination = tmp_path / "custody"
    if kind == "nested":
        destination = source / "custody"
    elif kind == "existing":
        destination.mkdir()
    else:
        alias = tmp_path / "alias"
        alias.symlink_to(source, target_is_directory=True)
        source = alias
    with pytest.raises(IntakeRefusal):
        prepare_local_hyde_inventory(source, destination)


def test_custody_never_opens_or_extracts_archive_payloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import zipfile

    source = source_fixture(tmp_path / "raw")

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Archive payload access is outside byte-custody scope")

    monkeypatch.setattr(zipfile.ZipFile, "open", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "extract", forbidden)
    monkeypatch.setattr(zipfile.ZipFile, "extractall", forbidden)
    product = prepare_local_hyde_inventory(source, tmp_path / "custody")
    replay_local_hyde_inventory(product, source)


@pytest.mark.parametrize("entry", ["source", "destination", "retained", "replay"])
def test_symlink_ancestors_are_refused_consistently(tmp_path: Path, entry: str) -> None:
    real = tmp_path / "real"
    real.mkdir()
    source = source_fixture(real / "raw")
    product = prepare_local_hyde_inventory(source, real / "custody")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(IntakeRefusal, match="path_symlink"):
        if entry == "source":
            prepare_local_hyde_inventory(alias / "raw", tmp_path / "new")
        elif entry == "destination":
            prepare_local_hyde_inventory(source, alias / "new")
        elif entry == "retained":
            read_local_hyde_inventory(
                alias / "custody", expected_manifest_sha256=product.manifest_sha256
            )
        else:
            replay_local_hyde_inventory(product, alias / "raw")


def test_actual_producer_file_drift_refuses_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.hyde.local import contracts

    source = source_fixture(tmp_path / "raw")
    package = Path(contracts.__file__).parent.parents[3]
    mirror = tmp_path / "producer" / "bijux_pollenomics"
    for name in contracts.implementation_identity():
        target = mirror / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((package / name).read_bytes())
    monkeypatch.setattr(
        contracts,
        "__file__",
        str(mirror / "collection/sources/hyde/local/contracts.py"),
    )
    original = reading.read_local_hyde_inventory

    def changed(
        directory: Path, *, expected_manifest_sha256: str
    ) -> LocalHydeInventory:
        result = original(directory, expected_manifest_sha256=expected_manifest_sha256)
        implementation = mirror / "collection/sources/hyde/local/inventory.py"
        implementation.write_bytes(
            implementation.read_bytes() + b"\n# actual source-byte mutation\n"
        )
        return result

    monkeypatch.setattr(reading, "read_local_hyde_inventory", changed)
    with pytest.raises(IntakeRefusal, match="producer_changed"):
        prepare_local_hyde_inventory(source, tmp_path / "custody")
    assert not (tmp_path / "custody").exists()
