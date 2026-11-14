from __future__ import annotations

import json

import pytest

from bijux_pollenomics.collection.sources.neotoma.site_inventory.connected_resources import (
    build_neotoma_connected_resources,
    parse_neotoma_site_datasets,
)


def body(rows: list[dict[str, object]]) -> bytes:
    return json.dumps({"status": "success", "data": rows}).encode()


def test_connected_resources_distinguishes_same_unit_and_other_unit_types() -> None:
    source = body(
        [
            {
                "site": {
                    "siteid": 12,
                    "collectionunitid": 100,
                    "unittype": "Core",
                    "handle": "ABBO",
                    "datasets": [
                        {"datasetid": 201, "datasettype": "pollen"},
                        {
                            "datasetid": 202,
                            "datasettype": "geochronologic",
                            "notes": None,
                        },
                        {"datasetid": 203, "datasettype": "loss-on-ignition"},
                    ],
                }
            },
            {
                "site": {
                    "siteid": 12,
                    "collectionunitid": 101,
                    "unittype": "Trap",
                    "datasets": [{"datasetid": 204, "datasettype": "pollen trap"}],
                }
            },
        ]
    )
    result = build_neotoma_connected_resources(
        site_ids=(12,),
        retained_units={100: 12},
        retained_datasets={201: 100},
        responses={12: source},
    )
    rows = result["datasets"]
    assert [(row["dataset_id"], row["relationship"]) for row in rows] == [
        (201, "retained_dataset"),
        (202, "additional_dataset_same_unit"),
        (203, "additional_dataset_same_unit"),
        (204, "dataset_other_unit"),
    ]
    assert rows[1]["source_payload"] == {
        "datasetid": 202,
        "datasettype": "geochronologic",
        "notes": None,
    }
    assert result["collection_units"][1]["source_payload"]["unittype"] == "Trap"
    assert result["scientific_admission"] == "not_asserted"


def test_connected_resources_preserves_successful_empty_as_observed_metadata() -> None:
    result = build_neotoma_connected_resources(
        site_ids=(12,),
        retained_units={100: 12},
        retained_datasets={201: 100},
        responses={12: body([])},
    )
    assert result["successful_empty_site_ids"] == [12]
    assert result["unobserved_retained_dataset_ids"] == [201]
    assert result["absence_certified"] is False


@pytest.mark.parametrize(
    "rows",
    [
        [{"site": {"siteid": 999, "collectionunitid": 100, "datasets": []}}],
        [{"site": {"siteid": True, "collectionunitid": 100, "datasets": []}}],
        [{"site": {"siteid": 12, "collectionunitid": 0, "datasets": []}}],
        [
            {
                "site": {
                    "siteid": 12,
                    "collectionunitid": 100,
                    "datasets": [
                        {"datasetid": 201, "datasettype": "pollen"},
                        {"datasetid": 201, "datasettype": "pollen"},
                    ],
                }
            }
        ],
        [
            {"site": {"siteid": 12, "collectionunitid": 100, "datasets": []}},
            {"site": {"siteid": 12, "collectionunitid": 100, "datasets": []}},
        ],
    ],
)
def test_connected_site_metadata_refuses_wrong_invalid_or_duplicate_identity(
    rows: list[dict[str, object]],
) -> None:
    with pytest.raises(ValueError):
        parse_neotoma_site_datasets(12, body(rows))


def test_connected_resources_requires_exact_response_closure() -> None:
    with pytest.raises(ValueError, match="closure"):
        build_neotoma_connected_resources(
            site_ids=(12, 13),
            retained_units={},
            retained_datasets={},
            responses={12: body([])},
        )


def test_connected_resources_refuses_one_dataset_under_two_current_units() -> None:
    rows: list[dict[str, object]] = [
        {
            "site": {
                "siteid": 12,
                "collectionunitid": unit,
                "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
            }
        }
        for unit in (100, 101)
    ]
    with pytest.raises(ValueError, match="dataset|parent"):
        build_neotoma_connected_resources(
            site_ids=(12,),
            retained_units={},
            retained_datasets={},
            responses={12: body(rows)},
        )
