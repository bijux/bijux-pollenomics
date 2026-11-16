"""A collection publishes source, normalized and review surfaces as one new tree."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import collection
from bijux_pollenomics.collection.sources.neotoma.review import (
    write_neotoma_review_outputs,
)
from bijux_pollenomics.collection.workflow.context_collection import (
    collect_context_source,
)
from bijux_pollenomics.collection.workflow.planning.source_registry import (
    CONTEXT_SOURCE_SPECS,
)
from bijux_pollenomics.core.files import write_json

from .native_products import collect


def test_collection_refuses_existing_outputs_before_source_access(
    tmp_path: Path, source: list[str]
) -> None:
    output = tmp_path / "neotoma"
    prior = output / "raw/neotoma_pollen_dataset_inventory.json"
    prior.parent.mkdir(parents=True)
    prior.write_bytes(b"original source inventory")
    derived = output / "relational/user-reviewed.json"
    derived.parent.mkdir()
    derived.write_bytes(b"independently reviewed derived source")
    with pytest.raises(FileExistsError):
        collect(output)
    assert source == []
    assert prior.read_bytes() == b"original source inventory"
    assert derived.read_bytes() == b"independently reviewed derived source"


def test_failed_later_surface_does_not_publish_partial_collection(
    tmp_path: Path, source: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = write_json

    def fail(path: Path, payload: object, **kwargs: Any) -> None:
        if path.name == "neotoma_pollen_sites.json":
            raise OSError("site surface cannot be written")
        writer(path, payload, **kwargs)

    monkeypatch.setattr(collection, "write_json", fail)
    output = tmp_path / "neotoma"
    with pytest.raises(OSError, match="site surface"):
        collect(output)
    assert not output.exists()
    assert (
        tmp_path / ".neotoma.staging/raw/neotoma_pollen_dataset_inventory.json"
    ).is_file()


def test_success_returns_published_paths_for_complete_collection(
    tmp_path: Path, source: list[str]
) -> None:
    output = tmp_path / "nested/neotoma"
    report = collect(output)
    assert report.output_dir == output
    assert report.raw_path == output / "raw/neotoma_pollen_sites.json"
    for path in (
        report.raw_path,
        report.normalized_csv_path,
        report.normalized_geojson_path,
    ):
        assert path.is_file() and output in path.parents
    assert (output / "raw/neotoma_pollen_dataset_downloads/manifest.json").is_file()
    assert not (output.parent / ".neotoma.staging").exists()


def test_collection_preserves_preexisting_staging_and_declines_source_access(
    tmp_path: Path, source: list[str]
) -> None:
    staging = tmp_path / ".neotoma.staging"
    staging.mkdir()
    marker = staging / "source-recovery.json"
    marker.write_bytes(b"original failed attempt")
    with pytest.raises(FileExistsError):
        collect(tmp_path / "neotoma")
    assert source == [] and marker.read_bytes() == b"original failed attempt"


def test_collection_refuses_symlink_ancestry_before_source_access(
    tmp_path: Path, source: list[str]
) -> None:
    real = tmp_path / "physical"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        collect(alias / "neotoma")
    assert source == [] and list(real.iterdir()) == []


def test_collection_refuses_noncanonical_existing_output_before_source_access(
    tmp_path: Path, source: list[str]
) -> None:
    existing = tmp_path / "neotoma"
    existing.mkdir()
    (existing / "reviewed.json").write_bytes(b"reviewed source")
    missing = tmp_path / "missing"
    with pytest.raises(ValueError, match="physical"):
        collect(missing / ".." / "neotoma")
    assert source == [] and not missing.exists()
    assert (existing / "reviewed.json").read_bytes() == b"reviewed source"


def test_concurrent_destination_is_preserved_at_publication(
    tmp_path: Path, source: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "neotoma"
    review = write_neotoma_review_outputs

    def competitor(*args: Any, **kwargs: Any) -> None:
        review(*args, **kwargs)
        output.mkdir()
        (output / "user-notes.txt").write_text("independent concurrent work")

    monkeypatch.setattr(collection, "write_neotoma_review_outputs", competitor)
    with pytest.raises(FileExistsError):
        collect(output)
    assert (output / "user-notes.txt").read_text() == "independent concurrent work"
    assert sorted(path.name for path in output.iterdir()) == ["user-notes.txt"]


def test_context_orchestration_uses_source_owned_publication(
    tmp_path: Path, source: list[str]
) -> None:
    counts = collect_context_source(
        collect_function=collection.collect_neotoma_data,
        spec=CONTEXT_SOURCE_SPECS["neotoma"],
        output_root=tmp_path,
        country_boundaries={},
    )
    assert counts == {"neotoma_point_count": 0}
    manifest = tmp_path / "neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json"
    original = manifest.read_bytes()
    with pytest.raises(FileExistsError):
        collect_context_source(
            collect_function=collection.collect_neotoma_data,
            spec=CONTEXT_SOURCE_SPECS["neotoma"],
            output_root=tmp_path,
            country_boundaries={},
        )
    assert source == ["inventory"] and manifest.read_bytes() == original
