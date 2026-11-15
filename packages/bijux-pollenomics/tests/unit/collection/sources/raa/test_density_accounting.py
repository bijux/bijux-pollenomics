"""Source identities account for every included and excluded density record."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.raa.outputs import build_raa_density_geojson


def _polygon(west: float, south: float, east: float, north: float) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [[west, south], [east, south], [east, north], [west, north], [west, south]]
        ],
    }


def _boundary() -> dict[str, Any]:
    polygon = _polygon(18, 57, 18.9, 57.9)
    polygon["coordinates"].append(
        [[18.1, 57.1], [18.3, 57.1], [18.3, 57.3], [18.1, 57.3], [18.1, 57.1]]
    )
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": polygon, "properties": {}}],
    }


def _inventory() -> dict[str, Any]:
    values = [
        ("inside-a", {"type": "Point", "coordinates": [18.6, 57.6]}, "Fornlämning"),
        ("000inside-b", {"type": "Point", "coordinates": [18.7, 57.7]}, "Fornlämning"),
        ("hole", {"type": "Point", "coordinates": [18.2, 57.2]}, "Fornlämning"),
        ("outside", {"type": "Point", "coordinates": [18.95, 57.2]}, "Fornlämning"),
        ("missing", None, "Fornlämning"),
        ("empty", {"type": "Point", "coordinates": []}, "Fornlämning"),
        (
            "different-class",
            {"type": "Point", "coordinates": [18.6, 57.6]},
            "Möjlig fornlämning",
        ),
    ]
    return {
        "type": "FeatureCollection",
        "numberMatched": len(values),
        "features": [
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "lamningsnummer": key,
                    "antikvariskbedomningtyp_namn": status,
                },
            }
            for key, geometry, status in values
        ],
    }


def _membership(inventory: dict[str, Any], boundary: dict[str, Any]) -> Any:
    from bijux_pollenomics.collection.sources.raa.density_membership import (
        build_raa_density_membership,
    )

    return build_raa_density_membership(
        feature_inventory=inventory, sweden_boundary=boundary
    )


def test_every_original_source_id_has_one_conserved_disposition() -> None:
    inventory, boundary = _inventory(), _boundary()
    originals = deepcopy((inventory, boundary))
    ledger = _membership(inventory, boundary)
    assert ledger["schema_version"] == "raa-density-membership-v1"
    records = {record["native_id"]: record for record in ledger["records"]}
    assert {key: record["disposition"] for key, record in records.items()} == {
        "inside-a": "included",
        "000inside-b": "included",
        "hole": "excluded_outside_boundary",
        "outside": "excluded_outside_boundary",
        "missing": "unusable_geometry",
        "empty": "unusable_geometry",
        "different-class": "excluded_source_class",
    }
    assert len(ledger["records"]) == 7
    assert ledger["counts"] == {
        "archived": 7,
        "heritage_source_class": 6,
        "included": 2,
        "excluded_source_class": 1,
        "excluded_outside_boundary": 2,
        "unusable_geometry": 2,
    }
    assert (
        sum(
            ledger["counts"][key]
            for key in (
                "included",
                "excluded_source_class",
                "excluded_outside_boundary",
                "unusable_geometry",
            )
        )
        == 7
    )
    assert ledger["cells"] == [{"longitude": 18, "latitude": 57, "count": 2}]
    assert records["inside-a"]["grid_cell"] == [18, 57]
    assert records["inside-a"]["representative_point"] == [18.6, 57.6]
    assert records["missing"]["reason_code"] == "missing_geometry"
    assert records["empty"]["reason_code"] == "unrepresentable_geometry"
    assert records["different-class"]["source_status"] == "Möjlig fornlämning"
    assert ledger["scientific_admission"] is False
    assert ledger["raw_inventory_identity"] is None
    assert (inventory, boundary) == originals
    density = build_raa_density_geojson(
        feature_inventory=inventory, sweden_boundary=boundary
    )
    assert sum(
        feature["properties"]["count"]
        for feature in cast(list[dict[str, Any]], density["features"])
    ) == len(
        [record for record in ledger["records"] if record["disposition"] == "included"]
    )


def test_payload_identities_are_canonical_semantics_not_raw_byte_claims() -> None:
    inventory, boundary = _inventory(), _boundary()
    ledger = _membership(inventory, boundary)
    for field, payload in [
        ("feature_inventory_sha256", inventory),
        ("sweden_boundary_sha256", boundary),
    ]:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        assert (
            ledger["semantic_payload_identity"][field]
            == hashlib.sha256(encoded).hexdigest()
        )
        assert (
            hashlib.sha256(json.dumps(payload, indent=2).encode()).hexdigest()
            != ledger["semantic_payload_identity"][field]
        )
    assert (
        ledger["semantic_payload_identity"]["canonicalization"]
        == "json-sorted-keys-utf8-compact-v1"
    )
    reordered = dict(reversed(list(inventory.items())))
    assert _membership(reordered, boundary) == ledger
    changed = deepcopy(inventory)
    changed["features"][0]["geometry"]["coordinates"][0] = 18.65
    assert (
        _membership(changed, boundary)["semantic_payload_identity"]
        != ledger["semantic_payload_identity"]
    )


@pytest.mark.parametrize(
    "geometry",
    [
        _polygon(18.5, 57.5, 18.6, 57.6),
        {"type": "LineString", "coordinates": [[18.5, 57.5], [18.6, 57.6]]},
    ],
)
def test_nonpoint_representative_geometry_keeps_source_type_and_method(
    geometry: object,
) -> None:
    inventory = _inventory()
    inventory["features"] = inventory["features"][:1]
    inventory["numberMatched"] = 1
    inventory["features"][0]["geometry"] = geometry
    record = _membership(inventory, _boundary())["records"][0]
    assert record["disposition"] == "included"
    assert record["geometry_type"] in {"Polygon", "LineString"}
    assert record["representative_method"] == "geometry_to_representative_point"


@pytest.mark.parametrize("empty", [True, False])
def test_empty_or_all_excluded_populations_remain_explicit(empty: bool) -> None:
    inventory = _inventory()
    inventory["features"] = [] if empty else inventory["features"][2:]
    inventory["numberMatched"] = len(inventory["features"])
    ledger = _membership(inventory, _boundary())
    assert ledger["counts"]["archived"] == (0 if empty else 5)
    assert ledger["counts"]["included"] == 0
    assert ledger["cells"] == []
    assert len(ledger["records"]) == (0 if empty else 5)


@pytest.mark.parametrize("identifier", [None, "", 1, True, "inside-a"])
def test_density_cannot_drop_or_merge_invalid_native_identities(
    identifier: object,
) -> None:
    inventory = _inventory()
    inventory["features"][1]["properties"]["lamningsnummer"] = identifier
    with pytest.raises(ValueError, match="lamningsnummer"):
        build_raa_density_geojson(
            feature_inventory=inventory, sweden_boundary=_boundary()
        )


def test_density_does_not_treat_unknown_population_as_complete() -> None:
    inventory = _inventory()
    del inventory["numberMatched"]
    with pytest.raises(ValueError, match="population"):
        build_raa_density_geojson(
            feature_inventory=inventory, sweden_boundary=_boundary()
        )


@pytest.mark.parametrize(
    "geometry",
    [
        [],
        {"type": "Point", "coordinates": "bad"},
        {"type": "Point", "coordinates": [10**400, 57.6]},
    ],
)
def test_unrepresentable_native_geometry_still_has_an_explicit_source_id_disposition(
    geometry: object,
) -> None:
    inventory = _inventory()
    inventory["features"][0]["geometry"] = geometry
    ledger = _membership(inventory, _boundary())
    record = next(row for row in ledger["records"] if row["native_id"] == "inside-a")
    assert record["disposition"] == "unusable_geometry"
    assert record["reason_code"] == "unrepresentable_geometry"
    assert ledger["counts"]["archived"] == len(ledger["records"]) == 7


def test_metadata_producer_and_public_density_share_membership_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.raa import outputs

    monkeypatch.setattr(outputs, "fetch_text", lambda *_args, **_kwargs: "<schema />")
    monkeypatch.setattr(
        outputs, "fetch_json", lambda *_args, **_kwargs: {"domains": []}
    )
    metadata = outputs.fetch_raa_archaeology_metadata(
        _inventory(), {"Sweden": _boundary()}
    )
    ledger = cast(dict[str, Any], metadata["density_membership"])
    assert ledger["counts"]["heritage_source_class"] == 6
    assert ledger["counts"]["included"] == 2
    density = cast(dict[str, Any], metadata["density_geojson"])
    assert sum(feature["properties"]["count"] for feature in density["features"]) == 2
    assert metadata["density_geojson"] == build_raa_density_geojson(
        feature_inventory=_inventory(), sweden_boundary=_boundary()
    )
    layer = cast(dict[str, Any], metadata["layer_metadata"])
    assert layer["counts"]["fornlamning"] == 6


@pytest.mark.parametrize(
    "geometry",
    [
        None,
        {"type": "Point", "coordinates": [18, 57]},
        {"type": "Polygon", "coordinates": []},
    ],
)
def test_unusable_boundary_does_not_turn_unknown_membership_into_exclusion(
    geometry: object,
) -> None:
    boundary = _boundary()
    boundary["features"][0]["geometry"] = geometry
    with pytest.raises(ValueError, match="boundary"):
        _membership(_inventory(), boundary)


@pytest.mark.parametrize(
    "field", ["feature_inventory_sha256", "sweden_boundary_sha256"]
)
def test_collector_refuses_a_membership_ledger_for_other_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    from bijux_pollenomics.collection.sources.raa import collection, outputs

    inventory, boundary = _inventory(), _boundary()
    monkeypatch.setattr(outputs, "fetch_text", lambda *_args, **_kwargs: "<schema />")
    monkeypatch.setattr(outputs, "fetch_json", lambda *_args, **_kwargs: {})
    metadata = outputs.fetch_raa_archaeology_metadata(inventory, {"Sweden": boundary})
    ledger = cast(dict[str, Any], metadata["density_membership"])
    ledger["semantic_payload_identity"][field] = "0" * 64
    monkeypatch.setattr(collection, "fetch_raa_feature_inventory", lambda: inventory)
    monkeypatch.setattr(
        collection, "fetch_raa_archaeology_metadata", lambda **_kwargs: metadata
    )
    with pytest.raises(ValueError, match="membership input identity differs"):
        collection.collect_raa_data(tmp_path, {"Sweden": boundary})
    assert not (
        tmp_path / "derived" / "sweden_archaeology_density_membership.json"
    ).exists()
