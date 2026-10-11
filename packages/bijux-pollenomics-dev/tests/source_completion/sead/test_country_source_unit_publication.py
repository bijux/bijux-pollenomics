"""Guard two-file SEAD source-unit publication against stale inputs and rivals."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion import sead_country_source_units as units


def _stage_paths(parent: Path) -> list[Path]:
    return sorted(parent.glob(".output.*"))


def test_complete_staged_bytes_precede_successful_publication(tmp_path: Path) -> None:
    output = tmp_path / "output"
    products = {"rows.csv": b"country\nSE\n", "report.json": b'{"rows": 1}\n'}

    def check() -> None:
        stages = _stage_paths(tmp_path)
        assert len(stages) == 1
        assert {
            part.name: part.read_bytes() for part in stages[0].iterdir()
        } == products
        assert not output.exists()

    units._publish_products(output, products, check)
    assert {part.name: part.read_bytes() for part in output.iterdir()} == products
    assert _stage_paths(tmp_path) == []


def test_postread_source_change_refuses_without_partial_publication(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    source = tmp_path / "source.json"
    source.write_bytes(b"original")
    observed = {source: hashlib.sha256(source.read_bytes()).hexdigest()}

    def check() -> None:
        source.write_bytes(b"changed")
        units._check_source_inputs(observed, tmp_path)

    with pytest.raises(ValueError, match="changed after read"):
        units._publish_products(
            output, {"rows.csv": b"a\n", "report.json": b"{}\n"}, check
        )
    assert not output.exists()
    assert _stage_paths(tmp_path) == []


def test_changed_normalized_materialization_refuses_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"

    def changed(*_args: object, **_kwargs: object) -> None:
        raise ValueError("normalized manifest changed")

    monkeypatch.setattr(units, "read_validated_sead_evidence_documents", changed)
    with pytest.raises(ValueError, match="normalized manifest changed"):
        units._publish_products(
            output,
            {"rows.csv": b"a\n", "report.json": b"{}\n"},
            lambda: units._check_source_inputs({}, tmp_path),
        )
    assert not output.exists()
    assert _stage_paths(tmp_path) == []


def test_competing_output_directory_is_preserved(tmp_path: Path) -> None:
    output = tmp_path / "output"
    products = {"rows.csv": b"a\n", "report.json": b"{}\n"}

    def rival() -> None:
        output.mkdir()
        (output / "competitor").write_bytes(b"retain")

    with pytest.raises(FileExistsError):
        units._publish_products(output, products, rival)
    assert (output / "competitor").read_bytes() == b"retain"
    assert sorted(path.name for path in output.iterdir()) == ["competitor"]
    assert _stage_paths(tmp_path) == []


def test_failed_stage_flush_leaves_no_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"

    def fail_flush(_descriptor: int) -> None:
        raise OSError("staged flush failed")

    monkeypatch.setattr(os, "fsync", fail_flush)
    with pytest.raises(OSError, match="staged flush failed"):
        units._publish_products(
            output, {"rows.csv": b"a\n", "report.json": b"{}\n"}, lambda: None
        )
    assert not output.exists()
    assert _stage_paths(tmp_path) == []


def test_partial_link_failure_removes_only_owned_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    products = {"rows.csv": b"a\n", "report.json": b"{}\n"}
    real_link = os.link

    def link(source: Path, target: Path, *, follow_symlinks: bool = True) -> None:
        if target.name == "report.json":
            target.write_bytes(b"competitor")
            raise FileExistsError(target)
        real_link(source, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "link", link)
    with pytest.raises(FileExistsError):
        units._publish_products(output, products, lambda: None)
    assert (output / "report.json").read_bytes() == b"competitor"
    assert sorted(path.name for path in output.iterdir()) == ["report.json"]
    assert _stage_paths(tmp_path) == []


def test_replaced_output_directory_is_never_cleaned_as_ours(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    moved = tmp_path / "moved-owner-output"
    products = {"rows.csv": b"a\n", "report.json": b"{}\n"}
    real_link = os.link

    def link(source: Path, target: Path, *, follow_symlinks: bool = True) -> None:
        if target.name == "report.json":
            output.rename(moved)
            output.mkdir()
            real_link(moved / "rows.csv", output / "rows.csv")
            raise FileExistsError(target)
        real_link(source, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "link", link)
    with pytest.raises(FileExistsError):
        units._publish_products(output, products, lambda: None)
    assert (output / "rows.csv").read_bytes() == b"a\n"
    assert (moved / "rows.csv").read_bytes() == b"a\n"
    assert _stage_paths(tmp_path) == []


def test_replaced_stage_directory_and_file_are_preserved(tmp_path: Path) -> None:
    output = tmp_path / "output"
    products = {"rows.csv": b"a\n", "report.json": b"{}\n"}
    moved = tmp_path / "moved-stage"

    def rival() -> None:
        stage = _stage_paths(tmp_path)[0]
        stage.rename(moved)
        stage.mkdir()
        (stage / "rows.csv").write_bytes(b"rival")
        raise ValueError("rival replaced stage")

    with pytest.raises(ValueError, match="rival replaced stage"):
        units._publish_products(output, products, rival)
    assert not output.exists()
    assert (moved / "rows.csv").read_bytes() == b"a\n"
    assert (_stage_paths(tmp_path)[0] / "rows.csv").read_bytes() == b"rival"


def test_replaced_staged_file_is_never_unlinked(tmp_path: Path) -> None:
    output = tmp_path / "output"
    moved = tmp_path / "moved-rows.csv"

    def rival() -> None:
        stage = _stage_paths(tmp_path)[0]
        (stage / "rows.csv").rename(moved)
        (stage / "rows.csv").write_bytes(b"rival")
        raise ValueError("rival replaced staged file")

    with pytest.raises(ValueError, match="rival replaced staged file"):
        units._publish_products(
            output, {"rows.csv": b"a\n", "report.json": b"{}\n"}, rival
        )
    assert not output.exists()
    assert moved.read_bytes() == b"a\n"
    assert (_stage_paths(tmp_path)[0] / "rows.csv").read_bytes() == b"rival"


def test_stage_replacement_returning_normally_refuses_publication(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    moved = tmp_path / "moved-stage"
    products = {"rows.csv": b"a\n", "report.json": b"{}\n"}

    def rival() -> None:
        stage = _stage_paths(tmp_path)[0]
        stage.rename(moved)
        stage.mkdir()
        for name in products:
            (stage / name).write_bytes(b"rival")

    with pytest.raises(ValueError, match="publication directory was replaced"):
        units._publish_products(output, products, rival)
    assert not output.exists()
    assert {name: (moved / name).read_bytes() for name in products} == products
    assert {
        name: (_stage_paths(tmp_path)[0] / name).read_bytes() for name in products
    } == dict.fromkeys(products, b"rival")


def test_output_replacement_between_links_refuses_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    moved = tmp_path / "moved-output"
    products = {"rows.csv": b"a\n", "report.json": b"{}\n"}
    real_link = os.link

    def rival(source: Path, target: Path, *, follow_symlinks: bool = True) -> None:
        real_link(source, target, follow_symlinks=follow_symlinks)
        if target.name == "rows.csv":
            output.rename(moved)
            output.mkdir()
            (output / "rows.csv").write_bytes(b"rival")

    monkeypatch.setattr(os, "link", rival)
    with pytest.raises(ValueError, match="publication directory was replaced"):
        units._publish_products(output, products, lambda: None)
    assert (moved / "rows.csv").read_bytes() == products["rows.csv"]
    assert (output / "rows.csv").read_bytes() == b"rival"
    assert not (output / "report.json").exists()


def test_output_ancestor_link_and_parent_traversal_refuse(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    artifact_root = repository / "artifacts"
    artifact_root.mkdir(parents=True)
    (artifact_root / "linked").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="non-real directory"):
        units._absent_artifact_output(repository, artifact_root / "linked" / "output")
    with pytest.raises(ValueError, match="not canonical"):
        units._absent_artifact_output(
            repository, artifact_root / "retained" / ".." / "output"
        )
