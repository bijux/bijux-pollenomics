from __future__ import annotations

from pathlib import Path
import tempfile

from bijux_pollenomics.reporting.context import build_context_layers
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

    def test_nordic_atlas_stages_complete_archaeology_discovery_surface(self) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway"))
        nordic_scope = next(
            scope for scope in plan.regional_scopes if scope.key == "nordic"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "nordic-output"
            output.mkdir()
            derived = root / "sead" / "derived"
            self._write_point_geojson(
                root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
                layer_key="sead-sites",
                layer_label="SEAD sites",
            )
            self._write_point_geojson(
                root / "sead" / "normalized" / "nordic_temporal_evidence.geojson",
                layer_key="sead-temporal-evidence",
                layer_label="SEAD temporal evidence",
                time_start_bp=1000,
            )
            self._write_point_geojson(
                derived / "sweden_archaeology_site_discovery.geojson",
                layer_key="sweden-archaeology-site-discovery",
                layer_label="Sweden archaeology site discovery",
                record_id="10:dating_range:7:discovery",
                time_start_bp=1000,
            )
            for name in (
                "sweden_archaeology_site_discovery.json",
                "sweden_archaeology_site_discovery.csv",
                "sweden_archaeology_site_discovery.md",
            ):
                (derived / name).write_text("governed companion\n", encoding="utf-8")

            point_layers, _, extra_artifacts = build_context_layers(
                samples=(),
                version="v66",
                output_dir=output,
                context_root=root,
                geography_scope=nordic_scope,
            )

            discovery = next(
                layer
                for layer in point_layers
                if layer["key"] == "sweden-archaeology-site-discovery"
            )
            staged_names = {name for _, name in extra_artifacts}
            features = discovery["features"]

            self.assertEqual(discovery["group"], "archaeology-discovery")
            self.assertTrue(discovery["applies_time_filter"])
            self.assertEqual(
                features[0]["evidence_row_id"],  # type: ignore[index]
                "10:dating_range:7:discovery",
            )
            self.assertIn("sead-sites", {layer["key"] for layer in point_layers})
            self.assertNotIn(
                "sead-temporal-evidence", {layer["key"] for layer in point_layers}
            )
            self.assertEqual(
                staged_names,
                {
                    "nordic_environmental_sites.geojson",
                    "sweden_archaeology_site_discovery.geojson",
                    "sweden_archaeology_site_discovery.json",
                    "sweden_archaeology_site_discovery.csv",
                    "sweden_archaeology_site_discovery.md",
                },
            )
            self.assertTrue(all((output / name).is_file() for name in staged_names))
