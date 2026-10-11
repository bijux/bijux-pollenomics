from __future__ import annotations

import pytest

from bijux_pollenomics.collection.sources.raa.inventory import (
    declared_population,
    decode_source_object,
    native_feature_ids,
    source_features,
    validate_inventory,
)
from bijux_pollenomics.collection.sources.raa.outputs import build_raa_inventory_summary


def _feature(identifier: object = "A") -> dict[str, object]:
    return {"type": "Feature", "properties": {"lamningsnummer": identifier}}


@pytest.mark.parametrize(
    "value",
    [None, True, False, -1, 1.0, 1.5, "unknown", "", "01", "+1", " 1", "１", [], {}],
)
def test_population_refuses_coercion_or_unknown(value: object) -> None:
    with pytest.raises(ValueError, match="population"):
        declared_population({"numberMatched": value})


@pytest.mark.parametrize("value", [0, 1, 2**53 + 1, "0", "1", "9007199254740993"])
def test_explicit_wfs_population_keeps_exact_integer(value: int | str) -> None:
    assert declared_population({"numberMatched": value}) == int(value)


def test_absent_population_is_not_measured_from_rows() -> None:
    with pytest.raises(ValueError, match="missing"):
        validate_inventory({"type": "FeatureCollection", "features": [_feature()]})


def test_zero_population_is_not_replaced_by_other_alias() -> None:
    with pytest.raises(ValueError, match="disagree"):
        declared_population({"numberMatched": 0, "totalFeatures": 1})
    assert declared_population({"numberMatched": 0, "totalFeatures": "0"}) == 0
    assert declared_population({"totalFeatures": "1"}) == 1


@pytest.mark.parametrize("value", [None, "", " ", False, True, 1, 1.0, [], {}])
def test_native_id_requires_nonblank_source_string(value: object) -> None:
    with pytest.raises(ValueError, match="lamningsnummer"):
        validate_inventory(
            {
                "type": "FeatureCollection",
                "features": [_feature(value)],
                "numberMatched": 1,
            }
        )


def test_duplicate_id_refuses_and_unicode_identity_remains_exact() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        native_feature_ids([_feature("Å"), _feature("Å")])
    assert native_feature_ids([_feature("Å"), _feature("Å")]) == ["Å", "Å"]


@pytest.mark.parametrize(
    "features", [None, {}, "", [None], [True], [{}], [{"type": "GeometryCollection"}]]
)
def test_no_feature_member_is_silently_skipped(features: object) -> None:
    with pytest.raises(ValueError):
        source_features({"type": "FeatureCollection", "features": features})


def test_declared_empty_inventory_reconciles_all_summary_denominators() -> None:
    inventory = {"type": "FeatureCollection", "features": [], "numberMatched": 0}
    assert validate_inventory(inventory) == []
    summary = build_raa_inventory_summary(inventory)
    for key in (
        "number_matched",
        "archived_feature_count",
        "identified_feature_count",
        "heritage_site_count",
        "heritage_or_possible_site_count",
    ):
        assert summary[key] == 0


def test_summary_refuses_missing_id_instead_of_reporting_partial_identity_as_complete() -> (
    None
):
    with pytest.raises(ValueError, match="lamningsnummer"):
        build_raa_inventory_summary(
            {
                "type": "FeatureCollection",
                "features": [_feature(None)],
                "numberMatched": 1,
            }
        )


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e400", "-1e400"])
def test_nonfinite_json_never_enters_source_object(token: str) -> None:
    with pytest.raises(ValueError, match="nonfinite"):
        decode_source_object('{"nested":{"value":' + token + "}}")


def test_json_native_large_integer_zero_and_unicode_are_preserved() -> None:
    assert decode_source_object(
        '{"Å":9007199254740993,"zero":0,"fraction":0.5,"missing":null}'
    ) == {"Å": 9007199254740993, "zero": 0, "fraction": 0.5, "missing": None}
