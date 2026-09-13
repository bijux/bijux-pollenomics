from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import cast
import unittest
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.raa.collection import (
    build_raa_density_geojson,
    collect_raa_data,
    count_raa_features,
    fetch_raa_feature_inventory,
    fetch_raa_feature_page,
)

GeoJsonFeature = dict[str, object]
GeoJsonCollection = dict[str, list[GeoJsonFeature] | str]


class RaaDataTests(unittest.TestCase):
    def test_count_and_density_are_derived_from_archived_features(self) -> None:
        feature_inventory = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [18.2, 57.4]},
                    "properties": {
                        "lamningsnummer": "A",
                        "antikvariskbedomningtyp_namn": "Fornlämning",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [18.8, 57.7]},
                    "properties": {
                        "lamningsnummer": "B",
                        "antikvariskbedomningtyp_namn": "Fornlämning",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [19.1, 58.3]},
                    "properties": {
                        "lamningsnummer": "C",
                        "antikvariskbedomningtyp_namn": "Möjlig fornlämning",
                    },
                },
            ],
        }
        sweden_boundary = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [17.0, 57.0],
                                [20.0, 57.0],
                                [20.0, 59.0],
                                [17.0, 59.0],
                                [17.0, 57.0],
                            ]
                        ],
                    },
                    "properties": {},
                }
            ],
        }

        density = build_raa_density_geojson(
            feature_inventory=feature_inventory, sweden_boundary=sweden_boundary
        )
        density_features = cast(
            list[GeoJsonFeature], cast(GeoJsonCollection, density)["features"]
        )

        self.assertEqual(count_raa_features(feature_inventory), 3)
        self.assertEqual(
            count_raa_features(feature_inventory, heritage_statuses={"Fornlämning"}), 2
        )
        self.assertEqual(
            count_raa_features(
                feature_inventory,
                heritage_statuses={"Fornlämning", "Möjlig fornlämning"},
            ),
            3,
        )
        self.assertEqual(len(density_features), 1)
        properties = cast(dict[str, object], density_features[0]["properties"])
        self.assertEqual(properties["count"], 2)

    def test_fetch_raa_feature_page_uses_explicit_sort_key(self) -> None:
        with patch(
            "bijux_pollenomics.collection.sources.raa.collection.fetch_text",
            return_value=json.dumps({"type": "FeatureCollection", "features": []}),
        ) as fetch_text:
            fetch_raa_feature_page(start_index=0)

        self.assertEqual(
            fetch_text.call_args.kwargs["params"]["sortBy"], "lamningsnummer"
        )

    def test_fetch_raa_feature_inventory_paginates_all_features(self) -> None:
        pages = [
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [18.0, 57.0]},
                        "properties": {"lamningsnummer": "A"},
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [19.0, 58.0]},
                        "properties": {"lamningsnummer": "B"},
                    },
                ],
                "numberMatched": 3,
                "timeStamp": "2026-03-31T11:00:00Z",
            },
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [20.0, 59.0]},
                        "properties": {"lamningsnummer": "C"},
                    },
                ],
                "numberMatched": 3,
                "timeStamp": "2026-03-31T11:00:01Z",
            },
        ]

        with patch(
            "bijux_pollenomics.collection.sources.raa.collection.fetch_raa_feature_page",
            side_effect=pages,
        ):
            payload = fetch_raa_feature_inventory()
        payload_features = cast(
            list[GeoJsonFeature], cast(GeoJsonCollection, payload)["features"]
        )

        self.assertEqual(len(payload_features), 3)
        self.assertEqual(payload["numberMatched"], 3)

    def test_fetch_raa_feature_inventory_rejects_short_paging(self) -> None:
        pages = [
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [18.0, 57.0]},
                        "properties": {"lamningsnummer": "A"},
                    },
                ],
                "numberMatched": 2,
            },
            {
                "type": "FeatureCollection",
                "features": [],
                "numberMatched": 2,
            },
        ]

        with (
            patch(
                "bijux_pollenomics.collection.sources.raa.collection.fetch_raa_feature_page",
                side_effect=pages,
            ),
            self.assertRaisesRegex(ValueError, "paging ended before"),
        ):
            fetch_raa_feature_inventory()

    def test_collect_raa_data_writes_raw_feature_archive(self) -> None:
        feature_inventory = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [18.0, 57.0]},
                    "properties": {
                        "lamningsnummer": "A",
                        "antikvariskbedomningtyp_namn": "Fornlämning",
                    },
                }
            ],
            "numberMatched": 1,
        }
        metadata = {
            "capabilities_xml": "<wfs />",
            "schema_xml": "<schema />",
            "domain_payload": {"domains": []},
            "layer_metadata": {
                "counts": {
                    "all_published_sites": 1,
                    "fornlamning": 1,
                }
            },
            "density_geojson": {"type": "FeatureCollection", "features": []},
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "raa"
            with (
                patch(
                    "bijux_pollenomics.collection.sources.raa.collection.fetch_raa_feature_inventory",
                    return_value=feature_inventory,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.raa.collection.fetch_raa_archaeology_metadata",
                    return_value=metadata,
                ) as fetch_metadata,
            ):
                report = collect_raa_data(
                    output_root, country_boundaries={"Sweden": {"features": []}}
                )

            raw_payload = json.loads(report.raw_points_path.read_text(encoding="utf-8"))
            summary_payload = json.loads(
                (
                    output_root
                    / "raw"
                    / "publicerade_lamningar_centrumpunkt_summary.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(raw_payload["numberMatched"], 1)
        self.assertEqual(
            raw_payload["features"][0]["properties"]["lamningsnummer"], "A"
        )
        self.assertEqual(summary_payload["archived_feature_count"], 1)
        self.assertEqual(summary_payload["heritage_site_count"], 1)
        self.assertEqual(
            fetch_metadata.call_args.kwargs["feature_inventory"], feature_inventory
        )


if __name__ == "__main__":
    unittest.main()


@pytest.mark.parametrize("later_population", [1, 3, None, True, 2.0])
def test_paging_refuses_population_drift_or_malformed_declaration(
    later_population: object,
) -> None:
    pages = [
        {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {"lamningsnummer": "A"}}],
            "numberMatched": 2,
        },
        {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {"lamningsnummer": "B"}}],
            "numberMatched": later_population,
        },
    ]
    with (
        patch(
            "bijux_pollenomics.collection.sources.raa.collection.fetch_raa_feature_page",
            side_effect=pages,
        ),
        pytest.raises(ValueError, match="population"),
    ):
        fetch_raa_feature_inventory()


