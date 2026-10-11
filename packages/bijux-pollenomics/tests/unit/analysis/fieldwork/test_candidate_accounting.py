from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.analysis.fieldwork.candidate_accounting import (
    read_screened_registry,
)
from bijux_pollenomics.analysis.fieldwork.candidate_registry import (
    build_sweden_lake_candidate_registry,
)
from bijux_pollenomics.collection.contracts.families.authority import (
    _svar_authority_state,
)


def _feature(properties: dict[str, object]) -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "Point", "coordinates": [14.0, 57.0]},
    }


def _registry(path: Path, features: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("name", None, "name_null"),
        ("name", "", "name_empty"),
        ("name", "  ", "name_empty"),
        ("name", 0, "name_not_string"),
        ("name", False, "name_not_string"),
        ("name", [], "name_not_string"),
        ("name", {}, "name_not_string"),
        ("sjoid", None, "identity_null"),
        ("sjoid", "", "identity_empty"),
        ("sjoid", "  ", "identity_empty"),
        ("sjoid", 0, "identity_not_string"),
        ("sjoid", False, "identity_not_string"),
        ("sjoid", [], "identity_not_string"),
        ("sjoid", {}, "identity_not_string"),
    ],
)
def test_native_wrong_or_missing_tokens_are_not_stringified(
    tmp_path: Path, field: str, value: object, reason: str
) -> None:
    properties: dict[str, object] = {"sjoid": "native:1", "name": "Lake"}
    properties[field] = value
    path = tmp_path / "registry.json"
    _registry(path, [_feature(properties)])
    rows, review = read_screened_registry(path)
    assert not rows
    assert review["source_lake_count"] == 1
    exclusions = cast(list[dict[str, object]], review["screening_exclusions"])
    assert exclusions == [
        {
            "source_feature_index": 0,
            "reason_code": reason,
            "source_fields": properties,
        }
    ]
    retained = cast(dict[str, object], exclusions[0]["source_fields"])[field]
    assert type(retained) is type(value)


@pytest.mark.parametrize(
    ("field", "reason"), [("name", "name_absent"), ("sjoid", "identity_absent")]
)
def test_absence_remains_distinct_from_explicit_null(
    tmp_path: Path, field: str, reason: str
) -> None:
    properties: dict[str, object] = {"sjoid": "native:1", "name": "Lake"}
    del properties[field]
    path = tmp_path / "registry.json"
    _registry(path, [_feature(properties)])
    _, review = read_screened_registry(path)
    exclusion = cast(list[dict[str, object]], review["screening_exclusions"])[0]
    assert exclusion["reason_code"] == reason
    assert field not in cast(dict[str, object], exclusion["source_fields"])


def test_total_partition_preserves_malformed_occurrences_and_exact_bytes(
    tmp_path: Path,
) -> None:
    features: list[object] = [
        _feature({"sjoid": "0", "name": "Lake Zero", "area_km2": 0}),
        None,
        0,
        [],
        {"type": "Feature", "properties": None},
        {"type": "Feature", "properties": {"sjoid": "native:2", "name": "Lake Two"}},
        _feature({"sjoid": "native:3", "name": ""}),
    ]
    path = tmp_path / "registry.json"
    _registry(path, features)
    rows, review = read_screened_registry(path)
    assert review["source_lake_count"] == 7
    assert review["screening_eligible_lake_count"] == 1
    assert review["screening_excluded_lake_count"] == 6
    assert rows[0]["lake_id"] == "0"
    assert rows[0]["properties"]["area_km2"] == 0
    exclusions = cast(list[dict[str, object]], review["screening_exclusions"])
    assert [r["source_feature_index"] for r in exclusions] == list(range(1, 7))
    assert [r["source_feature_value"] for r in exclusions[:3]] == [None, 0, []]
    assert review["registry_sha256"] == sha256(path.read_bytes()).hexdigest()
    assert review["registry_byte_count"] == path.stat().st_size
    old_hash = review["registry_sha256"]
    path.write_bytes(path.read_bytes() + b"\n")
    new_rows, new_review = read_screened_registry(path)
    assert new_rows == rows
    assert new_review["registry_sha256"] != old_hash


@pytest.mark.parametrize("kind", [None, "NotAFeature", "feature", "", 0, False, [], {}])
def test_wrong_feature_kind_retains_native_fields_and_token(
    tmp_path: Path, kind: object
) -> None:
    feature = _feature({"sjoid": "native:1", "name": "Lake One"})
    feature["type"] = kind
    path = tmp_path / "registry.json"
    _registry(path, [feature])
    rows, review = read_screened_registry(path)
    assert not rows
    assert review["source_lake_count"] == 1
    assert review["screening_excluded_lake_count"] == 1
    exclusion = cast(list[dict[str, object]], review["screening_exclusions"])[0]
    assert exclusion == {
        "source_feature_index": 0,
        "reason_code": "feature_kind_invalid",
        "source_fields": {"sjoid": "native:1", "name": "Lake One"},
        "source_feature_type": kind,
    }
    assert type(exclusion["source_feature_type"]) is type(kind)


