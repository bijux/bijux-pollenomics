from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.bundles.published_reports import (
    publish_published_reports_tree,
)
from bijux_pollenomics.reporting.bundles.summary_builders import (
    build_published_reports_summary,
)
from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.models import CountryReport, MultiCountryMapReport
from bijux_pollenomics.reporting.models import PublishedReportsReport


class PublicationGeographyTests(unittest.TestCase):
    def test_build_published_geography_plan_defines_world_region_country_lineage(self) -> None:
        plan = build_published_geography_plan(
            ("Sweden", "Norway", "Finland", "Denmark", "Germany")
        )

        self.assertEqual(plan.world_scope.output_dir_parts, ("world",))
        self.assertEqual(
            [scope.output_dir_parts for scope in plan.regional_scopes],
            [("regions", "europe-plus"), ("regions", "nordic")],
        )
        self.assertEqual(plan.country_scopes[0].output_dir_parts, ("countries", "sweden"))
        germany_scope = next(scope for scope in plan.country_scopes if scope.label == "Germany")
        self.assertEqual(germany_scope.parent_key, "europe_plus")

    def test_build_published_reports_summary_exposes_world_region_and_country_bundles(self) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway"))
        report = MultiCountryMapReport(
            title="World Evidence Surface",
            slug="world",
            version="v66",
            generated_on="2026-05-09",
            countries=("Sweden", "Norway"),
            country_sample_counts={"Sweden": 1, "Norway": 1},
            total_unique_samples=2,
            output_dir=Path("/tmp/docs/report/world"),
            scope_key="world",
            scope_label="World",
            scope_kind="world",
        )
        published = build_published_reports_summary(
            report=PublishedReportsReport(
                version="v66",
                generated_on="2026-05-09",
                countries=("Sweden", "Norway"),
                shared_map_dir=Path("/tmp/docs/report/world"),
                country_output_dirs=(
                    Path("/tmp/docs/report/countries/sweden"),
                    Path("/tmp/docs/report/countries/norway"),
                ),
                summary_path=Path("/tmp/docs/report/published_reports_summary.json"),
                regional_output_dirs=(
                    Path("/tmp/docs/report/regions/europe-plus"),
                    Path("/tmp/docs/report/regions/nordic"),
                ),
                country_output_root=Path("/tmp/docs/report/countries"),
            ),
            map_report=report,
            plan=plan,
            scientific_artifacts={"animal_output_honesty_json": "animal_output_honesty.json"},
            repository_truth_artifacts={"repository_truth_posture_json": "repository_truth_posture.json"},
        )

        self.assertEqual(published["geography_bundles"]["world"]["slug"], "world")
        self.assertIn("europe-plus", published["geography_bundles"]["regions"])
        self.assertIn("nordic", published["geography_bundles"]["regions"])
        self.assertEqual(
            published["artifacts"]["country_bundles"]["sweden"]["parent_scope"],
            "nordic",
        )
        self.assertEqual(
            published["artifacts"]["publication_geography_registry_json"],
            "publication_geography_registry.json",
        )

    def test_publish_published_reports_tree_writes_geography_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging_output_root = Path(tmp) / "staging"
            output_root = Path(tmp) / "docs" / "report"
            version_dir = Path(tmp) / "v66"
            version_dir.mkdir(parents=True, exist_ok=True)

            def fake_generate_multi_country_map_fn(
                *,
                version_dir: Path,
                countries: tuple[str, ...],
                output_dir: Path,
                title: str,
                slug: str,
                context_root: Path | None,
                published_output_dir: Path | None,
                geography_scope,
            ) -> MultiCountryMapReport:
                del version_dir, context_root, published_output_dir
                output_dir.mkdir(parents=True, exist_ok=True)
                build_atlas_bundle_paths(output_dir, slug, "v66")
                (output_dir / "README.md").write_text(f"# {title}\n", encoding="utf-8")
                (output_dir / f"{slug}_map.html").write_text("<html></html>", encoding="utf-8")
                (output_dir / f"{slug}_bundle.json").write_text("{}", encoding="utf-8")
                (output_dir / f"{slug}_summary.json").write_text("{}", encoding="utf-8")
                (output_dir / f"{slug}_samples.geojson").write_text(
                    json.dumps(
                        {
                            "type": "FeatureCollection",
                            "features": [
                                {
                                    "properties": {
                                        "genetic_id": f"{slug}:{country.lower()}"
                                    }
                                }
                                for country in countries
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                (output_dir / f"{slug}_animal_atlas_evidence.json").write_text(
                    json.dumps(
                        [
                            {"evidence_row_id": f"{slug}:animal:{country.lower()}"}
                            for country in countries
                        ]
                    ),
                    encoding="utf-8",
                )
                return MultiCountryMapReport(
                    title=title,
                    slug=slug,
                    version="v66",
                    generated_on="2026-05-09",
                    countries=tuple(countries),
                    country_sample_counts={country: 1 for country in countries},
                    total_unique_samples=len(countries),
                    output_dir=output_dir,
                    scope_key=geography_scope.key,
                    scope_label=geography_scope.label,
                    scope_kind=geography_scope.kind,
                    parent_scope_key=geography_scope.parent_key,
                )

            def fake_generate_country_report_fn(
                *,
                version_dir: Path,
                country: str,
                output_dir: Path,
                map_reference,
                published_output_dir: Path | None,
                context_root: Path | None,
            ) -> CountryReport:
                del version_dir, published_output_dir, context_root
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / f"{country.lower()}_aadr_v66_samples.geojson").write_text(
                    json.dumps(
                        {
                            "type": "FeatureCollection",
                            "features": [
                                {
                                    "properties": {
                                        "genetic_id": f"{country.lower()}:human:one"
                                    }
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                (output_dir / "README.md").write_text(
                    f"map={map_reference[1] if map_reference else ''}\n",
                    encoding="utf-8",
                )
                (output_dir / f"{country.lower()}_animal_adna_v66_summary.json").write_text(
                    json.dumps(
                        {
                            "sample_rows": [
                                {
                                    "evidence_row_id": f"nordic:animal:{country.lower()}"
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                return CountryReport(
                    country=country,
                    version="v66",
                    generated_on="2026-05-09",
                    total_unique_samples=1,
                    total_unique_localities=1,
                    dataset_row_counts={"1240k": 1},
                    samples=(),
                    localities=(),
                    output_dir=output_dir,
                )

            with (
                patch(
                    "bijux_pollenomics.reporting.bundles.published_reports.publish_public_animal_reporting_outputs",
                    return_value={"animal_country_species_coverage_json": "animal_country_species_coverage.json"},
                ),
                patch(
                    "bijux_pollenomics.reporting.bundles.published_reports.publish_animal_foundation_outputs",
                    side_effect=lambda output_root, **_: (
                        (output_root / "animal_publication_release_gate.json").write_text(
                            json.dumps({"overall_ok": True}), encoding="utf-8"
                        ),
                        {"animal_publication_release_gate_json": "animal_publication_release_gate.json"},
                    )[1],
                ),
                patch(
                    "bijux_pollenomics.reporting.bundles.published_reports.publish_repository_truth_outputs",
                    side_effect=lambda output_root, **_: (
                        (output_root / "repository_claim_audit.json").write_text(
                            json.dumps({"overall_ok": True}), encoding="utf-8"
                        ),
                        {"repository_truth_posture_json": "repository_truth_posture.json"},
                    )[1],
                ),
                patch(
                    "bijux_pollenomics.reporting.bundles.published_reports.build_public_animal_output_audit",
                    return_value={"rows": [], "report_root": str(output_root)},
                ),
                patch(
                    "bijux_pollenomics.reporting.bundles.published_reports.render_public_animal_output_audit_markdown",
                    return_value="# audit\n",
                ),
            ):
                report = publish_published_reports_tree(
                    staging_output_root,
                    version_dir=version_dir,
                    output_root=output_root,
                    normalized_countries=("Sweden", "Norway"),
                    title="World Evidence Surface",
                    atlas_slug="world",
                    context_root=Path(tmp) / "data",
                    build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
                    build_published_reports_summary_fn=build_published_reports_summary,
                    generate_country_report_fn=fake_generate_country_report_fn,
                    generate_multi_country_map_fn=fake_generate_multi_country_map_fn,
                    slugify_fn=lambda value: value.lower(),
                    write_summary_json_fn=lambda path, payload: path.write_text(
                        json.dumps(payload, indent=2), encoding="utf-8"
                    ),
                )

            self.assertEqual(report.shared_map_dir, output_root / "world")
            self.assertEqual(
                report.regional_output_dirs,
                (
                    output_root / "regions" / "europe-plus",
                    output_root / "regions" / "nordic",
                ),
            )
            self.assertEqual(report.country_output_root, output_root / "countries")
            self.assertTrue(
                (staging_output_root / "publication_geography_registry.json").is_file()
            )
            self.assertTrue(
                (staging_output_root / "publication_geography_subset_validation.json").is_file()
            )
            self.assertTrue(
                (staging_output_root / "publication_country_onboarding_contract.json").is_file()
            )
            self.assertIn(
                "../../regions/nordic/nordic_map.html",
                (staging_output_root / "countries" / "sweden" / "README.md").read_text(
                    encoding="utf-8"
                ),
            )


if __name__ == "__main__":
    unittest.main()
