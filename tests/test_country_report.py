from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.reporting import (
    generate_country_report,
    generate_multi_country_map,
    generate_published_reports,
    load_country_samples,
)


HEADER = "\t".join(
    [
        "Genetic ID",
        "Master ID",
        "Group ID",
        "Locality",
        "Political Entity",
        "Lat.",
        "Long.",
        "Publication abbreviation",
        "Year first published",
        "Full Date",
        "Date mean in BP",
        "Data type",
        "Molecular Sex",
    ]
)


class CountryReportTests(unittest.TestCase):
    def test_load_country_samples_deduplicates_across_datasets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            self.write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "SE2\tSE2\tSweden_Group\tSigtuna\tSweden\t59.61731\t17.72361\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperC\t2020\t700 BCE\t2650\tAG\tM",
                ],
            )
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                    "SE3\tSE3\tSweden_Group\tBirka\tSweden\t59.3350\t17.5420\tPaperD\t2023\t700 CE\t1250\tHO\tU",
                ],
            )

            samples, dataset_counts = load_country_samples(root, "Sweden")

            self.assertEqual(dataset_counts["1240k"], 2)
            self.assertEqual(dataset_counts["ho"], 2)
            self.assertEqual(len(samples), 3)
            datasets_by_id = {sample.genetic_id: sample.datasets for sample in samples}
            self.assertEqual(datasets_by_id["SE1"], ("1240k", "ho"))
            self.assertEqual(datasets_by_id["SE2"], ("1240k",))
            self.assertEqual(datasets_by_id["SE3"], ("ho",))

    def test_generate_country_report_writes_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            self.write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "SE2\tSE2\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                ],
            )
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            report = generate_country_report(root, "Sweden", output)

            self.assertEqual(report.total_unique_samples, 2)
            self.assertEqual(report.total_unique_localities, 1)
            self.assertTrue((output / "README.md").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_samples.csv").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_localities.csv").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_samples.geojson").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_samples.md").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_summary.json").exists())
            self.assertFalse((output / "sweden_aadr_v62.0_map.html").exists())

            with (output / "sweden_aadr_v62.0_samples.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["political_entity"], "Sweden")

            geojson = json.loads((output / "sweden_aadr_v62.0_samples.geojson").read_text(encoding="utf-8"))
            self.assertEqual(geojson["type"], "FeatureCollection")
            self.assertEqual(len(geojson["features"]), 2)

    def test_generate_country_report_can_link_to_shared_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            generate_country_report(
                root,
                "Sweden",
                output,
                map_reference=("Nordic Countries map", "../nordic/nordic_aadr_v62.0_map.html"),
            )

            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("Shared interactive map", readme_text)
            self.assertIn("../nordic/nordic_aadr_v62.0_map.html", readme_text)

    def test_generate_country_report_uses_country_specific_copy_and_locality_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "finland"
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "FI1\tFI1\tFinland_Group\t\tFinland\t60.2\t24.9\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            generate_country_report(root, "Finland", output)

            readme_text = (output / "README.md").read_text(encoding="utf-8")
            samples_csv = (output / "finland_aadr_v62.0_samples.csv").read_text(encoding="utf-8")
            self.assertIn("| Dataset | Finland rows |", readme_text)
            self.assertIn("combined inventory for `Finland` contains `1` unique samples", readme_text)
            self.assertIn("Unspecified locality", readme_text)
            self.assertIn("Unspecified locality", samples_csv)

    def test_generate_country_report_handles_zero_matching_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "iceland"
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            report = generate_country_report(root, "Iceland", output)

            self.assertEqual(report.total_unique_samples, 0)
            self.assertEqual(report.total_unique_localities, 0)
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            samples_markdown = (output / "iceland_aadr_v62.0_samples.md").read_text(encoding="utf-8")
            self.assertIn("Unique AADR samples: `0`", readme_text)
            self.assertIn("No latitude values available", readme_text)
            self.assertIn("No matching localities", readme_text)
            self.assertIn("Machine-readable summary", readme_text)
            self.assertIn("Total samples: `0`.", samples_markdown)

    def test_generate_multi_country_map_writes_shared_map_with_country_toggles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic"
            self.write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                ],
            )
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "FI1\tFI1\tFinland_Group\tTurku\tFinland\t60.4518\t22.2666\tPaperC\t2020\t700 CE\t1250\tHO\tU",
                ],
            )

            report = generate_multi_country_map(
                version_dir=root,
                countries=["Sweden", "Norway", "Finland"],
                output_dir=output,
                title="Nordic Countries",
                slug="nordic",
            )

            self.assertEqual(report.total_unique_samples, 3)
            self.assertTrue((output / "README.md").exists())
            self.assertTrue((output / "nordic_aadr_v62.0_map.html").exists())
            self.assertTrue((output / "nordic_aadr_v62.0_samples.geojson").exists())
            self.assertTrue((output / "nordic_aadr_v62.0_summary.json").exists())
            self.assertTrue((output / "_map_assets" / "leaflet" / "leaflet.js").exists())

            map_html = (output / "nordic_aadr_v62.0_map.html").read_text(encoding="utf-8")
            self.assertIn("Country Filters", map_html)
            self.assertIn("country-checkbox", map_html)
            self.assertIn("Sweden", map_html)
            self.assertIn("Norway", map_html)
            self.assertIn("Finland", map_html)
            self.assertIn("markerClusterGroup", map_html)
            self.assertIn("AADR release", map_html)
            self.assertIn("Restore defaults", map_html)
            self.assertIn("Time Window", map_html)
            self.assertIn("time-start-slider", map_html)
            self.assertIn("time-interval-slider", map_html)
            self.assertIn("100 years", map_html)
            self.assertIn("time_year_bp", map_html)
            self.assertIn("Research Workspace", map_html)
            self.assertIn("--font-display:", map_html)
            self.assertIn("font-family: var(--font-body);", map_html)
            self.assertIn("Workspace Brief", map_html)
            self.assertIn("id=\"workspace-brief-geography\"", map_html)
            self.assertIn("renderWorkspaceBrief", map_html)
            self.assertIn("id=\"stat-visible-points-note\"", map_html)
            self.assertIn("id=\"stat-context-sources-note\"", map_html)
            self.assertIn("id=\"topbar-state-pill\"", map_html)
            self.assertIn("__TITLE__ map".replace("__TITLE__", "Nordic Countries"), map_html)
            self.assertIn("id=\"section-nav\"", map_html)
            self.assertIn("data-section-target=\"layer-panel\"", map_html)
            self.assertIn("data-section-target=\"filters-panel\"", map_html)
            self.assertIn("id=\"filter-chips\"", map_html)
            self.assertIn("renderFilterChips", map_html)
            self.assertIn("data-layer-preset=\"context\"", map_html)
            self.assertIn("Evidence only", map_html)
            self.assertIn("applyLayerPreset", map_html)
            self.assertIn("layer-state-pill", map_html)
            self.assertIn("layer-swatch-stack", map_html)
            self.assertIn("data-group-toggle=", map_html)
            self.assertIn("data-group-collapse=", map_html)
            self.assertIn("Hide group", map_html)
            self.assertIn("id=\"search-clear\"", map_html)
            self.assertIn("search-result-meta", map_html)
            self.assertIn("syncSectionNavWithScroll", map_html)
            self.assertIn("id=\"time-record-count\"", map_html)
            self.assertIn("data-time-interval=\"full\"", map_html)
            self.assertIn("syncTimePresetButtons", map_html)
            self.assertIn("id=\"legend-toggle\"", map_html)
            self.assertIn("legend-group-label", map_html)
            self.assertIn("setLegendCollapsed", map_html)
            self.assertIn("id=\"mobile-panel-close\"", map_html)
            self.assertIn("id=\"mobile-scrim\"", map_html)
            self.assertIn("syncMobilePanelState", map_html)
            self.assertIn("event.key === 'Escape'", map_html)
            self.assertIn("id=\"focus-card\"", map_html)
            self.assertIn("id=\"focus-zoom\"", map_html)
            self.assertIn("Focused Record", map_html)
            self.assertIn("setFocusState", map_html)
            self.assertIn("renderFocusCard", map_html)
            self.assertIn("id=\"floating-legend\"", map_html)
            self.assertIn("right: 16px;", map_html)
            self.assertIn("width: min(300px, calc(100vw - 32px));", map_html)
            self.assertIn("window.matchMedia('(max-width: 900px)')", map_html)
            self.assertIn("Show filters", map_html)
            self.assertIn("params.set('panel', sidebar.classList.contains('is-collapsed') ? 'collapsed' : 'open')", map_html)
            self.assertNotIn("<title>Nordic Countries AADR v62.0 Map</title>", map_html)
            self.assertIn("./_map_assets/leaflet/leaflet.css", map_html)
            self.assertNotIn("unpkg.com/leaflet", map_html)

            geojson = json.loads((output / "nordic_aadr_v62.0_samples.geojson").read_text(encoding="utf-8"))
            self.assertEqual(len(geojson["features"]), 3)

    def test_generate_multi_country_map_can_include_context_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic"
            context_root = Path(tmp) / "data"
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            self.write_geojson(
                context_root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
                layer_key="landclim-sites",
                layer_label="LandClim pollen sites",
                category="Pollen sequence",
            )
            self.write_geojson(
                context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
                layer_key="neotoma-pollen",
                layer_label="Neotoma pollen sites",
                category="Pollen",
            )
            self.write_geojson(
                context_root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
                layer_key="sead-sites",
                layer_label="SEAD sites",
                category="Environmental archaeology",
            )
            archaeology_metadata = {
                "layer_key": "raa-archaeology",
                "layer_label": "RAÄ archaeology density",
                "country": "Sweden",
                "counts": {"all_published_sites": 100},
            }
            self.write_json(
                context_root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson",
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[[16.0, 58.0], [19.0, 58.0], [19.0, 60.0], [16.0, 60.0], [16.0, 58.0]]],
                            },
                            "properties": {
                                "country": "Sweden",
                                "name": "Sweden",
                                "layer_key": "country-boundaries",
                                "layer_label": "Country boundaries",
                            },
                        }
                    ],
                },
            )
            self.write_json(
                context_root / "landclim" / "normalized" / "nordic_reveals_grid_cells.geojson",
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[[16.0, 58.0], [17.0, 58.0], [17.0, 59.0], [16.0, 59.0], [16.0, 58.0]]],
                            },
                            "properties": {
                                "source": "LandClim",
                                "layer_key": "landclim-reveals-grid",
                                "layer_label": "LandClim REVEALS grid cells",
                                "category": "Vegetation reconstruction",
                                "country": "Sweden",
                                "record_id": "16,58,17,59",
                                "name": "17E 59N grid cell",
                                "geometry_type": "Polygon",
                                "subtitle": "1 degree REVEALS grid-cell coverage",
                                "description": "",
                                "source_url": "https://doi.org/10.1594/PANGAEA.937075",
                                "record_count": 1,
                                "popup_rows": [
                                    {"label": "Datasets", "value": "LandClim II REVEALS grids"},
                                    {"label": "Time windows", "value": "1 windows"},
                                ],
                            },
                        }
                    ],
                },
            )
            self.write_json(
                context_root / "raa" / "normalized" / "sweden_archaeology_layer.json",
                archaeology_metadata,
            )
            self.write_json(
                context_root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[[16.0, 58.0], [17.0, 58.0], [17.0, 59.0], [16.0, 59.0], [16.0, 58.0]]],
                            },
                            "properties": {
                                "country": "Sweden",
                                "count": 5,
                                "count_label": "5",
                            },
                        }
                    ],
                },
            )

            generate_multi_country_map(
                version_dir=root,
                countries=["Sweden"],
                output_dir=output,
                title="Nordic Countries",
                slug="nordic",
                context_root=context_root,
            )

            map_html = (output / "nordic_aadr_v62.0_map.html").read_text(encoding="utf-8")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("Country Filters", map_html)
            self.assertIn("Search Visible Records", map_html)
            self.assertIn("Map Scope", map_html)
            self.assertIn("Time Window", map_html)
            self.assertIn("Copy link", map_html)
            self.assertIn("Primary Evidence", map_html)
            self.assertIn("Country boundaries", map_html)
            self.assertIn(".sidebar:not(.is-collapsed) ~ .map-stage .floating-legend", map_html)
            self.assertIn("LandClim pollen sites", map_html)
            self.assertIn("LandClim REVEALS grid cells", map_html)
            self.assertIn("Neotoma pollen sites", map_html)
            self.assertIn("SEAD sites", map_html)
            self.assertIn("RAÄ archaeology density", map_html)
            self.assertIn("Machine-readable summary", readme_text)
            self.assertIn("nordic_pollen_site_sequences.geojson", readme_text)
            self.assertIn("nordic_reveals_grid_cells.geojson", readme_text)
            self.assertIn("nordic_pollen_sites.geojson", readme_text)
            self.assertIn("# Nordic Countries Research Map", readme_text)
            self.assertTrue((output / "nordic_pollen_site_sequences.geojson").exists())
            self.assertTrue((output / "nordic_reveals_grid_cells.geojson").exists())
            self.assertTrue((output / "nordic_pollen_sites.geojson").exists())
            self.assertTrue((output / "nordic_environmental_sites.geojson").exists())
            self.assertTrue((output / "sweden_archaeology_layer.json").exists())
            self.assertTrue((output / "sweden_archaeology_density.geojson").exists())
            self.assertTrue((output / "nordic_country_boundaries.geojson").exists())

    def test_generate_multi_country_map_handles_empty_aadr_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "north-atlantic"
            self.write_anno(
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
            map_html = (output / "north-atlantic_aadr_v62.0_map.html").read_text(encoding="utf-8")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("No visible point records are available under the current filters.", map_html)
            self.assertIn("| Iceland | 0 |", readme_text)

    def test_generate_published_reports_writes_shared_and_country_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report"
            context_root = Path(tmp) / "data"
            self.write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                ],
            )
            self.write_geojson(
                context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
                layer_key="neotoma-pollen",
                layer_label="Neotoma pollen sites",
                category="Pollen",
            )

            report = generate_published_reports(
                version_dir=root,
                countries=["Sweden", "Norway"],
                output_root=output,
                title="Nordic Countries",
                slug="nordic",
                context_root=context_root,
            )

            self.assertEqual(report.countries, ("Sweden", "Norway"))
            self.assertTrue((output / "published_reports_summary.json").exists())
            self.assertTrue((output / "nordic" / "nordic_aadr_v62.0_map.html").exists())
            self.assertTrue((output / "sweden" / "README.md").exists())
            self.assertTrue((output / "norway" / "README.md").exists())
            sweden_readme = (output / "sweden" / "README.md").read_text(encoding="utf-8")
            self.assertIn("../nordic/nordic_aadr_v62.0_map.html", sweden_readme)

    def write_anno(self, path: Path, rows: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")

    def write_geojson(self, path: Path, layer_key: str, layer_label: str, category: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                    "properties": {
                        "layer_key": layer_key,
                        "layer_label": layer_label,
                        "category": category,
                        "country": "Sweden",
                        "name": f"{layer_label} Record",
                        "subtitle": f"{layer_label} subtitle",
                        "description": "",
                        "source_url": "https://example.com",
                        "popup_rows": [{"label": "Source", "value": layer_label}],
                    },
                }
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def write_json(self, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
