from __future__ import annotations

from pathlib import Path
import tempfile
from typing import cast
import unittest
from unittest.mock import patch

import pytest

from bijux_pollenomics.reporting import (
    generate_multi_country_map,
)


from ..fixtures.aadr import write_anno
from ..fixtures.animal_adna import write_tracked_animal_species
from ..fixtures.context_sources import (
    write_geojson,
    write_neotoma_context,
    write_sead_context,
)
from ..fixtures.files import write_json
from ..static_assets import read_static_atlas_payload_text


pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_multi_country_map_can_include_context_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temporary_root = Path(tmp).resolve()
            root = temporary_root / "v62.0"
            output = temporary_root / "docs" / "report" / "nordic-atlas"
            context_root = temporary_root / "data"
            gallery_root = temporary_root / "docs" / "gallery"
            gallery_root.mkdir(parents=True, exist_ok=True)
            (gallery_root / "2026-02-26-data-collection.JPG").write_bytes(b"jpeg")
            (gallery_root / "2026-02-26-data-collection.mp4").write_bytes(b"mp4")
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            write_geojson(
                context_root
                / "landclim"
                / "normalized"
                / "nordic_pollen_site_sequences.geojson",
                layer_key="landclim-sites",
                layer_label="LandClim pollen sites",
                category="Pollen sequence",
            )
            write_neotoma_context(context_root)
            write_tracked_animal_species(
                context_root / "adna" / "species" / "ovis_aries",
                latin_name="Ovis aries",
                common_name="sheep",
                locality="Sweden sheep lead",
                political_entity="Sweden",
                project_accession="PRJEB59481",
                support_class="accepted",
                product_role="domesticated_core",
                nordic_inclusion=True,
                chronology_bucket="1001-3000 BP",
                paper_title="Baltic short-tailed sheep aDNA",
                paper_doi="10.1000/sheep",
            )
            write_tracked_animal_species(
                context_root / "adna" / "species" / "rangifer_tarandus",
                latin_name="Rangifer tarandus",
                common_name="reindeer",
                locality="Svalbard reindeer lead",
                political_entity="Norway",
                project_accession="PRJEB60484",
                support_class="comparator_only",
                product_role="comparator",
                nordic_inclusion=True,
                chronology_bucket="0-1000 BP",
                paper_title="Ancient reindeer context",
                paper_doi="10.1000/reindeer",
            )
            sead_manifest_sha256, sead_admission_sha256 = write_sead_context(
                context_root
            )
            archaeology_metadata = {
                "layer_key": "raa-archaeology",
                "layer_label": "RAÄ archaeology density",
                "country": "Sweden",
                "counts": {"all_published_sites": 100},
            }
            write_json(
                context_root
                / "boundaries"
                / "normalized"
                / "nordic_country_boundaries.geojson",
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
                                        [19.0, 58.0],
                                        [19.0, 60.0],
                                        [16.0, 60.0],
                                        [16.0, 58.0],
                                    ]
                                ],
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
            write_json(
                context_root
                / "landclim"
                / "normalized"
                / "nordic_reveals_grid_cells.geojson",
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
                                    {
                                        "label": "Datasets",
                                        "value": "LandClim II REVEALS grids",
                                    },
                                    {"label": "Time windows", "value": "1 windows"},
                                ],
                            },
                        }
                    ],
                },
            )
            write_json(
                context_root / "raa" / "normalized" / "sweden_archaeology_layer.json",
                cast(dict[str, object], archaeology_metadata),
            )
            write_json(
                context_root
                / "raa"
                / "normalized"
                / "sweden_archaeology_density.geojson",
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
                                "country": "Sweden",
                                "count": 5,
                                "count_label": "5",
                            },
                        }
                    ],
                },
            )

            with (
                patch(
                    "bijux_pollenomics.reporting.map_document.evidence_projection.sead.SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
                    sead_manifest_sha256,
                ),
                patch(
                    "bijux_pollenomics.reporting.map_document.evidence_projection.sead.SEAD_GOVERNED_ADMISSION_SHA256",
                    sead_admission_sha256,
                ),
            ):
                generate_multi_country_map(
                    version_dir=root,
                    countries=["Sweden"],
                    output_dir=output,
                    title="Nordic Evidence Atlas",
                    slug="nordic-atlas",
                    context_root=context_root,
                )

            map_html = (output / "nordic-atlas_map.html").read_text(encoding="utf-8")
            atlas_payload_text = read_static_atlas_payload_text(output, "nordic-atlas")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("Country Filters", map_html)
            self.assertIn("Search points and sites", map_html)
            self.assertIn("Filters", map_html)
            self.assertIn("Date Window", map_html)
            self.assertIn("Copy link", map_html)
            self.assertIn("Country boundaries", atlas_payload_text)
            self.assertIn("dock-layer-chip", map_html)
            self.assertIn('class="control-panel"', map_html)
            self.assertIn("width: min(288px, calc(100vw - 32px));", map_html)
            self.assertIn('details class="control-group"', map_html)
            self.assertIn("LandClim pollen sites", atlas_payload_text)
            self.assertIn("LandClim REVEALS grid cells", atlas_payload_text)
            self.assertIn("Neotoma pollen sites", atlas_payload_text)
            self.assertIn("SEAD sites", atlas_payload_text)
            self.assertIn("Fieldwork documentation", atlas_payload_text)
            self.assertIn(r"Lyngsj\u00f6n Lake field sampling", atlas_payload_text)
            self.assertIn(
                "../../gallery/2026-02-26-data-collection.mp4",
                atlas_payload_text,
            )
            self.assertIn("popup-media-link", map_html)
            self.assertNotIn(r"RA\u00c4 archaeology density", atlas_payload_text)
            self.assertNotIn("Search Visible Records", map_html)
            self.assertNotIn(
                ".sidebar:not(.is-collapsed) ~ .map-stage .floating-legend", map_html
            )
            self.assertIn("Machine-readable summary", readme_text)
            self.assertIn(
                "This bundle is a generated publication artifact, not a source dataset.",
                readme_text,
            )
            self.assertIn(
                "Local leaflet assets are copied into `./_map_assets`", readme_text
            )
            self.assertIn(
                "Basemap tiles are still requested from the active cartographic provider at runtime",
                readme_text,
            )
            self.assertIn(
                "Ranking artifacts are published alongside it and carry stricter evidence boundaries than the map view itself.",
                readme_text,
            )
            self.assertIn("nordic_pollen_site_sequences.geojson", readme_text)
            self.assertIn("nordic_reveals_grid_cells.geojson", readme_text)
            self.assertIn("nordic_pollen_sites.geojson", readme_text)
            self.assertIn("# Nordic Evidence Atlas", readme_text)
            self.assertTrue((output / "nordic_pollen_site_sequences.geojson").exists())
            self.assertTrue((output / "nordic_reveals_grid_cells.geojson").exists())
            self.assertTrue((output / "nordic_pollen_sites.geojson").exists())
            self.assertTrue((output / "nordic_environmental_sites.geojson").exists())
            self.assertTrue((output / "sweden_archaeology_layer.json").exists())
            self.assertFalse((output / "sweden_archaeology_density.geojson").exists())
            self.assertTrue((output / "nordic_country_boundaries.geojson").exists())

    def test_generate_multi_country_map_uses_context_layer_dates_for_time_window(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            context_root = Path(tmp) / "data"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t\t\tHO\tF",
                ],
            )
            write_json(
                context_root
                / "boundaries"
                / "normalized"
                / "nordic_country_boundaries.geojson",
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
                                        [19.0, 58.0],
                                        [19.0, 60.0],
                                        [16.0, 60.0],
                                        [16.0, 58.0],
                                    ]
                                ],
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
            write_json(
                context_root
                / "landclim"
                / "normalized"
                / "nordic_reveals_grid_cells.geojson",
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
                                "time_start_bp": 100,
                                "time_end_bp": 3200,
                                "popup_rows": [
                                    {"label": "Time windows", "value": "100-3200 BP"},
                                ],
                            },
                        }
                    ],
                },
            )

            generate_multi_country_map(
                version_dir=root,
                countries=["Sweden"],
                output_dir=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
                context_root=context_root,
            )

            map_html = (output / "nordic-atlas_map.html").read_text(encoding="utf-8")
            self.assertIn("const TIME_MIN_BP = 100;", map_html)
            self.assertIn("const TIME_MAX_BP = 3200;", map_html)
            self.assertIn("const TIME_HAS_DATA = true;", map_html)
            self.assertIn("const DEFAULT_TIME_START_BP = 100;", map_html)
            self.assertIn("const DEFAULT_TIME_INTERVAL_YEARS = 3100;", map_html)
            self.assertIn('data-time-interval="5000">5000 years</button>', map_html)
            self.assertIn('data-time-interval="50000">50000 years</button>', map_html)
            self.assertIn('data-time-interval="full">Full span</button>', map_html)
            self.assertIn(
                "const admission = featureTimeAdmission(feature);", map_html
            )
            self.assertIn(
                "if (admission.status === 'invalid') return false;", map_html
            )
            self.assertIn(
                "if (admission.status === 'untimed' && layer.semantic_role === "
                "'source_chronology_context') return false;",
                map_html,
            )
            self.assertIn(
                "if (admission.status === 'untimed') {", map_html
            )

    def test_generate_multi_country_map_rejects_context_point_layers_without_identity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            context_root = Path(tmp) / "data"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            write_json(
                context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                            "properties": {
                                "layer_label": "Neotoma pollen sites",
                                "country": "Sweden",
                                "name": "Broken record",
                            },
                        }
                    ],
                },
            )

            with self.assertRaisesRegex(ValueError, "layer_key"):
                generate_multi_country_map(
                    version_dir=root,
                    countries=["Sweden"],
                    output_dir=output,
                    title="Nordic Evidence Atlas",
                    slug="nordic-atlas",
                    context_root=context_root,
                )

    def test_generate_multi_country_map_rejects_context_polygon_layers_with_point_geometry(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            context_root = Path(tmp) / "data"
            write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            write_json(
                context_root
                / "landclim"
                / "normalized"
                / "nordic_reveals_grid_cells.geojson",
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                            "properties": {
                                "layer_key": "landclim-reveals-grid",
                                "layer_label": "LandClim REVEALS grid cells",
                            },
                        }
                    ],
                },
            )

            with self.assertRaisesRegex(ValueError, "Polygon or MultiPolygon"):
                generate_multi_country_map(
                    version_dir=root,
                    countries=["Sweden"],
                    output_dir=output,
                    title="Nordic Evidence Atlas",
                    slug="nordic-atlas",
                    context_root=context_root,
                )
