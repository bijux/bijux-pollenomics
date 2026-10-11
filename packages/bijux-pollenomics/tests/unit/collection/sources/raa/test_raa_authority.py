from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

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
            "properties": {
                "lamningsnummer": "A",
                "antikvariskbedomningtyp_namn": "Fornlämning",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [19.0, 58.0]},
            "properties": {
                "lamningsnummer": "B",
                "antikvariskbedomningtyp_namn": "Möjlig fornlämning",
            },
        },
    ]
    _write_json(
        root / "raa/raw/publicerade_lamningar_centrumpunkt.geojson",
        {"type": "FeatureCollection", "features": raw_features, "numberMatched": 2},
    )
    _write_json(
        root / "raa/raw/publicerade_lamningar_centrumpunkt_summary.json",
        {
            "archived_feature_count": 2,
            "heritage_site_count": 1,
            "number_matched": 2,
            "identified_feature_count": 2,
            "heritage_or_possible_site_count": 2,
        },
    )
    _write_json(
        root / "raa/normalized/sweden_archaeology_layer.json",
        {
            "counts": {
                "fornlamning": 1,
                "all_published_sites": 2,
                "fornlamning_or_possible": 2,
            },
            "density_feature_count": 1,
        },
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


@pytest.mark.parametrize("count", [None, False, True, -1, 0.5, 1.0, "0", [], {}])
def test_invalid_density_count_never_disappears_in_matching_total(
    tmp_path: Path, count: object
) -> None:
    _write_reconciled_fixture(tmp_path)
    density_path = tmp_path / "raa/normalized/sweden_archaeology_density.geojson"
    density = json.loads(density_path.read_text())
    density["features"].append({"type": "Feature", "properties": {"count": count}})
    _write_json(density_path, density)
    metadata_path = tmp_path / "raa/normalized/sweden_archaeology_layer.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["density_feature_count"] = 2
    _write_json(metadata_path, metadata)
    decision = assess_raa_density_authority(tmp_path)
    assert not decision.admitted
    assert "invalid_density_cell_count" in decision.reason_codes
    assert decision.density_site_count is None


@pytest.mark.parametrize("properties", [{}, None])
def test_absent_density_count_is_not_zero(tmp_path: Path, properties: object) -> None:
    _write_reconciled_fixture(tmp_path)
    path = tmp_path / "raa/normalized/sweden_archaeology_density.geojson"
    _write_json(
        path,
        {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": properties}],
        },
    )
    decision = assess_raa_density_authority(tmp_path)
    assert "invalid_density_cell_count" in decision.reason_codes
    assert decision.density_site_count is None


def test_explicit_zero_density_cell_preserves_complete_total(tmp_path: Path) -> None:
    _write_reconciled_fixture(tmp_path)
    path = tmp_path / "raa/normalized/sweden_archaeology_density.geojson"
    density = json.loads(path.read_text())
    density["features"].append({"type": "Feature", "properties": {"count": 0}})
    _write_json(path, density)
    path = tmp_path / "raa/normalized/sweden_archaeology_layer.json"
    metadata = json.loads(path.read_text())
    metadata["density_feature_count"] = 2
    _write_json(path, metadata)
    decision = assess_raa_density_authority(tmp_path)
    assert decision.admitted
    assert decision.density_site_count == 1
    assert decision.density_feature_count == 2


@pytest.mark.parametrize("member", [None, False, 4, {}, {"type": "NotFeature"}])
@pytest.mark.parametrize(
    "surface",
    [
        "raw/publicerade_lamningar_centrumpunkt.geojson",
        "normalized/sweden_archaeology_density.geojson",
    ],
)
def test_malformed_authority_members_are_not_filtered(
    tmp_path: Path, member: object, surface: str
) -> None:
    _write_reconciled_fixture(tmp_path)
    path = tmp_path / "raa" / surface
    value = json.loads(path.read_text())
    value["features"].append(member)
    _write_json(path, value)
    decision = assess_raa_density_authority(tmp_path)
    assert not decision.admitted
    assert decision.reason_codes == ("invalid_authority_inventory",)


@pytest.mark.parametrize(
    "surface,field,reason",
    [
        (
            "raw/publicerade_lamningar_centrumpunkt_summary.json",
            "number_matched",
            "summary_population_mismatch",
        ),
        (
            "raw/publicerade_lamningar_centrumpunkt_summary.json",
            "identified_feature_count",
            "summary_identified_count_mismatch",
        ),
        (
            "raw/publicerade_lamningar_centrumpunkt_summary.json",
            "heritage_or_possible_site_count",
            "summary_possible_heritage_count_mismatch",
        ),
        (
            "normalized/sweden_archaeology_layer.json",
            "all_published_sites",
            "metadata_archived_count_mismatch",
        ),
        (
            "normalized/sweden_archaeology_layer.json",
            "fornlamning_or_possible",
            "metadata_possible_heritage_count_mismatch",
        ),
    ],
)
@pytest.mark.parametrize("replacement", [None, True, 2.0, 3])
def test_all_declared_summary_counts_are_bound(
    tmp_path: Path, surface: str, field: str, reason: str, replacement: object
) -> None:
    _write_reconciled_fixture(tmp_path)
    path = tmp_path / "raa" / surface
    payload = json.loads(path.read_text())
    target = payload.get("counts", payload)
    target[field] = replacement
    _write_json(path, payload)
    decision = assess_raa_density_authority(tmp_path)
    assert not decision.admitted
    assert reason in decision.reason_codes


@pytest.mark.parametrize(
    "surface,old,new",
    [
        (
            "raw/publicerade_lamningar_centrumpunkt.geojson",
            '"numberMatched": 2',
            '"numberMatched": 999, "numberMatched": 2',
        ),
        (
            "raw/publicerade_lamningar_centrumpunkt.geojson",
            '"lamningsnummer": "A"',
            '"lamningsnummer": "X", "lamningsnummer": "A"',
        ),
        (
            "normalized/sweden_archaeology_density.geojson",
            '"count": 1',
            '"count": null, "count": 1',
        ),
        (
            "raw/publicerade_lamningar_centrumpunkt_summary.json",
            '"archived_feature_count": 2',
            '"archived_feature_count": 9, "archived_feature_count": 2',
        ),
        (
            "normalized/sweden_archaeology_layer.json",
            '"fornlamning": 1',
            '"fornlamning": 1, "fornlamning": 1',
        ),
        (
            "review/spatiotemporal_review.json",
            '"release_status": "accepted"',
            '"release_status": "refused", "release_status": "accepted"',
        ),
    ],
)
def test_authority_refuses_duplicate_json_claims_before_comparison(
    tmp_path: Path, surface: str, old: str, new: str
) -> None:
    _write_reconciled_fixture(tmp_path)
    path = tmp_path / "raa" / surface
    text = path.read_text()
    assert text.count(old) == 1
    path.write_text(text.replace(old, new))
    decision = assess_raa_density_authority(tmp_path)
    assert not decision.admitted
    assert decision.reason_codes == ("invalid_authority_artifact",)
