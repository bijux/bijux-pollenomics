"""Consequential land-use replay separates scientific and presentation changes."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.sweden_land_use_replay import (
    compare_historical,
    semantic_diff,
)

REPOSITORY = Path(__file__).resolve().parents[4]
PRODUCT = REPOSITORY / "docs/report/countries/sweden/sweden_land_use_synthesis_v66.json"


def test_semantic_categories_keep_independent_changes_distinct() -> None:
    published = json.loads(PRODUCT.read_text(encoding="utf-8"))
    assert all(
        not items
        for items in semantic_diff(published, published, renderings_equal=True).values()
    )

    changed = deepcopy(published)
    changed["rows"].pop()
    changed["rows"][0]["forest_cover"] = 1.0
    changed["rows"][0]["latitude"] = 55.0
    changed["rows"][0]["quality_class"] = "no_pollen_data"
    changed["context_radius_km"] = 21
    changed["rows"][0]["time_label"] = "reader label only"
    differences = semantic_diff(published, changed, renderings_equal=False)
    assert all(differences.values())
    assert any(
        "forest_cover" in row["path"] for row in differences["scientific_result"]
    )
    assert any(
        "quality_class" in row["path"] for row in differences["admission_or_exclusion"]
    )
    assert any(
        "context_radius_km" in row["path"] for row in differences["policy_or_weighting"]
    )
    assert any(
        "latitude" in row["path"] for row in differences["normalized_identity_or_value"]
    )
    assert any("time_label" in row["path"] for row in differences["presentation"])

    rendering_only = semantic_diff(published, published, renderings_equal=False)
    assert rendering_only["presentation"] == [
        {
            "path": "serialized_json_csv_or_markdown",
            "before": "published",
            "after": "replay",
        }
    ]
    assert all(
        not rendering_only[key] for key in rendering_only if key != "presentation"
    )


def test_new_unclassified_product_field_refuses_semantic_replay() -> None:
    published = json.loads(PRODUCT.read_text(encoding="utf-8"))
    changed = deepcopy(published)
    changed["rows"][0]["unreviewed_measure"] = 1
    with pytest.raises(ValueError, match="Unclassified rows"):
        semantic_diff(published, changed, renderings_equal=True)


def test_real_named_lake_revision_explains_membership_change(tmp_path: Path) -> None:
    comparison = compare_historical(REPOSITORY, "0a3a42ad", tmp_path)
    assert comparison["direct_source_paths_changed"] == []
    assert comparison["baseline_target_count"] == 2
    assert comparison["current_target_count"] == 6
    assert comparison["baseline_time_row_count"] == 50
    assert comparison["current_time_row_count"] == 150
    assert comparison["change_counts"] == {
        "source_membership": 106,
        "normalized_identity_or_value": 0,
        "policy_or_weighting": 1,
        "admission_or_exclusion": 1,
        "scientific_result": 0,
        "presentation": 0,
    }
    assert any(
        path.endswith("/targets.py")
        for path in comparison["land_use_policy_paths_changed"]
    )
