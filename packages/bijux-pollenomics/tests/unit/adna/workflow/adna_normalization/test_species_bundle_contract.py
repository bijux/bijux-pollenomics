from __future__ import annotations

import unittest

from bijux_pollenomics.adna import build_species_normalization_bundle

from .marks import GENERATED_ARTIFACTS

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_species_normalization_bundle_builds_project_and_study_summaries_for_horse(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("horse")

        self.assertEqual(
            bundle.schema_version,
            "adna-nonhuman-normalization-bundle.v1",
        )
        self.assertEqual(bundle.species.latin_name, "Equus caballus")
        self.assertTrue(bundle.sample_records)
        self.assertTrue(bundle.locality_records)
        self.assertTrue(bundle.project_summaries)
        self.assertTrue(bundle.study_summaries)
        self.assertTrue(bundle.lineage_records)
        self.assertTrue(bundle.refusals)
        self.assertEqual(len(bundle.sample_records), 550)
        self.assertEqual(len(bundle.locality_records), 240)
        self.assertEqual(len(bundle.coordinate_provenance_records), 208)
        project = next(
            item
            for item in bundle.project_summaries
            if item.project_accession == "PRJEB22390"
        )
        self.assertEqual(project.domestication_status, "domesticated_core")
        self.assertEqual(project.support_class, "domesticated_core_curated")
        self.assertEqual(project.coordinate_policy, "site_level_coordinates_expected")
        self.assertEqual(project.chronology_policy, "bp_interval_expected")
        self.assertEqual(project.paper_url, "https://doi.org/10.1126/science.aao3297")
        self.assertEqual(project.review_strength, "primary_paper_pinned")
        sample = next(
            item
            for item in bundle.sample_records
            if item.project_accession == "PRJEB22390"
            and item.archive_native_sample_id == "CGG_1_018173"
        )
        self.assertEqual(sample.paper_doi, "10.1126/science.aao3297")
        self.assertEqual(sample.inclusion_status, "site_curated")
        self.assertEqual(sample.sample_basis, "supplementary_table_sample_label_anchor")
        self.assertEqual(sample.chronology_strength, "sample_owned_interval")
        self.assertEqual(sample.chronology_normalization_status, "normalized_point")
        self.assertEqual(sample.chronology.evidence_class, "direct_radiocarbon_date")
        self.assertEqual(sample.chronology.precision_posture, "sample_precise_point")
        self.assertEqual(
            sample.locality_identity.locality_text,
            "Botai",
        )
        coordinate_provenance = next(
            item
            for item in bundle.coordinate_provenance_records
            if item.project_accession == "PRJEB44430" and item.site_label == "Ginnerup"
        )
        self.assertEqual(coordinate_provenance.mapping_posture, "mappable_point")
        self.assertEqual(
            coordinate_provenance.coordinate_basis, "supplementary_table_coordinates"
        )
        self.assertEqual(coordinate_provenance.coordinate_confidence, "exact")
        site_evidence = next(
            item
            for item in bundle.site_evidence_records
            if item.project_accession == "PRJEB31613" and item.site_label == "Uppsala"
        )
        self.assertEqual(site_evidence.source_support_status, "supplementary_table_row")
        self.assertIn("Uppsala", site_evidence.exact_source_text)
        self.assertEqual(
            bundle.lineage_records[0].schema_version,
            "adna-normalization-lineage.v1",
        )
        locality = next(
            item for item in bundle.locality_records if item.locality == "Ginnerup"
        )
        self.assertTrue(locality.nordic_inclusion)
        self.assertEqual(locality.coordinate_confidence, "exact")
        self.assertEqual(locality.sample_count, 2)
        self.assertEqual((locality.time_start_bp, locality.time_end_bp), (4944, 4961))

    def test_species_normalization_bundle_deduplicates_project_tokens_deterministically(
        self,
    ) -> None:
        first = build_species_normalization_bundle("horse")
        second = build_species_normalization_bundle("horse")

        self.assertEqual(
            [item.summary_token for item in first.project_summaries],
            sorted(item.summary_token for item in first.project_summaries),
        )
        self.assertEqual(first.as_dict(), second.as_dict())

    def test_species_normalization_bundle_carries_nordic_context_and_caveats(
        self,
    ) -> None:
        sheep_bundle = build_species_normalization_bundle("sheep")
        sheep_project = next(
            item
            for item in sheep_bundle.project_summaries
            if item.project_accession == "PRJEB59481"
        )
        camel_bundle = build_species_normalization_bundle("camel")
        camel_project = next(
            item
            for item in camel_bundle.project_summaries
            if item.project_accession == "SRP073444"
        )

        self.assertEqual(sheep_project.nordic_relevance, "nordic_relevant_mapped")
        self.assertNotIn("unmapped", sheep_project.interpretation_caveat)
        self.assertEqual(camel_project.nordic_relevance, "non_nordic")
        self.assertIn(
            "not as shipped Nordic evidence", camel_project.interpretation_caveat
        )
        sheep_locality = next(
            item
            for item in sheep_bundle.locality_records
            if "PRJEB59481" in item.project_accessions
        )
        self.assertTrue(sheep_locality.nordic_inclusion)
        self.assertEqual(sheep_locality.coordinate_confidence, "approximate")
        self.assertIn("Nordic", sheep_locality.nordic_inclusion_reason)
        horse_localities = {
            (item.locality, item.identity.political_entity)
            for item in build_species_normalization_bundle("horse").locality_records
            if item.nordic_inclusion
        }
        self.assertEqual(
            horse_localities,
            {
                ("Berufjordur", "Iceland"),
                ("Granastaðir", "Iceland"),
                ("Uppsala", "Sweden"),
                ("Ginnerup", "Denmark"),
            },
        )
