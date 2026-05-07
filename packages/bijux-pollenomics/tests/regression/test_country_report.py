from __future__ import annotations

from collections.abc import Collection
import csv
import json
from pathlib import Path
import tempfile
from typing import cast
import unittest
from unittest.mock import patch

from bijux_pollenomics.reporting import (
    generate_country_report,
    generate_multi_country_map,
    generate_published_reports,
    load_country_samples,
)
from bijux_pollenomics.reporting.bundles import (
    build_atlas_bundle_paths,
    build_country_bundle_paths,
)
from bijux_pollenomics.reporting.models import SampleRecord
from bijux_pollenomics.reporting.rendering import (
    build_sample_geojson_feature,
    serialize_sample_record,
)
from tests.support.aadr import AADR_HEADER, write_anno_file


class CountryReportTests(unittest.TestCase):
    def test_bundle_path_builders_keep_artifact_names_stable(self) -> None:
        country_paths = build_country_bundle_paths(
            Path("/tmp/sweden"), "Sweden", "v62.0"
        )
        atlas_paths = build_atlas_bundle_paths(
            Path("/tmp/nordic-atlas"), "nordic-atlas", "v62.0"
        )

        self.assertEqual(
            country_paths.samples_csv_path.name, "sweden_aadr_v62.0_samples.csv"
        )
        self.assertEqual(
            country_paths.localities_csv_path.name, "sweden_aadr_v62.0_localities.csv"
        )
        self.assertEqual(
            country_paths.samples_markdown_path.name, "sweden_aadr_v62.0_samples.md"
        )
        self.assertEqual(
            country_paths.bundle_manifest_path.name, "sweden_aadr_v62.0_bundle.json"
        )
        self.assertEqual(
            country_paths.animal_summary_json_path.name,
            "sweden_animal_adna_v62.0_summary.json",
        )
        self.assertEqual(
            country_paths.animal_species_csv_path.name,
            "sweden_animal_adna_v62.0_species.csv",
        )
        self.assertEqual(
            country_paths.animal_localities_geojson_path.name,
            "sweden_animal_adna_v62.0_localities.geojson",
        )
        self.assertEqual(
            country_paths.animal_citations_markdown_path.name,
            "sweden_animal_adna_v62.0_citations.md",
        )
        self.assertEqual(
            country_paths.animal_warnings_markdown_path.name,
            "sweden_animal_adna_v62.0_warnings.md",
        )
        self.assertEqual(atlas_paths.map_html_path.name, "nordic-atlas_map.html")
        self.assertEqual(
            atlas_paths.samples_geojson_path.name, "nordic-atlas_samples.geojson"
        )
        self.assertEqual(
            atlas_paths.animal_localities_geojson_path.name,
            "nordic-atlas_animal_localities.geojson",
        )
        self.assertEqual(
            atlas_paths.domesticated_animal_localities_geojson_path.name,
            "nordic-atlas_domesticated_animal_localities.geojson",
        )
        self.assertEqual(
            atlas_paths.comparator_animal_localities_geojson_path.name,
            "nordic-atlas_comparator_animal_localities.geojson",
        )
        self.assertEqual(
            atlas_paths.animal_atlas_evidence_csv_path.name,
            "nordic-atlas_animal_atlas_evidence.csv",
        )
        self.assertEqual(
            atlas_paths.animal_atlas_evidence_json_path.name,
            "nordic-atlas_animal_atlas_evidence.json",
        )
        self.assertEqual(
            atlas_paths.animal_point_traceability_json_path.name,
            "nordic-atlas_animal_point_traceability.json",
        )
        self.assertEqual(
            atlas_paths.candidate_sites_csv_path.name,
            "nordic-atlas_candidate_sites.csv",
        )
        self.assertEqual(
            atlas_paths.candidate_sites_json_path.name,
            "nordic-atlas_candidate_sites.json",
        )
        self.assertEqual(
            atlas_paths.candidate_sites_markdown_path.name,
            "nordic-atlas_candidate_sites.md",
        )
        self.assertEqual(
            atlas_paths.candidate_site_sensitivity_json_path.name,
            "nordic-atlas_candidate_site_sensitivity.json",
        )
        self.assertEqual(
            atlas_paths.candidate_site_sensitivity_markdown_path.name,
            "nordic-atlas_candidate_site_sensitivity.md",
        )
        self.assertEqual(
            atlas_paths.candidate_ranking_engine_manifest_path.name,
            "nordic-atlas_candidate_ranking_engine_manifest.json",
        )
        self.assertEqual(
            atlas_paths.evidence_surface_json_path.name,
            "nordic-atlas_evidence_surface.json",
        )
        self.assertEqual(
            atlas_paths.evidence_surface_markdown_path.name,
            "nordic-atlas_evidence_surface.md",
        )
        self.assertEqual(
            atlas_paths.scientific_review_json_path.name,
            "nordic-atlas_scientific_review.json",
        )
        self.assertEqual(
            atlas_paths.scientific_review_markdown_path.name,
            "nordic-atlas_scientific_review.md",
        )
        self.assertEqual(
            atlas_paths.bundle_manifest_path.name, "nordic-atlas_bundle.json"
        )
        self.assertEqual(
            atlas_paths.summary_json_path.name, "nordic-atlas_summary.json"
        )

    def test_sample_serialization_contract_stays_aligned_between_csv_and_geojson(
        self,
    ) -> None:
        sample = self.sample_record(
            genetic_id="SE1",
            locality="Uppsala",
            political_entity="Sweden",
            datasets=("1240k", "ho"),
        )

        csv_payload = serialize_sample_record(sample)
        geojson_feature = build_sample_geojson_feature(sample)
        properties = cast(dict[str, object], geojson_feature["properties"])
        geometry = cast(dict[str, object], geojson_feature["geometry"])

        self.assertEqual(csv_payload["genetic_id"], properties["genetic_id"])
        self.assertEqual(csv_payload["locality"], properties["locality"])
        self.assertEqual(
            csv_payload["political_entity"],
            properties["political_entity"],
        )
        self.assertEqual(csv_payload["datasets"], properties["datasets"])
        self.assertEqual(
            csv_payload["date_stddev_bp"],
            properties["date_stddev_bp"],
        )
        self.assertEqual(csv_payload["time_start_bp"], properties["time_start_bp"])
        self.assertEqual(csv_payload["time_end_bp"], properties["time_end_bp"])
        self.assertEqual(csv_payload["time_label"], properties["time_label"])
        self.assertEqual(
            geometry["coordinates"],
            [sample.longitude, sample.latitude],
        )

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

    def test_load_country_samples_skips_rows_without_identity_or_numeric_coordinates(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            self.write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "SE2\tSE2\tSweden_Group\tBirka\tSweden\tbad\t17.5420\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                    "SE3\tSE3\tSweden_Group\tSigtuna\tSweden\t59.61731\t17.72361\tPaperC\t2020\t700 BCE\t2650\tAG\tM",
                ],
            )

            samples, dataset_counts = load_country_samples(root, "Sweden")

            self.assertEqual(dataset_counts["1240k"], 1)
            self.assertEqual(len(samples), 1)
            self.assertEqual(samples[0].genetic_id, "SE3")

    def test_load_country_samples_derives_bp_interval_from_mean_and_stddev_when_available(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            anno_path = root / "ho" / "v62.0_HO_public.anno"
            anno_path.parent.mkdir(parents=True, exist_ok=True)
            anno_path.write_text(
                "\t".join(
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
                        "Date standard deviation in BP",
                        "Data type",
                        "Molecular Sex",
                    ]
                )
                + "\n"
                + "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\t125\tHO\tF\n",
                encoding="utf-8",
            )

            samples, _ = load_country_samples(root, "Sweden")

            self.assertEqual(len(samples), 1)
            self.assertEqual(samples[0].date_stddev_bp, "125")
            self.assertEqual(samples[0].time_start_bp, 2200)
            self.assertEqual(samples[0].time_end_bp, 2700)
            self.assertEqual(samples[0].time_mean_bp, 2450)
            self.assertEqual(samples[0].time_label, "500 BCE")

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
            self.assertTrue((output / "sweden_aadr_v62.0_bundle.json").exists())
            self.assertTrue((output / "sweden_aadr_v62.0_summary.json").exists())
            self.assertFalse((output / "sweden_aadr_v62.0_map.html").exists())

            with (output / "sweden_aadr_v62.0_samples.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["political_entity"], "Sweden")
            with (output / "sweden_aadr_v62.0_localities.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                locality_rows = list(csv.DictReader(handle))
            self.assertEqual(locality_rows[0]["time_start_bp"], "2450")
            self.assertEqual(locality_rows[0]["time_end_bp"], "2550")
            self.assertEqual(locality_rows[0]["time_label"], "2450-2550 BP")

            geojson = json.loads(
                (output / "sweden_aadr_v62.0_samples.geojson").read_text(
                    encoding="utf-8"
                )
            )
            summary = json.loads(
                (output / "sweden_aadr_v62.0_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(geojson["type"], "FeatureCollection")
            self.assertEqual(len(geojson["features"]), 2)
            self.assertEqual(
                summary["artifacts"]["bundle_manifest"],
                "sweden_aadr_v62.0_bundle.json",
            )
            self.assertEqual(
                summary["artifacts"]["samples_csv"], "sweden_aadr_v62.0_samples.csv"
            )
            self.assertEqual(
                summary["artifacts"]["summary_json"], "sweden_aadr_v62.0_summary.json"
            )

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
                map_reference=(
                    "Nordic Evidence Atlas",
                    "../nordic-atlas/nordic-atlas_map.html",
                ),
            )

            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("Shared interactive map", readme_text)
            self.assertIn("../nordic-atlas/nordic-atlas_map.html", readme_text)
            self.assertIn(
                "Environmental and archaeology context layers are published in the shared map bundle",
                readme_text,
            )

    def test_generate_country_report_can_publish_country_animal_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            context_root = Path(tmp) / "data"
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            self.write_tracked_animal_species(
                context_root / "adna" / "ovis_aries",
                latin_name="Ovis aries",
                common_name="sheep",
                locality="Uppland sheep lead",
                political_entity="Sweden",
                project_accession="PRJEB59481",
                support_class="accepted",
                product_role="domesticated_core",
                nordic_inclusion=True,
                chronology_bucket="1001-3000 BP",
                paper_title="Baltic short-tailed sheep aDNA",
                paper_doi="10.1000/sheep",
            )

            generate_country_report(root, "Sweden", output, context_root=context_root)

            self.assertTrue((output / "sweden_animal_adna_v62.0_summary.json").exists())
            self.assertTrue((output / "sweden_animal_adna_v62.0_species.csv").exists())
            self.assertTrue(
                (output / "sweden_animal_adna_v62.0_localities.geojson").exists()
            )
            self.assertTrue(
                (output / "sweden_animal_adna_v62.0_citations.md").exists()
            )
            self.assertTrue(
                (output / "sweden_animal_adna_v62.0_warnings.md").exists()
            )
            summary = json.loads(
                (output / "sweden_aadr_v62.0_summary.json").read_text(encoding="utf-8")
            )
            animal_summary = json.loads(
                (output / "sweden_animal_adna_v62.0_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            readme_text = (output / "README.md").read_text(encoding="utf-8")

            self.assertEqual(summary["animal_adna"]["total_species"], 1)
            self.assertEqual(animal_summary["total_localities"], 1)
            self.assertEqual(
                animal_summary["species_rows"][0]["assignment_confidence"],
                "exact_country",
            )
            self.assertIn("## Animal aDNA Country Outputs", readme_text)
            self.assertIn("sweden_animal_adna_v62.0_species.csv", readme_text)
            self.assertIn("Country-Resolved Animal Species", readme_text)

    def test_generate_country_report_marks_regional_animal_projection_in_warnings(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            context_root = Path(tmp) / "data"
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            self.write_tracked_animal_species(
                context_root / "adna" / "ovis_aries",
                latin_name="Ovis aries",
                common_name="sheep",
                locality="Baltic sheep lead",
                political_entity="Baltic Sea Region",
                project_accession="PRJEB59481",
                support_class="accepted",
                product_role="domesticated_core",
                nordic_inclusion=True,
                chronology_bucket="1001-3000 BP",
                paper_title="Baltic short-tailed sheep aDNA",
                paper_doi="10.1000/sheep",
            )

            generate_country_report(root, "Sweden", output, context_root=context_root)

            animal_summary = json.loads(
                (output / "sweden_animal_adna_v62.0_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            warnings_text = (
                output / "sweden_animal_adna_v62.0_warnings.md"
            ).read_text(encoding="utf-8")

            self.assertEqual(
                animal_summary["localities"][0]["country_assignment_confidence"],
                "regional_projection",
            )
            self.assertIn("regional_projection", warnings_text)
            self.assertIn("not one country-exact excavation label", warnings_text)

    def test_generate_country_report_replaces_stale_bundle_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            output.mkdir(parents=True, exist_ok=True)
            stale_file = output / "obsolete.txt"
            stale_file.write_text("stale", encoding="utf-8")
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            generate_country_report(root, "Sweden", output)

            self.assertFalse(stale_file.exists())
            self.assertTrue((output / "README.md").exists())

    def test_generate_country_report_preserves_previous_bundle_when_publication_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "sweden"
            output.mkdir(parents=True, exist_ok=True)
            preserved_file = output / "README.md"
            preserved_file.write_text("kept", encoding="utf-8")
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            def fail_after_partial_write(path: Path, samples: object) -> None:
                path.write_text("partial", encoding="utf-8")
                raise RuntimeError("write failure")

            with (
                patch(
                    "bijux_pollenomics.reporting.service.write_samples_csv",
                    side_effect=fail_after_partial_write,
                ),
                self.assertRaisesRegex(RuntimeError, "write failure"),
            ):
                generate_country_report(root, "Sweden", output)

            self.assertEqual(preserved_file.read_text(encoding="utf-8"), "kept")
            self.assertFalse((output.parent / ".sweden.tmp").exists())

    def test_generate_country_report_uses_country_specific_copy_and_locality_placeholder(
        self,
    ) -> None:
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
            samples_csv = (output / "finland_aadr_v62.0_samples.csv").read_text(
                encoding="utf-8"
            )
            self.assertIn("| Dataset | Finland rows |", readme_text)
            self.assertIn(
                "| Locality | Samples | Latitude | Longitude | BP coverage | Datasets |",
                readme_text,
            )
            self.assertIn(
                "It inventories only Homo sapiens aDNA sample rows that match the `Finland` country filter.",
                readme_text,
            )
            self.assertIn(
                "combined inventory for `Finland` contains `1` unique Homo sapiens aDNA samples",
                readme_text,
            )
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
            samples_markdown = (output / "iceland_aadr_v62.0_samples.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Unique Homo sapiens aDNA samples: `0`", readme_text)
            self.assertIn("No latitude values available", readme_text)
            self.assertIn("No matching localities", readme_text)
            self.assertIn("Machine-readable summary", readme_text)
            self.assertIn(
                "This country bundle is valid even when the filter returns zero Homo sapiens aDNA samples.",
                readme_text,
            )
            self.assertIn("Total Homo sapiens aDNA samples: `0`.", samples_markdown)

    def test_generate_multi_country_map_writes_shared_map_with_country_toggles(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
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
                (output / "nordic-atlas_candidate_ranking_engine_manifest.json").exists()
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
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("Country Filters", map_html)
            self.assertIn("country-checkbox", map_html)
            self.assertIn("Sweden", map_html)
            self.assertIn("Norway", map_html)
            self.assertIn("Finland", map_html)
            self.assertIn("markerClusterGroup", map_html)
            self.assertIn("Nordic Atlas", map_html)
            self.assertIn("Restore defaults", map_html)
            self.assertIn("time-start-slider", map_html)
            self.assertIn("time-interval-slider", map_html)
            self.assertIn("100 years", map_html)
            self.assertIn("time_year_bp", map_html)
            self.assertIn("time_start_bp", map_html)
            self.assertIn("time_end_bp", map_html)
            self.assertIn("Map controls", map_html)
            self.assertIn("Filters", map_html)
            self.assertIn("--font-display:", map_html)
            self.assertIn("font-family: var(--font-body);", map_html)
            self.assertIn("Search points and sites", map_html)
            self.assertIn("Loading live map state", map_html)
            self.assertIn("Loading view state", map_html)
            self.assertIn("renderControlPanelSummary", map_html)
            self.assertIn("countActiveOverrides", map_html)
            self.assertIn('id="topbar-state-pill"', map_html)
            self.assertIn(
                "Calculating time-aware records in the active BP window.", map_html
            )
            self.assertIn("Move over map", map_html)
            self.assertIn("No selection", map_html)
            self.assertNotIn("4 countries · 0 layers · 0 visible points", map_html)
            self.assertIn("basemap-preview--voyager", map_html)
            self.assertIn("Minimal contrast for evidence-first inspection.", map_html)
            self.assertIn(
                "__TITLE__".replace("__TITLE__", "Nordic Evidence Atlas"), map_html
            )
            self.assertIn('class="control-panel"', map_html)
            self.assertIn('details class="control-group" open', map_html)
            self.assertIn('id="dock-layer-filters"', map_html)
            self.assertIn('id="dock-layer-summary"', map_html)
            self.assertIn('id="dock-time-summary"', map_html)
            self.assertIn('data-layer-preset="context"', map_html)
            self.assertIn("Evidence only", map_html)
            self.assertIn("applyLayerPreset", map_html)
            self.assertIn("dock-layer-chip", map_html)
            self.assertIn('id="search-clear"', map_html)
            self.assertIn("search-result-meta", map_html)
            self.assertIn('id="time-record-count"', map_html)
            self.assertIn('data-time-interval="full"', map_html)
            self.assertIn("syncTimePresetButtons", map_html)
            self.assertIn("featureTimeWindow", map_html)
            self.assertIn("featureInTimeWindow", map_html)
            self.assertIn("featureTimeLabel", map_html)
            self.assertIn('id="legend-toggle"', map_html)
            self.assertIn("legend-group-label", map_html)
            self.assertIn("setLegendCollapsed", map_html)
            self.assertIn('id="mobile-panel-close"', map_html)
            self.assertIn('id="mobile-scrim"', map_html)
            self.assertIn("syncMobilePanelState", map_html)
            self.assertIn("event.key === 'Escape'", map_html)
            self.assertNotIn("Research Workspace", map_html)
            self.assertNotIn("Workspace Brief", map_html)
            self.assertNotIn("renderWorkspaceBrief", map_html)
            self.assertNotIn("renderCoverageMatrix", map_html)
            self.assertNotIn("renderFilterChips", map_html)
            self.assertNotIn("syncSectionNavWithScroll", map_html)
            self.assertIn('id="help-dialog"', map_html)
            self.assertIn("Workspace Guide", map_html)
            self.assertIn("openHelpDialog", map_html)
            self.assertIn('id="focus-card"', map_html)
            self.assertIn('id="focus-previous"', map_html)
            self.assertIn('id="focus-next"', map_html)
            self.assertIn('id="focus-zoom"', map_html)
            self.assertIn("Focused Record", map_html)
            self.assertIn("setFocusState", map_html)
            self.assertIn("focusPointAtVisibleIndex", map_html)
            self.assertIn("renderFocusCard", map_html)
            self.assertIn('id="center-readout"', map_html)
            self.assertIn("status-pill-label", map_html)
            self.assertIn('id="floating-legend"', map_html)
            self.assertIn("width: min(288px, calc(100vw - 32px));", map_html)
            self.assertIn(".control-panel.is-collapsed", map_html)
            self.assertIn("window.matchMedia('(max-width: 900px)')", map_html)
            self.assertIn("Show controls", map_html)
            self.assertIn(
                "params.set('panel', sidebar.classList.contains('is-collapsed') ? 'collapsed' : 'open')",
                map_html,
            )
            self.assertNotIn("<title>Nordic Countries AADR v62.0 Map</title>", map_html)
            self.assertIn("./_map_assets/leaflet/leaflet.css", map_html)
            self.assertNotIn("unpkg.com/leaflet", map_html)
            self.assertIn(
                "When the tracked data root contains mapped animal aDNA locality records",
                readme_text,
            )

            geojson = json.loads(
                (output / "nordic-atlas_samples.geojson").read_text(encoding="utf-8")
            )
            summary = json.loads(
                (output / "nordic-atlas_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(geojson["features"]), 3)
            self.assertEqual(summary["schema_version"], "atlas-bundle-summary.v1")
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
            self.assertEqual(
                summary["artifacts"]["extra_files"][-1]["filename"],
                "nordic-atlas_scientific_review.md",
            )

    def test_generate_multi_country_map_ships_public_animal_layers_and_filters(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            context_root = Path(tmp) / "data"
            self.write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                ],
            )
            self.write_tracked_animal_species(
                context_root / "adna" / "ovis_aries",
                latin_name="Ovis aries",
                common_name="sheep",
                locality="Baltic sheep lead",
                political_entity="Sweden",
                project_accession="PRJEB59481",
                support_class="accepted",
                product_role="domesticated_core",
                nordic_inclusion=True,
                chronology_bucket="1001-3000 BP",
                paper_title="Baltic short-tailed sheep aDNA",
                paper_doi="10.1000/sheep",
            )
            self.write_tracked_animal_species(
                context_root / "adna" / "rangifer_tarandus",
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

            generate_multi_country_map(
                version_dir=root,
                countries=["Sweden", "Norway"],
                output_dir=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
                context_root=context_root,
            )

            self.assertTrue((output / "nordic-atlas_animal_localities.geojson").exists())
            self.assertTrue(
                (output / "nordic-atlas_domesticated_animal_localities.geojson").exists()
            )
            self.assertTrue(
                (output / "nordic-atlas_comparator_animal_localities.geojson").exists()
            )
            self.assertTrue((output / "nordic-atlas_animal_atlas_evidence.csv").exists())
            self.assertTrue((output / "nordic-atlas_animal_atlas_evidence.json").exists())
            self.assertTrue(
                (output / "nordic-atlas_animal_point_traceability.json").exists()
            )

            map_html = (output / "nordic-atlas_map.html").read_text(encoding="utf-8")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            summary = json.loads(
                (output / "nordic-atlas_summary.json").read_text(encoding="utf-8")
            )
            animal_geojson = json.loads(
                (output / "nordic-atlas_animal_localities.geojson").read_text(
                    encoding="utf-8"
                )
            )

            self.assertIn("Animal Evidence", map_html)
            self.assertIn("Species Focus", map_html)
            self.assertIn("Animal Scope", map_html)
            self.assertIn("Chronology Buckets", map_html)
            self.assertIn("Nordic animal leads only", map_html)
            self.assertIn("Domesticated animal aDNA", map_html)
            self.assertIn("Comparator animal aDNA", map_html)
            self.assertIn("data-animal-species", map_html)
            self.assertIn("data-animal-scope", map_html)
            self.assertIn("data-animal-chronology", map_html)
            self.assertIn("featureMatchesAnimalFilters", map_html)
            self.assertIn("Ovis aries", map_html)
            self.assertIn("Rangifer tarandus", map_html)
            self.assertIn("Baltic sheep lead", map_html)
            self.assertIn("Svalbard reindeer lead", map_html)

            self.assertIn("## Animal aDNA Layers", readme_text)
            self.assertIn("Public Animal Filters", readme_text)
            self.assertIn("Domesticated-core animal evidence", readme_text)
            self.assertIn("Comparator animal evidence", readme_text)
            self.assertIn("Nordic animal leads only", readme_text)
            self.assertIn("Approximate or inferred coordinates remain visible", readme_text)

            self.assertEqual(summary["animal_atlas"]["total_species"], 2)
            self.assertEqual(summary["animal_atlas"]["domesticated_species_count"], 1)
            self.assertEqual(summary["animal_atlas"]["comparator_species_count"], 1)
            self.assertEqual(
                summary["artifacts"]["animal_localities_geojson"],
                "nordic-atlas_animal_localities.geojson",
            )
            self.assertEqual(
                summary["artifacts"]["animal_atlas_evidence_csv"],
                "nordic-atlas_animal_atlas_evidence.csv",
            )
            self.assertEqual(
                summary["artifacts"]["animal_atlas_evidence_json"],
                "nordic-atlas_animal_atlas_evidence.json",
            )
            self.assertEqual(
                summary["artifacts"]["animal_point_traceability_json"],
                "nordic-atlas_animal_point_traceability.json",
            )
            self.assertIn("Species focus", summary["animal_atlas"]["filter_surfaces"])
            self.assertIn(
                "Nordic animal leads only",
                summary["animal_atlas"]["filter_surfaces"],
            )
            self.assertEqual(
                summary["animal_atlas"]["direct_coordinate_feature_count"],
                0,
            )
            self.assertEqual(
                summary["animal_atlas"]["named_site_geocoded_feature_count"],
                2,
            )
            self.assertEqual(
                summary["animal_atlas"]["weaker_geography_feature_count"],
                0,
            )

            self.assertEqual(len(animal_geojson["features"]), 2)
            sheep_properties = animal_geojson["features"][0]["properties"]
            self.assertIn("feature_id", sheep_properties)
            self.assertIn("evidence_row_id", sheep_properties)
            self.assertIn("site_record_id", sheep_properties)
            self.assertIn("sample_record_ids", sheep_properties)
            self.assertIn("coordinate_basis", sheep_properties)
            self.assertIn("source_artifact_path", sheep_properties)

    def test_generate_multi_country_map_can_include_context_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            context_root = Path(tmp) / "data"
            gallery_root = Path(tmp) / "docs" / "gallery"
            gallery_root.mkdir(parents=True, exist_ok=True)
            (gallery_root / "2026-02-26-data-collection.JPG").write_bytes(b"jpeg")
            (gallery_root / "2026-02-26-data-collection.mp4").write_bytes(b"mp4")
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            self.write_geojson(
                context_root
                / "landclim"
                / "normalized"
                / "nordic_pollen_site_sequences.geojson",
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
            self.write_tracked_animal_species(
                context_root / "adna" / "ovis_aries",
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
            self.write_tracked_animal_species(
                context_root / "adna" / "rangifer_tarandus",
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
            self.write_geojson(
                context_root
                / "sead"
                / "normalized"
                / "nordic_environmental_sites.geojson",
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
            self.write_json(
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
            self.write_json(
                context_root / "raa" / "normalized" / "sweden_archaeology_layer.json",
                cast(dict[str, object], archaeology_metadata),
            )
            self.write_json(
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

            generate_multi_country_map(
                version_dir=root,
                countries=["Sweden"],
                output_dir=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
                context_root=context_root,
            )

            map_html = (output / "nordic-atlas_map.html").read_text(encoding="utf-8")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("Country Filters", map_html)
            self.assertIn("Search points and sites", map_html)
            self.assertIn("Filters", map_html)
            self.assertIn("Date Window", map_html)
            self.assertIn("Copy link", map_html)
            self.assertIn("Country boundaries", map_html)
            self.assertIn("dock-layer-chip", map_html)
            self.assertIn('class="control-panel"', map_html)
            self.assertIn("width: min(288px, calc(100vw - 32px));", map_html)
            self.assertIn('details class="control-group"', map_html)
            self.assertIn("LandClim pollen sites", map_html)
            self.assertIn("LandClim REVEALS grid cells", map_html)
            self.assertIn("Neotoma pollen sites", map_html)
            self.assertIn("SEAD sites", map_html)
            self.assertIn("Fieldwork documentation", map_html)
            self.assertIn("Lyngsjön Lake field sampling", map_html)
            self.assertIn("../../gallery/2026-02-26-data-collection.mp4", map_html)
            self.assertIn("popup-media-link", map_html)
            self.assertIn("RAÄ archaeology density", map_html)
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
            self.assertTrue((output / "sweden_archaeology_density.geojson").exists())
            self.assertTrue((output / "nordic_country_boundaries.geojson").exists())

    def test_generate_multi_country_map_uses_context_layer_dates_for_time_window(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            context_root = Path(tmp) / "data"
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t\t\tHO\tF",
                ],
            )
            self.write_json(
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
            self.write_json(
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
            self.assertIn('data-time-interval="full">Full span</button>', map_html)

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
            map_html = (output / "north-atlantic_map.html").read_text(encoding="utf-8")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            self.assertIn("No visible records", map_html)
            self.assertIn("restore the default map state", map_html)
            self.assertIn("| Iceland | 0 |", readme_text)

    def test_generate_multi_country_map_rejects_context_point_layers_without_identity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            context_root = Path(tmp) / "data"
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            self.write_json(
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
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )
            self.write_json(
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

    def test_generate_multi_country_map_replaces_stale_bundle_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            output.mkdir(parents=True, exist_ok=True)
            stale_file = output / "stale.geojson"
            stale_file.write_text("stale", encoding="utf-8")
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            generate_multi_country_map(
                version_dir=root,
                countries=["Sweden"],
                output_dir=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
            )

            self.assertFalse(stale_file.exists())
            self.assertTrue((output / "nordic-atlas_map.html").exists())

    def test_generate_multi_country_map_preserves_previous_bundle_when_publication_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            output.mkdir(parents=True, exist_ok=True)
            preserved_file = output / "README.md"
            preserved_file.write_text("kept", encoding="utf-8")
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            def fail_after_partial_write(
                path: Path, payload: dict[str, object]
            ) -> None:
                path.write_text("partial", encoding="utf-8")
                raise RuntimeError("summary failure")

            with (
                patch(
                    "bijux_pollenomics.reporting.service.write_summary_json",
                    side_effect=fail_after_partial_write,
                ),
                self.assertRaisesRegex(RuntimeError, "summary failure"),
            ):
                generate_multi_country_map(
                    version_dir=root,
                    countries=["Sweden"],
                    output_dir=output,
                    title="Nordic Evidence Atlas",
                    slug="nordic-atlas",
                )

            self.assertEqual(preserved_file.read_text(encoding="utf-8"), "kept")
            self.assertFalse((output.parent / ".nordic-atlas.tmp").exists())

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
            self.write_tracked_animal_species(
                context_root / "adna" / "ovis_aries",
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
            self.write_tracked_animal_species(
                context_root / "adna" / "rangifer_tarandus",
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

            report = generate_published_reports(
                version_dir=root,
                countries=["Sweden", "Norway"],
                output_root=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
                context_root=context_root,
            )

            self.assertEqual(report.countries, ("Sweden", "Norway"))
            self.assertTrue((output / "published_reports_summary.json").exists())
            self.assertTrue((output / "animal_output_audit.json").exists())
            self.assertTrue((output / "animal_output_audit.md").exists())
            self.assertTrue((output / "animal_country_species_coverage.json").exists())
            self.assertTrue((output / "animal_country_species_coverage.md").exists())
            self.assertTrue((output / "animal_human_chronology_overlap.json").exists())
            self.assertTrue((output / "animal_pollen_chronology_overlap.json").exists())
            self.assertTrue(
                (output / "animal_first_appearance_by_country.json").exists()
            )
            self.assertTrue((output / "nordic_farming_history_scenario.json").exists())
            self.assertTrue(
                (output / "nordic-atlas" / "nordic-atlas_map.html").exists()
            )
            self.assertTrue((output / "sweden" / "README.md").exists())
            self.assertTrue((output / "norway" / "README.md").exists())
            self.assertTrue(
                (output / "sweden" / "sweden_animal_adna_v62.0_summary.json").exists()
            )
            self.assertTrue(
                (output / "norway" / "norway_animal_adna_v62.0_summary.json").exists()
            )
            sweden_readme = (output / "sweden" / "README.md").read_text(
                encoding="utf-8"
            )
            published_summary = json.loads(
                (output / "published_reports_summary.json").read_text(encoding="utf-8")
            )
            animal_output_audit = json.loads(
                (output / "animal_output_audit.json").read_text(encoding="utf-8")
            )
            atlas_summary = json.loads(
                (output / "nordic-atlas" / "nordic-atlas_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            atlas_traceability = json.loads(
                (
                    output / "nordic-atlas" / "nordic-atlas_animal_point_traceability.json"
                ).read_text(encoding="utf-8")
            )
            sweden_animal_geojson = json.loads(
                (
                    output / "sweden" / "sweden_animal_adna_v62.0_localities.geojson"
                ).read_text(encoding="utf-8")
            )
            sweden_summary = json.loads(
                (output / "sweden" / "sweden_aadr_v62.0_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn("../nordic-atlas/nordic-atlas_map.html", sweden_readme)
            self.assertIn(">Nordic Evidence Atlas</a>", sweden_readme)
            self.assertEqual(report.shared_map_dir, output / "nordic-atlas")
            self.assertIn(output / "sweden", report.country_output_dirs)
            self.assertEqual(
                published_summary["artifacts"]["shared_bundle"]["slug"], "nordic-atlas"
            )
            self.assertEqual(
                published_summary["artifacts"]["shared_bundle"]["bundle_manifest"],
                "nordic-atlas_bundle.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["animal_output_audit_json"],
                "animal_output_audit.json",
            )
            self.assertEqual(
                published_summary["artifacts"]["animal_output_audit_markdown"],
                "animal_output_audit.md",
            )
            self.assertEqual(
                published_summary["artifacts"]["public_animal_reporting"][
                    "animal_country_species_coverage_json"
                ],
                "animal_country_species_coverage.json",
            )
            self.assertEqual(animal_output_audit["report_root"], str(output))
            sheep_audit_row = next(
                row
                for row in animal_output_audit["species_rows"]
                if row["species_latin_name"] == "Ovis aries"
            )
            self.assertEqual(sheep_audit_row["country_output_count"], 1)
            self.assertIn("sweden", published_summary["artifacts"]["country_bundles"])
            self.assertEqual(
                published_summary["artifacts"]["country_bundles"]["sweden"][
                    "bundle_manifest"
                ],
                "sweden_aadr_v62.0_bundle.json",
            )
            self.assertEqual(sweden_summary["animal_adna"]["total_species"], 1)
            self.assertEqual(atlas_summary["output_dir"], str(output / "nordic-atlas"))
            self.assertEqual(sweden_summary["output_dir"], str(output / "sweden"))
            self.assertNotIn(".report.tmp", atlas_summary["output_dir"])
            self.assertNotIn(".report.tmp", sweden_summary["output_dir"])
            self.assertEqual(
                atlas_summary["artifacts"]["animal_point_traceability_json"],
                "nordic-atlas_animal_point_traceability.json",
            )
            sweden_evidence_row_ids = {
                feature["properties"]["evidence_row_id"]
                for feature in sweden_animal_geojson["features"]
            }
            atlas_evidence_row_ids = {
                row["evidence_row_id"]
                for row in atlas_traceability["rows"]
                if row["species_latin_name"] == "Ovis aries"
            }
            self.assertEqual(sweden_evidence_row_ids, atlas_evidence_row_ids)

    def test_generate_published_reports_removes_stale_bundle_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report"
            self.write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperB\t2021\t600 BCE\t2550\tAG\tM",
                ],
            )

            generate_published_reports(
                version_dir=root,
                countries=["Sweden", "Norway"],
                output_root=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
            )
            self.assertTrue((output / "norway").exists())

            generate_published_reports(
                version_dir=root,
                countries=["Sweden"],
                output_root=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
            )

            self.assertFalse((output / "norway").exists())
            self.assertTrue((output / "sweden").exists())

    def test_generate_published_reports_preserves_previous_tree_when_publication_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report"
            preserved_file = output / "published_reports_summary.json"
            output.mkdir(parents=True, exist_ok=True)
            preserved_file.write_text("kept", encoding="utf-8")
            self.write_anno(
                root / "ho" / "v62.0_HO_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                ],
            )

            def fail_after_partial_write(
                path: Path, payload: dict[str, object]
            ) -> None:
                path.write_text("partial", encoding="utf-8")
                raise RuntimeError("summary failure")

            with (
                patch(
                    "bijux_pollenomics.reporting.service.write_summary_json",
                    side_effect=fail_after_partial_write,
                ),
                self.assertRaisesRegex(RuntimeError, "summary failure"),
            ):
                generate_published_reports(
                    version_dir=root,
                    countries=["Sweden"],
                    output_root=output,
                    title="Nordic Evidence Atlas",
                    slug="nordic-atlas",
                )

            self.assertEqual(preserved_file.read_text(encoding="utf-8"), "kept")
            self.assertFalse((output.parent / ".report.tmp").exists())

    def write_anno(self, path: Path, rows: list[str]) -> None:
        write_anno_file(path, rows, header=AADR_HEADER)

    def write_geojson(
        self, path: Path, layer_key: str, layer_label: str, category: str
    ) -> None:
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

    def write_json(
        self, path: Path, payload: dict[str, object] | Collection[str]
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def write_tracked_animal_species(
        self,
        species_root: Path,
        *,
        latin_name: str,
        common_name: str,
        locality: str,
        political_entity: str,
        project_accession: str,
        support_class: str,
        product_role: str,
        nordic_inclusion: bool,
        chronology_bucket: str,
        paper_title: str,
        paper_doi: str,
    ) -> None:
        species_root.mkdir(parents=True, exist_ok=True)
        species_slug = species_root.name
        stable_token = f"{species_slug}:project-locality:{project_accession.lower()}"
        sample_token = f"{species_slug}:sample:{project_accession.lower()}"
        sample_site_token = f"{species_slug}:sample-site:{project_accession.lower()}"
        inclusion_status = (
            "comparator_site_curated"
            if product_role == "comparator"
            else "nordic_lead_site_curated"
            if nordic_inclusion
            else "site_curated"
        )
        self.write_json(
            species_root / "normalized" / "locality_summaries.json",
            {
                "localities": [
                    {
                        "identity": {
                            "namespace": "animal-locality",
                            "stable_token": stable_token,
                            "locality_text": locality,
                            "political_entity": political_entity,
                            "source_anchor_tokens": [project_accession],
                        },
                        "species_latin_name": latin_name,
                        "species_common_name": common_name,
                        "source_family": "ENA",
                        "source_releases": ["tracked"],
                        "record_modalities": ["metadata_only"],
                        "review_strengths": ["paper_pinned"],
                        "provenance_qualities": ["tracked_curated"],
                        "locality": locality,
                        "coordinates": {
                            "latitude": 59.4,
                            "longitude": 18.1,
                            "latitude_text": "59.4",
                            "longitude_text": "18.1",
                            "confidence": "approximate",
                        },
                        "sample_count": 1,
                        "sample_ids": [f"{project_accession}:lead"],
                        "datasets": ["animal-adna"],
                        "chronology": {
                            "original_text": chronology_bucket,
                            "time_start_bp": 1200,
                            "time_end_bp": 1600,
                            "time_mean_bp": 1400,
                            "dating_basis": "bp_window",
                        },
                        "sample_namespace": "animal-locality",
                        "project_accessions": [project_accession],
                        "original_location_text": locality,
                        "nordic_inclusion": nordic_inclusion,
                        "nordic_inclusion_reason": "Curated Nordic lead",
                        "interpretation_note": "Tracked atlas locality lead",
                    }
                ]
            },
        )
        self.write_json(
            species_root / "normalized" / "sample_records.json",
            {
                "schema_version": "adna-sample-record-export.v1",
                "species_latin_name": latin_name,
                "samples": [
                    {
                        "identity": {
                            "namespace": f"{species_slug}:curated_sample",
                            "stable_token": sample_token,
                            "accession_lineage": [
                                f"species:{latin_name}",
                                "source:ENA",
                                f"project:{project_accession}",
                                f"sample:{project_accession}",
                            ],
                        },
                        "locality_identity": {
                            "namespace": f"{species_slug}:sample_locality",
                            "stable_token": sample_site_token,
                            "locality_text": locality,
                            "political_entity": political_entity,
                            "source_anchor_tokens": [project_accession, "project_accession_anchor"],
                        },
                        "species_latin_name": latin_name,
                        "species_common_name": common_name,
                        "source_family": "ENA",
                        "source_release": project_accession,
                        "record_modality": "archive_reads",
                        "review_strength": "primary_paper_pinned",
                        "provenance_quality": "manual_curation_only",
                        "master_id": project_accession,
                        "group_id": project_accession,
                        "locality": locality,
                        "political_entity": political_entity,
                        "coordinates": {
                            "latitude": None,
                            "longitude": None,
                            "latitude_text": "",
                            "longitude_text": "",
                            "confidence": "withheld",
                        },
                        "publication": paper_title,
                        "year_first_published": "2024",
                        "full_date": chronology_bucket,
                        "chronology": {
                            "original_text": chronology_bucket,
                            "time_start_bp": 1200,
                            "time_end_bp": 1600,
                            "time_mean_bp": 1400,
                            "date_stddev_bp": "",
                            "dating_basis": "bp_window",
                        },
                        "data_type": "archive_project_context",
                        "molecular_sex": "",
                        "datasets": [f"{species_slug}:project:{project_accession}"],
                        "project_accession": project_accession,
                        "paper_doi": paper_doi,
                        "paper_url": f"https://doi.org/{paper_doi}",
                        "supplementary_source": f"supplementary/{project_accession}.pdf",
                        "inclusion_status": inclusion_status,
                        "inclusion_note": "Curated into the atlas evidence contract.",
                        "sample_basis": "project_accession_anchor",
                    }
                ],
            },
        )
        self.write_json(
            species_root / "normalized" / "coordinate_provenance.json",
            {
                "schema_version": "adna-coordinate-provenance-export.v1",
                "species_latin_name": latin_name,
                "coordinate_provenance": [
                    {
                        "project_accession": project_accession,
                        "species_latin_name": latin_name,
                        "species_common_name": common_name,
                        "site_label": locality,
                        "original_place_text": locality,
                        "resolved_place_text": locality,
                        "political_entity": political_entity,
                        "source_artifact_path": f"adna/source_library/papers/{paper_doi.replace('/', '-')}/article.html",
                        "source_locator": "supplementary table",
                        "coordinate_basis": "named_site_geocoding",
                        "mapping_posture": "mappable_point",
                        "latitude_text": "59.4",
                        "longitude_text": "18.1",
                        "geocoding_method": "manual_named_place_resolution",
                        "geocoder_or_gazetteer": "test archaeological site anchor",
                        "confidence_rationale": "Test fixture publishes one named-place geocode.",
                        "coordinate_confidence": "approximate",
                        "paper_doi": paper_doi,
                        "paper_url": f"https://doi.org/{paper_doi}",
                        "supplementary_source": f"supplementary/{project_accession}.pdf",
                        "chronology_text": chronology_bucket,
                        "time_start_bp": 1200,
                        "time_end_bp": 1600,
                        "dating_basis": "bp_window",
                        "comparator_context": product_role == "comparator",
                        "domestication_context": product_role,
                        "interpretation_note": "Test fixture named-place coordinate provenance.",
                        "support_gap_note": "",
                    }
                ],
            },
        )
        self.write_json(
            species_root / "normalized" / "site_evidence.json",
            {
                "schema_version": "adna-site-evidence-export.v1",
                "species_latin_name": latin_name,
                "site_evidence": [
                    {
                        "project_accession": project_accession,
                        "species_latin_name": latin_name,
                        "species_common_name": common_name,
                        "site_label": locality,
                        "political_entity": political_entity,
                        "source_artifact_path": f"adna/source_library/papers/{paper_doi.replace('/', '-')}/article.html",
                        "source_artifact_kind": "article_html_body_quote",
                        "source_locator": "supplementary table",
                        "exact_source_text": f"{locality} named in supplementary support.",
                        "source_support_status": "article_exact_quote",
                        "paper_doi": paper_doi,
                        "paper_url": f"https://doi.org/{paper_doi}",
                        "supplementary_source": f"supplementary/{project_accession}.pdf",
                        "coordinate_basis": "site_level_localities",
                        "latitude_text": "59.4",
                        "longitude_text": "18.1",
                        "chronology_text": chronology_bucket,
                        "time_start_bp": 1200,
                        "time_end_bp": 1600,
                        "dating_basis": "bp_window",
                        "comparator_context": product_role == "comparator",
                        "domestication_context": product_role,
                        "interpretation_note": "Test fixture site evidence row.",
                        "support_gap_note": "",
                    }
                ],
            },
        )
        self.write_json(
            species_root / "reports" / "support_summary.json",
            {
                "dataset_review": {
                    "product_role": product_role,
                    "chronology_bucket": chronology_bucket,
                }
            },
        )
        review_bucket = (
            "comparator_projects" if support_class == "comparator_only" else "accepted_projects"
        )
        self.write_json(
            species_root / "review" / "species_review.json",
            {
                "accepted_projects": []
                if review_bucket != "accepted_projects"
                else [
                    {
                        "project_accession": project_accession,
                        "support_class": support_class,
                        "reason": "Mapped locality retained in atlas.",
                        "paper_title": paper_title,
                        "paper_doi": paper_doi,
                        "nordic_relevance": "nordic_lead" if nordic_inclusion else "non_nordic",
                        "nordic_relevance_reason": "Curated Nordic lead",
                    }
                ],
                "rejected_projects": [],
                "too_weak_projects": [],
                "comparator_projects": []
                if review_bucket != "comparator_projects"
                else [
                    {
                        "project_accession": project_accession,
                        "support_class": support_class,
                        "reason": "Comparator evidence remains visible with caveats.",
                        "paper_title": paper_title,
                        "paper_doi": paper_doi,
                        "nordic_relevance": "nordic_lead" if nordic_inclusion else "non_nordic",
                        "nordic_relevance_reason": "Curated Nordic lead",
                    }
                ],
                "nordic_unmapped_leads": [],
            },
        )
        citation_manifest = (
            "project_accession,paper_title,paper_doi,publication_year,journal_title\n"
            f"{project_accession},{paper_title},{paper_doi},2024,Tracked Animal Journal\n"
        )
        citation_path = species_root / "manifests" / "citation_manifest.csv"
        citation_path.parent.mkdir(parents=True, exist_ok=True)
        citation_path.write_text(citation_manifest, encoding="utf-8")

    def sample_record(
        self,
        genetic_id: str,
        locality: str,
        political_entity: str,
        datasets: tuple[str, ...],
    ) -> SampleRecord:
        from bijux_pollenomics.adna import (
            AdnaChronology,
            AdnaCoordinate,
            AdnaLocalityIdentity,
            AdnaSampleIdentity,
        )
        from bijux_pollenomics.reporting.models import SampleRecord

        return SampleRecord(
            identity=AdnaSampleIdentity(
                namespace="homo_sapiens:aadr_genetic_id",
                stable_token=genetic_id,
                accession_lineage=(
                    "species:Homo sapiens",
                    "source:AADR",
                    f"dataset:{datasets[0]}",
                    f"genetic_id:{genetic_id}",
                ),
            ),
            locality_identity=AdnaLocalityIdentity(
                namespace="homo_sapiens:locality",
                stable_token=(
                    f"homo_sapiens:aadr:{political_entity.casefold()}:{locality.casefold()}:"
                    "59-8586-17-6389"
                ),
                locality_text=locality,
                political_entity=political_entity,
                source_anchor_tokens=("AADR", "59.8586", "17.6389"),
            ),
            species_latin_name="Homo sapiens",
            species_common_name="human",
            source_family="AADR",
            source_release="v62.0",
            record_modality="metadata_only",
            review_strength="curated_release_metadata",
            provenance_quality="release_manifest_pinned",
            master_id=genetic_id,
            group_id=f"{political_entity}_Group",
            locality=locality,
            political_entity=political_entity,
            coordinates=AdnaCoordinate(
                latitude=59.8586,
                longitude=17.6389,
                latitude_text="59.8586",
                longitude_text="17.6389",
                confidence="unknown",
            ),
            publication="PaperA",
            year_first_published="2022",
            full_date="500 BCE",
            chronology=AdnaChronology(
                original_text="2200-2700 BP",
                time_start_bp=2200,
                time_end_bp=2700,
                time_mean_bp=2450,
                dating_basis="bp_mean_and_stddev",
            ),
            data_type="AG",
            molecular_sex="F",
            datasets=datasets,
        )


if __name__ == "__main__":
    unittest.main()
