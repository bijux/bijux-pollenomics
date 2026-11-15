"""Portable native source archives keep bytes, role refusals and source epochs."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest


def test_portable_archive_has_exact_sources_and_closed_download_partition(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        load_neotoma_source_archive,
        write_neotoma_source_archive,
    )

    inputs = catalogue_sources(auxiliary_type="unregistered native proxy")
    catalogue, digest, sources = publish_catalogue(inputs)
    output = tmp_path / "source-resources"
    manifest = write_neotoma_source_archive(
        output,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
    )
    pin = sha256((output / "manifest.json").read_bytes()).hexdigest()
    assert load_neotoma_source_archive(output, expected_manifest_sha256=pin) == manifest
    index = json.loads((output / "downloads/index.json").read_bytes())
    assert len(index["resources"]) == 8
    assert index["partitions"] == {
        "available_source_entity": 4,
        "blocked_exposure_role": 4,
    }
    for row in index["resources"]:
        if row["state"] == "blocked_exposure_role":
            assert "download_path" not in row
            continue
        source = row["source"]
        expected = sources[source["capture_manifest_sha256"]] / source["body_file"]
        assert (output / row["download_path"]).read_bytes() == expected.read_bytes()
    assert index["scientific_admission"] == "not_asserted"
    assert str(tmp_path) not in (output / "downloads/index.json").read_text()
    assert (output / "catalogue/manifest.json").read_bytes() == (
        catalogue / "manifest.json"
    ).read_bytes()


@pytest.mark.parametrize("mutation", ["body", "index", "extra", "rehashed_extra"])
def test_archive_readback_refuses_tampering(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    tmp_path: Path,
    mutation: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        load_neotoma_source_archive,
        write_neotoma_source_archive,
    )

    catalogue, digest, sources = publish_catalogue(catalogue_sources())
    output = tmp_path / "source-resources"
    write_neotoma_source_archive(
        output,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
    )
    pin = sha256((output / "manifest.json").read_bytes()).hexdigest()
    if mutation == "body":
        next(
            (output / "captures").glob("*/dataset-201-current-attempt-1.body")
        ).write_bytes(b"foreign")
    elif mutation == "index":
        (output / "downloads/index.json").write_text("{}")
    else:
        (output / "foreign.json").write_text("{}")
        if mutation == "rehashed_extra":
            path = output / "manifest.json"
            manifest = json.loads(path.read_bytes())
            manifest["files"]["foreign.json"] = {
                "bytes": 2,
                "sha256": sha256(b"{}").hexdigest(),
            }
            manifest["source_bytes"] += 2
            path.write_text(json.dumps(manifest))
            pin = sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="identity|population"):
        load_neotoma_source_archive(output, expected_manifest_sha256=pin)


def test_source_archive_preserves_existing_destination(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        write_neotoma_source_archive,
    )

    catalogue, digest, sources = publish_catalogue(catalogue_sources())
    output = tmp_path / "source-resources"
    output.mkdir()
    witness = output / "user.json"
    witness.write_bytes(b"user evidence")
    with pytest.raises(FileExistsError):
        write_neotoma_source_archive(
            output,
            catalogue_directory=catalogue,
            expected_catalogue_manifest_sha256=digest,
            capture_sources=sources,
        )
    assert witness.read_bytes() == b"user evidence"
