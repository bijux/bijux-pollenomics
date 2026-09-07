"""External context-layer projection coverage."""

from __future__ import annotations

import unittest
from typing import cast

from bijux_pollenomics.reporting.context import (
    build_external_point_layer,
    build_external_polygon_layer,
)


class ExternalLayerTests(unittest.TestCase):
    def test_external_null_interval_preserves_valid_standalone_mean(self) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [18, 59]},
                        "properties": {
                            "layer_key": "mean-only",
                            "layer_label": "Mean-only chronology",
                            "time_start_bp": None,
                            "time_end_bp": None,
                            "time_mean_bp": 123,
                        },
                    }
                ],
            }
        )

        feature = cast(list[dict[str, object]], layer["features"])[0]
        self.assertTrue(layer["applies_time_filter"])
        self.assertIsNone(feature["time_start_bp"])
        self.assertIsNone(feature["time_end_bp"])
        self.assertEqual(feature["time_mean_bp"], 123)

    def test_external_small_negative_and_nonfinite_bp_never_round_into_time(
        self,
    ) -> None:
        for value in (-0.4, "-0.4", float("inf"), "inf"):
            with self.subTest(value=value):
                layer = build_external_point_layer(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [18, 59],
                                },
                                "properties": {
                                    "layer_key": "invalid-mean",
                                    "layer_label": "Invalid mean",
                                    "time_mean_bp": value,
                                },
                            }
                        ],
                    }
                )

                feature = cast(list[dict[str, object]], layer["features"])[0]
                semantics = cast(dict[str, object], feature["temporal_semantics"])
                self.assertFalse(layer["applies_time_filter"])
                self.assertIsNone(feature["time_mean_bp"])
                self.assertEqual(semantics["comparability_posture"], "refused")
                self.assertIn(
                    semantics["refusal_reason_code"], {"negative_bp", "non_finite"}
                )

    def test_external_invalid_declared_mean_does_not_replace_it_with_midpoint(
        self,
    ) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [18, 59]},
                        "properties": {
                            "layer_key": "invalid-mean",
                            "layer_label": "Invalid mean",
                            "time_start_bp": 100,
                            "time_end_bp": 200,
                            "time_mean_bp": -0.4,
                            "temporal_semantics": {
                                "comparability_posture": "numeric_interval"
                            },
                        },
                    }
                ],
            }
        )

        feature = cast(list[dict[str, object]], layer["features"])[0]
        semantics = cast(dict[str, object], feature["temporal_semantics"])
        self.assertEqual(feature["time_start_bp"], 100)
        self.assertEqual(feature["time_end_bp"], 200)
        self.assertIsNone(feature["time_mean_bp"])
        self.assertIn("negative_bp", semantics["uncertainty_notes"])

    def test_external_negative_bp_remains_context_without_numeric_admission(
        self,
    ) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-70.7, -33.9],
                        },
                        "properties": {
                            "layer_key": "future-context",
                            "layer_label": "Future-dated source context",
                            "time_start_bp": -10,
                            "time_end_bp": 20,
                            "time_mean_bp": 5,
                            "time_label": "source interval -10 to 20 BP",
                            "temporal_semantics": {
                                "comparability_posture": "numeric_interval",
                                "time_start_bp": -10,
                                "time_end_bp": 20,
                                "time_mean_bp": 5,
                            },
                        },
                    }
                ],
            }
        )

        self.assertFalse(layer["applies_time_filter"])
        feature = cast(list[dict[str, object]], layer["features"])[0]
        self.assertEqual((feature["longitude"], feature["latitude"]), (-70.7, -33.9))
        self.assertIsNone(feature["time_start_bp"])
        self.assertIsNone(feature["time_end_bp"])
        self.assertIsNone(feature["time_mean_bp"])
        semantics = cast(dict[str, object], feature["temporal_semantics"])
        self.assertEqual(semantics["comparability_posture"], "refused")
        self.assertEqual(semantics["uncertainty_notes"], ["negative_bp"])

    def test_external_point_layers_enable_time_filter_when_temporal_properties_exist(
        self,
    ) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                        "properties": {
                            "layer_key": "landclim-sites",
                            "layer_label": "LandClim pollen sites",
                            "country": "Sweden",
                            "name": "Lake One",
                            "category": "Pollen sequence",
                            "time_start_bp": 0,
                            "time_end_bp": 700,
                        },
                    }
                ],
            }
        )

        self.assertTrue(layer["applies_time_filter"])
        self.assertTrue(layer["default_enabled"])
        layer_features = cast(list[dict[str, object]], layer["features"])
        self.assertEqual(layer_features[0]["time_start_bp"], 0)
        self.assertEqual(layer_features[0]["time_end_bp"], 700)
        self.assertEqual(layer_features[0]["time_mean_bp"], 350)
        self.assertEqual(layer_features[0]["time_label"], "0-700 BP")
        self.assertEqual(
            layer_features[0]["temporal_window_label"],
            "Recent and historical (0-1000 BP)",
        )

    def test_external_temporal_sead_layer_is_time_filterable_by_default(self) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                        "properties": {
                            "layer_key": "sead-temporal-evidence",
                            "layer_label": "SEAD temporal evidence",
                            "country": "Sweden",
                            "site_uuid": "site-uuid-1",
                            "name": "Dated chronology",
                            "category": "Environmental archaeology chronology",
                            "time_start_bp": 1200,
                            "time_end_bp": 1800,
                        },
                    }
                ],
            }
        )

        self.assertTrue(layer["applies_time_filter"])
        self.assertTrue(layer["default_enabled"])
        layer_features = cast(list[dict[str, object]], layer["features"])
        self.assertEqual(layer_features[0]["time_start_bp"], 1200)
        self.assertEqual(layer_features[0]["time_end_bp"], 1800)
        self.assertEqual(layer_features[0]["site_uuid"], "site-uuid-1")

    def test_external_point_layers_do_not_treat_context_labels_as_numeric_time(
        self,
    ) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                        "properties": {
                            "layer_key": "sead-sites",
                            "layer_label": "SEAD environmental sites",
                            "country": "Sweden",
                            "name": "Undated site",
                            "category": "Environmental archive",
                            "time_label": "Relative chronology available",
                            "temporal_semantics": {
                                "comparability_posture": "context_only",
                                "temporal_window_key": "unresolved",
                                "temporal_window_label": "Unresolved",
                            },
                        },
                    }
                ],
            }
        )

        self.assertFalse(layer["applies_time_filter"])

    def test_external_point_layers_enable_time_filter_for_mixed_sead_chronology(
        self,
    ) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                        "properties": {
                            "layer_key": "sead-sites",
                            "layer_label": "SEAD environmental sites",
                            "country": "Sweden",
                            "name": "Dated site",
                            "category": "Environmental archive",
                            "time_start_bp": 1200,
                            "time_end_bp": 1800,
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [18.0, 60.0]},
                        "properties": {
                            "layer_key": "sead-sites",
                            "layer_label": "SEAD environmental sites",
                            "country": "Sweden",
                            "name": "Undated site",
                            "category": "Environmental archive",
                            "temporal_semantics": {
                                "comparability_posture": "unresolved",
                                "temporal_window_key": "unresolved",
                                "temporal_window_label": "Unresolved",
                            },
                        },
                    },
                ],
            }
        )

        self.assertTrue(layer["applies_time_filter"])
        self.assertFalse(layer["default_enabled"])

    def test_external_polygon_layers_enable_time_filter_when_temporal_properties_exist(
        self,
    ) -> None:
        layer = build_external_polygon_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [16.0, 58.0],
                                    [17.0, 58.0],
                                    [17.0, 59.0],
                                    [16.0, 59.0],
                                    [16.0, 58.0],
                                ]
                            ],
                        },
                        "properties": {
                            "layer_key": "landclim-reveals-grid",
                            "layer_label": "LandClim REVEALS grid cells",
                            "country": "Sweden",
                            "time_start_bp": 100,
                            "time_end_bp": 1200,
                        },
                    }
                ],
            }
        )

        self.assertTrue(layer["applies_time_filter"])
