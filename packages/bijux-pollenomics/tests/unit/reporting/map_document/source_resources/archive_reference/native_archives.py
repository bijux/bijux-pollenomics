"""Authentic finite catalogue/archive publications for metadata reader contracts."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    write_neotoma_source_archive,
)

from .....collection.sources.neotoma.resource_catalogue.reading.catalogue_publication import (
    publish_catalogue as publish_catalogue,
)


@pytest.fixture
def archive_inputs(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    tmp_path: Path,
) -> tuple[Path, str, Path, str]:
    catalogue, digest, sources = publish_catalogue(catalogue_sources())
    archive = tmp_path / "source-resources"
    write_neotoma_source_archive(
        archive,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
    )
    return (
        catalogue,
        digest,
        archive,
        sha256((archive / "manifest.json").read_bytes()).hexdigest(),
    )
