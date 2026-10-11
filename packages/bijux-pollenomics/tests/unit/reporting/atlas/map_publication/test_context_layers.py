from __future__ import annotations

import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from bijux_pollenomics.reporting.context import (
    RAA_ATLAS_INPUT_STATUS_FILENAME,
    build_context_layers,
    build_raa_atlas_input_status,
)
from bijux_pollenomics.reporting.context.raa import (
    RAA_V018_DENSITY_SHA256,
    RAA_V018_METADATA_SHA256,
)
from bijux_pollenomics.reporting.geography import build_published_geography_plan

from .support import MapPublicationTestCase


class ContextLayerPublicationTests(MapPublicationTestCase):
    def test_context_layers_withhold_nordic_only_overlays_from_broader_scopes(
        self,
    ) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway"))
        world_scope = plan.world_scope
        nordic_scope = next(
            scope for scope in plan.regional_scopes if scope.key == "nordic"
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "world-output").mkdir(parents=True, exist_ok=True)
            (root / "nordic-output").mkdir(parents=True, exist_ok=True)
            self._write_point_geojson(
                root
                / "landclim"
                / "normalized"
                / "nordic_pollen_site_sequences.geojson",
                layer_key="landclim-sites",
                layer_label="LandClim pollen sequences",
            )
            self._write_polygon_geojson(
                root
                / "boundaries"
                / "normalized"
                / "nordic_country_boundaries.geojson",
                layer_key="country-boundaries",
                layer_label="Country boundaries",
            )

            world_point_layers, world_polygon_layers, _ = build_context_layers(
                samples=(),
                version="v66",
                output_dir=root / "world-output",
                context_root=root,
                geography_scope=world_scope,
            )
            nordic_point_layers, nordic_polygon_layers, _ = build_context_layers(
                samples=(),
                version="v66",
                output_dir=root / "nordic-output",
                context_root=root,
                geography_scope=nordic_scope,
            )

        self.assertEqual([layer["key"] for layer in world_point_layers], ["aadr"])
        self.assertEqual(
            [layer["key"] for layer in world_polygon_layers], ["country-boundaries"]
        )
        self.assertEqual(
            [layer["key"] for layer in nordic_point_layers],
            ["aadr", "landclim-sites"],
        )
        self.assertEqual(
            [layer["key"] for layer in nordic_polygon_layers],
            ["country-boundaries"],
        )

    def test_retained_raa_density_is_default_display_only_degraded_context(
        self,
    ) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway"))
        nordic_scope = next(
            scope for scope in plan.regional_scopes if scope.key == "nordic"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "nordic-output"
            output.mkdir()
            self._write_json(
                root / "raa/normalized/sweden_archaeology_layer.json",
                {
                    "counts": {
                        "all_published_sites": 761917,
                        "fornlamning": 318265,
                    }
                },
            )
            self._write_json(
                root / "raa/normalized/sweden_archaeology_density.geojson",
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
                            "properties": {"country": "Sweden", "count": 339412},
                        }
                    ],
                },
            )

            def retained_hash(path: Path) -> str:
                if path.name == "sweden_archaeology_layer.json":
                    return RAA_V018_METADATA_SHA256
                if path.name == "sweden_archaeology_density.geojson":
                    return RAA_V018_DENSITY_SHA256
                raise AssertionError(path)

            with patch(
                "bijux_pollenomics.reporting.context.raa._file_sha256",
                side_effect=retained_hash,
            ):
                _, polygon_layers, extra_artifacts = build_context_layers(
                    samples=(),
                    version="v66",
                    output_dir=output,
                    context_root=root,
                    geography_scope=nordic_scope,
                )

            status = json.loads(
                (output / RAA_ATLAS_INPUT_STATUS_FILENAME).read_text(encoding="utf-8")
            )
            staged_names = {name for _, name in extra_artifacts}

        layer = next(
            layer for layer in polygon_layers if layer["key"] == "raa-archaeology"
        )
        self.assertTrue(layer["default_enabled"])
        self.assertEqual(layer["authority_status"], "degraded")
        self.assertFalse(layer["source_authority_admitted"])
        self.assertEqual(
            layer["retained_surface_status"], "retained_historical_context"
        )
        self.assertEqual(layer["contribution_role"], "display_only")
        self.assertFalse(layer["candidate_ranking_eligible"])
        self.assertFalse(layer["scientific_classification_eligible"])
        self.assertFalse(layer["scientific_selection_enabled"])
        self.assertEqual(layer["propagation_status"], "refused")
        self.assertEqual(layer["edge_count"], 0)
        self.assertFalse(layer["applies_time_filter"])
        self.assertIn("degraded historical context", layer["description"])
        self.assertEqual(
            layer["display_warning_codes"],
            ["retained_density_metadata_count_mismatch"],
        )
        self.assertEqual(
            layer["density_count_accounting"],
            {
                "status": "observed_retained_normalized_pair",
                "density_feature_count": 1,
                "density_cell_count_sum": 339412,
                "metadata_fornlamning_count": 318265,
                "difference": 21147,
                "reconciled": False,
            },
        )
        self.assertIn("339,412 summed cell counts", layer["density_count_label"])
        self.assertIn("318,265 metadata", layer["density_count_label"])
        self.assertEqual(status["atlas_input_status"], "degraded")
        self.assertEqual(
            status["reason_codes"],
            [
                "missing_raw_inventory",
                "missing_raw_summary",
                "missing_scientific_review",
            ],
        )
        self.assertEqual(status["geometry_publication"]["status"], "retained_context")
        self.assertEqual(
            status["geometry_publication"]["default_map_state"],
            "enabled_degraded_context",
        )
        self.assertTrue(status["geometry_publication"]["default_enabled"])
        self.assertEqual(
            status["geometry_publication"]["warning_codes"],
            ["retained_density_metadata_count_mismatch"],
        )
        self.assertEqual(status["retained_context_identity"]["status"], "exact_v0.1.8")
        self.assertFalse(
            status["geometry_publication"]["retained_density_is_authoritative"]
        )
        self.assertEqual(status["country_scope"]["Sweden"], "source_coverage")
        self.assertEqual(status["country_scope"]["Norway"], "outside_source_scope")
        self.assertEqual(
            status["country_source_coverage"]["Sweden"],
            {
                "availability_status": "available_collected",
                "lifecycle_status": "refused",
                "fact_basis": "governed_assignment",
            },
        )
        self.assertEqual(
            status["country_source_coverage"]["Norway"]["availability_status"],
            "not_applicable",
        )
        self.assertNotIn(
            status["atlas_input_status"],
            {
                row["availability_status"]
                for row in status["country_source_coverage"].values()
            },
        )
        self.assertEqual(len(status["inputs"]["normalized_density"]["sha256"]), 64)
        self.assertIn("sweden_archaeology_layer.json", staged_names)
        self.assertIn(RAA_ATLAS_INPUT_STATUS_FILENAME, staged_names)
        self.assertIn("sweden_archaeology_density.geojson", staged_names)

    def test_substituted_retained_raa_pair_is_withheld(self) -> None:
        plan = build_published_geography_plan(("Sweden",))
        nordic_scope = next(
            scope for scope in plan.regional_scopes if scope.key == "nordic"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "nordic-output"
            output.mkdir()
            self._write_json(
                root / "raa/normalized/sweden_archaeology_layer.json",
                {"counts": {"fornlamning": 1}},
            )
            self._write_json(
                root / "raa/normalized/sweden_archaeology_density.geojson",
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": None,
                            "properties": {"country": "Sweden", "count": 1},
                        }
                    ],
                },
            )

            _, polygon_layers, extra_artifacts = build_context_layers(
                samples=(),
                version="v66",
                output_dir=output,
                context_root=root,
                geography_scope=nordic_scope,
            )
            status = json.loads(
                (output / RAA_ATLAS_INPUT_STATUS_FILENAME).read_text(encoding="utf-8")
            )

        self.assertNotIn("raa-archaeology", {layer["key"] for layer in polygon_layers})
        self.assertEqual(status["atlas_input_status"], "degraded")
        self.assertEqual(status["retained_context_identity"]["status"], "substituted")
        self.assertEqual(status["geometry_publication"]["status"], "withheld")
        self.assertFalse(status["geometry_publication"]["default_enabled"])
        self.assertIn(
            "retained_context_identity_mismatch",
            status["geometry_publication"]["warning_codes"],
        )
        self.assertNotIn(
            "sweden_archaeology_density.geojson",
            {name for _, name in extra_artifacts},
        )

    def test_reconciled_reviewed_raa_density_is_default_enabled(self) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway"))
        nordic_scope = next(
            scope for scope in plan.regional_scopes if scope.key == "nordic"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "nordic-output"
            output.mkdir()
            self._write_reconciled_raa_fixture(root)

            _, polygon_layers, extra_artifacts = build_context_layers(
                samples=(),
                version="v66",
                output_dir=output,
                context_root=root,
                geography_scope=nordic_scope,
            )
            status = json.loads(
                (output / RAA_ATLAS_INPUT_STATUS_FILENAME).read_text(encoding="utf-8")
            )
            staged_names = {name for _, name in extra_artifacts}

        layer = next(
            layer for layer in polygon_layers if layer["key"] == "raa-archaeology"
        )
        self.assertTrue(layer["default_enabled"])
        self.assertEqual(status["atlas_input_status"], "admitted")
        self.assertEqual(status["reason_codes"], [])
        self.assertEqual(status["geometry_publication"]["status"], "published")
        self.assertEqual(status["authority_counts"]["heritage_site_count"], 1)
        self.assertEqual(
            status["country_source_coverage"]["Sweden"]["lifecycle_status"],
            "admitted",
        )
        self.assertIn("sweden_archaeology_density.geojson", staged_names)

    def test_absent_raa_inputs_have_refused_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status = build_raa_atlas_input_status(Path(tmp))

        geometry_publication = status["geometry_publication"]
        inputs = status["inputs"]
        self.assertIsInstance(geometry_publication, dict)
        self.assertIsInstance(inputs, dict)
        assert isinstance(geometry_publication, dict)
        assert isinstance(inputs, dict)
        self.assertEqual(status["atlas_input_status"], "refused")
        self.assertEqual(geometry_publication["status"], "withheld")
        self.assertTrue(
            all(isinstance(row, dict) and not row["present"] for row in inputs.values())
        )

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def _write_reconciled_raa_fixture(self, root: Path) -> None:
        raw_feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [18.0, 57.0]},
            "properties": {
                "lamningsnummer": "A",
                "antikvariskbedomningtyp_namn": "Fornlämning",
            },
        }
        self._write_json(
            root / "raa/raw/publicerade_lamningar_centrumpunkt.geojson",
            {
                "type": "FeatureCollection",
                "features": [raw_feature],
                "numberMatched": 1,
            },
        )
        self._write_json(
            root / "raa/raw/publicerade_lamningar_centrumpunkt_summary.json",
            {
                "archived_feature_count": 1,
                "heritage_site_count": 1,
                "number_matched": 1,
                "identified_feature_count": 1,
                "heritage_or_possible_site_count": 1,
            },
        )
        self._write_json(
            root / "raa/normalized/sweden_archaeology_layer.json",
            {
                "counts": {
                    "all_published_sites": 1,
                    "fornlamning": 1,
                    "fornlamning_or_possible": 1,
                },
                "density_feature_count": 1,
            },
        )
        self._write_json(
            root / "raa/normalized/sweden_archaeology_density.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [17.0, 57.0],
                                    [18.0, 57.0],
                                    [18.0, 58.0],
                                    [17.0, 58.0],
                                    [17.0, 57.0],
                                ]
                            ],
                        },
                        "properties": {"country": "Sweden", "count": 1},
                    }
                ],
            },
        )
        self._write_json(
            root / "raa/review/spatiotemporal_review.json",
            {"release_status": "accepted", "reviewer_id": "qualified-reviewer"},
        )
