"""Literal source publication retains its own original roster and independent anchors."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil
from typing import Any

from .native_products import pin


def test_unit_archive_is_portable_with_original_roster_outside_shared_legacy_context(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        load_neotoma_unit_metadata_archive,
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products()
    output = tmp_path / "archive"
    manifest = write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    original = inputs["original"].read_bytes()
    assert (output / f"rosters/{pin(inputs['original'])}.json").read_bytes() == original
    assert (
        manifest["native_body_copies"] == 0
        and manifest["scientific_admission"] == "not_asserted"
    )
    assert sum(name.endswith(".body") for name in manifest["files"]) == 2
    assert not (output / "native").exists()
    shutil.rmtree(inputs["source"])
    inputs["original"].unlink()
    loaded = load_neotoma_unit_metadata_archive(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        **inputs["reader"],
    )
    assert loaded == manifest


def test_existing_destination_and_redirected_stage_are_preserved(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path, monkeypatch: Any
) -> None:
    import pytest

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        publication,
    )

    from .native_products import observe_units

    inputs = unit_products()
    existing = tmp_path / "existing"
    existing.mkdir()
    marker = existing / "foreign.json"
    marker.write_bytes(b'{"foreign":true}')
    opened = observe_units(monkeypatch, set())
    with pytest.raises(FileExistsError):
        publication.write_neotoma_unit_metadata_archive(existing, **inputs["writer"])
    assert marker.read_bytes() == b'{"foreign":true}'
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    owner = OwnedTreeWriter
    foreign_stages = []

    def replace_stage(path: Path, **kwargs: Any) -> Any:
        path.mkdir()
        foreign_stages.append(path)
        (path / "foreign.json").write_bytes(b"foreign stage")
        return owner(path, **kwargs)

    monkeypatch.setattr(publication, "OwnedTreeWriter", replace_stage)
    with pytest.raises(FileExistsError):
        publication.write_neotoma_unit_metadata_archive(
            tmp_path / "output", **inputs["writer"]
        )
    assert opened == []
    assert (foreign_stages[0] / "foreign.json").read_bytes() == b"foreign stage"
    assert not (tmp_path / "output").exists()


def test_combined_external_input_budget_is_checked_before_unit_or_roster_buffer(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path, monkeypatch: Any
) -> None:
    import pytest

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        publication,
    )

    from .native_products import observe_units

    inputs = unit_products()
    physical = (
        sum(path.stat().st_size for path in inputs["source"].iterdir())
        + inputs["original"].stat().st_size
    )
    monkeypatch.setattr(publication, "MAX_BYTES", physical - 1)
    original_open = Path.open

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path != inputs["original"], "Over-budget external original roster opened"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError, match="budget"):
        publication.write_neotoma_unit_metadata_archive(
            tmp_path / "archive", **inputs["writer"]
        )
    assert opened == []
