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