def test_absent_feature_kind_is_distinct_from_null(tmp_path: Path) -> None:
    feature = _feature({"record_id": "native:1", "name": "Lake One"})
    del feature["type"]
    path = tmp_path / "registry.json"
    _registry(path, [feature])
    rows, review = read_screened_registry(path)
    assert not rows
    exclusion = cast(list[dict[str, object]], review["screening_exclusions"])[0]
    assert exclusion["reason_code"] == "feature_kind_invalid"
    assert "source_feature_type" not in exclusion
    assert exclusion["source_fields"] == {"record_id": "native:1", "name": "Lake One"}


@pytest.mark.parametrize(
    "content",
    [
        "{}",
        "[]",
        '{"type":"FeatureCollection"}',
        '{"type":"FeatureCollection","features":null}',
        '{"type":"FeatureCollection","features":[],"features":[]}',
        '{"type":"FeatureCollection","features":[NaN]}',
        '{"type":"FeatureCollection","features":[1e999]}',
    ],
)
def test_ambiguous_or_invalid_container_refuses(tmp_path: Path, content: str) -> None:
    path = tmp_path / "registry.json"
    path.write_text(content)
    with pytest.raises(ValueError):
        read_screened_registry(path)


@pytest.mark.parametrize("sjoid", [None, ""])
def test_explicit_record_id_fallback_preserves_native_fields(
    tmp_path: Path, sjoid: object
) -> None:
    path = tmp_path / "registry.json"
    properties = {"sjoid": sjoid, "record_id": "native:0", "name": "Lake"}
    _registry(path, [_feature(properties)])
    rows, _ = read_screened_registry(path)
    assert rows[0]["lake_id"] == "native:0"
    assert rows[0]["properties"] == properties


def test_empty_screen_with_pollen_is_accounted_without_nearest_failure(
    tmp_path: Path,
) -> None:
    path = tmp_path / "registry.json"
    _registry(path, [_feature({"sjoid": "native:1", "name": None})])
    pollen = tmp_path / "pollen.json"
    _registry(pollen, [_feature({"country": "Sweden", "record_id": "sample:1"})])
    registry, review = build_sweden_lake_candidate_registry(
        svar_geojson_path=path, pollen_geojson_paths=[pollen], generated_on="fixture"
    )
    assert registry["features"] == []
    assert review["source_lake_count"] == 1
    assert review["screening_eligible_lake_count"] == 0
    assert review["screening_excluded_lake_count"] == 1
    assert review["pollen_linked_lake_count"] == 0


def test_new_byte_bound_review_does_not_grant_publication_authority(
    tmp_path: Path,
) -> None:
    source = tmp_path / "svar/normalized/sweden_lake_registry.geojson"
    _registry(
        source,
        [
            _feature({"sjoid": "zero", "name": "Lake Zero", "area_km2": 0}),
            _feature({"sjoid": "null", "name": "Lake Null", "area_km2": None}),
            _feature({"sjoid": "unnamed", "name": ""}),
        ],
    )
    registry, review = build_sweden_lake_candidate_registry(
        svar_geojson_path=source,
        pollen_geojson_paths=[],
        generated_on="fixture",
        named_targets=["Lake Zero", "Lake Null"],
    )
    features = cast(list[dict[str, object]], registry["features"])
    properties = [cast(dict[str, object], f["properties"]) for f in features]
    by_id = {p["sjoid"]: p for p in properties}
    assert by_id["zero"]["area_km2"] == 0
    assert by_id["null"]["area_km2"] is None
    assert by_id["zero"]["sampling_area_screen"] == "micro_basin_review"
    assert by_id["null"]["sampling_area_screen"] == "mapped_area_unresolved"
    assert review["source_lake_count"] == 3
    assert review["screening_eligible_lake_count"] == 2
    for relative, content in {
        "svar/raw/svar_lake_registry_manifest.json": {
            "source": "SMHI SVAR",
            "matched_lake_count": 3,
            "normalized_lake_count": 3,
        },
        "svar/normalized/svar_summary.json": {"source": "SMHI SVAR", "lake_count": 3},
        "svar/review/sweden_lake_candidate_registry.geojson": registry,
        "svar/review/lake_candidate_registry_review.json": review,
    }.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content))
    assert review["registry_sha256"] == sha256(source.read_bytes()).hexdigest()
    assert "release_status" not in review and "reviewer_id" not in review
    authority = _svar_authority_state(tmp_path)
    assert authority.status == "review_required"
    assert authority.reason_codes == ("qualified_svar_publication_review_missing",)
