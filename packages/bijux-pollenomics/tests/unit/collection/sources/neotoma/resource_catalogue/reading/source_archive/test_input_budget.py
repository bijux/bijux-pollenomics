"""Archive input ownership and whole publication caps precede native buffers."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import archive
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    publication,
)


def forbid_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    native = Path.open

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            pytest.fail("native body buffer opened before archive input preflight")
        return native(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)


@pytest.mark.parametrize(
    "mutation", ["sparse_oversize", "extra", "protected_extra", "length", "hardlink"]
)
def test_invalid_consumed_capture_refuses_before_any_source_body(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    inputs = catalogue_sources()
    catalogue, pin, sources = publish_catalogue(inputs)
    capture = next(iter(inputs["resource_captures"].values()))
    body = capture / "dataset-201-current-attempt-1.body"
    if mutation == "sparse_oversize":
        for index in range(32):
            with (capture / f"undeclared-{index}.body").open("wb") as stream:
                stream.truncate(16 * 1024 * 1024)
    elif mutation in {"extra", "protected_extra"}:
        name = (
            "dataset-203-current-attempt-1.body"
            if mutation == "protected_extra"
            else "undeclared.body"
        )
        (capture / name).write_bytes(b"unowned")
    elif mutation == "length":
        body.write_bytes(body.read_bytes() + b" ")
    else:
        os.link(body, tmp_path / "foreign-alias")
    forbid_bodies(monkeypatch)
    output = tmp_path / "archive"
    with pytest.raises(ValueError):
        archive.write_neotoma_source_archive(
            output,
            catalogue_directory=catalogue,
            expected_catalogue_manifest_sha256=pin,
            capture_sources=sources,
        )
    assert not output.exists()
    assert not (tmp_path / ".archive.staging").exists()


@pytest.mark.parametrize("overhead", ["index", "manifest", "file_count"])
def test_generated_index_and_manifest_are_in_the_pre_read_publication_budget(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    overhead: str,
) -> None:
    catalogue, pin, sources = publish_catalogue(catalogue_sources())
    reference = tmp_path / "reference"
    manifest = archive.write_neotoma_source_archive(
        reference,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=pin,
        capture_sources=sources,
    )
    if overhead == "file_count":
        monkeypatch.setattr(publication, "MAX_FILES", len(manifest["files"]))
    else:
        budget = manifest["source_bytes"]
        if overhead == "index":
            budget -= manifest["files"]["downloads/index.json"]["bytes"]
        monkeypatch.setattr(publication, "MAX_BYTES", budget)
    forbid_bodies(monkeypatch)
    with pytest.raises(ValueError):
        archive.write_neotoma_source_archive(
            tmp_path / "over-budget",
            catalogue_directory=catalogue,
            expected_catalogue_manifest_sha256=pin,
            capture_sources=sources,
        )
    assert not (tmp_path / ".over-budget.staging").exists()


def test_exact_publication_budget_and_unused_resolvers_preserve_bytes(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalogue, pin, sources = publish_catalogue(catalogue_sources())
    reference = tmp_path / "reference"
    manifest = archive.write_neotoma_source_archive(
        reference,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=pin,
        capture_sources=sources,
    )
    monkeypatch.setattr(
        publication,
        "MAX_BYTES",
        manifest["source_bytes"] + (reference / "manifest.json").stat().st_size,
    )
    monkeypatch.setattr(publication, "MAX_FILES", len(manifest["files"]) + 1)
    unused = tmp_path / "unused-resolver"
    stat = Path.stat

    def observed(path: Path, **kwargs: Any) -> os.stat_result:
        if path == unused:
            pytest.fail("unconsumed source resolver inspected")
        return stat(path, **kwargs)

    monkeypatch.setattr(Path, "stat", observed)
    target = tmp_path / "exact-budget"
    archive.write_neotoma_source_archive(
        target,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=pin,
        capture_sources={**sources, "0" * 64: unused},
    )
    for relative in {"manifest.json", *manifest["files"]}:
        assert (
            sha256((reference / relative).read_bytes()).hexdigest()
            == sha256((target / relative).read_bytes()).hexdigest()
        )
