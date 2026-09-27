"""Retained frame input integrity and country-shard identity boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.context_frame_candidate import (
    collect_retained_features,
    generate_context_frame_candidates,
    record_digest,
)


def test_context_features_deduplicate_identical_country_overlap_in_source_order() -> (
    None
):
    feature = {"properties": {"record_id": "source:1", "value": None}}
    other = {"properties": {"record_id": "source:2", "value": 0}}
    assert collect_retained_features(
        [
            {"feature_indexes": [5, 2], "features": [other, feature]},
            {"feature_indexes": [2], "features": [feature]},
        ]
    ) == [feature, other]


def test_context_features_refuse_conflicting_country_overlap() -> None:
    with pytest.raises(ValueError, match="conflicting source records"):
        collect_retained_features(
            [
                {"feature_indexes": [2], "features": [{"value": None}]},
                {"feature_indexes": [2], "features": [{"value": 0}]},
            ]
        )


def test_context_candidate_requires_absent_owned_destination(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="repository artifacts"):
        generate_context_frame_candidates(
            tmp_path,
            tmp_path / "outside",
            tmp_path,
            tmp_path / "geometry.json",
            "a" * 64,
            "b" * 64,
        )
    destination = tmp_path / "artifacts/candidate"
    destination.mkdir(parents=True)
    with pytest.raises(ValueError, match="destination must be absent"):
        generate_context_frame_candidates(
            tmp_path,
            destination,
            tmp_path,
            tmp_path / "geometry.json",
            "a" * 64,
            "b" * 64,
        )


def test_context_candidate_refuses_native_input_digest_before_source_reads(
    tmp_path: Path,
) -> None:
    product = tmp_path / "product"
    product.mkdir()
    (product / "manifest.json").write_text("{}")
    geometry = tmp_path / "geometry.json"
    geometry.write_text("{}")
    destination = tmp_path / "artifacts/candidate"
    with pytest.raises(ValueError, match="native input digest mismatch"):
        generate_context_frame_candidates(
            tmp_path, destination, product, geometry, "a" * 64, "b" * 64
        )
    assert not destination.exists()


def test_context_identity_keeps_source_null_separate_from_zero() -> None:
    assert record_digest({"native_value": None}) != record_digest({"native_value": 0})
