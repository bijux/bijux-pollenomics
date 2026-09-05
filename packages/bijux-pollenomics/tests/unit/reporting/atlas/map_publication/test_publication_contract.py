from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_publication import (
    build_map_publication_contract,
    resolve_map_scope_policy,
)
from bijux_pollenomics.reporting.models import MultiCountryMapReport

from .support import MapPublicationTestCase


class PublicationContractTests(MapPublicationTestCase):
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

        self.assertEqual(
            contract["role_counts"]["shared_world_scale_layer"],  # type: ignore[index]
            1,
        )
        self.assertEqual(
            contract["role_counts"]["region_filtered_layer"],  # type: ignore[index]
            1,
        )
        self.assertEqual(
            contract["role_counts"]["scope_specific_overlay"],  # type: ignore[index]
            1,
        )
