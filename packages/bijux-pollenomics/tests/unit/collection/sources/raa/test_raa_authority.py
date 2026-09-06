from __future__ import annotations

import json
from pathlib import Path
import tempfile

from bijux_pollenomics.collection.sources.raa import (
    assess_raa_density_authority,
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_reconciled_fixture(root: Path, *, reviewer_id: str = "reviewer-1") -> None:
    raw_features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [18.0, 57.0]},
            "properties": {"antikvariskbedomningtyp_namn": "Fornlämning"},
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [19.0, 58.0]},
            "properties": {"antikvariskbedomningtyp_namn": "Möjlig fornlämning"},
        },
    ]
    _write_json(
        root / "raa/raw/publicerade_lamningar_centrumpunkt.geojson",
        {"type": "FeatureCollection", "features": raw_features},
    )
    _write_json(
        root / "raa/raw/publicerade_lamningar_centrumpunkt_summary.json",
        {"archived_feature_count": 2, "heritage_site_count": 1},
    )
    _write_json(
        root / "raa/normalized/sweden_archaeology_layer.json",
        {"counts": {"fornlamning": 1}, "density_feature_count": 1},
    )
    _write_json(
        root / "raa/normalized/sweden_archaeology_density.geojson",
        {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {"count": 1}}],
        },
    )
    _write_json(
        root / "raa/review/spatiotemporal_review.json",
        {"release_status": "accepted", "reviewer_id": reviewer_id},
    )


def test_raa_density_authority_requires_every_governing_surface() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        decision = assess_raa_density_authority(Path(tmp))

    assert decision.admitted is False
    assert decision.reason_codes == (
        "missing_raw_inventory",
        "missing_raw_summary",
        "missing_normalized_metadata",
        "missing_density_surface",
        "missing_scientific_review",
    )
    assert decision.heritage_site_count is None


def test_raa_density_authority_admits_reconciled_human_reviewed_surface() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_reconciled_fixture(root)

        decision = assess_raa_density_authority(root)

    assert decision.admitted is True
    assert decision.reason_codes == ()
    assert decision.archived_feature_count == 2
    assert decision.heritage_site_count == 1
    assert decision.density_site_count == 1
    assert decision.density_feature_count == 1
    assert decision.reviewer_id == "reviewer-1"


def test_raa_density_authority_refuses_count_conflict_and_missing_reviewer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_reconciled_fixture(root, reviewer_id="")
        density_path = root / "raa/normalized/sweden_archaeology_density.geojson"
        _write_json(
            density_path,
            {
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "properties": {"count": 3}}],
            },
        )

        decision = assess_raa_density_authority(root)

    assert decision.admitted is False
    assert "density_site_count_mismatch" in decision.reason_codes
    assert "scientific_review_not_accepted" in decision.reason_codes
