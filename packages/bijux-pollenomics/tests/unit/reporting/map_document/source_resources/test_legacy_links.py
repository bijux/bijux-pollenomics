"""Old numerical records join only through their exact native Neotoma namespace."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
)

from .conftest import legacy_site


def test_join_preserves_old_record_and_separates_unmatched_sites(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
) -> None:
    root, digest, _ = atlas_catalogue()
    old = [legacy_site(), legacy_site("999")]
    before = deepcopy(old)
    result = load_atlas_resource_catalogue(
        AtlasResourceCatalogueInput(root, digest), legacy_neotoma_records=old
    )
    assert old == before
    assert result.legacy_site_references == (
        {
            "record_id": "neotoma:site:12",
            "site_id": "12",
            "status": "matched",
            "dataset_ids": ["201", "202"],
        },
        {
            "record_id": "neotoma:site:999",
            "site_id": "999",
            "status": "site_not_in_resource_catalogue",
            "dataset_ids": [],
        },
    )
    assert (
        result.site_records[0]["legacy_numerical_membership"]
        == "joined_original_record"
    )
    assert result.site_records[1]["legacy_numerical_membership"] == "not_joined"
    assert result.summary["numerical_atlas_denominator_changed"] is False


@pytest.mark.parametrize(
    ("surface", "key", "value"),
    [
        ("overview", "source_family", "sead"),
        ("overview", "source_site_id", 12),
        ("overview", "source_site_id", True),
        ("overview", "source_site_id", "012"),
        ("overview", "source_site_id", " 12"),
        ("overview", "source_site_id", "13"),
        ("overview", "site_id", "sead:site:12"),
        ("record", "record_id", "sead:site:12"),
    ],
)
def test_mismatched_or_non_neotoma_legacy_namespace_refuses(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    surface: str,
    key: str,
    value: object,
) -> None:
    root, digest, _ = atlas_catalogue()
    record = legacy_site()
    target = record if surface == "record" else record["tabs"]["overview"]
    target[key] = value
    with pytest.raises(ValueError, match="legacy Neotoma"):
        load_atlas_resource_catalogue(
            AtlasResourceCatalogueInput(root, digest), legacy_neotoma_records=[record]
        )


def test_duplicate_old_native_site_identity_refuses(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
) -> None:
    root, digest, _ = atlas_catalogue()
    with pytest.raises(ValueError, match="duplicate legacy Neotoma"):
        load_atlas_resource_catalogue(
            AtlasResourceCatalogueInput(root, digest),
            legacy_neotoma_records=[legacy_site(), legacy_site()],
        )
