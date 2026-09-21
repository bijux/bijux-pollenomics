from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.reporting.map_publication import (
    build_map_point_traceability,
    render_map_point_traceability_markdown,
)
from bijux_pollenomics.reporting.models import MultiCountryMapReport

from .support import MapPublicationTestCase


class PointTraceabilityPublicationTests(MapPublicationTestCase):
    def test_point_traceability_normalizes_layer_metadata_without_data_loss(
        self,
    ) -> None:
        report = MultiCountryMapReport(
            title="Nordic Evidence Surface",
            slug="nordic",
            version="v66",
            generated_on="2026-05-09",
            countries=("Sweden", "Norway"),
            country_sample_counts={"Sweden": 1, "Norway": 1},
            total_unique_samples=2,
            output_dir=Path("/tmp/docs/report/regions/nordic"),
            scope_key="nordic",
            scope_label="Nordic",
            scope_kind="region",
            parent_scope_key="europe_plus",
        )
        payload = build_map_point_traceability(
            report=report,
            point_layers=[
                {
                    "key": "zebra",
                    "label": "Zebra layer",
                    "group": "animal-evidence",
                    "source_name": "Example source",
                    "traceability_artifact": "zebra.json",
                    "traceability_reference": "https://example.test/zebra",
                    "features": [
                        {
                            "evidence_row_id": "zebra:1",
                            "title": "Zebra one",
                            "country": "Sweden",
                            "source_url": "https://example.test/zebra/1",
                            "species_latin_name": "Equus quagga",
                            "animal_scope": "comparator",
                            "coordinate_confidence": "exact",
                        }
                    ],
                },
                {
                    "key": "aadr",
                    "label": "Human samples",
                    "source_name": "AADR",
                    "features": [
                        {"title": "Sample one", "country": "Norway"},
                        {"title": "Sample two", "country": "Sweden"},
                    ],
                },
            ],
        )

        self.assertEqual(payload["schema_version"], "map-point-traceability.v2")
        self.assertEqual(payload["scope_key"], "nordic")
        self.assertEqual(payload["row_count"], 3)
        self.assertEqual(payload["layer_counts"], {"aadr": 2, "zebra": 1})
        layers = payload["layers"]
        self.assertIsInstance(layers, list)
        self.assertEqual([layer["layer_key"] for layer in layers], ["aadr", "zebra"])
        self.assertEqual(layers[0]["row_count"], 2)
        self.assertEqual(
            layers[0]["field_counts"],
            {
                "title": 2,
                "country": 2,
                "source_url": 0,
                "species_latin_name": 0,
                "animal_scope": 0,
                "coordinate_confidence": 0,
            },
        )
        self.assertNotIn("source_url", layers[0]["records"][0])
        self.assertEqual(layers[1]["records"][0]["record_id"], "zebra:1")
        self.assertNotIn("layer_key", layers[1]["records"][0])
        self.assertNotIn("scope_key", layers[1]["records"][0])

        markdown = render_map_point_traceability_markdown(payload)
        self.assertIn("Visible point rows: `3`", markdown)
        self.assertIn("| Zebra layer | zebra:1 | Sweden | zebra.json |", markdown)

        with self.assertRaisesRegex(ValueError, "layer key is duplicated"):
            build_map_point_traceability(
                report=report,
                point_layers=[
                    {"key": "aadr", "features": []},
                    {"key": "aadr", "features": []},
                ],
            )