def test_empty_capture_requires_declared_zero_and_preserves_it() -> None:
    page = {"type": "FeatureCollection", "features": [], "numberMatched": 0}
    with patch(
        "bijux_pollenomics.collection.sources.raa.collection.fetch_raa_feature_page",
        return_value=page,
    ) as fetch:
        inventory = fetch_raa_feature_inventory()
    assert inventory["numberMatched"] == 0
    assert inventory["features"] == []
    fetch.assert_called_once()


def test_capture_does_not_replace_declared_zero_with_nonempty_observed_rows() -> None:
    page = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"lamningsnummer": "A"}}],
        "numberMatched": 0,
    }
    with (
        patch(
            "bijux_pollenomics.collection.sources.raa.collection.fetch_raa_feature_page",
            return_value=page,
        ),
        pytest.raises(ValueError, match="count mismatch"),
    ):
        fetch_raa_feature_inventory()


@pytest.mark.parametrize(
    "text",
    [
        '{"type":"FeatureCollection","features":[],"numberMatched":999,"numberMatched":0}',
        '{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"lamningsnummer":"A","lamningsnummer":"B"}}],"numberMatched":1}',
        '{"type":"FeatureCollection","features":[],"numberMatched":NaN}',
        '{"type":"FeatureCollection","features":[],"numberMatched":1e400}',
    ],
)
def test_wfs_text_is_validated_before_claims_are_collapsed(text: str) -> None:
    with (
        patch(
            "bijux_pollenomics.collection.sources.raa.collection.fetch_text",
            return_value=text,
        ),
        pytest.raises(ValueError),
    ):
        fetch_raa_feature_page(start_index=0)
