"""Actual source-owned publication refuses overlap, mutation and existing output."""

from pathlib import Path
import sqlite3
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.raa.geometry import (
    audit_raa_geometry,
    service,
)
from bijux_pollenomics.collection.sources.raa.geometry.rows import (
    iter_geometry_documents,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from .support import add_geometry, database, gpkg, identity, point


def test_repeat_and_manifest_immutability(tmp_path: Path) -> None:
    source = database(tmp_path)
    add_geometry(source, "point", gpkg(point()))
    pin, size = identity(source)
    a = audit_raa_geometry(
        source,
        expected_sha256=pin,
        expected_byte_count=size,
        destination=tmp_path / "first",
    )
    b = audit_raa_geometry(
        source,
        expected_sha256=pin,
        expected_byte_count=size,
        destination=tmp_path / "second",
    )
    assert a.manifest_sha256 == b.manifest_sha256
    a.manifest()["boundary"] = "changed caller projection"
    assert a.manifest()["boundary"] != "changed caller projection"
    assert identity(source) == (pin, size)


def test_source_overlap_and_symlink_refuse_before_writes(tmp_path: Path) -> None:
    source = database(tmp_path)
    pin, size = identity(source)
    for output in (
        source.parent / "audit",
        source.parent / "bridge/../audit",
        tmp_path,
    ):
        with pytest.raises(ValueError, match="overlap"):
            audit_raa_geometry(
                source,
                expected_sha256=pin,
                expected_byte_count=size,
                destination=output,
            )
    alias = tmp_path / "alias"
    alias.symlink_to(source)
    with pytest.raises(ValueError, match="symlink"):
        audit_raa_geometry(
            alias,
            expected_sha256=pin,
            expected_byte_count=size,
            destination=tmp_path / "audit",
        )
    assert set(source.parent.iterdir()) == {source}


def test_invalid_input_does_not_stage(tmp_path: Path) -> None:
    source = database(tmp_path)
    pin, size = identity(source)
    with pytest.raises(ValueError, match="SHA256"):
        audit_raa_geometry(
            source,
            expected_sha256="0" * 64,
            expected_byte_count=size,
            destination=tmp_path / "outputs/audit",
        )
    assert not (tmp_path / "outputs").exists()
    with sqlite3.connect(source) as con:
        con.execute("PRAGMA user_version=0")
    pin, size = identity(source)
    with pytest.raises(ValueError, match="application/version"):
        audit_raa_geometry(
            source,
            expected_sha256=pin,
            expected_byte_count=size,
            destination=tmp_path / "outputs/audit",
        )
    assert not (tmp_path / "outputs").exists()


def test_no_replace_race_preserves_other_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = database(tmp_path)
    pin, size = identity(source)
    output = tmp_path / "audit"

    def competitor(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        (final_output_root / "other").write_text("preserve")
        publish_new_output_tree(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(service, "publish_new_output_tree", competitor)
    with pytest.raises(FileExistsError):
        audit_raa_geometry(
            source, expected_sha256=pin, expected_byte_count=size, destination=output
        )
    assert (output / "other").read_text() == "preserve"


def test_source_mutation_during_stream_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = database(tmp_path)
    add_geometry(source, "point", gpkg(point()))
    pin, size = identity(source)
    original = iter_geometry_documents

    def mutate(con: Any) -> Any:
        yield from original(con)
        with source.open("ab") as stream:
            stream.write(b"changed")

    monkeypatch.setattr(service, "iter_geometry_documents", mutate)
    with pytest.raises(ValueError, match="byte count mismatch"):
        audit_raa_geometry(
            source,
            expected_sha256=pin,
            expected_byte_count=size,
            destination=tmp_path / "audit",
        )
    assert not (tmp_path / "audit").exists()
