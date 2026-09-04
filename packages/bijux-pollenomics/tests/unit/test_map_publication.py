from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.context import build_context_layers
from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.state import build_map_document_state
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE
from bijux_pollenomics.reporting.map_publication import (
    build_map_publication_contract,
    resolve_map_scope_policy,
)
from bijux_pollenomics.reporting.models import MultiCountryMapReport


class MapPublicationUnitTests(unittest.TestCase):
    def test_scope_policies_keep_distinct_bounds_and_basemaps(self) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway", "Germany"))
        world_policy = resolve_map_scope_policy(plan.world_scope)
        europe_plus_policy = resolve_map_scope_policy(
            next(scope for scope in plan.regional_scopes if scope.key == "europe_plus")
        )
        nordic_policy = resolve_map_scope_policy(
            next(scope for scope in plan.regional_scopes if scope.key == "nordic")
        )

        self.assertEqual(world_policy.default_basemap, "voyager")
        self.assertEqual(europe_plus_policy.default_basemap, "light")
        self.assertEqual(nordic_policy.default_basemap, "voyager")
        self.assertLess(
            world_policy.minimum_bounds[0][1], europe_plus_policy.minimum_bounds[0][1]
        )
        self.assertLess(
            europe_plus_policy.minimum_bounds[0][1], nordic_policy.minimum_bounds[0][1]
        )

    def test_map_document_state_uses_scope_floor_bounds(self) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway"))
        world_policy = resolve_map_scope_policy(plan.world_scope)
        state = build_map_document_state(
            policy=world_policy,
            point_layers=[
                {
                    "features": [
                        {"latitude": 59.33, "longitude": 18.06},
                    ]
                }
            ],
            polygon_layers=[],
        )

        self.assertEqual(state.initial_diameter_km, world_policy.initial_diameter_km)
        self.assertLessEqual(state.bounds[0][1], world_policy.minimum_bounds[0][1])
        self.assertGreaterEqual(state.bounds[1][1], world_policy.minimum_bounds[1][1])

    def test_map_time_state_rejects_non_numeric_values_and_preserves_zero(self) -> None:
        plan = build_published_geography_plan(("Sweden",))
        policy = resolve_map_scope_policy(plan.world_scope)
        state = build_map_document_state(
            policy=policy,
            point_layers=[
                {
                    "features": [
                        {
                            "latitude": 59.33,
                            "longitude": 18.06,
                            "time_start_bp": None,
                            "time_end_bp": "",
                            "time_mean_bp": False,
                            "time_year_bp": "nan",
                        },
                        {
                            "latitude": 55.60,
                            "longitude": 13.00,
                            "time_start_bp": 0,
                            "time_end_bp": 100,
                        },
                    ]
                }
            ],
            polygon_layers=[],
        )

        self.assertTrue(state.has_time_data)
        self.assertEqual(state.time_min_bp, 0)
        self.assertEqual(state.time_max_bp, 100)

    def test_map_time_state_refuses_partial_or_reversed_intervals(self) -> None:
        policy = resolve_map_scope_policy(
            build_published_geography_plan(("Sweden",)).world_scope
        )
        state = build_map_document_state(
            policy=policy,
            point_layers=[
                {
                    "features": [
                        {"time_start_bp": 0, "time_mean_bp": 25},
                        {"time_start_bp": 100, "time_end_bp": 50},
                    ]
                }
            ],
            polygon_layers=[],
        )

        self.assertFalse(state.has_time_data)
        self.assertEqual((state.time_min_bp, state.time_max_bp), (0, 0))

    def test_browser_time_parser_distinguishes_null_from_zero(self) -> None:
        self.assertIn(
            "value === null || value === undefined || typeof value === 'boolean'",
            MAP_DOCUMENT_TEMPLATE,
        )
        self.assertIn("numeric >= 0", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("if (intervalDeclared)", MAP_DOCUMENT_TEMPLATE)
        self.assertIn(
            "start !== null && end !== null && start <= end", MAP_DOCUMENT_TEMPLATE
        )
        self.assertNotIn(
            "const start = Number(feature.time_start_bp)", MAP_DOCUMENT_TEMPLATE
        )

    def test_browser_time_parser_matches_server_interval_refusals(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required to verify browser semantics")
        block_start = MAP_DOCUMENT_TEMPLATE.index("function finiteTimeValue")
        block_end = MAP_DOCUMENT_TEMPLATE.index(
            "function pointFeatureInTimeWindow", block_start
        )
        parser_source = MAP_DOCUMENT_TEMPLATE[block_start:block_end]
        cases = [
            {"time_start_bp": 0, "time_end_bp": 100},
            {"time_start_bp": 0, "time_mean_bp": 25},
            {"time_start_bp": 100, "time_end_bp": 50},
            {"time_start_bp": -1, "time_end_bp": 50},
            {"time_mean_bp": 25},
            {"time_year_bp": -1},
        ]
        encoded_cases = json.dumps(cases)
        script = parser_source + (
            "\nconst cases = " + encoded_cases + "; console.log(JSON.stringify({"
            "windows: cases.map(featureTimeWindow), "
            "labels: cases.map((feature) => featureTimeLabel({"
            "...feature, time_label: 'source label'}))}));"
        )

        result = subprocess.run(
            [str(node), "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            json.loads(result.stdout)["windows"],
            [
                {"start": 0, "end": 100},
                None,
                None,
                None,
                {"start": 25, "end": 25},
                None,
            ],
        )
        self.assertEqual(
            json.loads(result.stdout)["labels"],
            ["source label", "", "", "", "source label", ""],
        )

    def test_basemap_failure_has_bounded_failover_and_tile_free_mode(self) -> None:
        self.assertIn('data-basemap="none"', MAP_DOCUMENT_TEMPLATE)
        self.assertIn("zoomControl: false, maxZoom: 20", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("const MAX_PROVIDER_TILE_ERRORS = 3", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("layer.on('tileerror'", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("failedBasemaps.add(name)", MAP_DOCUMENT_TEMPLATE)
        self.assertIn(
            "Basemap degraded: no basemap. Evidence data unaffected.",
            MAP_DOCUMENT_TEMPLATE,
        )
        self.assertNotIn("apiKey", MAP_DOCUMENT_TEMPLATE)

    def test_rendered_map_keeps_policy_default_and_complete_failover_order(
        self,
    ) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway", "Germany"))
        europe_plus_policy = resolve_map_scope_policy(
            next(scope for scope in plan.regional_scopes if scope.key == "europe_plus")
        )
        html = render_multi_country_map_html(
            "Europe Plus",
            "test-build",
            "2026-09-04",
            ("Sweden", "Norway", "Germany"),
            europe_plus_policy,
            [],
            [],
            "../../../assets",
        )

        self.assertIn("const DEFAULT_BASEMAP = 'light';", html)
        self.assertIn("currentBasemap !== DEFAULT_BASEMAP", html)
        self.assertIn("setBasemap(DEFAULT_BASEMAP, { manual: true })", html)
        self.assertNotIn("currentBasemap !== 'voyager'", html)
        self.assertIn("for (const candidate of BASEMAP_FALLBACK_ORDER)", html)
        self.assertIn("if (candidate === name) continue;", html)

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

    def test_map_publication_contract_distinguishes_layer_roles(self) -> None:
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
        policy = resolve_map_scope_policy(
            next(
                scope
                for scope in build_published_geography_plan(
                    ("Sweden", "Norway")
                ).regional_scopes
                if scope.key == "nordic"
            )
        )
        bundle_paths = build_atlas_bundle_paths(Path("/tmp/nordic"), "nordic", "v66")
        contract = build_map_publication_contract(
            report=report,
            policy=policy,
            point_layers=[
                {
                    "key": "aadr",
                    "label": "AADR-v66 aDNA samples",
                    "source_name": "Allen Ancient DNA Resource",
                    "coverage_label": "Country assignment follows the AADR political entity field.",
                    "count": 2,
                    "default_enabled": True,
                    "applies_country_filter": True,
                    "applies_time_filter": True,
                },
                {
                    "key": "landclim-sites",
                    "label": "LandClim pollen sequences",
                    "source_name": "LandClim",
                    "coverage_label": "Pollen sequences staged from the LandClim normalization bundle.",
                    "count": 1,
                    "default_enabled": True,
                    "applies_country_filter": True,
                    "applies_time_filter": False,
                },
            ],
            polygon_layers=[
                {
                    "key": "country-boundaries",
                    "label": "Country boundaries",
                    "source_name": "Natural Earth country boundaries",
                    "coverage_label": "Published country outlines used for framing and scope-aware map filtering.",
                    "count": 2,
                    "default_enabled": True,
                    "applies_country_filter": True,
                    "applies_time_filter": False,
                }
            ],
            countries=report.countries,
            map_html_name=bundle_paths.map_html_path.name,
            summary_json_name=bundle_paths.summary_json_path.name,
            traceability_json_name=bundle_paths.map_point_traceability_json_path.name,
        )

        self.assertEqual(contract["role_counts"]["shared_world_scale_layer"], 1)
        self.assertEqual(contract["role_counts"]["region_filtered_layer"], 1)
        self.assertEqual(contract["role_counts"]["scope_specific_overlay"], 1)

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
                features[0]["evidence_row_id"], "10:dating_range:7:discovery"
            )
            self.assertNotIn("sead-sites", {layer["key"] for layer in point_layers})
            self.assertNotIn(
                "sead-temporal-evidence", {layer["key"] for layer in point_layers}
            )
            self.assertEqual(
                staged_names,
                {
                    "sweden_archaeology_site_discovery.geojson",
                    "sweden_archaeology_site_discovery.json",
                    "sweden_archaeology_site_discovery.csv",
                    "sweden_archaeology_site_discovery.md",
                },
            )
            self.assertTrue(all((output / name).is_file() for name in staged_names))

    @staticmethod
    def _write_point_geojson(
        path: Path,
        *,
        layer_key: str,
        layer_label: str,
        record_id: str = "",
        time_start_bp: int | None = None,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [18.06, 59.33],
                            },
                            "properties": {
                                "layer_key": layer_key,
                                "layer_label": layer_label,
                                "name": "Example point",
                                "category": "Context",
                                "subtitle": "Example context layer",
                                "country": "Sweden",
                                "record_id": record_id,
                                "time_start_bp": time_start_bp,
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _write_polygon_geojson(path: Path, *, layer_key: str, layer_label: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [10.0, 55.0],
                                        [11.0, 55.0],
                                        [11.0, 56.0],
                                        [10.0, 56.0],
                                        [10.0, 55.0],
                                    ]
                                ],
                            },
                            "properties": {
                                "layer_key": layer_key,
                                "layer_label": layer_label,
                                "subtitle": "Example polygon layer",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
