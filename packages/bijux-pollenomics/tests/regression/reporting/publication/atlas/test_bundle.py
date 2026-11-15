from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

import pytest

from bijux_pollenomics.reporting import (
    generate_multi_country_map,
)

from ..fixtures.aadr import write_anno
from ..static_assets import read_static_atlas_runtime

pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_multi_country_map_writes_shared_map_with_country_toggles(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                ],
            )
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "FI1\tFI1\tFinland_Group\tTurku\tFinland\t60.4518\t22.2666\tPaperC\t2020\t700 CE\t1250\tHO\tU",
                ],
            )

            report = generate_multi_country_map(
                version_dir=root,
                countries=["Sweden", "Norway", "Finland"],
                output_dir=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
            )

            self.assertEqual(report.total_unique_samples, 3)
            self.assertTrue((output / "README.md").exists())
            self.assertTrue((output / "nordic-atlas_map.html").exists())
            self.assertTrue((output / "nordic-atlas_samples.geojson").exists())
            self.assertTrue((output / "nordic-atlas_candidate_sites.csv").exists())
            self.assertTrue((output / "nordic-atlas_candidate_sites.json").exists())
            self.assertTrue((output / "nordic-atlas_candidate_sites.md").exists())
            self.assertTrue(
                (output / "nordic-atlas_candidate_site_sensitivity.json").exists()
            )
            self.assertTrue(
                (output / "nordic-atlas_candidate_site_sensitivity.md").exists()
            )
            self.assertTrue(
                (
                    output / "nordic-atlas_candidate_ranking_engine_manifest.json"
                ).exists()
            )
            self.assertTrue((output / "nordic-atlas_evidence_surface.json").exists())
            self.assertTrue((output / "nordic-atlas_evidence_surface.md").exists())
            self.assertTrue((output / "nordic-atlas_scientific_review.json").exists())
            self.assertTrue((output / "nordic-atlas_scientific_review.md").exists())
            self.assertTrue((output / "nordic-atlas_bundle.json").exists())
            self.assertTrue((output / "nordic-atlas_summary.json").exists())
            self.assertTrue(
                (output / "_map_assets" / "leaflet" / "leaflet.js").exists()
            )

            map_html = (output / "nordic-atlas_map.html").read_text(encoding="utf-8")
            runtime_text = read_static_atlas_runtime(output, "nordic-atlas")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            candidate_csv_bytes = (
                output / "nordic-atlas_candidate_sites.csv"
            ).read_bytes()
            point_traceability_text = (
                output / "nordic-atlas_point_traceability.md"
            ).read_text(encoding="utf-8")
            self.assertNotIn(b"\r\n", candidate_csv_bytes)
            self.assertNotIn(" \n", point_traceability_text)
            self.assertIn("Country Filters", map_html)
            self.assertIn("country-checkbox", runtime_text)
            countries = re.search(
                r"^\s*const COUNTRIES = (.+);$", runtime_text, re.MULTILINE
            )
            self.assertIsNotNone(countries)
            assert countries is not None
            self.assertCountEqual(
                json.loads(countries.group(1)), ["Sweden", "Norway", "Finland"]
            )
            self.assertIn("markerClusterGroup", runtime_text)
            self.assertIn("Nordic Evidence Atlas", map_html)
            self.assertIn("Restore defaults", map_html)
            self.assertIn("time-start-slider", map_html)
            self.assertIn("time-interval-slider", map_html)
            self.assertIn("100 years", map_html)
            self.assertIn("time_year_bp", runtime_text)
            self.assertIn("time_start_bp", runtime_text)
            self.assertIn("time_end_bp", runtime_text)
            self.assertIn("Map controls", map_html)
            self.assertIn("Filters", map_html)
            self.assertIn("--font-display:", map_html)
            self.assertIn("font-family:var(--font-body);", map_html)
            self.assertIn("Search points and sites", map_html)
            self.assertIn("Loading live map state", map_html)
            self.assertIn("Loading view state", map_html)
            self.assertIn("renderControlPanelSummary", runtime_text)
            self.assertIn("countActiveOverrides", runtime_text)
            self.assertIn('id="topbar-state-pill"', map_html)
            self.assertIn(
                "Calculating time-aware records in the active BP window.", map_html
            )
            self.assertIn("Move over map", map_html)
            self.assertIn("No selection", map_html)
            self.assertNotIn("4 countries · 0 layers · 0 visible points", map_html)
            self.assertIn("basemap-preview--street", map_html)
            self.assertIn(
                "Keyless OpenStreetMap roads, labels, and place context.", map_html
            )
            self.assertIn(
                "Keyless OpenTopoMap relief context for landform reading.", map_html
            )
            self.assertIn(
                "Offline mode keeps evidence and orientation controls usable",
                map_html,
            )
            self.assertIn(
                "__TITLE__".replace("__TITLE__", "Nordic Evidence Atlas"), map_html
            )
            self.assertIn('class="control-panel is-collapsed"', map_html)
            self.assertIn('details class="control-group">', map_html)
            self.assertNotIn('details class="control-group" open', map_html)
            self.assertIn('id="dock-layer-filters"', map_html)
            self.assertIn('id="dock-layer-summary"', map_html)
            self.assertIn('id="dock-time-summary"', map_html)
            self.assertIn('data-layer-preset="context"', map_html)
            self.assertIn("Evidence only", map_html)
            self.assertIn("applyLayerPreset", runtime_text)
            self.assertIn("dock-layer-chip", map_html)
            self.assertIn('id="search-clear"', map_html)
            self.assertIn("search-result-meta", map_html)
            self.assertIn('id="time-record-count"', map_html)
            self.assertIn('data-time-interval="full"', map_html)
            self.assertIn("syncTimePresetButtons", runtime_text)
            self.assertIn("featureTimeWindow", runtime_text)
            self.assertIn("featureInTimeWindow", runtime_text)
            self.assertIn("featureTimeLabel", runtime_text)
            self.assertIn('id="legend-toggle"', map_html)
            self.assertIn("legend-group-label", map_html)
            self.assertIn("setLegendCollapsed", runtime_text)
            self.assertIn('id="mobile-panel-close"', map_html)
            self.assertIn('id="mobile-scrim"', map_html)
            self.assertIn("syncMobilePanelState", runtime_text)
            self.assertIn("event.key === 'Escape'", runtime_text)
            self.assertNotIn("Research Workspace", map_html)
            self.assertNotIn("Workspace Brief", map_html)
            self.assertNotIn("renderWorkspaceBrief", runtime_text)
            self.assertNotIn("renderCoverageMatrix", runtime_text)
            self.assertNotIn("renderFilterChips", runtime_text)
            self.assertNotIn("syncSectionNavWithScroll", runtime_text)
            self.assertIn('id="help-dialog"', map_html)
            self.assertIn("Workspace Guide", map_html)
            self.assertIn("openHelpDialog", runtime_text)
            self.assertIn('id="focus-card"', map_html)
            self.assertIn('id="focus-previous"', map_html)
            self.assertIn('id="focus-next"', map_html)
            self.assertIn('id="focus-zoom"', map_html)
            self.assertIn("Focused Record", map_html)
            self.assertIn("setFocusState", runtime_text)
            self.assertIn("focusPointAtVisibleIndex", runtime_text)
            self.assertIn("renderFocusCard", runtime_text)
            self.assertIn('id="center-readout"', map_html)
            self.assertIn("status-pill-label", map_html)
            self.assertIn('id="floating-legend"', map_html)
            self.assertIn("width:min(288px, calc(100vw - 32px));", map_html)
            self.assertIn(".control-panel.is-collapsed", map_html)
            self.assertIn("window.matchMedia('(max-width: 900px)')", runtime_text)
            self.assertIn("Show controls", map_html)
            self.assertIn(
                "params.set('panel', sidebar.classList.contains('is-collapsed') ? 'collapsed' : 'open')",
                runtime_text,
            )
            self.assertNotIn("<title>Nordic Countries AADR v62.0 Map</title>", map_html)
            self.assertIn("./_map_assets/leaflet/leaflet.css", map_html)
            self.assertNotIn("unpkg.com/leaflet", map_html)
            self.assertIn(
                "plus any governed contextual and animal surfaces that",
                readme_text,
            )
            self.assertIn(
                "Animal temporal windows when animal layers are present",
                readme_text,
            )

            geojson = json.loads(
                (output / "nordic-atlas_samples.geojson").read_text(encoding="utf-8")
            )
            summary = json.loads(
                (output / "nordic-atlas_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(geojson["features"]), 3)
            self.assertEqual(
                summary["schema_version"],
                "geographic-evidence-surface-summary.v1",
            )
            self.assertEqual(summary["artifacts"]["map_html"], "nordic-atlas_map.html")
            self.assertEqual(
                summary["artifacts"]["samples_geojson"], "nordic-atlas_samples.geojson"
            )
            self.assertEqual(
                summary["artifacts"]["evidence_surface_json"],
                "nordic-atlas_evidence_surface.json",
            )
            self.assertEqual(
                summary["artifacts"]["evidence_surface_markdown"],
                "nordic-atlas_evidence_surface.md",
            )
            self.assertEqual(
                summary["artifacts"]["scientific_review_json"],
                "nordic-atlas_scientific_review.json",
            )
            self.assertEqual(
                summary["artifacts"]["scientific_review_markdown"],
                "nordic-atlas_scientific_review.md",
            )
            extra_names = [
                row["filename"] for row in summary["artifacts"]["extra_files"]
            ]
            self.assertEqual(len(extra_names), len(set(extra_names)))
            self.assertIn("nordic-atlas_scientific_review.md", extra_names)
            self.assertTrue(any(".atlas-runtime." in name for name in extra_names))
            self.assertTrue(
                any(".atlas-index-transport." in name for name in extra_names)
            )

    def test_generate_multi_country_map_handles_empty_aadr_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "north-atlantic"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            report = generate_multi_country_map(
                version_dir=root,
                countries=["Iceland"],
                output_dir=output,
                title="North Atlantic",
                slug="north-atlantic",
            )

            self.assertEqual(report.total_unique_samples, 0)
            map_html = (output / "north-atlantic_map.html").read_text(encoding="utf-8")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("No visible records", map_html)
            self.assertIn("restore the default map state", map_html)
            self.assertIn("| Iceland | 0 |", readme_text)


@pytest.mark.parametrize("damage", [None, "path_escape", "byte_count", "integrity"])
def test_declared_runtime_reader_authenticates_each_code_reference(
    tmp_path: Path, damage: str | None
) -> None:
    body = b"globalThis.fixture = true;"
    digest = hashlib.sha256(body).digest()
    name = f"source_map.atlas-runtime.{digest.hex()[:16]}.js"
    (tmp_path / name).write_bytes(body)
    reference: dict[str, object] = {
        "path": name,
        "byte_count": len(body),
        "integrity": "sha256-" + base64.b64encode(digest).decode("ascii"),
    }
    if damage == "path_escape":
        reference["path"] = "../" + name
    elif damage == "byte_count":
        reference["byte_count"] = len(body) + 1
    elif damage == "integrity":
        reference["integrity"] = "sha256-" + base64.b64encode(bytes(32)).decode("ascii")
    (tmp_path / "source_map.html").write_text(
        '<script id="atlas-static-bootstrap" type="application/json">'
        + json.dumps({"runtime": reference})
        + "</script>",
        encoding="utf-8",
    )
    if damage is None:
        assert read_static_atlas_runtime(tmp_path, "source") == body.decode("ascii")
    else:
        with pytest.raises(AssertionError):
            read_static_atlas_runtime(tmp_path, "source")
