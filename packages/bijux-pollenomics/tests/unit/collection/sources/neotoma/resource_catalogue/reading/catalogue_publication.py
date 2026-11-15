"""Shared publication and access fixtures for selected native resource reading."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as api


@pytest.fixture
def resource_reader() -> Callable[..., dict[str, Any]]:
    return api.read_neotoma_catalogue_resource


@pytest.fixture
def publish_catalogue(
    tmp_path: Path,
) -> Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]]:
    def publish(inputs: dict[str, Any]) -> tuple[Path, str, dict[str, Path]]:
        catalogue = api.build_neotoma_resource_catalogue(**inputs)
        sources = {
            **inputs["metadata_captures"],
            **inputs["resource_captures"],
            **inputs.get("source_captures", {}),
        }
        output = tmp_path / "public"
        api.write_neotoma_resource_catalogue(
            output,
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources=sources,
        )
        return (
            output,
            sha256((output / "manifest.json").read_bytes()).hexdigest(),
            sources,
        )

    return publish


class _NoOutcomeResolver(dict[str, Path]):
    def __contains__(self, key: object) -> bool:
        raise AssertionError("External outcome resolver accessed before access refusal")

    def __getitem__(self, key: str) -> Path:
        raise AssertionError("External outcome resolver accessed before access refusal")


@pytest.fixture
def no_outcome_resolver() -> dict[str, Path]:
    return _NoOutcomeResolver()
