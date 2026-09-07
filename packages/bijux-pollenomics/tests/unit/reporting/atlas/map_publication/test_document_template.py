from __future__ import annotations

import json
import shutil
import subprocess

from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.template import (
    MAP_DOCUMENT_TEMPLATE,
    load_map_document_template,
)
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy

from .support import MapPublicationTestCase


class MapDocumentTemplateTests(MapPublicationTestCase):
    def test_map_document_template_is_loaded_from_the_packaged_resource(self) -> None:
        self.assertEqual(load_map_document_template(), MAP_DOCUMENT_TEMPLATE)
        self.assertTrue(MAP_DOCUMENT_TEMPLATE.startswith('\n<html lang="en">'))
        self.assertTrue(MAP_DOCUMENT_TEMPLATE.endswith("</html>\n"))

    def test_browser_time_parser_distinguishes_null_from_zero(self) -> None:
        self.assertIn(
            "value === null || value === undefined || typeof value === 'boolean'",
            MAP_DOCUMENT_TEMPLATE,
        )
        self.assertIn(
            "Number.isFinite(numeric) ? numeric : null", MAP_DOCUMENT_TEMPLATE
        )
        self.assertIn("if (startDeclared || endDeclared)", MAP_DOCUMENT_TEMPLATE)
        self.assertIn(
            "start === null || end === null || start > end", MAP_DOCUMENT_TEMPLATE
        )
        self.assertIn(
            "if (admission.status === 'refused') return '';", MAP_DOCUMENT_TEMPLATE
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
        self.assertIn('id="view-controls"', MAP_DOCUMENT_TEMPLATE)
        self.assertIn('id="basemap-switch"', MAP_DOCUMENT_TEMPLATE)
        self.assertIn('aria-controls="basemap-switch"', MAP_DOCUMENT_TEMPLATE)
        self.assertIn("OpenStreetMap · no key", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("OpenTopoMap · no key", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("Offline · no tiles", MAP_DOCUMENT_TEMPLATE)
        self.assertNotIn(
            ".basemap-copy {\n        display: none;", MAP_DOCUMENT_TEMPLATE
        )
        self.assertIn("viewControls.open = true", MAP_DOCUMENT_TEMPLATE)
        self.assertIn(
            "activeButton.focus({ preventScroll: true })", MAP_DOCUMENT_TEMPLATE
        )
        self.assertIn(
            "grid-template-columns: minmax(0, 1fr);",
            MAP_DOCUMENT_TEMPLATE,
        )
        self.assertIn("overflow-x: hidden;", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("overflow-wrap: anywhere;", MAP_DOCUMENT_TEMPLATE)
        self.assertIn(
            ".control-group-body {\n        display: grid;\n        gap: 10px;\n        min-width: 0;\n        width: 100%;",
            MAP_DOCUMENT_TEMPLATE,
        )
        self.assertIn(
            "basemapSwitch.scrollIntoView({\n          block: 'nearest',\n          behavior: 'auto',",
            MAP_DOCUMENT_TEMPLATE,
        )
        self.assertIn(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png", MAP_DOCUMENT_TEMPLATE
        )
        self.assertNotIn("basemaps.cartocdn.com", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("zoomControl: false, maxZoom: 20", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("const MAX_PROVIDER_TILE_ERRORS = 3", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("layer.on('tileerror'", MAP_DOCUMENT_TEMPLATE)
        self.assertIn("failedBasemaps.add(name)", MAP_DOCUMENT_TEMPLATE)
        self.assertIn(
            "Basemap degraded: no basemap. Evidence data unaffected.",
            MAP_DOCUMENT_TEMPLATE,
        )
        self.assertNotIn("apiKey", MAP_DOCUMENT_TEMPLATE)

    def test_map_document_has_no_favicon_network_dependency(self) -> None:
        self.assertIn('<link rel="icon" href="data:,">', MAP_DOCUMENT_TEMPLATE)

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

        self.assertIn("const DEFAULT_BASEMAP = 'street';", html)
        self.assertIn("currentBasemap !== DEFAULT_BASEMAP", html)
        self.assertIn("setBasemap(DEFAULT_BASEMAP, { manual: true })", html)
        self.assertNotIn("currentBasemap !== 'street'", html)
        self.assertIn("for (const candidate of BASEMAP_FALLBACK_ORDER)", html)
        self.assertIn("if (candidate === name) continue;", html)
        self.assertNotIn("Open prepared chronology playback", html)

    def test_nordic_map_links_to_prepared_chronology_playback(self) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway"))
        nordic_policy = resolve_map_scope_policy(
            next(scope for scope in plan.regional_scopes if scope.key == "nordic")
        )

        html = render_multi_country_map_html(
            "Nordic",
            "test-build",
            "2026-09-06",
            ("Sweden", "Norway"),
            nordic_policy,
            [],
            [],
            "../../../assets",
        )

        self.assertIn('href="../../../public/nordic-atlas/chronology-playback/"', html)
        self.assertIn("Open prepared chronology playback", html)
        self.assertNotIn("__CHRONOLOGY_PLAYBACK_ACTION__", html)
