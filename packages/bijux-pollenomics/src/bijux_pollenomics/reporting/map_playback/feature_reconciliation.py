"""Reconcile source-chronology facet metadata to published features."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import cast

from .contracts import PlaybackContractError


def _closed_interval(row: Mapping[str, object]) -> tuple[float | int, float | int]:
    younger = row.get("time_min_bp")
    older = row.get("time_max_bp")
    if (
        isinstance(younger, bool)
        or not isinstance(younger, (float, int))
        or isinstance(older, bool)
        or not isinstance(older, (float, int))
        or not math.isfinite(float(younger))
        or not math.isfinite(float(older))
        or younger < 0
        or younger > older
    ):
        raise PlaybackContractError(
            "source chronology facet lacks a valid [younger_bp, older_bp] extent"
        )
    return younger, older


def _rows_by_value(value: object) -> dict[str, Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise PlaybackContractError("source chronology facet rows must be a sequence")
    rows: dict[str, Mapping[str, object]] = {}
    for candidate in value:
        if not isinstance(candidate, Mapping):
            raise PlaybackContractError("source chronology facet row must be an object")
        row = cast(Mapping[str, object], candidate)
        key = _required_text(row, "value")
        if key in rows:
            raise PlaybackContractError(f"duplicate source chronology facet: {key}")
        rows[key] = row
    return rows


def _required_text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PlaybackContractError(f"source chronology {field} must not be empty")
    return value


def _positive_int(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PlaybackContractError(f"source chronology {field} must be positive")
    return value


def _required_mapping(row: Mapping[str, object], field: str) -> Mapping[str, object]:
    value = row.get(field)
    if not isinstance(value, Mapping):
        raise PlaybackContractError(f"source chronology {field} must be an object")
    return value


def _rows_by_key(value: object, *, field: str) -> dict[str, Mapping[str, object]]:
    if not isinstance(value, list):
        raise PlaybackContractError("source chronology preset rows must be a list")
    rows: dict[str, Mapping[str, object]] = {}
    for value_row in value:
        if not isinstance(value_row, Mapping):
            raise PlaybackContractError(
                "source chronology preset row must be an object"
            )
        key = _required_text(value_row, field)
        if key in rows:
            raise PlaybackContractError("source chronology preset key is duplicated")
        rows[key] = value_row
    return rows


def reconcile_facet_metadata_to_features(
    layer: Mapping[str, object], facets: Mapping[str, object]
) -> None:
    raw_features = layer.get("features")
    if not isinstance(raw_features, list) or any(
        not isinstance(feature, Mapping) for feature in raw_features
    ):
        raise PlaybackContractError(
            "source chronology playback requires its exact layer features"
        )
    features = cast(list[Mapping[str, object]], raw_features)
    if layer.get("count") != len(features):
        raise PlaybackContractError(
            "source chronology layer count differs from features"
        )
    expected_level = _required_text(layer, "node_level")
    source_snapshot_id = _required_text(layer, "source_snapshot_id")
    build_id = _required_text(layer, "build_id")
    node_ids: set[str] = set()
    for feature in features:
        node_id = _required_text(feature, "node_id")
        if node_id in node_ids:
            raise PlaybackContractError("source chronology feature node is duplicated")
        node_ids.add(node_id)
        if (
            feature.get("node_level") != expected_level
            or feature.get("source_snapshot_id") != source_snapshot_id
            or feature.get("build_id") != build_id
            or feature.get("semantic_role") != "source_chronology_context"
            or feature.get("propagation_eligible") is not False
        ):
            raise PlaybackContractError("source chronology feature identity differs")
        _feature_interval(feature)
        _positive_int(feature, "observation_denominator")
        _required_text(feature, "record_id")
        _required_text(feature, "country")
    _compare_feature_aggregate(facets, features)
    _compare_source_unit_counts(facets, features)

    if expected_level == "source_ecological_code":
        for row in _rows_by_value(facets.get("source_ecological_codes")).values():
            source_code = _required_text(row, "source_code")
            _compare_feature_aggregate(
                row,
                [
                    feature
                    for feature in features
                    if feature.get("source_ecological_code") == source_code
                ],
            )
    if expected_level == "source_taxon":
        taxon_rows = _rows_by_value(facets.get("source_taxa"))
        for feature_key, row in taxon_rows.items():
            _compare_feature_aggregate(
                row,
                [
                    feature
                    for feature in features
                    if feature.get("feature_key") == feature_key
                ],
            )
        accountability = _required_mapping(facets, "source_label_preset_accountability")
        for row in _rows_by_key(accountability.get("presets"), field="key").values():
            member_ids = _integer_ids(row.get("member_taxon_ids"))
            _compare_feature_aggregate(
                row,
                [
                    feature
                    for feature in features
                    if type(feature.get("source_taxon_id")) is int
                    and feature.get("source_taxon_id") in member_ids
                ],
            )
        union = _required_mapping(accountability, "union")
        union_ids = _integer_ids(union.get("member_taxon_ids"))
        _compare_feature_aggregate(
            union,
            [
                feature
                for feature in features
                if type(feature.get("source_taxon_id")) is int
                and feature.get("source_taxon_id") in union_ids
            ],
        )


def _compare_source_unit_counts(
    facets: Mapping[str, object], features: Sequence[Mapping[str, object]]
) -> None:
    declared = _rows_by_value(facets.get("source_unit_counts"))
    feature_units = {_required_text(feature, "source_unit") for feature in features}
    if set(declared) != feature_units:
        raise PlaybackContractError("source chronology source-unit inventory differs")
    for source_unit, row in declared.items():
        selected = [
            feature for feature in features if feature.get("source_unit") == source_unit
        ]
        expected = {
            "node_count": len(selected),
            "observation_denominator": sum(
                _positive_int(feature, "observation_denominator")
                for feature in selected
            ),
        }
        if any(row.get(field) != value for field, value in expected.items()):
            raise PlaybackContractError(
                "source chronology source-unit feature aggregate differs"
            )


def _integer_ids(value: object) -> frozenset[int]:
    if not isinstance(value, list) or any(type(item) is not int for item in value):
        raise PlaybackContractError("source-label preset member IDs are invalid")
    ids = frozenset(cast(list[int], value))
    if len(ids) != len(value):
        raise PlaybackContractError("source-label preset member IDs are duplicated")
    return ids


def _compare_feature_aggregate(
    declared: Mapping[str, object], features: Sequence[Mapping[str, object]]
) -> None:
    expected = _feature_aggregate(features)
    if any(declared.get(field) != value for field, value in expected.items()):
        raise PlaybackContractError("source chronology feature aggregate differs")
    raw_countries = declared.get("country_counts")
    if not isinstance(raw_countries, list):
        raise PlaybackContractError("source chronology country rows are unavailable")
    country_names = ("Sweden", "Denmark", "Norway", "Finland")
    for row, country in zip(raw_countries, country_names, strict=True):
        if not isinstance(row, Mapping) or row.get("value") != country:
            raise PlaybackContractError("source chronology country identity differs")
        country_expected = _feature_aggregate(
            [feature for feature in features if feature.get("country") == country]
        )
        if any(row.get(field) != value for field, value in country_expected.items()):
            raise PlaybackContractError(
                "source chronology country feature aggregate differs"
            )


def _feature_aggregate(
    features: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    if not features:
        return {
            "site_count": 0,
            "node_count": 0,
            "observation_denominator": 0,
            "time_min_bp": None,
            "time_max_bp": None,
        }
    intervals = [_feature_interval(feature) for feature in features]
    return {
        "site_count": len(
            {_required_text(feature, "record_id") for feature in features}
        ),
        "node_count": len(features),
        "observation_denominator": sum(
            _positive_int(feature, "observation_denominator") for feature in features
        ),
        "time_min_bp": min(interval[0] for interval in intervals),
        "time_max_bp": max(interval[1] for interval in intervals),
    }


def _feature_interval(
    feature: Mapping[str, object],
) -> tuple[float | int, float | int]:
    return _closed_interval(
        {
            "time_min_bp": feature.get("time_start_bp"),
            "time_max_bp": feature.get("time_end_bp"),
        }
    )


__all__ = ["reconcile_facet_metadata_to_features"]
