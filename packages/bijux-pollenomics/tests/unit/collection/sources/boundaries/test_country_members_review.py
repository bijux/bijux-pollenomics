"""Country review preserves administrative source ownership after aggregation."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.boundaries.archive import (
    build_combined_country_boundaries,
)
from bijux_pollenomics.collection.sources.boundaries.collection import (
    collect_boundaries_data,
)
from bijux_pollenomics.collection.sources.boundaries.review import (
    _build_boundary_review,
)
from bijux_pollenomics.collection.sources.boundaries.review.authority import (
    _load_boundary_authority,
)
from bijux_pollenomics.collection.sources.boundaries.store import (
    NORDIC_ADMIN0_MEMBERS,
    NORDIC_WITH_ALAND_PROFILE,
)
from bijux_pollenomics.core.geospatial.geojson import feature_list

from .test_aland_selection import _source
from .test_boundary_country_review import _authority, _collection, _rectangle


def test_retained_member_receipt_loads_with_capture_and_build_dates_separate(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.geojson"
    source.write_text(json.dumps(_source()))
    data = tmp_path / "data"
    collect_boundaries_data(
        data / "boundaries",
        source_path=source,
        source_captured_at_utc="2026-10-27T22:49:30.769189+00:00",
    )
    authority = _load_boundary_authority(data)
    review = _build_boundary_review(authority)
    identity = review["boundary_authority"]
    assert isinstance(identity, dict)
    assert identity["acquisition_mode"] == "retained_asset"
    assert identity["source_capture_date"] == "2026-10-27"
    assert (
        identity["source_artifact_build_date"]
        == authority.source_manifest["generated_on"]
    )


def test_merged_country_review_retains_each_source_member_and_part() -> None:
    original = _authority()
    finland = original.boundaries["Finland"]
    finland["features"] = feature_list(finland) + feature_list(
        _collection("Finland", "ALD", _rectangle(15, 0, 16, 1))
    )
    original.source_manifest["country_selection_profile"] = NORDIC_WITH_ALAND_PROFILE
    original.source_manifest["country_admin0_members"] = {
        country: list(members) for country, members in NORDIC_ADMIN0_MEMBERS.items()
    }
    authority = replace(
        original,
        normalized_collection=build_combined_country_boundaries(original.boundaries),
    )
    review = _build_boundary_review(authority)
    countries = review["countries"]
    assert isinstance(countries, list)
    entry = next(row for row in countries if row["country_code"] == "FI")
    assert entry["admin0_members"] == ["FIN", "ALD"]
    assert entry["feature_count"] == 2
    assert entry["polygon_part_count"] == 2
    assert [row["source_admin0_code"] for row in entry["polygon_part_inventory"]] == [
        "FIN",
        "ALD",
    ]
    assert entry["qualified_review_status"] == "pending"
    authority.normalized_collection["features"] = feature_list(
        build_combined_country_boundaries(_authority().boundaries)
    )
    with pytest.raises(ValueError, match="did not retain all parts"):
        _build_boundary_review(authority)


def test_duplicate_normalized_country_refuses() -> None:
    authority = _authority()
    features = feature_list(authority.normalized_collection)
    authority.normalized_collection["features"] = features + [features[0]]
    with pytest.raises(ValueError, match="Duplicate normalized"):
        _build_boundary_review(authority)
