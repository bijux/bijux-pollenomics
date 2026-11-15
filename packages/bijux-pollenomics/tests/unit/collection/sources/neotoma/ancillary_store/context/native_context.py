"""Immutable native archive and exposure context for source custody controls."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def context_inputs(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    tmp_path: Path,
) -> dict[str, Any]:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        write_neotoma_source_archive,
    )

    inputs = catalogue_sources()
    catalogue, pin, captures = publish_catalogue(inputs)
    native = tmp_path / "native"
    write_neotoma_source_archive(
        native,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=pin,
        capture_sources=captures,
    )
    authority = tmp_path / "authority.json"
    authority.write_bytes(b'{ "status": "observed_metadata_review", "rights": null }\n')
    legacy = tmp_path / "legacy.json"
    raw = inputs["roster_path"].read_bytes()
    legacy.write_bytes(b" \n" + raw + b"\n")
    return {
        "native_archive_directory": native,
        "expected_native_archive_sha256": sha256(
            (native / "manifest.json").read_bytes()
        ).hexdigest(),
        "legacy_rosters": {sha256(legacy.read_bytes()).hexdigest(): legacy},
        "exposure_authority": authority,
        "expected_exposure_authority_sha256": sha256(
            authority.read_bytes()
        ).hexdigest(),
    }
