from __future__ import annotations

import unittest

from bijux_pollenomics.adna.projects.evidence.sites import (
    build_species_site_evidence_rows,
    resolve_project_site_evidence,
)


class AdnaSiteEvidenceUnitTests(unittest.TestCase):
    def test_resolve_project_site_evidence_expands_botai_to_sample_owned_sites(
        self,
    ) -> None:
        rows = resolve_project_site_evidence("PRJEB22390")

        self.assertGreater(len(rows), 10)
        botai = next(row for row in rows if row.site_label == "Botai")
        self.assertEqual(botai.source_support_status, "supplementary_table_row")
        self.assertIn("Botai_1_5500", botai.exact_source_text)
        self.assertIn("aao3297_tables15.xlsx", botai.source_artifact_path)

    def test_resolve_project_site_evidence_prefers_direct_horse_sample_rows(
        self,
    ) -> None:
        rows = resolve_project_site_evidence("PRJEB31613")

        uppsala = next(row for row in rows if row.site_label == "Uppsala")
        self.assertEqual(uppsala.political_entity, "Sweden")
        self.assertEqual(uppsala.source_support_status, "supplementary_table_row")
        self.assertEqual(uppsala.coordinate_basis, "supplementary_table_coordinates")
        self.assertEqual(uppsala.latitude_text, "59.860999999999997")
        self.assertEqual(uppsala.longitude_text, "17.638999999999999")
        self.assertIn("Uppsala_Upps02_1317", uppsala.exact_source_text)

    def test_build_species_site_evidence_rows_keeps_requested_accession_order(
        self,
    ) -> None:
        rows = build_species_site_evidence_rows(("PRJEB59481", "PRJEB60484", "unknown"))

        self.assertEqual(
            [row.project_accession for row in rows],
            ["PRJEB59481", "PRJEB59481", "PRJEB60484"],
        )

    def test_baltic_sheep_sites_are_sample_bound_without_invented_time(self) -> None:
        rows = resolve_project_site_evidence("PRJEB59481")

        self.assertEqual(
            {row.site_label for row in rows}, {"Kastelholm", "Stora Förvar"}
        )
        self.assertTrue(
            all(row.source_support_status == "archive_sample_record" for row in rows)
        )
        self.assertTrue(all(row.time_start_bp is None for row in rows))
        self.assertTrue(all(row.time_end_bp is None for row in rows))
        self.assertTrue(all(row.chronology_text == "" for row in rows))
        self.assertTrue(
            all(
                row.source_artifact_path.endswith(".xml")
                and "/ena_samples/SAMEA" in row.source_artifact_path
                for row in rows
            )
        )
        self.assertTrue(all(row.source_locator.endswith("/DESCRIPTION") for row in rows))
        self.assertTrue(
            all("Sheep humerus excavated in" in row.exact_source_text for row in rows)
        )

    def test_cat_sites_do_not_flatten_distinct_sample_chronologies(self) -> None:
        rows = resolve_project_site_evidence("PRJEB81815")

        self.assertEqual(len(rows), 61)
        self.assertTrue(
            all(row.source_support_status == "supplementary_table_row" for row in rows)
        )
        self.assertTrue(
            all(
                row.domestication_context == "mixed_source_native_cat_taxa"
                for row in rows
            )
        )
        shared_date_site = next(
            row for row in rows if row.site_label == "Haithabu, settlement area"
        )
        multi_date_site = next(
            row for row in rows if row.site_label == "Roca vecchia (Melendugno, Lecce)"
        )
        self.assertEqual(shared_date_site.chronology_text, "900-1150 BP")
        self.assertEqual(multi_date_site.chronology_text, "")
        self.assertTrue(
            all("transect" not in row.site_label.casefold() for row in rows)
        )

    def test_cattle_site_evidence_marks_archive_backed_gap_explicitly(self) -> None:
        rows = resolve_project_site_evidence("PRJNA705960")

        self.assertEqual(rows[0].source_support_status, "archive_description_quote")
        self.assertIn("Galicia", rows[0].exact_source_text)
        self.assertEqual(rows[0].coordinate_basis, "unresolved_location_state")
        self.assertEqual(rows[0].latitude_text, "")
        self.assertEqual(rows[0].longitude_text, "")
        self.assertIsNone(rows[0].time_start_bp)
        self.assertIsNone(rows[0].time_end_bp)
        self.assertIn("No local primary paper", rows[0].support_gap_note)
        self.assertIn("progenitor", rows[0].interpretation_note)

    def test_context_sources_do_not_gain_unsupported_coordinates_or_numeric_time(
        self,
    ) -> None:
        for accession in ("SRS1407451", "PRJEB60484", "SRP073444"):
            row = resolve_project_site_evidence(accession)[0]
            self.assertEqual(row.coordinate_basis, "unresolved_location_state")
            self.assertEqual(row.latitude_text, "")
            self.assertEqual(row.longitude_text, "")
            self.assertIsNone(row.time_start_bp)
            self.assertIsNone(row.time_end_bp)

        camel = resolve_project_site_evidence("SRP073444")[0]
        self.assertEqual(
            camel.site_label, "Site 1040 near Wadi Halfa dromedary context"
        )
        self.assertEqual(camel.chronology_text, "Late Pleistocene")

    def test_comparator_site_evidence_rows_stay_marked_as_comparators(self) -> None:
        reindeer = resolve_project_site_evidence("PRJEB60484")[0]
        donkey = resolve_project_site_evidence("PRJEB52849")[0]

        self.assertTrue(reindeer.comparator_context)
        self.assertTrue(donkey.comparator_context)
        self.assertEqual(reindeer.domestication_context, "comparator_context")
        self.assertEqual(donkey.domestication_context, "comparator_context")

    def test_aurochs_sites_remain_wild_or_progenitor_context(self) -> None:
        rows = resolve_project_site_evidence("PRJEB75467")

        self.assertEqual(len(rows), 5)
        self.assertTrue(
            all(
                row.domestication_context == "wild_or_progenitor_context"
                and not row.comparator_context
                for row in rows
            )
        )


if __name__ == "__main__":
    unittest.main()
