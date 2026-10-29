"""Project genuine normalized-source census metadata without publishing source records."""

from __future__ import annotations

import json
from typing import Any

from ..svar import _exact, _object, _require

FIELDS = (
    "record_id",
    "sjoid",
    "sj_uuid",
    "sj_vatten_id",
    "area_km2",
    "country",
    "layer_key",
)


def redact_joins(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove native IDs and full-source indices; preserve all 99 typed field checks."""
    _exact(len(rows), 99)
    result = []
    for index, row in enumerate(rows):
        _require(
            set(row)
            == {
                "subset_index",
                "record_id",
                "full_source_matches",
                "match_count",
                "geometry_role",
            },
            "Native join metadata fields differ",
        )
        _require(
            type(row["record_id"]) is str and bool(row["record_id"]),
            "Native subset locator missing",
        )
        _exact(row["subset_index"], index)
        _exact(row["match_count"], 1)
        matches = row["full_source_matches"]
        _require(
            type(matches) is list and len(matches) == 1,
            "Unique native full-source match required",
        )
        match = _object(matches[0])
        _require(
            set(match) == {"full_source_index", "field_agreement"}
            and type(match["full_source_index"]) is int
            and 0 <= match["full_source_index"] < 40565,
            "Native full-source index differs",
        )
        result.append(
            {
                "subset_index": index,
                "match_count": 1,
                "full_source_matches": [{"field_agreement": match["field_agreement"]}],
            }
        )
    validate_public_joins(result)
    return result


def validate_public_joins(rows: list[dict[str, Any]]) -> None:
    _exact(len(rows), 99)
    for index, row in enumerate(rows):
        _require(
            set(row) == {"subset_index", "match_count", "full_source_matches"},
            "Public join leaks or omits fields",
        )
        _exact(row["subset_index"], index)
        _exact(row["match_count"], 1)
        matches = row["full_source_matches"]
        _require(
            type(matches) is list
            and len(matches) == 1
            and set(matches[0]) == {"field_agreement"},
            "Public join match structure differs",
        )
        agreement = _object(matches[0]["field_agreement"])
        _exact(set(agreement), set(FIELDS))
        for field in FIELDS:
            _exact(
                agreement[field],
                {
                    "subset_present": True,
                    "full_present": True,
                    "typed_value_equal": True,
                },
            )


def public_census(
    census: dict[str, Any], review: dict[str, Any], joins: list[dict[str, Any]]
) -> dict[str, Any]:
    """Construct an aggregate witness; native geometry, property and identity values stay private."""
    validate_public_joins(joins)
    _require(
        review.get("complete_independent_source_and_typed_ledger_equal") is True,
        "Full independent source comparison absent",
    )
    _exact(review.get("actual_exit"), 0)
    _exact(census.get("candidate"), review.get("candidate"))
    _exact(census.get("measured_source"), review.get("measured_source"))
    _exact(census.get("feature_ledger"), review.get("feature_ledger"))
    source = _object(census.get("source"))
    _require(
        source.get("sha256")
        == "d9a1943d1a35e7ab6d48e06156fef625e7c62c8bc410cecf9d8f592ccb07dfd8",
        "Exact normalized source identity differs",
    )
    _exact(source.get("bytes"), 261041034)
    measured = _object(census.get("measured_source"))
    _exact(measured.get("feature_array_items"), 40565)
    _exact(measured.get("proper_Feature_objects"), 40565)
    _exact(measured.get("missing_or_null_geometry"), 0)
    geometry = {}
    for raw, count in _object(measured.get("geometry_type_counts")).items():
        key = json.loads(raw)
        _require(
            type(key) is list
            and len(key) == 2
            and key[0] == "string"
            and type(key[1]) is str,
            "Native geometry label differs",
        )
        _require(
            type(count) is int and count >= 0, "Native geometry count type differs"
        )
        geometry[key[1]] = count
    _exact(geometry, {"Polygon": 37516, "MultiPolygon": 3049})
    identity = _object(measured.get("native_identity_field_counts"))
    _exact(set(identity), {"record_id", "sjoid", "sj_uuid", "sj_vatten_id"})
    for field in identity:
        usable = 40565 if field in {"record_id", "sjoid"} else 40564
        _exact(
            identity[field],
            {
                "nonempty_string_values": usable,
                "distinct_values": usable,
                "duplicate_occurrences": 0,
                "duplicate_values": 0,
                "missing_or_null_or_empty_or_non_string": 40565 - usable,
            },
        )
    properties = _object(measured.get("property_native_type_counts"))
    _exact(
        set(properties),
        {
            "source",
            "layer_key",
            "layer_label",
            "category",
            "country",
            "record_id",
            "name",
            "register_name",
            "water_name",
            "fallback_name",
            "sjoid",
            "sj_uuid",
            "sj_vatten_id",
            "district",
            "water_surface_elevation_m",
            "area_km2",
            "lake_name_status",
            "source_url",
            "geometry_type",
        },
    )
    for field, kinds in properties.items():
        _require(
            type(field) is str and type(kinds) is dict,
            "Native property type census differs",
        )
        _require(
            all(type(count) is int and count >= 0 for count in kinds.values())
            and sum(kinds.values()) == 40565,
            "Native property count types or denominator differ",
        )
    _exact(measured.get("non_object_properties"), 0)
    for field in (
        "original_review_population_membership_available",
        "identity_of_the_42_difference_established",
        "raw_WFS_export_link_qualified",
        "provider_units_CRS_or_effective_basin_area_qualified",
        "source_dates_are_chronology",
        "rights_or_human_review_admitted",
        "ranking_admitted",
    ):
        _require(review.get(field) is False, "Census scientific/source scope expanded")
    _exact(review.get("current_ranked_candidate_count"), 0)
    _exact(review.get("retained_export_population_claim"), 40565)
    _exact(review.get("retained_review_population_claim"), 40523)
    _exact(review.get("measured_minus_export_claim"), 0)
    _exact(review.get("measured_minus_review_claim"), 42)
    return {
        "schema_version": "svar-normalized-feature-aggregate.v1",
        "original_execution_candidate": census["candidate"],
        "source_identity": {
            "role": "privately_retained_normalized_SVAR_export",
            "sha256": source["sha256"],
            "bytes": source["bytes"],
            "source_payload_published": False,
        },
        "measured_features": {
            "feature_items": 40565,
            "proper_Feature_objects": 40565,
            "missing_or_null_geometry": 0,
            "geometry_types": geometry,
            "native_identity_field_counts": measured["native_identity_field_counts"],
            "property_native_type_counts": measured["property_native_type_counts"],
            "non_object_properties": measured["non_object_properties"],
        },
        "subset_agreement": {
            "subset_rows": 99,
            "rows_with_exactly_one_full_match": 99,
            "join_fields": list(FIELDS),
            "typed_agreement_counts": dict.fromkeys(FIELDS, 99),
            "Point_vs_full_geometry_equivalence_claimed": False,
            "nearest_pollen_selection_rule_reexecuted": False,
        },
        "population_comparison": {
            "retained_export_claim": 40565,
            "retained_review_claim": 40523,
            "measured_minus_export": 0,
            "measured_minus_review": 42,
            "original_review_full_population_membership_available": False,
            "identities_or_cause_of_42_difference_established": False,
        },
        "scope": {
            "raw_WFS_export_parity": False,
            "provider_units_or_CRS_qualified": False,
            "geometry_topology_or_effective_basin_area_qualified": False,
            "source_dates_are_lake_chronology": False,
            "rights_or_qualified_human_review_admitted": False,
            "ranking_admitted": False,
            "current_ranked_candidates": 0,
            "raw_properties_geometry_or_native_ID_values_published": False,
            "new_metadata_native_execution_claimed": False,
        },
        "private_observation_identities": {
            "feature_ledger": {
                key: census["feature_ledger"][key] for key in ("sha256", "bytes")
            },
            "native_subset_join_metadata": {
                key: review["subset_joins"][key] for key in ("sha256", "bytes")
            },
            "payloads_published": False,
        },
        "interpretation": "Descriptive measurements of the retained normalized file and exact seven-field checks for all99public subset records. Matching source counts do not recover the old40523identity inventory, establish a provider capture/rights route or admit a governing registry/ranking. Normalized field labels are not independent provider-unit or CRS qualification.",
    }
