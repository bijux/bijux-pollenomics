from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.materialization.requests import (
    project_synthetic_neotoma_request,
    publication,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from .fixture import projection_fixture


def test_competing_output_tree_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = projection_fixture(tmp_path)
    original = publish_new_output_tree

    def compete(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        (final_output_root / "foreign").write_text("preserve")
        original(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(publication, "publish_new_output_tree", compete)
    with pytest.raises(FileExistsError):
        project_synthetic_neotoma_request(**inputs)
    assert (inputs["output_directory"] / "foreign").read_text() == "preserve"
    assert not (inputs["output_directory"] / "request.json").exists()


def test_changed_source_before_publication_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = projection_fixture(tmp_path)
    original = publication._write

    def change(path: Path, content: bytes) -> None:
        original(path, content)
        if path.name == "lineage.json":
            part = inputs["raw_root"] / "part-001.json"
            part.write_bytes(part.read_bytes() + b"\n")

    monkeypatch.setattr(publication, "_write", change)
    with pytest.raises(ValueError, match="Source authority changed"):
        project_synthetic_neotoma_request(**inputs)
    assert not inputs["output_directory"].exists()


def test_changed_auxiliary_evidence_before_publication_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = projection_fixture(tmp_path)
    original = publication._write

    def change(path: Path, content: bytes) -> None:
        original(path, content)
        if path.name == "lineage.json":
            part = inputs["input_root"] / "parameters.txt"
            part.write_bytes(part.read_bytes() + b"\n")

    monkeypatch.setattr(publication, "_write", change)
    with pytest.raises(LRARefusal) as error:
        project_synthetic_neotoma_request(**inputs)
    assert error.value.reason_code == "projection_evidence_changed"
    assert not inputs["output_directory"].exists()


def test_real_source_template_is_not_an_approval_switch(tmp_path: Path) -> None:
    inputs = projection_fixture(tmp_path)
    inputs["request_template"]["data_kind"] = "source_observations"
    with pytest.raises(LRARefusal) as error:
        project_synthetic_neotoma_request(**inputs)
    assert error.value.reason_code == "source_projection_requires_governed_admission"


def test_symlinked_evidence_refuses_even_with_matching_digest(tmp_path: Path) -> None:
    inputs = projection_fixture(tmp_path)
    evidence = inputs["request_template"]["evidence"][0]
    original = inputs["input_root"] / evidence["path"]
    outside = tmp_path / "foreign-evidence"
    original.rename(outside)
    original.symlink_to(outside)
    assert hashlib.sha256(outside.read_bytes()).hexdigest() == evidence["sha256"]
    with pytest.raises(LRARefusal) as error:
        project_synthetic_neotoma_request(**inputs)
    assert error.value.reason_code == "invalid_projection_evidence_path"
