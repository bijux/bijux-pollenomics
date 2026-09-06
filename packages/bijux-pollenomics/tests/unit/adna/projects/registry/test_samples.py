from __future__ import annotations

from collections import Counter
import unittest

from bijux_pollenomics.adna.projects.registry.samples import (
    _matching_locality_lead,
    build_species_curated_sample_rows,
)
from bijux_pollenomics.adna.projects.registry.localities import AdnaProjectLocalityLead


class AdnaSampleRegistryUnitTests(unittest.TestCase):
    def test_species_curated_sample_rows_cover_all_tracked_project_units(self) -> None:
        rows = build_species_curated_sample_rows("horse")

        self.assertEqual(
            Counter(row.project_accession for row in rows),
            Counter(
                {
                    "PRJEB10854": 1,
                    "PRJEB19970": 15,
                    "PRJEB22390": 42,
                    "PRJEB31613": 245,
                    "PRJEB44430": 248,
                    "PRJEB56293": 1,
                    "PRJEB7537": 1,
                    "PRJEB9799": 1,
                }
            ),
        )
        botai = next(
            row
            for row in rows
            if row.project_accession == "PRJEB22390" and row.site_label == "Botai"
        )
        self.assertEqual(botai.site_label, "Botai")
        self.assertEqual(botai.inclusion_status, "site_curated")

        nordic = next(
            row
            for row in rows
            if row.project_accession == "PRJEB31613" and row.site_label == "Uppsala"
        )
        self.assertEqual(nordic.political_entity, "Sweden")
        self.assertEqual(nordic.coordinate_basis, "supplementary_table_coordinates")
        self.assertEqual(nordic.chronology_text, "1217-1417 BP")

        ginnerup = next(
            row
            for row in rows
            if row.project_accession == "PRJEB44430" and row.site_label == "Ginnerup"
        )
        self.assertEqual(ginnerup.political_entity, "Denmark")
        self.assertEqual(ginnerup.latitude_text, "56.41134")
        self.assertEqual(ginnerup.longitude_text, "10.74481")
        self.assertEqual(ginnerup.chronology_text, "4961 BP")

    def test_species_curated_sample_rows_preserve_supplementary_path_when_archived(
        self,
    ) -> None:
        rows = build_species_curated_sample_rows("sheep")
        baltic = next(row for row in rows if row.project_accession == "PRJEB59481")

        self.assertEqual(baltic.paper_doi, "10.1093/gbe/evae114")
        self.assertEqual(baltic.inclusion_status, "nordic_lead_site_curated")
        self.assertEqual(baltic.supplementary_source, "")

    def test_baltic_sheep_samples_select_their_exact_locality_lead(self) -> None:
        rows = tuple(
            row
            for row in build_species_curated_sample_rows("sheep")
            if row.project_accession == "PRJEB59481"
        )

        self.assertEqual(len(rows), 5)
        self.assertEqual(
            {row.paper_native_sample_label: row.site_label for row in rows},
            {
                "AKAS001": "Kastelholm",
                "AKAS002": "Kastelholm",
                "ASTF001": "Stora Förvar",
                "ASTF002": "Stora Förvar",
                "ASTF003": "Stora Förvar",
            },
        )
        by_label = {row.paper_native_sample_label: row for row in rows}
        self.assertEqual(
            {
                label: (row.time_start_bp, row.time_end_bp)
                for label, row in by_label.items()
            },
            {
                "AKAS001": (340, 527),
                "AKAS002": (400, 450),
                "ASTF001": (3699, 3957),
                "ASTF002": (3936, 4151),
                "ASTF003": (None, None),
            },
        )
        self.assertEqual(
            {(row.latitude_text, row.longitude_text) for row in rows},
            {("60.23", "20.08"), ("57.29", "17.97")},
        )
        self.assertTrue(
            all(row.coordinate_basis == "archive_coordinates" for row in rows)
        )

    def test_cat_samples_keep_sample_owned_time_taxonomy_and_coordinate_refusals(
        self,
    ) -> None:
        rows = tuple(
            row
            for row in build_species_curated_sample_rows("cat")
            if row.project_accession == "PRJEB81815"
        )

        self.assertEqual(len(rows), 87)
        self.assertEqual(
            Counter(row.inclusion_status for row in rows),
            {"site_curated": 84, "sample_context_blocked": 3},
        )
        self.assertEqual(
            sum(bool(row.latitude_text and row.longitude_text) for row in rows), 56
        )
        self.assertTrue(
            all(
                row.latitude_text == row.longitude_text == ""
                for row in rows
                if row.coordinate_basis == "withheld_sample_coordinate"
            )
        )
        self.assertTrue(all(row.time_start_bp is None for row in rows))
        self.assertTrue(all(row.time_end_bp is None for row in rows))
        self.assertTrue(
            all("transect" not in row.site_label.casefold() for row in rows)
        )

    def test_locality_selection_requires_sample_owned_place_identity(
        self,
    ) -> None:
        locality_lead = AdnaProjectLocalityLead(
            project_accession="example",
            locality_text="Example Site",
            political_entity="Denmark",
            latitude_text="",
            longitude_text="",
            coordinate_basis="unresolved_location_state",
            chronology_text="",
            time_start_bp=None,
            time_end_bp=None,
            interpretation_note="source-backed site identity",
        )

        self.assertIsNone(
            _matching_locality_lead((locality_lead,), "Different Site", "")
        )
        self.assertIsNone(_matching_locality_lead((locality_lead,), "N/A", "N/A"))
        self.assertIsNone(
            _matching_locality_lead((locality_lead,), "Example Site", "Sweden")
        )
        with self.assertRaisesRegex(ValueError, "Multiple locality leads"):
            _matching_locality_lead((locality_lead, locality_lead), "Example Site", "")

    def test_placeholder_locality_does_not_inherit_an_unrelated_project_lead(
        self,
    ) -> None:
        connemara = next(
            row
            for row in build_species_curated_sample_rows("horse")
            if row.paper_native_sample_label == "Connemara_0004A"
        )

        self.assertEqual(connemara.inclusion_status, "sample_context_blocked")
        self.assertEqual(
            connemara.site_label,
            "site detail not yet extracted from tracked source support",
        )
        self.assertEqual(connemara.latitude_text, "")
        self.assertEqual(connemara.longitude_text, "")

    def test_species_curated_sample_rows_mark_comparator_context_explicitly(
        self,
    ) -> None:
        donkey_rows = build_species_curated_sample_rows("donkey")
        donkey = next(
            row for row in donkey_rows if row.project_accession == "PRJEB52849"
        )
        reindeer_rows = build_species_curated_sample_rows("reindeer")
        reindeer = next(
            row for row in reindeer_rows if row.project_accession == "PRJEB60484"
        )

        self.assertEqual(donkey.sample_basis, "project_accession_anchor")
        self.assertEqual(donkey.inclusion_status, "comparator_site_curated")
        self.assertEqual(reindeer.inclusion_status, "sample_context_blocked")
        self.assertIn("site and chronology extraction", reindeer.inclusion_note)


if __name__ == "__main__":
    unittest.main()
