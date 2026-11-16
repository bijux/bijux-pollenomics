"""Bibliography exposes source attribution without inspecting contributor bodies."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from bijux_pollenomics.collection.sources.landclim import build_landclim_bibliography
from bijux_pollenomics.collection.sources.landclim.catalog import (
    LANDCLIM_BIBLIOGRAPHY,
    LANDCLIM_DATASET_METADATA,
    LANDCLIM_LOCAL_FILENAME_BY_SOURCE_NAME,
)


def test_contributor_resource_is_linked_only_to_its_native_dataset() -> None:
    bibliography = cast(dict[str, Any], build_landclim_bibliography())
    datasets = {row["dataset_id"]: row for row in bibliography["datasets"]}
    assert datasets["937075"]["attribution_resources"] == [
        {
            "resource_key": "landclim-ii-contributors",
            "role": "dataset_contributor_attribution",
            "source_filename": "LandClimII_contributors.xlsx",
            "local_filename": "landclim_ii_contributors.xlsx",
            "source_url": "https://download.pangaea.de/dataset/937075/files/LandClimII_contributors.xlsx",
        }
    ]
    assert datasets["897303"]["attribution_resources"] == []
    assert datasets["900966"]["attribution_resources"] == []
    descriptor = datasets["937075"]["attribution_resources"][0]
    assert (
        LANDCLIM_LOCAL_FILENAME_BY_SOURCE_NAME[descriptor["source_filename"]]
        == descriptor["local_filename"]
    )


def test_attribution_discovery_never_opens_source_or_contact_bodies() -> None:
    with (
        patch.object(Path, "open", side_effect=AssertionError("source body opened")),
        patch.object(
            Path, "read_bytes", side_effect=AssertionError("source bytes read")
        ),
        patch.object(Path, "read_text", side_effect=AssertionError("source text read")),
    ):
        bibliography = cast(dict[str, Any], build_landclim_bibliography())
    assert bibliography["schema_version"] == "landclim-bibliography.v1"
    assert bibliography["dataset_count"] == 3
    assert bibliography["reference_count"] == 4
    assert bibliography["references"] == list(LANDCLIM_BIBLIOGRAPHY)
    for row in bibliography["datasets"]:
        metadata = LANDCLIM_DATASET_METADATA[row["dataset_id"]]
        assert all(
            row[key] == metadata[key]
            for key in ("label", "citation", "doi", "publication_year")
        )
        assert row["license"] == "CC-BY-4.0"


def test_each_call_returns_independent_attribution_metadata() -> None:
    first = cast(dict[str, Any], build_landclim_bibliography())
    source = next(row for row in first["datasets"] if row["dataset_id"] == "937075")
    source["attribution_resources"][0]["role"] = "caller mutation"
    second = cast(dict[str, Any], build_landclim_bibliography())
    source = next(row for row in second["datasets"] if row["dataset_id"] == "937075")
    assert (
        source["attribution_resources"][0]["role"] == "dataset_contributor_attribution"
    )
