"""Retained previews cannot relabel source indices, missingness or admission."""

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.hyde.ascii import (
    prepare_hyde_ascii_window,
    read_hyde_ascii_window,
)
from bijux_pollenomics.collection.sources.hyde.local.contracts import encode, sha256
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .test_preparation import fixture


@pytest.mark.parametrize(
    "change",
    [
        "posture",
        "missing",
        "count_bool",
        "header",
        "parent",
        "name",
        "crc",
        "eof",
        "token",
        "window_size",
        "extra_file",
        "producer_digest",
    ],
)
def test_rehashed_internal_contradictions_refuse(tmp_path: Path, change: str) -> None:
    source, custody, selection = fixture(tmp_path)
    product = prepare_hyde_ascii_window(
        custody.directory,
        expected_custody_manifest_sha256=custody.manifest_sha256,
        source_root=source,
        selection=selection,
        destination=tmp_path / "result",
    )
    root = product.directory
    manifest = json.loads((root / "manifest.json").read_text())
    window = json.loads((root / "window.json").read_text())
    if change == "posture":
        manifest["public_release_allowed"] = True
    elif change == "missing":
        window["missing_mask"][0] = False
    elif change == "count_bool":
        manifest["counts"]["selected_missing"] = True
    elif change == "header":
        window["header"]["tokens"][4][1] = "0.1"
    elif change == "parent":
        manifest["custody_manifest_sha256"] = "0" * 64
    elif change == "name":
        manifest["archive_member"]["name"] = "other.asc"
    elif change == "crc":
        manifest["member_payload"]["crc32"] += 1
    elif change == "eof":
        manifest["member_payload"]["complete_eof_verified"] = False
    elif change == "token":
        window["source_tokens"][0] = "NaN"
    elif change == "window_size":
        manifest["selection"]["row_stop"] = 1
    elif change == "extra_file":
        (root / "extra").write_text("unowned")
    else:
        manifest["producer"]["files_sha256"] = "0" * 64
    raw = encode(window)
    (root / "window.json").write_bytes(raw)
    manifest["files"]["window.json"] = {"bytes": len(raw), "sha256": sha256(raw)}
    raw_manifest = encode(manifest)
    (root / "manifest.json").write_bytes(raw_manifest)
    with pytest.raises(IntakeRefusal):
        read_hyde_ascii_window(root, expected_manifest_sha256=sha256(raw_manifest))


def test_read_preserves_historical_producer_and_rejects_ancestor_symlink(
    tmp_path: Path,
) -> None:
    source, custody, selection = fixture(tmp_path)
    actual = tmp_path / "actual"
    actual.mkdir()
    product = prepare_hyde_ascii_window(
        custody.directory,
        expected_custody_manifest_sha256=custody.manifest_sha256,
        source_root=source,
        selection=selection,
        destination=actual / "result",
    )
    assert (
        read_hyde_ascii_window(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )
        == product
    )
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    with pytest.raises(IntakeRefusal, match="path_symlink"):
        read_hyde_ascii_window(
            alias / "result", expected_manifest_sha256=product.manifest_sha256
        )


def test_wrong_manifest_refuses_before_window_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typing import BinaryIO

    source, custody, selection = fixture(tmp_path)
    product = prepare_hyde_ascii_window(
        custody.directory,
        expected_custody_manifest_sha256=custody.manifest_sha256,
        source_root=source,
        selection=selection,
        destination=tmp_path / "result",
    )
    original = Path.open
    opened: list[str] = []

    def tracked(path: Path, mode: str = "r") -> BinaryIO:
        assert mode == "rb"
        opened.append(path.name)
        return original(path, "rb")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", tracked)
        with pytest.raises(IntakeRefusal, match="manifest_digest_mismatch"):
            read_hyde_ascii_window(product.directory, expected_manifest_sha256="0" * 64)
    assert opened == ["manifest.json"]


@pytest.mark.parametrize(
    "name",
    [
        "../cropland2000AD.asc",
        "/cropland2000AD.asc",
        "C:/cropland2000AD.asc",
        "inside/../cropland2000AD.asc",
        "inside\\cropland2000AD.asc",
        "inside\x00cropland2000AD.asc",
    ],
)
def test_coordinated_native_name_cannot_claim_false_safety(
    tmp_path: Path, name: str
) -> None:
    source, custody, selection = fixture(tmp_path)
    product = prepare_hyde_ascii_window(
        custody.directory,
        expected_custody_manifest_sha256=custody.manifest_sha256,
        source_root=source,
        selection=selection,
        destination=tmp_path / "result",
    )
    root = product.directory
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["selection"]["expected_member_name"] = name
    manifest["archive_member"]["name"] = name
    occurrence = json.loads(manifest["archive_member"]["occurrence_json"])
    occurrence["name"] = name
    occurrence["decoded_filename"] = name
    assert occurrence["safe_relative_name"] is True
    manifest["archive_member"]["occurrence_json"] = encode(occurrence).decode("ascii")
    content = encode(manifest)
    (root / "manifest.json").write_bytes(content)
    with pytest.raises(
        IntakeRefusal, match="hyde_custody_(archive_semantics_invalid|text_invalid)"
    ):
        read_hyde_ascii_window(root, expected_manifest_sha256=sha256(content))


@pytest.mark.parametrize(
    "field,value",
    [
        ("decoded_filename", "other.asc"),
        ("directory", True),
        ("external_attributes", 0o120777 << 16),
        ("extra_hex", "not-hex"),
        ("date_time", [2025]),
        ("create_system", True),
    ],
)
def test_preview_uses_shared_complete_occurrence_semantics(
    tmp_path: Path, field: str, value: object
) -> None:
    source, custody, selection = fixture(tmp_path)
    product = prepare_hyde_ascii_window(
        custody.directory,
        expected_custody_manifest_sha256=custody.manifest_sha256,
        source_root=source,
        selection=selection,
        destination=tmp_path / "result",
    )
    root = product.directory
    manifest = json.loads((root / "manifest.json").read_text())
    occurrence = json.loads(manifest["archive_member"]["occurrence_json"])
    occurrence[field] = value
    manifest["archive_member"]["occurrence_json"] = encode(occurrence).decode("ascii")
    content = encode(manifest)
    (root / "manifest.json").write_bytes(content)
    with pytest.raises(IntakeRefusal):
        read_hyde_ascii_window(root, expected_manifest_sha256=sha256(content))
