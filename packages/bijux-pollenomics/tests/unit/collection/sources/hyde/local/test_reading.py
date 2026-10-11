"""Retained hashes cannot waive posture, occurrence or byte-identity consistency."""

from dataclasses import replace
import json
from pathlib import Path
from typing import BinaryIO

import pytest

from bijux_pollenomics.collection.sources.hyde.local import (
    prepare_local_hyde_inventory,
    read_local_hyde_inventory,
    replay_local_hyde_inventory,
)
from bijux_pollenomics.collection.sources.hyde.local.contracts import encode, sha256
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .test_inventory import source_fixture


def rehash(root: Path, manifest: dict[str, object]) -> str:
    manifest["files"] = {
        name: {
            "bytes": (root / name).stat().st_size,
            "sha256": sha256((root / name).read_bytes()),
        }
        for name in ("files.json", "archives.json", "metadata.json")
    }
    (root / "manifest.json").write_bytes(encode(manifest))
    return sha256((root / "manifest.json").read_bytes())


@pytest.mark.parametrize(
    "mutation",
    [
        "posture",
        "count_bool",
        "count",
        "occurrence",
        "archive_parent",
        "omit_archive",
        "omit_metadata",
        "metadata_bytes",
        "extra_file",
        "link",
        "duplicate_key",
        "dataset_digest",
    ],
)
def test_rehashed_retained_contradictions_refuse(tmp_path: Path, mutation: str) -> None:
    source = source_fixture(tmp_path / "raw")
    product = prepare_local_hyde_inventory(source, tmp_path / "custody")
    root = product.directory
    manifest = json.loads((root / "manifest.json").read_text())
    if mutation == "posture":
        manifest["public_release_allowed"] = True
    elif mutation == "count_bool":
        manifest["counts"]["file_count"] = False
    elif mutation == "count":
        manifest["counts"]["file_count"] += 1
    elif mutation == "dataset_digest":
        manifest["dataset_inventory_sha256"] = "0" * 64
    elif mutation in {"occurrence", "archive_parent", "omit_archive"}:
        rows = json.loads((root / "archives.json").read_text())
        if mutation == "occurrence":
            rows[2]["name_occurrence"] = 0
        elif mutation == "archive_parent":
            rows[0]["archive_sha256"] = "0" * 64
        else:
            rows = []
        (root / "archives.json").write_bytes(encode(rows))
    elif mutation in {"omit_metadata", "metadata_bytes"}:
        rows = json.loads((root / "metadata.json").read_text())
        if mutation == "omit_metadata":
            rows.pop()
        else:
            rows[0]["bytes_base64"] = ""
        (root / "metadata.json").write_bytes(encode(rows))
    elif mutation == "extra_file":
        (root / "unexpected").write_text("not owned")
    elif mutation == "duplicate_key":
        (root / "metadata.json").write_bytes(b'{"a":1,"a":2}\n')
    else:
        (root / "metadata.json").unlink()
        (root / "metadata.json").symlink_to(source / "License.txt")
    expected = rehash(root, manifest)
    with pytest.raises(IntakeRefusal):
        read_local_hyde_inventory(root, expected_manifest_sha256=expected)


def test_wrong_parent_is_refused_before_member_payload_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = source_fixture(tmp_path / "raw")
    product = prepare_local_hyde_inventory(source, tmp_path / "custody")
    original = Path.open
    opened = []

    def tracked(path: Path, mode: str = "r") -> BinaryIO:
        assert mode == "rb"
        opened.append(path.name)
        return original(path, "rb")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", tracked)
        with pytest.raises(IntakeRefusal, match="manifest_digest_mismatch"):
            read_local_hyde_inventory(
                product.directory, expected_manifest_sha256="0" * 64
            )
    assert opened == ["manifest.json"]


def test_external_replay_rejects_bytes_file_set_and_forged_result(
    tmp_path: Path,
) -> None:
    source = source_fixture(tmp_path / "raw")
    product = prepare_local_hyde_inventory(source, tmp_path / "custody")
    with pytest.raises(IntakeRefusal, match="product_identity_mismatch"):
        replay_local_hyde_inventory(replace(product, file_count=999), source)
    (source / "native.nc").write_bytes(b"changed native bytes")
    with pytest.raises(IntakeRefusal, match="source_replay_mismatch"):
        replay_local_hyde_inventory(product, source)


def test_retained_historical_producer_is_readable_but_exact_replay_requires_it(
    tmp_path: Path,
) -> None:
    source = source_fixture(tmp_path / "raw")
    product = prepare_local_hyde_inventory(source, tmp_path / "custody")
    manifest = json.loads((product.directory / "manifest.json").read_text())
    manifest["producer"]["files"]["collection/sources/hyde/local/inventory.py"] = (
        "0" * 64
    )
    manifest["producer"]["files_sha256"] = sha256(encode(manifest["producer"]["files"]))
    expected = rehash(product.directory, manifest)
    historical = read_local_hyde_inventory(
        product.directory, expected_manifest_sha256=expected
    )
    with pytest.raises(IntakeRefusal, match="producer_mismatch"):
        replay_local_hyde_inventory(historical, tmp_path / "source-must-not-be-opened")


def test_retained_ancestor_swap_during_read_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.hyde.local import reading

    source = source_fixture(tmp_path / "raw")
    real = tmp_path / "real"
    real.mkdir()
    product = prepare_local_hyde_inventory(source, real / "custody")
    original = reading._owned_bytes
    calls = 0

    def swapped(root: Path) -> dict[str, bytes]:
        nonlocal calls
        result = original(root)
        calls += 1
        if calls == 1:
            moved = tmp_path / "moved"
            real.rename(moved)
            real.symlink_to(moved, target_is_directory=True)
        return result

    monkeypatch.setattr(reading, "_owned_bytes", swapped)
    with pytest.raises(IntakeRefusal, match="path_symlink"):
        read_local_hyde_inventory(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )


def test_typed_selector_preserves_duplicate_ordinals_and_historical_custody(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.hyde.local import (
        select_local_hyde_archive_member,
    )

    source = source_fixture(tmp_path / "raw")
    product = prepare_local_hyde_inventory(source, tmp_path / "custody")
    first = select_local_hyde_archive_member(
        product, archive_path="native.zip", member_index=1
    )
    second = select_local_hyde_archive_member(
        product, archive_path="native.zip", member_index=2
    )
    assert first.name == second.name and first.member_index != second.member_index
    assert first.occurrence()["crc32"] != second.occurrence()["crc32"]
    with pytest.raises(IntakeRefusal):
        select_local_hyde_archive_member(
            product, archive_path="native.zip", member_index=100
        )
    with pytest.raises(IntakeRefusal):
        select_local_hyde_archive_member(
            replace(product, archive_member_count=0),
            archive_path="native.zip",
            member_index=1,
        )
