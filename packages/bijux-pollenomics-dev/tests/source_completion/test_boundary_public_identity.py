"""Public boundary claims must track the governed geometry and review receipt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import pytest

ROOT = next(
    parent
    for parent in Path(__file__).parents
    if (parent / "configs/pytest.ini").is_file()
)
PAGES = (
    ROOT / "docs/public/pollenomics-data/sources/boundaries.md",
    ROOT / "docs/public/pollenomics-data/publications/boundary-exports.md",
)


@pytest.mark.parametrize("page", PAGES)
def test_public_boundary_release_and_review_are_source_bound(page: Path) -> None:
    source = json.loads((ROOT / "data/boundaries/raw/source_manifest.json").read_text())
    review = json.loads((ROOT / "data/boundaries/review/manifest.json").read_text())
    normalized = ROOT / "data/boundaries/normalized/nordic_country_boundaries.geojson"
    text = page.read_text()

    assert source["source"] == review["boundary_authority"]["source"]
    assert source["version"] == review["boundary_authority"]["version"]
    assert source["version"] in text
    assert source["generated_on"] in text
    digest = hashlib.sha256(normalized.read_bytes()).hexdigest()
    assert digest == source["normalized_artifact"]["sha256"]
    assert digest == review["boundary_authority"]["normalized_artifact_sha256"]
    assert digest in text
    assert f"{review['point_count']:,}" in text
    assert str(review["point_review_count"]) in text
    assert review["release_posture"] in text
    assert "`v66`" in text and "Natural Earth release" in text
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if "://" not in target and not target.startswith("#"):
            assert (page.parent / target.split("#")[0]).exists(), target


def test_public_boundary_decision_denominators_match_governed_manifest() -> None:
    review = json.loads((ROOT / "data/boundaries/review/manifest.json").read_text())
    text = PAGES[0].read_text()
    labels = {
        "animal_adna": "animal aDNA",
        "landclim": "LandClim",
        "neotoma": "Neotoma",
        "sead": "SEAD",
    }
    summaries = review["source_summaries"]
    assert sum(row["row_count"] for row in summaries.values()) == review["point_count"]
    assert (
        sum(
            row["review_requirement_counts"].get("qualified_review_required", 0)
            for row in summaries.values()
        )
        == review["point_review_count"]
    )
    for key, summary in summaries.items():
        statuses = summary["decision_status_counts"]
        assert sum(statuses.values()) == summary["row_count"]
        expected = (
            "| "
            + " | ".join(
                [
                    labels[key],
                    f"{summary['row_count']:,}",
                    f"{statuses.get('assigned', 0):,}",
                    f"{statuses.get('review', 0):,}",
                    f"{statuses.get('unassigned', 0):,}",
                    f"{summary['country_counts']['UNASSIGNED']:,}",
                ]
            )
            + " |"
        )
        assert expected in text
